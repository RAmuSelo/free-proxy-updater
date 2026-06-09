"""Command-line interface for free-proxy-updater."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List, Optional, Sequence

from . import __version__
from .core import filter_by_type, write_proxies
from .sources import gather_proxies
from .validate import validate_proxies


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(
        prog="free-proxy-updater",
        description=(
            "Scrape public free-proxy lists (HTTP/SOCKS), validate them in "
            "parallel, and write the working ones to a file."
        ),
    )
    parser.add_argument(
        "--type",
        choices=["http", "socks4", "socks5", "all"],
        default="all",
        help="Proxy protocol to collect (default: all).",
    )
    parser.add_argument(
        "--out",
        default="proxies.txt",
        help="Output file for working proxies (default: proxies.txt).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=7.0,
        help="Per-request timeout in seconds (default: 7.0).",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=100,
        help="Maximum parallel workers for validation (default: 100).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and validate but do not write the output file.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (INFO-level) logging.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute the pipeline described by ``args``. Returns a process exit code."""
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    collected = gather_proxies(
        proxy_type=args.type,
        timeout=args.timeout,
        max_workers=args.max_workers,
    )
    collected = filter_by_type(collected, args.type)

    if not collected:
        print("No proxies collected from any source.", file=sys.stderr)
        return 1

    print(f"Collected {len(collected)} candidate proxies; validating...")
    working = validate_proxies(
        collected,
        timeout=args.timeout,
        max_workers=args.max_workers,
    )

    print(f"{len(working)} working proxies found.")

    if args.dry_run:
        print("Dry run: output file not written.")
        for proxy in working:
            print(proxy)
        return 0

    if not working:
        print("No working proxies; output file not written.", file=sys.stderr)
        return 1

    count = write_proxies(args.out, working)
    print(f"Wrote {count} proxies to {args.out}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point. Parses ``argv`` (defaults to ``sys.argv``) and runs."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
