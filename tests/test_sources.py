"""Tests for source gathering with the network fetcher monkeypatched out."""

import os
import sys
import unittest

# Make the src-layout package importable without installation, from any cwd.
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from free_proxy_updater import sources


SYNTHETIC_HTML_LIKE = (
    "# free proxies\n"
    "1.1.1.1:80\n"
    "2.2.2.2:8080\n"
    "garbage\n"
    "1.1.1.1:80\n"  # duplicate within a source
)

SYNTHETIC_SOCKS = "3.3.3.3:1080\n4.4.4.4:1080\n"


class FetchRawSourceTests(unittest.TestCase):
    def test_parses_text_from_injected_getter(self):
        # Replace the only network-touching function with a synthetic one.
        original = sources._get
        sources._get = lambda url, timeout: SYNTHETIC_HTML_LIKE
        try:
            result = sources.fetch_raw_source("http://example/list.txt", "http")
        finally:
            sources._get = original

        self.assertEqual(
            result,
            ["http://1.1.1.1:80", "http://2.2.2.2:8080"],
        )

    def test_network_error_returns_empty_list(self):
        def boom(url, timeout):
            raise RuntimeError("no network in tests")

        original = sources._get
        sources._get = boom
        try:
            self.assertEqual(
                sources.fetch_raw_source("http://example/x.txt", "http"),
                [],
            )
        finally:
            sources._get = original


class IterSourcesTests(unittest.TestCase):
    def test_all_covers_every_protocol(self):
        pairs = sources.iter_sources("all")
        protocols = {proto for _url, proto in pairs}
        self.assertEqual(protocols, set(sources.RAW_SOURCES))

    def test_single_protocol_only(self):
        pairs = sources.iter_sources("socks5")
        self.assertTrue(pairs)
        self.assertTrue(all(proto == "socks5" for _url, proto in pairs))

    def test_unknown_type_yields_nothing(self):
        self.assertEqual(sources.iter_sources("nope"), [])


class GatherProxiesTests(unittest.TestCase):
    def test_dedupes_across_sources(self):
        # Map each fake URL to canned text; patch the getter accordingly.
        per_url = {}
        for url in sources.RAW_SOURCES["http"]:
            per_url[url] = SYNTHETIC_HTML_LIKE
        for url in sources.RAW_SOURCES["socks5"]:
            per_url[url] = SYNTHETIC_SOCKS

        original = sources._get
        sources._get = lambda url, timeout: per_url.get(url, "")
        try:
            http_only = sources.gather_proxies("http", max_workers=2)
        finally:
            sources._get = original

        # Two http sources both return the same two proxies -> deduped to 2.
        self.assertEqual(
            sorted(http_only),
            ["http://1.1.1.1:80", "http://2.2.2.2:8080"],
        )

    def test_no_sources_returns_empty(self):
        self.assertEqual(sources.gather_proxies("nope"), [])


if __name__ == "__main__":
    unittest.main()
