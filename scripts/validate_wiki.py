#!/usr/bin/env python3
"""Validate schema, tags, and wikilinks for the wiki repository."""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict

from normalize_wiki import (
    CONTENT_DIRS,
    WIKI,
    build_page_index,
    load_build_tag_map,
    parse_frontmatter,
    split_frontmatter,
)

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(\|[^\]]+)?\]\]")


def iter_markdown_files():
    for subdir in CONTENT_DIRS:
        dir_path = os.path.join(WIKI, subdir)
        for filename in sorted(os.listdir(dir_path)):
            if filename.endswith(".md"):
                yield subdir, filename, os.path.join(dir_path, filename)


def main() -> int:
    valid_tags, _ = load_build_tag_map()
    all_paths, _ = build_page_index()
    errors: list[str] = []
    legacy_hits: defaultdict[str, list[str]] = defaultdict(list)

    expected_types = {"topics": "topic", "institutions": "institution", "regions": "region"}
    legacy_patterns = [
        "type: concept",
        "[[digital-humanities",
        "[[hong-kong]]",
        "[[ejournals]]",
        "[[academic-articles]]",
        "[[digital-archive]]",
    ]

    for subdir, filename, file_path in iter_markdown_files():
        rel_file = f"{subdir}/{filename}"
        with open(file_path, encoding="utf-8") as f:
            text = f.read()

        frontmatter_block, body = split_frontmatter(text)
        if frontmatter_block is None:
            errors.append(f"{rel_file}: missing frontmatter block")
            continue

        data, _ = parse_frontmatter(frontmatter_block)

        expected_type = expected_types.get(subdir)
        actual_type = data.get("type")
        if expected_type and actual_type != expected_type:
            errors.append(f"{rel_file}: expected type '{expected_type}', found '{actual_type}'")

        tags = data.get("tags")
        if isinstance(tags, list):
            invalid = [tag for tag in tags if tag not in valid_tags]
            if invalid:
                errors.append(f"{rel_file}: invalid tags {', '.join(invalid)}")

        for match in WIKILINK_RE.finditer(body):
            target = match.group(1)
            if "/" not in target:
                errors.append(f"{rel_file}: bare wikilink target '{target}'")
                continue
            if target not in all_paths:
                errors.append(f"{rel_file}: unresolved wikilink '{target}'")

        for pattern in legacy_patterns:
            if pattern in text:
                legacy_hits[pattern].append(rel_file)

    if errors:
        print("Validation failed:")
        for item in errors[:200]:
            print(f"  - {item}")
        if len(errors) > 200:
            print(f"  ... and {len(errors) - 200} more")
    else:
        print("Validation passed.")

    if legacy_hits:
        print("\nLegacy pattern hits:")
        for pattern, files in legacy_hits.items():
            print(f"  - {pattern}: {len(files)} file(s)")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
