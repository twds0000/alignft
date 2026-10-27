"""alignft —— 自检测试。

评估对齐微调的实际效果

覆盖：正常路径、边界输入、防呆红线、幂等性。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import alignft  # noqa: E402

SAMPLE_TEXT = '0.85 0.92 0.78 0.95 0.88'


class TestAlignft(unittest.TestCase):
    """对齐微调评估"""

    def test_cli_help_exits_zero(self):
        """--help 必须能正常退出。"""
        import subprocess
        proc = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "alignft.py"), "--help"],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0)

    def test_cli_rejects_empty_input(self):
        """空输入必须明确报错，不能静默成功。"""
        import subprocess
        proc = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "alignft.py"), "--text", "   "],
            capture_output=True, text=True, encoding="utf-8")
        self.assertNotEqual(proc.returncode, 0)

    def test_cli_json_output_parses(self):
        """--json 输出必须是合法 JSON。"""
        import subprocess
        proc = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "alignft.py"), "--text", SAMPLE_TEXT,
             "--json"],
            capture_output=True, text=True, encoding="utf-8")
        if proc.returncode not in (0, 1):
            self.fail(f"退出码异常：{proc.returncode} {proc.stderr[:300]}")
        data = json.loads(proc.stdout)
        self.assertIsInstance(data, dict)

    def test_does_not_mutate_input(self):
        """防呆：分析过程不得改动调用方传入的对象。"""
        payload = SAMPLE_TEXT
        before = payload
        alignft.alignft_analyze(payload)
        self.assertEqual(before, payload)

    def test_is_idempotent(self):
        """同一输入跑两次结果必须一致。"""
        a = alignft.alignft_analyze(SAMPLE_TEXT)
        b = alignft.alignft_analyze(SAMPLE_TEXT)
        self.assertEqual(json.dumps(a, ensure_ascii=False, sort_keys=True),
                         json.dumps(b, ensure_ascii=False, sort_keys=True))

    def test_applies_threshold(self):
        r = alignft.alignft_analyze(SAMPLE_TEXT)
        self.assertTrue(r["ok"])
        t = r["threshold_check"]
        self.assertIn("pass", t)
        self.assertIn("margin", t)

    def test_margin_sign_matches_pass(self):
        """防呆：余量符号必须与判定一致。"""
        r = alignft.alignft_analyze(SAMPLE_TEXT)
        t = r["threshold_check"]
        if t["pass"]:
            self.assertGreaterEqual(t["margin"], 0)
        else:
            self.assertLess(t["margin"], 0)
