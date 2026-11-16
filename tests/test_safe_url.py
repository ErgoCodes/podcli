import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from utils.safe_url import assert_public_url


class SafeUrlTests(unittest.TestCase):
    def test_rejects_internal_and_non_http(self):
        for url in (
            "file:///etc/passwd",
            "ftp://example.com/x",
            "http://localhost/x",
            "http://127.0.0.1/x",
            "http://2130706433/x",
            "http://[::1]/x",
            "http://[::ffff:7f00:1]/x",
            "http://169.254.169.254/latest/meta-data",
            "http://10.0.0.1/x",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    assert_public_url(url)

    def test_accepts_public_literal(self):
        assert_public_url("http://8.8.8.8/x")


if __name__ == "__main__":
    unittest.main()
