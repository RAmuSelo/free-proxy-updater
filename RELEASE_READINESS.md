# Release Readiness — free-proxy-updater

Status: **Ready for an initial `0.1.0` open-source release.**

## Checklist

| Item | Status | Notes |
|------|--------|-------|
| Clean, self-contained package (`src/` layout) | Done | `free_proxy_updater` with `cli`, `core`, `sources`, `validate`. |
| No personal / machine-specific paths | Done | Grep for `/Users/...` returns nothing. |
| No secrets / API keys / tokens | Done | No credentials anywhere; sources are public lists only. |
| No hardcoded private proxy lists | Done | Only public, community-maintained aggregators referenced. |
| CLI via `argparse` (no `input()`) | Done | `--type/--out/--timeout/--max-workers/--dry-run/--verbose/--version`. |
| Lazy `requests` / `PySocks` imports | Done | Imported inside fetch/validate functions only. |
| Network-free import & test suite | Done | Tests monkeypatch the single network function (`sources._get`) and inject an offline validation `checker`. |
| `pyproject.toml` (MIT, py>=3.9, deps, entry point) | Done | `free-proxy-updater = free_proxy_updater.cli:main`. |
| `LICENSE` (MIT) | Done | "The free-proxy-updater authors", 2026. |
| `README.md` with ethical/ToS note | Done | Responsible-use and respect-target-sites section included. |
| `.gitignore` | Done | Ignores build artifacts, venvs, generated `proxies.txt`. |
| Tests | Done | stdlib `unittest`; covers parsing, dedup, filtering, file writing, arg parsing, dry-run, pipeline exit codes. |

## How to test

```bash
python3 -m unittest discover -s tests
```

No network access is required or attempted.

## Known limitations / future work

- Source list is a small set of public raw `.txt` aggregators; availability of
  any individual list is outside this project's control. Adding/removing a
  source is a one-line change in `sources.RAW_SOURCES`.
- Live validation against the public test endpoint (`httpbin.org/ip`) is only
  exercised at runtime, never in tests. The endpoint is configurable in code.
- HTML-table scrapers from the original prototypes were intentionally dropped in
  favour of stable raw-text lists (no BeautifulSoup dependency, no brittle
  table-structure assumptions).

## Pre-publish reminders

- Replace the placeholder `project.urls` in `pyproject.toml` with the real
  repository URL before publishing.
- `git init` and remote/push are intentionally **not** part of this deliverable.
