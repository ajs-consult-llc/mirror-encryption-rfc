#!/usr/bin/env python3
"""Fill a Word file's table of contents so it works without a field update.

pandoc, and Quarto which runs it, writes the table of contents as an EMPTY
Word field marked dirty: Word fills it only if the reader accepts an update
when opening the file, Word on the web and on phones never do, and Google
Docs imports it as nothing at all. The headings carry no bookmarks either,
so there is nothing for a link to point at.

This rewrites the file in place:

1. a bookmark on every heading down to ``--depth``;
2. one entry per heading inside the TOC field, each a link to its bookmark,
   styled ``TOC1``..``TOC3`` (the styles are added if the file lacks them);
3. the field's dirty flag removed, so Word shows the entries as they are.

Word can still rebuild the field (right-click, Update Field) to add page
numbers. Standard library only; the XML is edited as text so every
namespace prefix Word depends on survives untouched.

    python3 tools/docx_toc.py _book/*.docx
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.dom import minidom

DOC = "word/document.xml"
STYLES = "word/styles.xml"
HEADING = re.compile(
    r'<w:p>(?P<ppr><w:pPr>(?:(?!</w:pPr>).)*?<w:pStyle w:val="Heading(?P<level>[1-9])"\s*/>(?:(?!</w:pPr>).)*?</w:pPr>)'
    r'(?P<rest>(?:(?!</w:p>).)*?)</w:p>',
    re.S,
)
TOC_FIELD = re.compile(
    r'<w:p><w:r><w:fldChar w:fldCharType="begin"(?: w:dirty="true")?\s*/>'
    r'<w:instrText xml:space="preserve">(?P<instr>TOC [^<]*)</w:instrText>'
    r'<w:fldChar w:fldCharType="separate"\s*/><w:fldChar w:fldCharType="end"\s*/></w:r></w:p>'
)
TOC_STYLES = "".join(
    f'<w:style w:type="paragraph" w:styleId="TOC{n}"><w:name w:val="toc {n}"/><w:basedOn w:val="Normal"/>'
    f'<w:next w:val="Normal"/><w:uiPriority w:val="39"/><w:unhideWhenUsed/>'
    f'<w:pPr><w:spacing w:before="0" w:after="60"/><w:ind w:left="{(n - 1) * 240}"/></w:pPr></w:style>'
    for n in (1, 2, 3)
)


def heading_text(rest: str) -> str:
    """The heading's words, still XML-escaped, so they can go straight into a <w:t>."""
    return "".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", rest))


def fill(document: str, depth: int) -> tuple[str, int]:
    field = TOC_FIELD.search(document)
    if not field:
        raise ValueError("no empty TOC field found: render with toc: true, or the file is already filled")
    ids = [int(i) for i in re.findall(r'<w:bookmarkStart w:id="(\d+)"', document)]
    next_id = max(ids, default=0) + 1
    entries: list[tuple[int, str, str]] = []

    def bookmark(m: re.Match[str]) -> str:
        nonlocal next_id
        level = int(m.group("level"))
        text = heading_text(m.group("rest"))
        if level > depth or not text.strip():
            return m.group(0)
        name = f"_TocRfc{len(entries) + 1:04d}"
        entries.append((level, name, text))
        bid = next_id
        next_id += 1
        return (f'<w:p>{m.group("ppr")}<w:bookmarkStart w:id="{bid}" w:name="{name}"/>'
                f'{m.group("rest")}<w:bookmarkEnd w:id="{bid}"/></w:p>')

    # Headings after the field only: the field must not list itself or what precedes it.
    head, tail = document[: field.end()], document[field.end():]
    tail = HEADING.sub(bookmark, tail)
    if not entries:
        raise ValueError("no headings found after the table of contents")

    def entry(level: int, name: str, text: str, first: bool) -> str:
        begin = ""
        if first:
            begin = ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
                     f'<w:r><w:instrText xml:space="preserve">{field.group("instr")}</w:instrText></w:r>'
                     '<w:r><w:fldChar w:fldCharType="separate"/></w:r>')
        return (f'<w:p><w:pPr><w:pStyle w:val="TOC{min(level, 3)}"/></w:pPr>{begin}'
                f'<w:hyperlink w:anchor="{name}" w:history="1"><w:r>'
                f'<w:t xml:space="preserve">{text}</w:t></w:r></w:hyperlink></w:p>')

    body = "".join(entry(lv, nm, tx, i == 0) for i, (lv, nm, tx) in enumerate(entries))
    body += '<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>'
    head = head[: field.start()] + body
    return head + tail, len(entries)


def process(path: Path, depth: int) -> int:
    with zipfile.ZipFile(path) as z:
        items = [(info, z.read(info.filename)) for info in z.infolist()]
    files = {info.filename: data for info, data in items}
    document, count = fill(files[DOC].decode("utf-8"), depth)
    styles = files[STYLES].decode("utf-8")
    if 'w:styleId="TOC1"' not in styles:
        styles = styles.replace("</w:styles>", TOC_STYLES + "</w:styles>")
    for name, text in ((DOC, document), (STYLES, styles)):
        minidom.parseString(text.encode("utf-8"))  # refuse to write XML that does not parse
        files[name] = text.encode("utf-8")
    tmp = path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        for info, _ in items:
            out.writestr(info, files[info.filename])
    tmp.replace(path)
    return count


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("docx", nargs="+", type=Path)
    ap.add_argument("--depth", type=int, default=3, help="deepest heading level listed (default 3)")
    args = ap.parse_args(argv)
    for path in args.docx:
        print(f"{path}: {process(path, args.depth)} entries, each linked to its heading")
    return 0


if __name__ == "__main__":
    sys.exit(main())
