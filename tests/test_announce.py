"""Tests for tools/announce.py: who gets added to the list, and who never does."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import announce  # noqa: E402

PAGE = {
    "questions": [
        {"id": "q-email", "type": "INPUT_EMAIL", "title": "Email"},
        {"id": "q-consent", "type": "CHECKBOX", "title": "Consent"},
    ],
    "submissions": [
        {"isCompleted": True, "responses": [{"questionId": "q-email", "answer": "a@example.com"},
                                            {"questionId": "q-consent", "answer": True}]},
        {"isCompleted": True, "responses": [{"questionId": "q-email", "answer": "no-consent@example.com"}]},
        {"isCompleted": False, "responses": [{"questionId": "q-email", "answer": "half@example.com"},
                                             {"questionId": "q-consent", "answer": True}]},
        {"isCompleted": True, "responses": [{"questionId": "q-email", "answer": " A@Example.com "},
                                            {"questionId": "q-consent", "answer": ["yes"]}]},
    ],
}


class Signups(unittest.TestCase):
    def test_incomplete_submissions_are_ignored(self) -> None:
        emails = [s.email for s in announce.signups_from([PAGE])]
        self.assertNotIn("half@example.com", emails)

    def test_consent_is_read_from_the_checkbox(self) -> None:
        by_email = {s.email: s.consented for s in announce.signups_from([PAGE])}
        self.assertTrue(by_email["a@example.com"])
        self.assertFalse(by_email["no-consent@example.com"])

    def test_a_form_without_a_consent_box_consents_nobody(self) -> None:
        page = {"questions": [PAGE["questions"][0]], "submissions": PAGE["submissions"][:1]}
        self.assertFalse(announce.signups_from([page])[0].consented)


class NewContacts(unittest.TestCase):
    def test_only_consented_and_unseen_addresses_each_once(self) -> None:
        add = announce.new_contacts(set(), announce.signups_from([PAGE]))
        self.assertEqual(add, ["a@example.com"])  # the second spelling is the same address

    def test_an_existing_contact_is_never_touched(self) -> None:
        # Someone who unsubscribed is still in the list; sync must not add or change them.
        add = announce.new_contacts({"A@EXAMPLE.COM"}, announce.signups_from([PAGE]))
        self.assertEqual(add, [])


if __name__ == "__main__":
    unittest.main()
