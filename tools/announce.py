#!/usr/bin/env python3
"""Email each RFC update to its subscribers, through the operator's Resend account.

    python3 tools/announce.py sync [--dry-run]   # new Tally sign-ups -> the Resend list
    python3 tools/announce.py draft <tag>        # a GitHub release -> a Resend broadcast DRAFT
    python3 tools/announce.py send <broadcast>   # send a draft, only after the editor approves it

Posts are GitHub releases. The release is the one source: the site's Updates page, the
repository's feed and this email are all made from it, so they cannot disagree.

The rules this tool keeps:

* Credentials come from Secret Manager with the caller's own gcloud identity. They are never
  printed, passed as arguments, or written to disk.
* ``sync`` only ADDS addresses it has never seen. It never changes an existing contact, so
  anyone who unsubscribed stays unsubscribed. It adds only sign-ups that ticked the consent box,
  and it prints counts, never addresses.
* ``draft`` never sends. ``send`` is its own command, run only after the editor has read the
  draft in Resend and approved it.

Configuration lives in ``.announce.json`` at the repository root. It is not committed, because
it names internal infrastructure; ``announce.example.json`` shows its shape.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / ".announce.json"
RESEND = "https://api.resend.com"
TALLY = "https://api.tally.so"
GITHUB = "https://api.github.com"
# Resend's API sits behind Cloudflare, which refuses Python's default User-Agent with a bare
# 403 (error code 1010) that looks like a permissions problem. A browser UA avoids it.
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
UNSUBSCRIBE = "{{{RESEND_UNSUBSCRIBE_URL}}}"  # Resend replaces this per recipient


@dataclasses.dataclass(frozen=True)
class Config:
    gcp_project: str
    resend_secret: str
    tally_secret: str
    tally_form_id: str
    resend_audience_id: str
    sender: str
    repo: str
    site_url: str
    reply_to: str | None = None

    @classmethod
    def load(cls) -> "Config":
        if not CONFIG.exists():
            sys.exit(f"missing {CONFIG.name}: copy announce.example.json and fill it in")
        raw = json.loads(CONFIG.read_text(encoding="utf-8"))
        fields = {f.name for f in dataclasses.fields(cls)}
        unknown = set(raw) - fields
        if unknown:
            sys.exit(f"{CONFIG.name} has unknown keys: {sorted(unknown)}")
        return cls(**raw)


def secret(cfg: Config, name: str) -> str:
    r = subprocess.run(["gcloud", "secrets", "versions", "access", "latest",
                        "--secret", name, "--project", cfg.gcp_project],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"cannot read secret {name}: {r.stderr.strip()}")
    return r.stdout.strip()


def call(method: str, url: str, key: str | None, payload: object | None = None) -> dict:
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"{e.code} from {method} {url.split('?')[0]}: {(e.read() or b'').decode()[:300]}")


# --- sync: Tally sign-ups -> the Resend list ---------------------------------------------------

@dataclasses.dataclass(frozen=True)
class Signup:
    email: str
    consented: bool


def signups_from(pages: list[dict]) -> list[Signup]:
    """Each completed submission's email and consent, from Tally's submissions pages.

    The email question is the one of type INPUT_EMAIL. Consent is the checkbox question, if
    the form has one; a form without one cannot record consent, so nobody counts as consenting.
    """
    out: list[Signup] = []
    for page in pages:
        questions = page.get("questions", [])
        email_ids = {q["id"] for q in questions if q.get("type") == "INPUT_EMAIL"}
        consent_ids = {q["id"] for q in questions if q.get("type") in ("CHECKBOX", "CHECKBOXES")}
        for sub in page.get("submissions", []):
            if sub.get("isCompleted") is False:
                continue
            email, consent = None, False
            for r in sub.get("responses", []):
                if r.get("questionId") in email_ids and isinstance(r.get("answer"), str):
                    email = r["answer"].strip()
                elif r.get("questionId") in consent_ids:
                    consent = bool(r.get("answer"))
            if email and "@" in email:
                out.append(Signup(email=email, consented=consent and bool(consent_ids)))
    return out


def new_contacts(existing: set[str], signups: list[Signup]) -> list[str]:
    """Addresses to add: consented, never seen before (case-insensitive), each once."""
    seen = {e.lower() for e in existing}
    add: list[str] = []
    for s in signups:
        key = s.email.lower()
        if s.consented and key not in seen:
            seen.add(key)
            add.append(s.email)
    return add


def tally_pages(cfg: Config, key: str) -> list[dict]:
    pages, page = [], 1
    while True:
        body = call("GET", f"{TALLY}/forms/{cfg.tally_form_id}/submissions?page={page}", key)
        pages.append(body)
        if not body.get("hasMore"):
            return pages
        page += 1


def resend_contacts(cfg: Config, key: str) -> set[str]:
    emails: set[str] = set()
    after = None
    while True:
        q = f"?limit=100&after={urllib.parse.quote(after)}" if after else "?limit=100"
        body = call("GET", f"{RESEND}/audiences/{cfg.resend_audience_id}/contacts{q}", key)
        data = body.get("data", [])
        emails.update(c["email"] for c in data if c.get("email"))
        if not body.get("has_more") or not data:
            return emails
        after = data[-1]["id"]


def cmd_sync(cfg: Config, dry_run: bool) -> int:
    signups = signups_from(tally_pages(cfg, secret(cfg, cfg.tally_secret)))
    resend_key = secret(cfg, cfg.resend_secret)
    add = new_contacts(resend_contacts(cfg, resend_key), signups)
    declined = sum(1 for s in signups if not s.consented)
    print(f"{len(signups)} sign-ups, {declined} without consent, {len(add)} new to add")
    if dry_run:
        return 0
    for email in add:
        call("POST", f"{RESEND}/audiences/{cfg.resend_audience_id}/contacts", resend_key,
             {"email": email, "unsubscribed": False})
        time.sleep(0.6)  # Resend allows a few requests a second
    print(f"added {len(add)}")
    return 0


# --- draft and send: a GitHub release -> a Resend broadcast --------------------------------------

def email_html(cfg: Config, title: str, body_html: str, release_url: str) -> str:
    return (
        "<div style=\"font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;"
        "max-width:600px;margin:0 auto;line-height:1.55;color:#1d2731\">"
        f"<h1 style=\"font-size:22px;font-weight:600\">{title}</h1>{body_html}"
        f"<p><a href=\"{release_url}\">Read it on GitHub</a> · <a href=\"{cfg.site_url}\">The RFC</a></p>"
        "<hr style=\"border:0;border-top:1px solid #d9e0e7\">"
        "<p style=\"font-size:12px;color:#5f7183\">You get this because you signed up for review-window "
        "notices for the Cloud Data Mirror RFC. Your address is used for nothing else and never shared. "
        f"<a href=\"{UNSUBSCRIBE}\">Unsubscribe</a>.</p></div>"
    )


def markdown_to_html(markdown: str) -> str:
    r = subprocess.run(["pandoc", "-f", "gfm", "-t", "html"], input=markdown,
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"pandoc failed: {r.stderr.strip()}")
    return r.stdout


def cmd_draft(cfg: Config, tag: str) -> int:
    rel = call("GET", f"{GITHUB}/repos/{cfg.repo}/releases/tags/{urllib.parse.quote(tag)}", None)
    if rel.get("draft"):
        sys.exit("that release is still a draft on GitHub: publish it first")
    title = rel.get("name") or tag
    payload: dict[str, object] = {
        "audience_id": cfg.resend_audience_id,
        "from": cfg.sender,
        "subject": title,
        "name": f"RFC update {tag}",
        "html": email_html(cfg, title, markdown_to_html(rel.get("body") or ""), rel["html_url"]),
    }
    if cfg.reply_to:
        payload["reply_to"] = cfg.reply_to
    made = call("POST", f"{RESEND}/broadcasts", secret(cfg, cfg.resend_secret), payload)
    print(f"draft broadcast {made.get('id')}: \"{title}\". Read it in Resend, then approve the send.")
    return 0


def cmd_send(cfg: Config, broadcast_id: str) -> int:
    done = call("POST", f"{RESEND}/broadcasts/{broadcast_id}/send", secret(cfg, cfg.resend_secret), {})
    print(f"sent: {done.get('id', broadcast_id)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sync", help="add new, consented Tally sign-ups to the Resend list")
    s.add_argument("--dry-run", action="store_true", help="count only; change nothing")
    d = sub.add_parser("draft", help="make a Resend broadcast draft from a GitHub release")
    d.add_argument("tag")
    n = sub.add_parser("send", help="send a draft broadcast, after the editor approves it")
    n.add_argument("broadcast_id")
    args = ap.parse_args(argv)
    cfg = Config.load()
    if args.cmd == "sync":
        return cmd_sync(cfg, args.dry_run)
    if args.cmd == "draft":
        return cmd_draft(cfg, args.tag)
    return cmd_send(cfg, args.broadcast_id)


if __name__ == "__main__":
    sys.exit(main())
