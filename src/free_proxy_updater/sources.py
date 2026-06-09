"""Free-proxy source fetchers.

Each fetcher downloads a publicly available list and returns raw text, which is
then parsed by :mod:`free_proxy_updater.core`. ``requests`` is imported lazily
inside :func:`_get` so that importing this module (and running the test suite)
never requires the network or the dependency to be installed.

Only well-known, publicly published free-proxy aggregators are referenced. No
private or paid endpoints are included.
"""

from __future__ import annotations

import concurrent.futures
import logging
from typing import Dict, List, Tuple

from .core import dedupe, parse_proxies

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

# Public raw text lists, keyed by protocol. These are community-maintained,
# openly published aggregators of free proxies.
RAW_SOURCES: Dict[str, Tuple[str, ...]] = {
    "http": (
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-LIST/master/http.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    ),
    "socks4": (
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-LIST/master/socks4.txt",
    ),
    "socks5": (
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-LIST/master/socks5.txt",
    ),
}


def _get(url: str, timeout: float) -> str:
    """Fetch ``url`` and return the body text. ``requests`` is imported lazily."""
    import requests  # local import keeps module import network/dependency free

    response = requests.get(url, headers=_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def fetch_raw_source(url: str, protocol: str, timeout: float = 10.0) -> List[str]:
    """Fetch a single raw list and parse it into ``scheme://ip:port`` proxies."""
    try:
        logger.info("Fetching %s proxies from %s", protocol.upper(), url)
        text = _get(url, timeout)
    except Exception as exc:  # network errors must not abort the whole run
        logger.warning("Failed to fetch %s: %s", url, exc)
        return []
    proxies = parse_proxies(text, default_protocol=protocol)
    logger.info("Parsed %d proxies from %s", len(proxies), url)
    return proxies


def iter_sources(proxy_type: str) -> List[Tuple[str, str]]:
    """Return ``(url, protocol)`` pairs to fetch for the requested type."""
    protocols = list(RAW_SOURCES) if proxy_type == "all" else [proxy_type]
    pairs: List[Tuple[str, str]] = []
    for proto in protocols:
        for url in RAW_SOURCES.get(proto, ()):  # unknown types yield nothing
            pairs.append((url, proto))
    return pairs


def gather_proxies(
    proxy_type: str = "all",
    timeout: float = 10.0,
    max_workers: int = 10,
) -> List[str]:
    """Fetch every relevant source in parallel and return de-duplicated proxies."""
    sources = iter_sources(proxy_type)
    if not sources:
        return []

    collected: List[str] = []
    workers = max(1, min(max_workers, len(sources)))
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=workers, thread_name_prefix="fetch"
    ) as executor:
        futures = [
            executor.submit(fetch_raw_source, url, proto, timeout)
            for url, proto in sources
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                collected.extend(future.result())
            except Exception as exc:  # defensive: a fetch task blew up
                logger.warning("A fetch task raised: %s", exc)

    unique = dedupe(collected)
    logger.info("Collected %d unique proxies", len(unique))
    return unique
