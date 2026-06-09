"""Pure, network-free proxy parsing and bookkeeping helpers.

Everything in this module is deterministic and side-effect free (apart from the
explicit file writer), which makes it the natural home for unit tests.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Optional

# Supported proxy protocol schemes.
PROTOCOLS = ("http", "socks4", "socks5")

# Matches an IPv4 ``ip:port`` pair, optionally preceded by a scheme such as
# ``http://`` or ``socks5://``. Surrounding whitespace and trailing data (for
# example a country code emitted by some raw lists) are ignored.
_PROXY_RE = re.compile(
    r"""
    ^\s*
    (?:(?P<scheme>https?|socks[45])://)?   # optional scheme
    (?P<ip>
        (?:25[0-5]|2[0-4]\d|1?\d?\d)       # 0-255
        (?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}
    )
    [:\s]                                  # ip / port separator
    (?P<port>\d{1,5})                      # port
    """,
    re.VERBOSE,
)


def normalize_protocol(protocol: str) -> str:
    """Return a canonical, lowercased protocol or raise ``ValueError``."""
    proto = (protocol or "").strip().lower()
    if proto not in PROTOCOLS:
        raise ValueError(
            f"unsupported protocol {protocol!r}; expected one of {PROTOCOLS}"
        )
    return proto


def parse_proxy_line(line: str, default_protocol: str = "http") -> Optional[str]:
    """Extract a single ``scheme://ip:port`` proxy from one text line.

    Comment lines (starting with ``#``) and anything that does not contain a
    valid ``ip:port`` pair return ``None``. A scheme present in the line wins
    over ``default_protocol``.
    """
    if line is None:
        return None
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    match = _PROXY_RE.match(stripped)
    if not match:
        return None

    port = int(match.group("port"))
    if not 0 < port <= 65535:
        return None

    scheme = match.group("scheme") or default_protocol
    scheme = scheme.lower()
    # ``https`` proxies are addressed over the ``http`` scheme by clients.
    if scheme == "https":
        scheme = "http"
    if scheme not in PROTOCOLS:
        return None

    return f"{scheme}://{match.group('ip')}:{port}"


def parse_proxies(text: str, default_protocol: str = "http") -> List[str]:
    """Parse every proxy found in a blob of text, preserving first-seen order."""
    return dedupe(
        parse_proxy_line(line, default_protocol) for line in (text or "").splitlines()
    )


def dedupe(proxies: Iterable[Optional[str]]) -> List[str]:
    """Drop ``None`` and duplicate entries while preserving order."""
    seen = set()
    result: List[str] = []
    for proxy in proxies:
        if not proxy or proxy in seen:
            continue
        seen.add(proxy)
        result.append(proxy)
    return result


def filter_by_type(proxies: Iterable[str], proxy_type: str) -> List[str]:
    """Return only proxies whose scheme matches ``proxy_type`` (``all`` keeps all)."""
    if proxy_type == "all":
        return [p for p in proxies if p]
    proto = normalize_protocol(proxy_type)
    prefix = f"{proto}://"
    return [p for p in proxies if p and p.startswith(prefix)]


def write_proxies(path: str, proxies: Iterable[str], header: bool = True) -> int:
    """Write ``proxies`` (sorted, de-duplicated) to ``path``; return the count."""
    unique = sorted(dedupe(proxies))
    with open(path, "w", encoding="utf-8") as handle:
        if header:
            handle.write("# Auto-generated working-proxy list.\n")
            handle.write("# Lines may be added or removed manually.\n\n")
        for proxy in unique:
            handle.write(f"{proxy}\n")
    return len(unique)
