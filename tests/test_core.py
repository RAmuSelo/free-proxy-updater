"""Tests for the pure parsing / bookkeeping logic in free_proxy_updater.core."""

import os
import sys
import tempfile
import unittest

# Make the src-layout package importable without installation, from any cwd.
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from free_proxy_updater import core


class ParseProxyLineTests(unittest.TestCase):
    def test_plain_ip_port_gets_default_scheme(self):
        self.assertEqual(
            core.parse_proxy_line("192.168.0.1:8080"),
            "http://192.168.0.1:8080",
        )

    def test_default_protocol_is_applied(self):
        self.assertEqual(
            core.parse_proxy_line("10.0.0.5:1080", default_protocol="socks5"),
            "socks5://10.0.0.5:1080",
        )

    def test_explicit_scheme_overrides_default(self):
        self.assertEqual(
            core.parse_proxy_line("socks4://1.2.3.4:9999", default_protocol="http"),
            "socks4://1.2.3.4:9999",
        )

    def test_https_scheme_is_normalized_to_http(self):
        self.assertEqual(
            core.parse_proxy_line("https://5.6.7.8:443"),
            "http://5.6.7.8:443",
        )

    def test_whitespace_and_trailing_data_ignored(self):
        # Some raw lists append a country code or use tabs.
        self.assertEqual(
            core.parse_proxy_line("  9.9.9.9\t3128 US "),
            "http://9.9.9.9:3128",
        )

    def test_comment_line_returns_none(self):
        self.assertIsNone(core.parse_proxy_line("# this is a comment"))

    def test_blank_line_returns_none(self):
        self.assertIsNone(core.parse_proxy_line("   "))

    def test_none_input_returns_none(self):
        self.assertIsNone(core.parse_proxy_line(None))

    def test_garbage_returns_none(self):
        self.assertIsNone(core.parse_proxy_line("not a proxy at all"))

    def test_invalid_octet_returns_none(self):
        self.assertIsNone(core.parse_proxy_line("999.1.1.1:80"))

    def test_out_of_range_port_returns_none(self):
        self.assertIsNone(core.parse_proxy_line("1.1.1.1:70000"))


class ParseProxiesTests(unittest.TestCase):
    def test_parses_and_dedupes_multiline_blob(self):
        blob = (
            "# header comment\n"
            "1.1.1.1:80\n"
            "2.2.2.2:8080\n"
            "1.1.1.1:80\n"          # duplicate
            "\n"
            "garbage line\n"
            "socks5://3.3.3.3:1080\n"
        )
        self.assertEqual(
            core.parse_proxies(blob),
            ["http://1.1.1.1:80", "http://2.2.2.2:8080", "socks5://3.3.3.3:1080"],
        )

    def test_empty_text_yields_empty_list(self):
        self.assertEqual(core.parse_proxies(""), [])


class DedupeTests(unittest.TestCase):
    def test_preserves_order_and_drops_none(self):
        self.assertEqual(
            core.dedupe(["a", None, "b", "a", "c", "b"]),
            ["a", "b", "c"],
        )


class FilterByTypeTests(unittest.TestCase):
    def setUp(self):
        self.proxies = [
            "http://1.1.1.1:80",
            "socks4://2.2.2.2:1080",
            "socks5://3.3.3.3:1080",
        ]

    def test_all_returns_everything(self):
        self.assertEqual(core.filter_by_type(self.proxies, "all"), self.proxies)

    def test_filters_single_type(self):
        self.assertEqual(
            core.filter_by_type(self.proxies, "socks5"),
            ["socks5://3.3.3.3:1080"],
        )

    def test_unknown_type_raises(self):
        with self.assertRaises(ValueError):
            core.filter_by_type(self.proxies, "ftp")


class NormalizeProtocolTests(unittest.TestCase):
    def test_normalizes_case_and_whitespace(self):
        self.assertEqual(core.normalize_protocol("  SOCKS5 "), "socks5")

    def test_rejects_unknown(self):
        with self.assertRaises(ValueError):
            core.normalize_protocol("gopher")


class WriteProxiesTests(unittest.TestCase):
    def test_writes_sorted_unique_with_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "proxies.txt")
            count = core.write_proxies(
                out,
                ["http://2.2.2.2:80", "http://1.1.1.1:80", "http://2.2.2.2:80"],
            )
            self.assertEqual(count, 2)
            with open(out, encoding="utf-8") as handle:
                content = handle.read()

        lines = content.splitlines()
        self.assertTrue(lines[0].startswith("#"))
        proxy_lines = [ln for ln in lines if ln and not ln.startswith("#")]
        self.assertEqual(proxy_lines, ["http://1.1.1.1:80", "http://2.2.2.2:80"])

    def test_write_without_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "p.txt")
            core.write_proxies(out, ["http://1.1.1.1:80"], header=False)
            with open(out, encoding="utf-8") as handle:
                content = handle.read()
        self.assertEqual(content, "http://1.1.1.1:80\n")


if __name__ == "__main__":
    unittest.main()
