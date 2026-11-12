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
    def _tmp_tree(self, tmp: str) -> None:
        self._saved = rfcsync.ROOT, rfcsync.DIAGRAMS, rfcsync.FIGURES
        rfcsync.ROOT = Path(tmp)
        rfcsync.DIAGRAMS, rfcsync.FIGURES = Path(tmp) / "diagrams", Path(tmp) / "figures"
        rfcsync.DIAGRAMS.mkdir()
        rfcsync.FIGURES.mkdir()
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        rfcsync.ROOT, rfcsync.DIAGRAMS, rfcsync.FIGURES = self._saved

    def test_a_diagram_becomes_its_picture_and_a_link_to_its_text_version(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._tmp_tree(tmp)
            for slug in ("a-flow-3-parties", "a-flow-3-parties-2"):
                (rfcsync.FIGURES / f"{slug}.png").write_bytes(b"png")
            (rfcsync.DIAGRAMS / "a-flow-3-parties.mmd").write_text(
                "sequenceDiagram\n  accTitle: Only a locked copy leaves\n  accDescr: The desktop sends a locked copy.\n  A->>B: one\n")
            text = ("x\n&#91;embedded content: a flow · 3 parties\\]\ny\n"
                    "&#91;embedded content: a flow · 3 parties\\]\nz")
            missing: list[str] = []
            found: list[rfcsync.Diagram] = []
            md = rfcsync.to_diagrams(text, rfcsync.DiagramNames(), missing, appendix_href="13-appendix-b.md",
                                     chapter="07-how.md", heading="How it works", found=found)
            self.assertIn("<!-- diagram: a flow · 3 parties -->\n![Only a locked copy leaves](../figures/a-flow-3-parties.png)"
                          "\n\n*[Text version](13-appendix-b.md#a-flow-3-parties)*\n<!-- /diagram -->", md)
            # the second has a picture but no text version yet: no link, and it is reported
            self.assertIn("![a flow · 3 parties](../figures/a-flow-3-parties-2.png)\n<!-- /diagram -->", md)
            self.assertEqual(missing, ["diagrams/a-flow-3-parties-2.mmd"])
            self.assertEqual([d.slug for d in found], ["a-flow-3-parties", "a-flow-3-parties-2"])
            self.assertEqual(rfcsync.to_placeholders(md, rfcsync.DiagramNames(), appendix_href="13-appendix-b.md"), text)
            with self.assertRaises(ValueError):  # a block edited by hand is refused
                rfcsync.to_placeholders(md.replace("Text version", "Text"), rfcsync.DiagramNames(),
                                        appendix_href="13-appendix-b.md")
            appendix = rfcsync.appendix_text("B", found)
            self.assertTrue(appendix.startswith(rfcsync.APPENDIX_MARK + "\n# Appendix B. The diagrams as text\n"))
            self.assertIn('<a id="a-flow-3-parties"></a>\n\n## a flow · 3 parties\n\n*Only a locked copy leaves*\n\n'
                          "In [How it works](07-how.md). The desktop sends a locked copy.\n\n```mermaid\nsequenceDiagram", appendix)
            self.assertNotIn("a-flow-3-parties-2", appendix)

    def test_the_docs_figure_caption_stays_under_the_picture_and_carries_the_link(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._tmp_tree(tmp)
            (rfcsync.FIGURES / "create.png").write_bytes(b"png")
            (rfcsync.DIAGRAMS / "create.mmd").write_text("sequenceDiagram\n  accTitle: Born on the desktop\n")
            names = {"Figure 6.2. Create: a locked copy": "create"}
            text = ("&#91;embedded content: Figure 6.2. Create: a locked copy\\]\n\n"
                    "**Figure 6.2.** Create: a locked copy\n\nnext paragraph")
            md = rfcsync.to_diagrams(text, rfcsync.DiagramNames(names), [], appendix_href="13-b.md")
            self.assertEqual(md, "<!-- diagram: Figure 6.2. Create: a locked copy -->\n"
                                 "![Born on the desktop](../figures/create.png)\n\n"
                                 "**Figure 6.2.** Create: a locked copy · [Text version](13-b.md#create)\n"
                                 "<!-- /diagram -->\n\nnext paragraph")
            self.assertEqual(rfcsync.to_placeholders(md, rfcsync.DiagramNames(names), appendix_href="13-b.md"), text)

    def test_a_renumbered_section_keeps_its_file_name(self) -> None:
        section = rfcsync.Section(heading="5. The design on one page", body="")
        self.assertEqual(rfcsync.chapter_name(7, section), "07-the-design-on-one-page.md")
        self.assertEqual(rfcsync.chapter_name(13, rfcsync.Section("Appendix A. Single or multi-tenant", "")),
                         "13-appendix-a-single-or-multi-tenant.md")

    def test_a_diagram_without_a_picture_stays_a_placeholder_and_is_reported(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._tmp_tree(tmp)
            missing: list[str] = []
            text = "&#91;embedded content: nothing yet\\]"
            self.assertEqual(rfcsync.to_diagrams(text, rfcsync.DiagramNames(), missing), text)
            self.assertEqual(missing, ["figures/nothing-yet.png"])

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
