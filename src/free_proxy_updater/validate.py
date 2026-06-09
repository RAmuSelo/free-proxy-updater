"""Parallel proxy validation.

Validation is performed lazily: the heavy imports (``socket`` is stdlib but
``requests`` / ``PySocks`` are optional) live inside the worker functions so the
module imports cleanly without the network or third-party dependencies.

Two strategies are offered:

* :func:`check_tcp` - a cheap TCP connect to ``ip:port`` (no extra deps).
* :func:`check_proxy` - a real HTTP request *through* the proxy (needs
  ``requests``; SOCKS proxies additionally need ``PySocks``).

By default :func:`validate_proxies` uses the HTTP check, falling back to the TCP
check when ``requests`` is unavailable.
"""

from __future__ import annotations

import concurrent.futures
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_TEST_URL = "https://httpbin.org/ip"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def split_host_port(proxy: str) -> Tuple[str, int]:
    """Split ``scheme://ip:port`` (or ``ip:port``) into ``(host, port)``."""
    remainder = proxy.split("://", 1)[-1]
    host, _, port = remainder.rpartition(":")
    return host, int(port)


def check_tcp(proxy: str, timeout: float = 7.0) -> Optional[str]:
    """Return ``proxy`` if a raw TCP connection to its host:port succeeds."""
    import socket  # stdlib, imported lazily to keep the worker self-contained

    try:
        host, port = split_host_port(proxy)
    except (ValueError, IndexError):
        return None

    sock = None
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        return proxy
    except OSError:
        return None
    finally:
        if sock is not None:
            sock.close()


def check_proxy(
    proxy: str, timeout: float = 7.0, test_url: str = DEFAULT_TEST_URL
) -> Optional[str]:
    """Return ``proxy`` if an HTTP request routed through it succeeds.

    ``requests`` (and ``PySocks`` for SOCKS proxies) are imported lazily.
    """
    try:
        import requests  # local import keeps module import dependency free
    except ImportError:
        return check_tcp(proxy, timeout=timeout)

    proxies = {"http": proxy, "https": proxy}
    try:
        response = requests.get(
            test_url, proxies=proxies, timeout=timeout, headers=_HEADERS
        )
        response.raise_for_status()
        return proxy
    except Exception:  # any failure means the proxy is not usable
        return None


def validate_proxies(
    proxies: List[str],
    timeout: float = 7.0,
    max_workers: int = 100,
    test_url: str = DEFAULT_TEST_URL,
    checker=check_proxy,
) -> List[str]:
    """Validate ``proxies`` in parallel and return the working subset (sorted).

    ``checker`` is injectable so tests can pass a deterministic, offline stub.
    """
    proxies = [p for p in proxies if p]
    if not proxies:
        return []

    working: List[str] = []
    workers = max(1, min(max_workers, len(proxies)))
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=workers, thread_name_prefix="validate"
    ) as executor:
        future_map = {
            executor.submit(checker, proxy, timeout, test_url): proxy
            for proxy in proxies
        }
        for future in concurrent.futures.as_completed(future_map):
            try:
                result = future.result()
            except Exception:  # defensive: a checker raised unexpectedly
                result = None
            if result:
                working.append(result)

    logger.info("%d/%d proxies are working", len(working), len(proxies))
    return sorted(working)
