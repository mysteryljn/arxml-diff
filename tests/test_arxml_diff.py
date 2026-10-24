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
if __name__=="__main__": unittest.main()
