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

    def test_a_chapter_gets_the_take_part_box_under_its_heading(self) -> None:
        out = qb.with_box("# 6. How it works\n\nText.", "chapters/08-how-it-works.md")
        self.assertTrue(out.startswith("# 6. How it works\n\n```{=html}\n<div class=\"rfc-take-part\" id=\"rfc-take-part\">"))
        self.assertIn('id="rfc-suggest"', out)
        self.assertIn("/edit/main/chapters/08-how-it-works.md", out)
        self.assertTrue(out.endswith("```\n\n\nText."))

    def test_source_links_go_back_to_the_repositorys_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "chapters").mkdir()
            (root / "_book" / "chapters").mkdir(parents=True)
            (root / "chapters" / "08-how.qmd").write_text("# How\n")
            (root / "chapters" / "14-appendix-b.qmd").write_text(qb.GENERATED_MARK + " -->\n# B\n")
            base = f"https://github.com/{qb.REPO}"
            page = (f'<a href="{base}/edit/main/chapters/08-how.qmd">e</a><a href="{base}/blob/main/chapters/08-how.qmd">v</a>'
                    f'<a href="{base}/edit/main/chapters/14-appendix-b.qmd">g</a><a href="{base}/edit/main/updates.qmd">u</a>'
                    f'<a href="{base}/edit/main/index.qmd">i</a>')
            (root / "_book" / "chapters" / "x.html").write_text(page)
            qb.after_render(root)
            out = (root / "_book" / "chapters" / "x.html").read_text()
            self.assertIn(f"{base}/edit/main/chapters/08-how.md", out)
            self.assertIn(f"{base}/blob/main/chapters/08-how.md", out)
            self.assertIn(f"{base}/tree/main/diagrams", out)
            self.assertIn(f"{base}/releases", out)
            self.assertIn(f"{base}/edit/main/index.md", out)
            self.assertNotIn(".qmd", out)

    def test_grouped_and_labelled_book_entries_follow_the_qmd(self) -> None:
        yml = ("  chapters:\n    - text: \"Home\"\n      href: index.md\n    - part: \"About\"\n      chapters:\n"
               "        - updates.qmd\n        - chapters/01-a.md\n    - chapters/02-b.md\n")
        self.assertEqual(qb.BOOK_ENTRY.sub(r"\1.qmd", yml),
                         yml.replace("index.md", "index.qmd").replace("01-a.md", "01-a.qmd").replace("02-b.md", "02-b.qmd"))

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
            appendix = (root / "chapters" / "02-appendix-a-b.qmd").read_text()
            self.assertTrue(appendix.startswith("# Single or multi-tenant\n"))
            yml = (root / "_quarto.yml").read_text()
            self.assertIn("    - index.qmd\n", yml)
            self.assertIn("    - chapters/02-appendix-a-b.qmd\n", yml)
            self.assertNotIn(".md\n", yml)


if __name__ == "__main__":
    unittest.main()
