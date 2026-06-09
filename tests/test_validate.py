"""Tests for validation logic using an offline, injected checker."""

import os
import sys
import unittest

# Make the src-layout package importable without installation, from any cwd.
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from free_proxy_updater import validate


class SplitHostPortTests(unittest.TestCase):
    def test_with_scheme(self):
        self.assertEqual(
            validate.split_host_port("socks5://1.2.3.4:1080"),
            ("1.2.3.4", 1080),
        )

    def test_without_scheme(self):
        self.assertEqual(
            validate.split_host_port("9.9.9.9:3128"),
            ("9.9.9.9", 3128),
        )


class ValidateProxiesTests(unittest.TestCase):
    def test_only_working_proxies_returned_sorted(self):
        good = {"http://2.2.2.2:80", "http://1.1.1.1:80"}

        def fake_checker(proxy, timeout, test_url):
            return proxy if proxy in good else None

        result = validate.validate_proxies(
            [
                "http://1.1.1.1:80",
                "http://2.2.2.2:80",
                "http://3.3.3.3:80",  # not in `good`
            ],
            checker=fake_checker,
        )
        self.assertEqual(result, ["http://1.1.1.1:80", "http://2.2.2.2:80"])

    def test_checker_exceptions_are_swallowed(self):
        def boom(proxy, timeout, test_url):
            raise RuntimeError("checker failed")

        self.assertEqual(
            validate.validate_proxies(["http://1.1.1.1:80"], checker=boom),
            [],
        )

    def test_empty_input_returns_empty(self):
        self.assertEqual(validate.validate_proxies([]), [])

    def test_none_entries_filtered(self):
        def always_ok(proxy, timeout, test_url):
            return proxy

        self.assertEqual(
            validate.validate_proxies([None, "http://1.1.1.1:80", ""], checker=always_ok),
            ["http://1.1.1.1:80"],
        )


if __name__ == "__main__":
    unittest.main()
