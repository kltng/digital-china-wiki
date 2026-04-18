#!/usr/bin/env python3
"""Rewrite Harvard EZProxy URLs to their canonical upstream form.

The proxy URL is preserved in a new `access_via_harvard:` frontmatter field.
Filenames are NOT changed (they are stable IDs for wikilinks).

Usage:
    python3 scripts/rewrite_ezproxy.py          # dry-run (default)
    python3 scripts/rewrite_ezproxy.py --apply  # write changes + log entry
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

WIKI = Path(__file__).resolve().parent.parent
PROXY_SUFFIX = ".ezp-prod1.hul.harvard.edu"
TODAY = dt.date.today().isoformat()

URL_LINE = re.compile(r"^(url:\s*)(\S+)\s*$", re.MULTILINE)
UPDATED_LINE = re.compile(r"^updated:\s*\S+\s*$", re.MULTILINE)

# Hosts whose dash-encoded form is ambiguous (original contains a literal dash).
# Populate after manual verification; unresolved entries are skipped.
AMBIGUOUS: dict[str, str | None] = {
    "harvard-ebook-hyread-com-tw": "www.hyread.com.tw",  # Harvard-only tenant; redirect to public site
}


def decode_proxy_host(inner: str) -> str | None:
    """Map the host-prefix (before .ezp-prod1…) to the canonical host.

    Pattern B — dot-appended: prefix already has dots, keep as-is.
    Pattern A — dash-encoded: no dots, replace every dash with a dot.
    Ambiguous — dash-encoded but original contains a literal dash: skip.
    """
    if inner in AMBIGUOUS:
        return AMBIGUOUS[inner]
    if "." in inner:
        return inner
    return inner.replace("-", ".")


def rewrite_url(url: str) -> str | None:
    m = re.match(r"^(https?://)([^/]+)(.*)$", url)
    if not m:
        return None
    scheme, host, rest = m.groups()
    if not host.endswith(PROXY_SUFFIX):
        return None
    inner = host[: -len(PROXY_SUFFIX)]
    canonical = decode_proxy_host(inner)
    if canonical is None:
        return None
    return f"{scheme}{canonical}{rest}"


def patch(text: str, canonical: str, proxy: str) -> str:
    text = URL_LINE.sub(lambda m: f"{m.group(1)}{canonical}", text, count=1)
    if UPDATED_LINE.search(text):
        text = UPDATED_LINE.sub(f"updated: {TODAY}", text, count=1)
    if "access_via_harvard:" not in text:
        text = re.sub(
            r"^(url:\s*\S+\s*\n)",
            rf"\1access_via_harvard: {proxy}\n",
            text,
            count=1,
            flags=re.MULTILINE,
        )
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes")
    args = ap.parse_args()

    rewrote, skipped = [], []
    for path in sorted(WIKI.rglob("*.md")):
        if path.is_relative_to(WIKI / "scripts"):
            continue
        text = path.read_text(encoding="utf-8")
        m = URL_LINE.search(text)
        if not m or PROXY_SUFFIX not in m.group(2):
            continue
        proxy_url = m.group(2)
        canonical = rewrite_url(proxy_url)
        rel = path.relative_to(WIKI)
        if canonical is None:
            skipped.append((rel, proxy_url))
            continue
        new_text = patch(text, canonical, proxy_url)
        if args.apply:
            path.write_text(new_text, encoding="utf-8")
        rewrote.append((rel, proxy_url, canonical))

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"=== {mode}: {len(rewrote)} rewrites, {len(skipped)} skipped ===\n")
    for rel, old, new in rewrote:
        print(f"  {rel}")
        print(f"    -  url: {old}")
        print(f"    +  url: {new}")
        print(f"    +  access_via_harvard: {old}")
    if skipped:
        print("\nSkipped (manual review):")
        for rel, url in skipped:
            print(f"  {rel}  ->  {url}")

    if args.apply and rewrote:
        log = WIKI / "log.md"
        entry = (
            f"\n## [{TODAY}] update | Rewrote {len(rewrote)} EZProxy URLs "
            f"to canonical form\n"
            f"- Preserved proxy URL in new `access_via_harvard:` frontmatter field\n"
            f"- {len(skipped)} skipped for manual review\n"
        )
        with log.open("a", encoding="utf-8") as f:
            f.write(entry)
        print(f"\nAppended entry to {log.relative_to(WIKI)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
