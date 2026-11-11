"""Tests for tools/docx_toc.py on the XML shape pandoc writes."""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import docx_toc  # noqa: E402

FIELD = ('<w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true" />'
         '<w:instrText xml:space="preserve">TOC \\o &quot;1-3&quot; \\h \\z \\u</w:instrText>'
         '<w:fldChar w:fldCharType="separate" /><w:fldChar w:fldCharType="end" /></w:r></w:p>')


def heading(level: int, text: str) -> str:
    return (f'<w:p><w:pPr><w:pStyle w:val="Heading{level}" /></w:pPr>'
            f'<w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>')


DOCUMENT = "<w:body>" + FIELD + heading(2, "1. Scope &amp; goals") + heading(3, "1.1 Detail") + heading(4, "Too deep") + "</w:body>"


class Fill(unittest.TestCase):
    def test_every_entry_links_to_a_bookmark_on_its_heading(self) -> None:
        out, count = docx_toc.fill(DOCUMENT, depth=3)
        self.assertEqual(count, 2)
        anchors = re.findall(r'w:anchor="([^"]+)"', out)
        marks = re.findall(r'w:bookmarkStart w:id="\d+" w:name="([^"]+)"', out)
        self.assertEqual(anchors, marks)
        self.assertIn("1. Scope &amp; goals</w:t></w:r></w:hyperlink>", out)  # escaping kept as is

    def test_the_field_is_no_longer_dirty_and_still_one_field(self) -> None:
        out, _ = docx_toc.fill(DOCUMENT, depth=3)
        self.assertNotIn("w:dirty", out)
        self.assertEqual(out.count('w:fldCharType="begin"'), 1)
        self.assertEqual(out.count('w:fldCharType="end"'), 1)

    def test_depth_limits_the_entries(self) -> None:
        _, count = docx_toc.fill(DOCUMENT, depth=2)
        self.assertEqual(count, 1)

    def test_a_filled_file_is_refused(self) -> None:
        out, _ = docx_toc.fill(DOCUMENT, depth=3)
        with self.assertRaises(ValueError):
            docx_toc.fill(out, depth=3)


if __name__ == "__main__":
    unittest.main()
