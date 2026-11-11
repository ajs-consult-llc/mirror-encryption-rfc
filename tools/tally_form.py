#!/usr/bin/env python3
"""The review-updates sign-up form in Tally, defined here and applied through Tally's API.

    python3 tools/tally_form.py create            # make the form; prints its id and link
    python3 tools/tally_form.py update <form id>  # make the live form match this file

The form asks for an email address and a consent tick, in plain words, and says what the
address is used for. tools/announce.py adds only sign-ups that ticked the box. The Tally key is
read from Secret Manager under the name in .announce.json, like every other credential here.

Email verification is off: it is a paid Tally feature, and the account is on the free plan.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

from announce import TALLY, Config, call, secret

NAME = "AI-Optimized Data Mirror RFC: review updates"  # the form's name inside Tally
DOC_TITLE = "Security Reference Architecture for AI-Optimized Data Mirrors (RFC)"
# The graphic, from a commit in the public repository: pinned, so the link cannot break.
IMAGE_URL = ("https://raw.githubusercontent.com/ajs-consult-llc/mirror-encryption-rfc/"
             "db85aa6057fbaa3e9b6fd6c4bfb764522305a604/assets/social/secure-message-mirror-banner.png")
IMAGE_ALT = ("AI-Optimized Data Mirror: your data, encrypted with your key, readable only by the AI "
             "you approve.")
LABEL = "Get review updates by email"
CONSENT = "Yes, send me review updates"
SMALL_PRINT = "Only for review updates. Never shared. Unsubscribe anytime."
BUTTON = "Keep me posted"
STYLES = {
    "theme": "CUSTOM",
    "color": {"background": "#ffffff", "text": "#1f2933", "accent": "#2f5f86",
              "buttonBackground": "#2f5f86", "buttonText": "#ffffff"},
    "direction": "ltr",
}
REVIEW = Path(__file__).resolve().parent / "review.json"  # the round's dates: one source


def block(kind: str, group: str, payload: dict) -> dict:
    uid = str(uuid.uuid4())
    return {"uuid": uid, "type": kind, "groupUuid": uid, "groupType": group, "payload": payload}


def blocks(site_url: str) -> list[dict]:
    """Short enough to fit one laptop screen: title, banner, one paragraph, the sign-up."""
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    details = (f"A request for comments (RFC) on a security reference architecture for AI-optimized "
               f"data mirrors: private copies of people's data that only the AI they approve can read. "
               f"Open for public comment until {review['closes']}. "
               f'<a href="{site_url}">Read the RFC</a>')
    return [
        block("FORM_TITLE", "TEXT", {"html": DOC_TITLE, "title": NAME, "button": {"label": BUTTON}}),
        block("IMAGE", "IMAGE", {"images": [{"name": "secure-message-mirror-banner.png", "url": IMAGE_URL}],
                                 "hasAltText": True, "altText": IMAGE_ALT}),
        block("TEXT", "TEXT", {"html": details}),
        block("TITLE", "QUESTION", {"html": LABEL}),
        block("INPUT_EMAIL", "INPUT_EMAIL", {"isRequired": True, "placeholder": "name@example.com",
                                             "requireVerification": False}),
        block("CHECKBOX", "CHECKBOXES", {"isRequired": True, "index": 0, "isFirst": True,
                                         "isLast": True, "text": CONSENT}),
        block("TEXT", "TEXT", {"html": f'<span style="color: #6b7785">{SMALL_PRINT}</span>'}),
    ]


def main(argv: list[str]) -> int:
    cfg = Config.load()
    key = secret(cfg, cfg.tally_secret)
    if argv[1:] == ["create"]:
        made = call("POST", f"{TALLY}/forms", key,
                    {"status": "PUBLISHED", "blocks": blocks(cfg.site_url), "settings": {"styles": STYLES}})
        print(f"form {made.get('id')}: https://tally.so/r/{made.get('id')}")
        return 0
    if len(argv) == 3 and argv[1] == "update":
        call("PATCH", f"{TALLY}/forms/{argv[2]}", key,
             {"name": NAME, "status": "PUBLISHED", "blocks": blocks(cfg.site_url), "settings": {"styles": STYLES}})
        print(f"updated https://tally.so/r/{argv[2]}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
