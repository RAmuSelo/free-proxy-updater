"""Tests for argument parsing and the CLI pipeline (fully offline)."""

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

# Make the src-layout package importable without installation, from any cwd.
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from free_proxy_updater import cli


class ArgParsingTests(unittest.TestCase):
    def test_defaults(self):
        args = cli.build_parser().parse_args([])
        self.assertEqual(args.type, "all")
        self.assertEqual(args.out, "proxies.txt")
        self.assertEqual(args.timeout, 7.0)
        self.assertEqual(args.max_workers, 100)
        self.assertFalse(args.dry_run)

    def test_custom_args(self):
        args = cli.build_parser().parse_args(
            ["--type", "socks5", "--out", "x.txt", "--timeout", "3",
             "--max-workers", "5", "--dry-run"]
        )
        self.assertEqual(args.type, "socks5")
        self.assertEqual(args.out, "x.txt")
        self.assertEqual(args.timeout, 3.0)
        self.assertEqual(args.max_workers, 5)
        self.assertTrue(args.dry_run)

    def test_invalid_type_rejected(self):
        with self.assertRaises(SystemExit):
            cli.build_parser().parse_args(["--type", "ftp"])


class _Patch:
    """Context manager that swaps module-level callables on cli and restores them."""

    def __init__(self, **replacements):
        self.replacements = replacements
        self.original = {}

    def __enter__(self):
        for name, value in self.replacements.items():
            self.original[name] = getattr(cli, name)
            setattr(cli, name, value)
        return self

    def __exit__(self, *exc):
        for name, value in self.original.items():
            setattr(cli, name, value)


class CliPipelineTests(unittest.TestCase):
    def _patch_pipeline(self, collected, working):
        return _Patch(
            gather_proxies=lambda **kw: list(collected),
            validate_proxies=lambda proxies, **kw: list(working),
        )

    def test_writes_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.txt")
            with self._patch_pipeline(
                collected=["http://1.1.1.1:80", "http://2.2.2.2:80"],
                working=["http://1.1.1.1:80"],
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = cli.main(["--out", out, "--type", "http"])

            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(out))
            with open(out, encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("http://1.1.1.1:80", content)

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.txt")
            with self._patch_pipeline(
                collected=["http://1.1.1.1:80"],
                working=["http://1.1.1.1:80"],
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = cli.main(["--out", out, "--type", "http", "--dry-run"])

            self.assertEqual(rc, 0)
            self.assertFalse(os.path.exists(out))
            self.assertIn("http://1.1.1.1:80", buf.getvalue())
            self.assertIn("Dry run", buf.getvalue())

    def test_no_proxies_collected_returns_error(self):
        with self._patch_pipeline(collected=[], working=[]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = cli.main(["--type", "http"])
        self.assertEqual(rc, 1)

    def test_collected_but_none_working_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.txt")
            with self._patch_pipeline(
                collected=["http://1.1.1.1:80"],
                working=[],
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = cli.main(["--out", out, "--type", "http"])
            self.assertEqual(rc, 1)
            self.assertFalse(os.path.exists(out))

    def test_type_filter_applied_to_collected(self):
        # gather returns mixed schemes; --type http must drop the socks one
        # before validation, so validate only ever sees http proxies.
        seen = {}

        def fake_validate(proxies, **kw):
            seen["proxies"] = list(proxies)
            return list(proxies)

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.txt")
            with _Patch(
                gather_proxies=lambda **kw: [
                    "http://1.1.1.1:80",
                    "socks5://2.2.2.2:1080",
                ],
                validate_proxies=fake_validate,
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    cli.main(["--out", out, "--type", "http"])

        self.assertEqual(seen["proxies"], ["http://1.1.1.1:80"])


if __name__ == "__main__":
    unittest.main()
