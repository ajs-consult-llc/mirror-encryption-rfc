#!/usr/bin/env python3
"""Turn the publish workflow's working copy into a Quarto book. Never run on a tree you will commit.

    python3 tools/quarto_build_copy.py

The repository keeps plain .md with ```mermaid fences, which GitHub shows and draws on its own
pages. Quarto draws diagrams only from ```{mermaid} cells, and only in .qmd files, so this
script rewrites the build copy:

- every fence becomes a Quarto cell, and a diagram's front-matter title becomes the figure's
  caption (Mermaid centres a sequence diagram's title badly and cuts long ones off; a caption
  wraps), shown above the figure by _quarto.yml;
- index.md and chapters/*.md become .qmd, and _quarto.yml's book list follows;
- an appendix chapter's heading drops its own "Appendix A. ", which Quarto adds itself;
- a link to another chapter's .md points at its .qmd, which Quarto turns into the page's link;
- a diagram's picture keeps its title as alt text only, since the picture shows the title itself.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^```mermaid\n(?P<body>.*?)^```$", re.M | re.S)
TITLE = re.compile(r'\A---\ntitle: "(?P<title>[^"\n]+)"\n---\n')
APPENDIX_HEADING = re.compile(r"\A(<!--[^\n]*-->\n)?# Appendix [A-Z]\. ")
PICTURE = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<src>(?:\.\./)?figures/[^)\s]+\.png)\)$", re.M)
CHAPTER_LINK = re.compile(r"\]\(((?:chapters/)?\d{2}-[a-z0-9-]+)\.md(#[^)]*)?\)")


def cell(body: str) -> str:
    """One Mermaid fence as a Quarto cell, its front-matter title moved into fig-cap."""
    m = TITLE.match(body)
    if m:
        body = f'%%| fig-cap: "{m.group("title")}"\n' + body[m.end():]
    return "```{mermaid}\n" + body + "```"


def convert(text: str) -> str:
    """Fences become Quarto cells, and links between chapters follow them to .qmd."""
    text = FENCE.sub(lambda m: cell(m.group("body")), text)
    # A picture exported from the doc already carries its title; as alt text only, Quarto does not
    # repeat it as a caption above the picture.
    text = PICTURE.sub(lambda m: f'![]({m.group("src")}){{fig-alt="{m.group("alt")}"}}', text)
    return CHAPTER_LINK.sub(lambda m: f"]({m.group(1)}.qmd{m.group(2) or ''})", text)


def appendix_chapters(quarto_yml: str) -> list[str]:
    tail = quarto_yml.split("  appendices:", 1)
    return re.findall(r"^    - (\S+\.md)$", tail[1], re.M) if len(tail) == 2 else []


def main(root: Path = ROOT) -> int:
    yml_path = root / "_quarto.yml"
    yml = yml_path.read_text(encoding="utf-8")
    appendices = set(appendix_chapters(yml))
    for md in [root / "index.md", *sorted((root / "chapters").glob("*.md"))]:
        rel = md.relative_to(root).as_posix()
        text = convert(md.read_text(encoding="utf-8"))
        if rel in appendices:
            text = APPENDIX_HEADING.sub(lambda m: (m.group(1) or "") + "# ", text, count=1)
        md.with_suffix(".qmd").write_text(text, encoding="utf-8")
        md.unlink()
    yml_path.write_text(re.sub(r"^(    - (?:index|chapters/\S+))\.md$", r"\1.qmd", yml, flags=re.M), encoding="utf-8")
    print(f"build copy: {len(list((root / 'chapters').glob('*.qmd'))) + 1} .qmd files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
