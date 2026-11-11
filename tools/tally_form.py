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

import sys
import uuid

from announce import TALLY, Config, call, secret

NAME = "Mirror Encryption RFC: review updates"  # the form's name inside Tally
TITLE = "Stay up to date on the review"
INTRO = ("We'll email you only when something happens: a review round opens, reaches its midpoint, "
         "closes, or its decisions are published. A handful of emails in all.")
LABEL = "Your email"
CONSENT = "Yes, send me review updates"
SMALL_PRINT = ("Used only for these updates. Never shared. Deleted when the review ends. "
               "Every email has an unsubscribe link.")
BUTTON = "Keep me posted"
STYLES = {
    "theme": "CUSTOM",
    "color": {"background": "#ffffff", "text": "#1f2933", "accent": "#2f5f86",
              "buttonBackground": "#2f5f86", "buttonText": "#ffffff"},
    "direction": "ltr",
}


def block(kind: str, group: str, payload: dict) -> dict:
    uid = str(uuid.uuid4())
    return {"uuid": uid, "type": kind, "groupUuid": uid, "groupType": group, "payload": payload}


def blocks() -> list[dict]:
    return [
        block("FORM_TITLE", "TEXT", {"html": TITLE, "title": NAME, "button": {"label": BUTTON}}),
        block("TEXT", "TEXT", {"html": INTRO}),
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
                    {"status": "PUBLISHED", "blocks": blocks(), "settings": {"styles": STYLES}})
        print(f"form {made.get('id')}: https://tally.so/r/{made.get('id')}")
        return 0
    if len(argv) == 3 and argv[1] == "update":
        call("PATCH", f"{TALLY}/forms/{argv[2]}", key,
             {"name": NAME, "status": "PUBLISHED", "blocks": blocks(), "settings": {"styles": STYLES}})
        print(f"updated https://tally.so/r/{argv[2]}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
