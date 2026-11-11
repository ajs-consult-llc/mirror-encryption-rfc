"""Tests for tools/updates_page.py: the Updates page made from releases."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import updates_page  # noqa: E402

SETTINGS = {"repo": "owner/repo", "signup_url": None}
POSTS = [
    {"tag_name": "round-1-open", "name": "Round 1 is open", "published_at": "2026-11-11T18:00:00Z",
     "html_url": "https://github.com/owner/repo/releases/tag/round-1-open",
     "body": "## Where\n\nComment in the review copy.\n```\n# not a heading\n```", "draft": False},
    {"tag_name": "later", "name": "Midpoint", "published_at": "2026-11-26T18:00:00Z",
     "html_url": "https://github.com/owner/repo/releases/tag/later", "body": "Half way.", "draft": False},
    {"tag_name": "secret", "name": "Not yet", "published_at": None, "html_url": "x", "body": "", "draft": True},
]


class Render(unittest.TestCase):
    def setUp(self) -> None:
        self.page = updates_page.render(SETTINGS, POSTS)

    def test_newest_first_and_drafts_left_out(self) -> None:
        self.assertLess(self.page.index("### Midpoint"), self.page.index("### Round 1 is open"))
        self.assertNotIn("Not yet", self.page)

    def test_post_headings_nest_below_the_post_title_but_code_is_untouched(self) -> None:
        self.assertIn("#### Where", self.page)
        self.assertIn("# not a heading", self.page)
        self.assertNotIn("### not a heading", self.page)

    def test_without_a_signup_link_the_page_says_so(self) -> None:
        self.assertIn("Email sign-up opens shortly.", self.page)
        with_link = updates_page.render({**SETTINGS, "signup_url": "https://tally.so/r/abc"}, [])
        self.assertIn("[Sign up](https://tally.so/r/abc)", with_link)
        self.assertIn("No updates yet.", with_link)

    def test_confirmation_is_claimed_only_when_the_form_verifies(self) -> None:
        self.assertNotIn("confirmed", self.page)
        verified = updates_page.render({**SETTINGS, "signup_verifies_email": True}, [])
        self.assertIn("confirmed before they are added", verified)

    def test_the_feed_is_linked(self) -> None:
        self.assertIn("https://github.com/owner/repo/releases.atom", self.page)


if __name__ == "__main__":
    unittest.main()
