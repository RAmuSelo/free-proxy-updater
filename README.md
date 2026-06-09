# free-proxy-updater

[![Tests](https://github.com/RAmuSelo/free-proxy-updater/actions/workflows/tests.yml/badge.svg)](https://github.com/RAmuSelo/free-proxy-updater/actions/workflows/tests.yml)

A small, dependency-light command-line tool that **collects public free-proxy
lists** (HTTP / SOCKS4 / SOCKS5), **validates them in parallel**, and writes the
working ones to a plain-text file.

It is meant as a developer / research utility — for example, building a rotating
pool for your own scraping experiments, load-testing against your own servers,
or studying proxy availability over time.

## Features

- Fetches from well-known, publicly published free-proxy aggregators.
- Supports `http`, `socks4`, `socks5`, or `all`.
- Parallel validation via a real HTTP request through each proxy (falls back to
  a cheap TCP connect when `requests` is not installed).
- De-duplicates and sorts output; one `scheme://ip:port` per line.
- `requests` / `PySocks` are imported **lazily**, so the package imports (and its
  test suite runs) without any network access or third-party dependency.

## Install

From source (editable):

```bash
pip install -e .
```

This installs the `free-proxy-updater` console command. Runtime dependencies are
`requests` and `PySocks` (the latter is only needed to validate SOCKS proxies).

## Usage

```bash
# Collect and validate all proxy types, write working ones to proxies.txt
free-proxy-updater

# Only SOCKS5, custom output, longer timeout, more verbose
free-proxy-updater --type socks5 --out socks5.txt --timeout 10 -v

# See what would be written without touching disk
free-proxy-updater --dry-run
```

### Options

| Flag             | Default       | Description                                          |
|------------------|---------------|------------------------------------------------------|
| `--type`         | `all`         | `http`, `socks4`, `socks5`, or `all`.                |
| `--out`          | `proxies.txt` | Output file for working proxies.                     |
| `--timeout`      | `7.0`         | Per-request timeout in seconds.                      |
| `--max-workers`  | `100`         | Maximum parallel validation workers.                 |
| `--dry-run`      | off           | Validate but do not write the output file.           |
| `--verbose`/`-v` | off           | INFO-level logging.                                  |
| `--version`      | —             | Print version and exit.                              |

### As a library

```python
from free_proxy_updater.sources import gather_proxies
from free_proxy_updater.validate import validate_proxies
from free_proxy_updater.core import write_proxies

candidates = gather_proxies("http")
working = validate_proxies(candidates)
write_proxies("proxies.txt", working)
```

## Ethical use & Terms of Service

This tool only contacts **publicly available** free-proxy lists. Please use it
responsibly:

- **Respect the target sites.** Keep request rates modest, honor `robots.txt`
  and each site's Terms of Service, and do not hammer endpoints.
- **Free public proxies are untrusted infrastructure.** They may log, modify, or
  intercept traffic. Never send credentials, personal data, or anything
  sensitive through them.
- **Only use proxies and reach targets you are authorized to use.** Do not use
  this tool to bypass access controls, evade bans, or for any unlawful purpose.
- You are solely responsible for how you use the proxies you collect.

## License

MIT — see [LICENSE](LICENSE).
