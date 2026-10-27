import tempfile
import unittest
from pathlib import Path
from arxml_diff import diff_files, main

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

    def test_colliding_namespaces_do_not_shift_paths(self):
        """Adding a namespaced sibling must not relabel existing nodes."""
        with tempfile.TemporaryDirectory() as tmp:
            before=Path(tmp)/"before.xml"; after=Path(tmp)/"after.xml"
            before.write_text(
                '<ROOT xmlns:a="urn:a"><a:X><VALUE>A</VALUE></a:X></ROOT>',
                encoding="utf-8",
            )
            after.write_text(
                '<ROOT xmlns:a="urn:a" xmlns:b="urn:b">'
                '<b:X><VALUE>B</VALUE></b:X>'
                '<a:X><VALUE>A</VALUE></a:X></ROOT>',
                encoding="utf-8",
            )

            report=diff_files(before,after)

            self.assertEqual(report["removed"], [])
            self.assertEqual(report["changed"], [])
            self.assertTrue(any("@{urn:b}X" in path for path in report["added"]))
            self.assertTrue(all("@{urn:a}X" not in path for path in report["added"]))

    def test_qualified_sibling_does_not_shift_unqualified_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            before=Path(tmp)/"before.xml"; after=Path(tmp)/"after.xml"
            before.write_text("<ROOT><X><VALUE>A</VALUE></X></ROOT>", encoding="utf-8")
            after.write_text(
                '<ROOT xmlns:a="urn:a"><X><VALUE>A</VALUE></X>'
                '<a:X><VALUE>B</VALUE></a:X></ROOT>',
                encoding="utf-8",
            )

            report=diff_files(before,after)

            self.assertEqual(report["removed"], [])
            self.assertEqual(report["changed"], [])
            self.assertTrue(any("@{urn:a}X" in path for path in report["added"]))

    def test_deeply_nested_document_does_not_hit_recursion_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            before=Path(tmp)/"before.xml"; after=Path(tmp)/"after.xml"
            depth=1100
            before.write_text("<ROOT>" + ("<NODE>" * depth) + "before" + ("</NODE>" * depth) + "</ROOT>", encoding="utf-8")
            after.write_text("<ROOT>" + ("<NODE>" * depth) + "after" + ("</NODE>" * depth) + "</ROOT>", encoding="utf-8")

            report=diff_files(before,after)

            self.assertFalse(report["ok"])
            self.assertTrue(report["changed"])

    def test_cli_returns_failure_when_files_differ(self):
        with tempfile.TemporaryDirectory() as tmp:
            before=Path(tmp)/"before.xml"; after=Path(tmp)/"after.xml"
            before.write_text("<ROOT><VALUE>1</VALUE></ROOT>", encoding="utf-8")
            after.write_text("<ROOT><VALUE>2</VALUE></ROOT>", encoding="utf-8")
            self.assertEqual(main([str(before), str(after)]), 1)
            self.assertEqual(main([str(before), str(before)]), 0)

    def test_cli_reports_unknown_xml_encoding_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            before=Path(tmp)/"before.xml"; after=Path(tmp)/"after.xml"
            before.write_bytes(b'<?xml version="1.0" encoding="BOGUS"?><ROOT/>')
            after.write_text("<ROOT/>", encoding="utf-8")

            self.assertEqual(main([str(before), str(after)]), 2)

if __name__=="__main__": unittest.main()
