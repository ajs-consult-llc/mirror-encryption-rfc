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
    def test_diagrams_round_trip_and_number_repeated_captions(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            saved = rfcsync.ROOT, rfcsync.DIAGRAMS
            rfcsync.ROOT = Path(tmp)
            rfcsync.DIAGRAMS = Path(tmp) / "diagrams"
            try:
                rfcsync.DIAGRAMS.mkdir()
                (rfcsync.DIAGRAMS / "a-flow-3-parties.mmd").write_text("sequenceDiagram\n  A->>B: one\n")
                (rfcsync.DIAGRAMS / "a-flow-3-parties-2.mmd").write_text("sequenceDiagram\n  A->>B: two\n")
                text = ("x\n&#91;embedded content: a flow · 3 parties\\]\ny\n"
                        "&#91;embedded content: a flow · 3 parties\\]\nz")
                missing: list[str] = []
                md = rfcsync.to_diagrams(text, rfcsync.DiagramNames(), missing)
                self.assertEqual(missing, [])
                self.assertIn("<!-- diagram: a flow · 3 parties -->\n```mermaid\nsequenceDiagram\n  A->>B: one\n```", md)
                self.assertIn("A->>B: two", md)
                self.assertEqual(rfcsync.to_placeholders(md, rfcsync.DiagramNames()), text)
                # Quarto's spelling of the fence is accepted too
                self.assertEqual(rfcsync.to_placeholders(md.replace("```mermaid", "```{mermaid}"), rfcsync.DiagramNames()), text)
                # editing the Mermaid inside a chapter is refused
                with self.assertRaises(ValueError):
                    rfcsync.to_placeholders(md.replace("one", "ONE"), rfcsync.DiagramNames())
            finally:
                rfcsync.ROOT, rfcsync.DIAGRAMS = saved

    def test_a_missing_diagram_stays_a_placeholder_and_is_reported(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            saved = rfcsync.ROOT, rfcsync.DIAGRAMS
            rfcsync.ROOT, rfcsync.DIAGRAMS = Path(tmp), Path(tmp) / "diagrams"
            try:
                missing: list[str] = []
                text = "&#91;embedded content: nothing yet\\]"
                self.assertEqual(rfcsync.to_diagrams(text, rfcsync.DiagramNames(), missing), text)
                self.assertEqual(missing, ["diagrams/nothing-yet.mmd"])
            finally:
                rfcsync.ROOT, rfcsync.DIAGRAMS = saved

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
