"""Tests for tools/rfcsync.py: the round trip and the three-way plan."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import rfcsync  # noqa: E402

EXPORT = "\n".join([
    "# Title",
    "",
    "Opening line.",
    "",
    "## 1. First",
    "",
    "Para one.",
    "",
    "### 1.1 Sub",
    "",
    "&#91;embedded content: a diagram · 3 parties\\]",
    "",
    "```",
    "## not a heading",
    "```",
    "",
    "## Appendix A. Last",
    "",
    "Para two.",
    "",
])


class RoundTrip(unittest.TestCase):
    def test_figures_round_trip(self) -> None:
        text = "x\n&#91;embedded content: a diagram · 3 parties\\]\ny"
        swapped = rfcsync.to_figures(text)
        self.assertIn("![a diagram · 3 parties](figures/a-diagram-3-parties.png)", swapped)
        self.assertEqual(rfcsync.to_placeholders(swapped), text)

    def test_headings_shift_outside_fences_only(self) -> None:
        shifted = rfcsync.shift_headings("## A\n```\n## code\n```\n### B", -1)
        self.assertEqual(shifted, "# A\n```\n## code\n```\n## B")
        self.assertEqual(rfcsync.shift_headings(shifted, +1), "## A\n```\n## code\n```\n### B")

    def test_parse_keeps_every_byte(self) -> None:
        parsed = rfcsync.parse(EXPORT)
        rebuilt = "\n".join([f"# {parsed.title}", parsed.opening, *(s.body for s in parsed.sections)])
        self.assertEqual(rebuilt, EXPORT)
        self.assertEqual([s.is_appendix for s in parsed.sections], [False, True])

    def test_the_real_base_round_trips(self) -> None:
        base = rfcsync.SYNC / "base.md"
        if not base.exists():
            self.skipTest("no export recorded yet")
        self.assertEqual(rfcsync.join(), base.read_text(encoding="utf-8"))


class Plan(unittest.TestCase):
    BASE = "A.\n\nB.\n\nC.\n\nD.\n"

    def test_github_only_change_is_not_a_conflict(self) -> None:
        steps = rfcsync.plan(self.BASE, self.BASE, "A.\n\nB2.\n\nC.\n\nD.\n")
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]["op"], "replace")
        self.assertEqual(steps[0]["old"], ["B."])
        self.assertEqual(steps[0]["new"], ["B2."])
        self.assertFalse(steps[0]["conflict"])

    def test_same_block_changed_on_both_sides_is_a_conflict(self) -> None:
        steps = rfcsync.plan(self.BASE, "A.\n\nB-doc.\n\nC.\n\nD.\n", "A.\n\nB-gh.\n\nC.\n\nD.\n")
        self.assertTrue(steps[0]["conflict"])

    def test_change_elsewhere_in_the_doc_does_not_block(self) -> None:
        steps = rfcsync.plan(self.BASE, "A.\n\nB.\n\nC.\n\nD-doc.\n", "A2.\n\nB.\n\nC.\n\nD.\n")
        self.assertEqual(len(steps), 1)
        self.assertFalse(steps[0]["conflict"])

    def test_insert_carries_its_anchor(self) -> None:
        steps = rfcsync.plan(self.BASE, self.BASE, "A.\n\nB.\n\nNew.\n\nC.\n\nD.\n")
        self.assertEqual(steps[0]["op"], "insert")
        self.assertEqual(steps[0]["after"], "B.")
        self.assertEqual(steps[0]["new"], ["New."])


if __name__ == "__main__":
    unittest.main()
