"""
Automated unit tests for Operator ToolExecutor and Golden Rules.
"""

import os
import shutil
import tempfile
import unittest

from orchestrator.tools import ToolExecutor


class TestToolExecutor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.executor = ToolExecutor(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_write_and_read_file(self):
        res_w = self.executor.write_file("test.txt", "line 1\nline 2\nline 3\n")
        self.assertEqual(res_w["status"], "success")

        res_r = self.executor.read_file("test.txt", start_line=1, end_line=2)
        self.assertEqual(res_r["status"], "success")
        self.assertIn("1: line 1", res_r["content"])
        self.assertIn("2: line 2", res_r["content"])

    def test_patch_file_golden_rule(self):
        # 1. Create file with target
        self.executor.write_file("code.py", "def hello():\n    return 'old'\n")

        # 2. Patch target
        res_p = self.executor.patch_file("code.py", "return 'old'", "return 'new'")
        self.assertEqual(res_p["status"], "success")
        self.assertIn("Asserted exactly 1 match", res_p["verification"])

        # 3. Read back and double check
        res_r = self.executor.read_file("code.py")
        self.assertIn("return 'new'", res_r["content"])
        self.assertNotIn("return 'old'", res_r["content"])

    def test_patch_file_rejects_duplicate_matches(self):
        # Golden rule: must match exactly 1 time
        self.executor.write_file("dup.py", "x = 1\nx = 1\n")
        res_p = self.executor.patch_file("dup.py", "x = 1", "x = 2")
        self.assertEqual(res_p["status"], "error")
        self.assertIn("matched 2 times", res_p["error"])

    def test_run_command(self):
        res = self.executor.run_command("Write-Output 'VERIFIED_CMD'")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["stdout"], "VERIFIED_CMD")


if __name__ == "__main__":
    unittest.main()
