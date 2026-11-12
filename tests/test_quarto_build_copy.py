import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import quarto_build_copy as qb  # noqa: E402


class BuildCopy(unittest.TestCase):
    def test_a_titled_diagram_becomes_a_captioned_cell(self) -> None:
        md = 'x\n```mermaid\n---\ntitle: "Only a locked copy leaves"\n---\nsequenceDiagram\n  A->>B: hi\n```\ny'
        self.assertEqual(qb.convert(md),
                         'x\n```{mermaid}\n%%| fig-cap: "Only a locked copy leaves"\nsequenceDiagram\n  A->>B: hi\n```\ny')

    def test_an_untitled_diagram_only_changes_its_fence(self) -> None:
        self.assertEqual(qb.convert("```mermaid\nflowchart LR\n  a --> b\n```"),
                         "```{mermaid}\nflowchart LR\n  a --> b\n```")

    def test_a_diagram_picture_keeps_its_title_as_alt_text_not_a_caption(self) -> None:
        self.assertEqual(qb.convert("x\n![Only a locked copy leaves](../figures/create-4-parties.png)\ny"),
                         'x\n![](../figures/create-4-parties.png){fig-alt="Only a locked copy leaves"}\ny')
        other = "![A logo](assets/logo.png)"
        self.assertEqual(qb.convert(other), other)

    def test_other_code_is_left_alone(self) -> None:
        text = "```sh\ngit commit -S\n```"
        self.assertEqual(qb.convert(text), text)

    def test_the_tree_becomes_qmd_and_the_appendix_loses_its_own_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "chapters").mkdir()
            (root / "index.md").write_text("opening\n")
            (root / "chapters" / "01-a.md").write_text("# A\n```mermaid\nflowchart LR\n```\n")
            (root / "chapters" / "02-appendix-a-b.md").write_text("# Appendix A. Single or multi-tenant\n")
            (root / "_quarto.yml").write_text("book:\n  chapters:\n    - index.md\n    - updates.qmd\n"
                                              "    - chapters/01-a.md\n  appendices:\n    - chapters/02-appendix-a-b.md\n")
            qb.main(root)
            self.assertEqual(sorted(p.name for p in (root / "chapters").iterdir()), ["01-a.qmd", "02-appendix-a-b.qmd"])
            self.assertTrue((root / "index.qmd").exists() and not (root / "index.md").exists())
            self.assertIn("```{mermaid}", (root / "chapters" / "01-a.qmd").read_text())
            self.assertEqual((root / "chapters" / "02-appendix-a-b.qmd").read_text(), "# Single or multi-tenant\n")
            yml = (root / "_quarto.yml").read_text()
            self.assertIn("    - index.qmd\n", yml)
            self.assertIn("    - chapters/02-appendix-a-b.qmd\n", yml)
            self.assertNotIn(".md\n", yml)


if __name__ == "__main__":
    unittest.main()
