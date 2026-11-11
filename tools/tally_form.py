#!/usr/bin/env python3
"""Create the review-updates sign-up form in Tally, through Tally's API.

    python3 tools/tally_form.py create      # prints the form id and its public link

The form asks for an email address and a consent tick, and says plainly what the address is
used for. tools/announce.py adds only sign-ups that ticked the box. The Tally key is read from
Secret Manager under the name in .announce.json, like every other credential here.

After creating it: put the id in .announce.json (tally_form_id) and the link in
tools/review.json (signup_url).
"""
from __future__ import annotations

import sys
import uuid

from announce import TALLY, Config, call, secret

TITLE = "Mirror Encryption RFC: review updates"
INTRO = ("Get an email when a review round opens, at its midpoint, when it closes, and when "
         "decisions are published. Your address is used only for these notices, never shared, and "
         "deleted when the review ends. Every email has an unsubscribe link.")
CONSENT = "Email me notices about this RFC's review windows. I can unsubscribe at any time."


def block(kind: str, group: str, payload: dict) -> dict:
    uid = str(uuid.uuid4())
    return {"uuid": uid, "type": kind, "groupUuid": uid, "groupType": group, "payload": payload}


def body(verify_email: bool) -> dict:
    return {
        "status": "PUBLISHED",
        "blocks": [
            block("FORM_TITLE", "TEXT", {"html": TITLE, "title": TITLE}),
            block("TEXT", "TEXT", {"html": INTRO}),
            block("INPUT_EMAIL", "INPUT_EMAIL", {"isRequired": True, "placeholder": "you@example.com",
                                                 "requireVerification": verify_email}),
            block("CHECKBOX", "CHECKBOXES", {"isRequired": True, "index": 0, "isFirst": True,
                                             "isLast": True, "text": CONSENT}),
        ],
    }


def main(argv: list[str]) -> int:
    if argv[1:] != ["create"]:
        print(__doc__)
        return 2
    cfg = Config.load()
    made = call("POST", f"{TALLY}/forms", secret(cfg, cfg.tally_secret), body(verify_email=True))
    form_id = made.get("id")
    print(f"form {form_id}: https://tally.so/r/{form_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
