# Contributing to free-proxy-updater

Thanks for your interest in improving `free-proxy-updater`. It is a small developer / research utility, and contributions that keep it focused and responsible are very welcome.

## Ground rules

- **No secrets in the repo.** Never commit API keys, tokens, credentials, or absolute paths from your machine.
- **Public sources only.** This tool contacts **only publicly available** free-proxy lists. Do not add private, paid, or access-controlled sources, and do not add anything that helps bypass access controls or evade bans.
- **Responsible use.** Keep request rates modest and honor each site's `robots.txt` and Terms of Service. Free public proxies are untrusted infrastructure; nothing in this tool should encourage sending credentials or sensitive data through them.
- **Keep dependencies lazy.** `requests` / `PySocks` are imported lazily so the package imports and its tests run without network access; please preserve that.

## Development setup

```bash
pip install -e .
python -m unittest discover -s tests
```

Note: the test suite does not touch the network — outbound requests are monkeypatched, so tests run offline.

## Making a change

- Keep pull requests small and focused on a single change.
- Add or update unittest tests to cover your change (keep network access monkeypatched).
- Keep CI green (the test suite runs on Python 3.9, 3.11, and 3.12).
- No new runtime dependencies without discussion first.

## Reporting bugs

Open an issue and include:

- What you ran (the exact command and flags).
- What you expected to happen, and what actually happened.
- Your OS and Python version.
- Relevant logs at `-v`, with any IPs/proxies redacted as needed.

Never paste secrets or absolute machine paths into an issue.

## Scope

- **In scope:** collecting public free-proxy lists, validating them in parallel, and writing the working ones to a file.
- **Out of scope:** private/paid proxy sources, and any feature intended to bypass access controls, evade bans, or otherwise enable unlawful use.
