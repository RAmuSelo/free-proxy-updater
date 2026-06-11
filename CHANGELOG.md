# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- CONTRIBUTING.md
- CHANGELOG.md
- A more specific README (Why + Roadmap)

### Planned

- JSON output and one file per protocol (today: a single plain-text list).
- A source-health report — which sources actually returned working proxies.
- Optional latency / anonymity checks during validation.

## [0.1.0] - 2026-06-08

### Added

- Collect public free-proxy lists from well-known published aggregators and validate them in parallel.
- Supports `http`, `socks4`, `socks5`, or `all` via `--type`.
- Parallel validation through a real HTTP request per proxy, falling back to a cheap TCP connect when `requests` is not installed.
- De-duplicated, sorted output: one `scheme://ip:port` per line.
- CLI flags: `--out`, `--timeout`, `--max-workers`, `--dry-run`, `--verbose`/`-v`, `--version`.
- Library API: `gather_proxies`, `validate_proxies`, `write_proxies`.
- Lazy `requests` / `PySocks` imports, so the package imports and its tests run with no network access or third-party dependency.
- Stdlib unittest test suite.
- GitHub Actions CI.
- MIT license.

[Unreleased]: https://github.com/RAmuSelo/free-proxy-updater/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/RAmuSelo/free-proxy-updater/releases/tag/v0.1.0
