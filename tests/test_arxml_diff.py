import tempfile
import unittest
from pathlib import Path
from arxml_diff import diff_files

class ArxmlTests(unittest.TestCase):
    def test_changed_and_added(self):
        with tempfile.TemporaryDirectory() as tmp:
            before=Path(tmp)/"before.xml"; after=Path(tmp)/"after.xml"
            before.write_text("<ROOT><ITEM><SHORT-NAME>A</SHORT-NAME><V>1</V></ITEM></ROOT>",encoding="utf-8")
            after.write_text("<ROOT><ITEM><SHORT-NAME>A</SHORT-NAME><V>2</V></ITEM><ITEM><SHORT-NAME>B</SHORT-NAME><V>1</V></ITEM></ROOT>",encoding="utf-8")
            report=diff_files(before,after); self.assertFalse(report["ok"]); self.assertTrue(report["changed"]); self.assertTrue(report["added"])

    def test_named_sibling_insertion_does_not_shift_existing_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            before=Path(tmp)/"before.xml"; after=Path(tmp)/"after.xml"
            before.write_text(
                "<ROOT><ITEM><SHORT-NAME>A</SHORT-NAME><V>1</V></ITEM>"
                "<ITEM><SHORT-NAME>B</SHORT-NAME><V>2</V></ITEM></ROOT>",
                encoding="utf-8",
            )
            after.write_text(
                "<ROOT><ITEM><SHORT-NAME>NEW</SHORT-NAME><V>9</V></ITEM>"
                "<ITEM><SHORT-NAME>A</SHORT-NAME><V>1</V></ITEM>"
                "<ITEM><SHORT-NAME>B</SHORT-NAME><V>2</V></ITEM></ROOT>",
                encoding="utf-8",
            )

            report=diff_files(before,after)

            self.assertEqual(report["removed"], [])
            self.assertEqual(report["changed"], [])
            self.assertTrue(report["added"])
            self.assertTrue(all("/ITEM[NEW][0]" in path for path in report["added"]))

    def test_reordered_named_siblings_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            before=Path(tmp)/"before.xml"; after=Path(tmp)/"after.xml"
            before.write_text(
                "<ROOT><ITEM><SHORT-NAME>A</SHORT-NAME><V>1</V></ITEM>"
                "<ITEM><SHORT-NAME>B</SHORT-NAME><V>2</V></ITEM></ROOT>",
                encoding="utf-8",
            )
            after.write_text(
                "<ROOT><ITEM><SHORT-NAME>B</SHORT-NAME><V>2</V></ITEM>"
                "<ITEM><SHORT-NAME>A</SHORT-NAME><V>1</V></ITEM></ROOT>",
                encoding="utf-8",
            )

            report=diff_files(before,after)

            self.assertEqual(report["added"], [])
            self.assertEqual(report["removed"], [])
            self.assertEqual(report["changed"], [])
            self.assertEqual(report["order_changed"], ["ROOT"])
            self.assertFalse(report["ok"])

    def test_namespace_uri_change_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            before=Path(tmp)/"before.xml"; after=Path(tmp)/"after.xml"
            before.write_text(
                '<ROOT xmlns="urn:autosar:release:1"><ITEM><SHORT-NAME>A</SHORT-NAME></ITEM></ROOT>',
                encoding="utf-8",
            )
            after.write_text(
                '<ROOT xmlns="urn:autosar:release:2"><ITEM><SHORT-NAME>A</SHORT-NAME></ITEM></ROOT>',
                encoding="utf-8",
            )

            report=diff_files(before,after)

            self.assertFalse(report["ok"])
            self.assertIn("ROOT", report["changed"])

    def test_namespaced_attribute_change_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            before=Path(tmp)/"before.xml"; after=Path(tmp)/"after.xml"
            before.write_text(
                '<ROOT xmlns:x="urn:vendor:one"><ITEM x:mode="safe" /></ROOT>',
                encoding="utf-8",
            )
            after.write_text(
                '<ROOT xmlns:x="urn:vendor:two"><ITEM x:mode="safe" /></ROOT>',
                encoding="utf-8",
            )

            report=diff_files(before,after)

            self.assertFalse(report["ok"])
            self.assertIn("ROOT/ITEM[0]", report["changed"])

    def test_mixed_content_tail_text_change_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            before=Path(tmp)/"before.xml"; after=Path(tmp)/"after.xml"
            before.write_text(
                "<ROOT><DESC>prefix<EM>value</EM>after</DESC></ROOT>",
                encoding="utf-8",
            )
            after.write_text(
                "<ROOT><DESC>prefix<EM>value</EM>updated</DESC></ROOT>",
                encoding="utf-8",
            )

            report=diff_files(before,after)

            self.assertFalse(report["ok"])
            self.assertIn("ROOT/DESC[0]/EM[0]", report["changed"])

if __name__=="__main__": unittest.main()
