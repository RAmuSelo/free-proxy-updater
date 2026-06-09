"""free-proxy-updater: scrape and validate public free-proxy lists.

A small, dependency-light CLI/library that collects proxies (HTTP / SOCKS4 /
SOCKS5) from publicly available free-proxy sources, validates them in parallel,
and writes the working ones to a file.

Network access is performed lazily inside the relevant functions so the package
can be imported (and unit-tested) without touching the network.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
