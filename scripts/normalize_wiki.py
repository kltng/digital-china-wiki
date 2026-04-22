#!/usr/bin/env python3
"""Normalize wiki frontmatter, wikilinks, and index output."""

from __future__ import annotations

import ast
import json
import os
import re
from collections import OrderedDict, defaultdict
from datetime import datetime

WIKI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIRS = ["topics", "institutions", "regions", "glossary", "resources"]
ALIAS_MAP_FILE = os.path.join(WIKI, "scripts", "alias_map.json")
BUILD_TAG_MAP_FILE = os.path.join(WIKI, "scripts", "build_tag_map.py")

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(\|[^\]]+)?\]\]")
BULLET_WIKILINK_RE = re.compile(r"^(\s*-\s)\[\[([^\]|]+)(\|[^\]]+)?\]\]\s*$")

CANONICAL_TAG_TARGETS = {
    "archive": "topics/archives",
    "bibliography": "topics/academic-research",
    "catalog": "topics/library-science",
    "database": "topics/digital-libraries",
    "dictionary": "glossary/academic-resources",
    "ebook": "topics/ebooks",
    "film_video": "topics/media-studies",
    "full_text": "topics/chinese-classics",
    "gis": "topics/maps-and-gis",
    "guide": "topics/research-methods",
    "map": "topics/maps-and-gis",
    "newspaper": "topics/newspapers",
    "organization": "topics/academic-research",
    "periodical": "topics/newspapers",
    "photo": "topics/museum-collections",
    "platform": "topics/digital-humanities",
    "statistical": "topics/social-sciences",
    "tool": "topics/digital-humanities",
    "social_media": "topics/media-studies",
    "website": "topics/academic-research",
    "art_history": "topics/museum-collections",
    "book_history": "topics/book-history",
    "buddhism": "topics/philosophy",
    "christianity": "topics/chinese-history",
    "classics": "topics/chinese-classics",
    "cold_war": "topics/political-history",
    "colonialism": "topics/taiwan-history",
    "digital_humanities": "topics/digital-humanities",
    "economic_history": "topics/social-sciences",
    "epigraphy": "topics/chinese-classics",
    "genealogy": "topics/chinese-history",
    "geography": "topics/maps-and-gis",
    "intellectual_history": "topics/chinese-intellectual-history",
    "language": "topics/chinese-classics",
    "legal_history": "topics/political-history",
    "literature": "topics/literature",
    "maritime": "topics/chinese-history",
    "medicine": "topics/social-sciences",
    "military_history": "topics/political-history",
    "music": "topics/media-studies",
    "museum_studies": "topics/museum-collections",
    "newspaper_studies": "topics/newspapers",
    "open_access": "topics/open-access",
    "philosophy": "topics/philosophy",
    "political_science": "topics/political-history",
    "rare_books": "topics/rare-books",
    "religion": "topics/philosophy",
    "social_history": "topics/chinese-history",
    "statistics": "topics/social-sciences",
    "prc": "regions/prc",
    "taiwan": "regions/taiwan",
    "japan": "regions/japan",
    "hong_kong": "regions/hong-kong",
    "global": "regions/global",
}

TOPIC_TAG_OVERRIDES = {
    "topics/academic-research": ["guide", "digital_humanities"],
    "topics/archives": ["archive", "social_history"],
    "topics/book-history": ["book_history", "rare_books"],
    "topics/chinese-classics": ["classics", "full_text"],
    "topics/chinese-history": ["social_history", "political_science"],
    "topics/chinese-intellectual-history": ["intellectual_history", "philosophy"],
    "topics/chinese-studies": ["digital_humanities", "guide"],
    "topics/digital-humanities": ["digital_humanities", "tool"],
    "topics/digital-libraries": ["database", "catalog"],
    "topics/east-asian-studies": ["digital_humanities", "guide"],
    "topics/ebooks": ["ebook", "full_text"],
    "topics/library-science": ["catalog", "guide"],
    "topics/literature": ["literature", "full_text"],
    "topics/maps-and-gis": ["map", "gis", "geography"],
    "topics/media-studies": ["newspaper_studies", "film_video"],
    "topics/museum-collections": ["museum_studies", "photo"],
    "topics/newspapers": ["newspaper", "periodical", "newspaper_studies"],
    "topics/open-access": ["open_access", "digital_humanities"],
    "topics/philosophy": ["philosophy", "intellectual_history"],
    "topics/political-history": ["political_science", "social_history"],
    "topics/rare-books": ["rare_books", "classics"],
    "topics/research-methods": ["guide", "digital_humanities"],
    "topics/social-sciences": ["statistics", "social_history"],
    "topics/taiwan-history": ["social_history", "taiwan"],
    "topics/taiwan-studies": ["digital_humanities", "taiwan"],
}

PLAIN_SCALAR_RE = re.compile(r"^[A-Za-z0-9_./:+-]+$")


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_build_tag_map() -> tuple[set[str], dict[str, list[str]]]:
    with open(BUILD_TAG_MAP_FILE, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=BUILD_TAG_MAP_FILE)

    valid_tags: set[str] = set()
    tag_map: dict[str, list[str]] = {}

    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id == "VALID_TAGS":
            valid_tags = set(ast.literal_eval(node.value))
        elif target.id == "TAG_MAP":
            tag_map = ast.literal_eval(node.value)

    return valid_tags, tag_map


def split_frontmatter(text: str) -> tuple[str | None, str]:
    if not text.startswith("---\n"):
        return None, text
    marker = "\n---\n"
    end = text.find(marker, 4)
    if end == -1:
        return None, text
    return text[4:end], text[end + len(marker) :]


def parse_scalar(raw: str):
    raw = raw.strip()
    if not raw:
        return ""
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    return raw


def parse_frontmatter(block: str) -> tuple[OrderedDict, list[str]]:
    data: OrderedDict[str, object] = OrderedDict()
    order: list[str] = []
    current_key: str | None = None
    for line in block.splitlines():
        if not line.strip():
            current_key = None
            continue
        if line.startswith("- ") and current_key:
            data.setdefault(current_key, [])
            assert isinstance(data[current_key], list)
            data[current_key].append(parse_scalar(line[2:]))
            continue
        match = re.match(r"^([A-Za-z0-9_]+):(.*)$", line)
        if not match:
            current_key = None
            continue
        key, raw_value = match.groups()
        raw_value = raw_value.strip()
        order.append(key)
        if not raw_value:
            data[key] = []
            current_key = key
        else:
            data[key] = parse_scalar(raw_value)
            current_key = None
    return data, order


def format_scalar(value) -> str:
    if isinstance(value, str) and PLAIN_SCALAR_RE.match(value):
        return value
    escaped = str(value).replace('"', '\\"')
    return f'"{escaped}"'


def format_frontmatter(data: OrderedDict, order: list[str]) -> str:
    lines: list[str] = ["---"]
    seen = set()
    for key in order + [k for k in data.keys() if k not in order]:
        if key in seen or key not in data:
            continue
        seen.add(key)
        value = data[key]
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            elif len(value) <= 4 and all(isinstance(item, str) and PLAIN_SCALAR_RE.match(item) for item in value):
                joined = ", ".join(value)
                lines.append(f"{key}: [{joined}]")
            else:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"- {format_scalar(item)}")
        else:
            lines.append(f"{key}: {format_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def build_page_index() -> tuple[set[str], dict[str, list[str]]]:
    all_paths: set[str] = set()
    basename_map: dict[str, list[str]] = defaultdict(list)
    for subdir in CONTENT_DIRS:
        dir_path = os.path.join(WIKI, subdir)
        for filename in sorted(os.listdir(dir_path)):
            if not filename.endswith(".md"):
                continue
            rel_path = f"{subdir}/{filename[:-3]}"
            basename = filename[:-3]
            all_paths.add(rel_path)
            basename_map[basename].append(rel_path)
    return all_paths, basename_map


def normalize_tag(tag: str, valid_tags: set[str], tag_map: dict[str, list[str]]) -> list[str]:
    tag = tag.strip()
    if not tag:
        return []
    if tag in valid_tags:
        return [tag]
    if tag in tag_map:
        return [mapped for mapped in tag_map[tag] if mapped in valid_tags]
    variant_candidates = {
        tag.replace("-", "_"),
        tag.replace("_", "-"),
        tag.lower(),
        tag.lower().replace("-", "_"),
    }
    for variant in variant_candidates:
        if variant in valid_tags:
            return [variant]
        if variant in tag_map:
            return [mapped for mapped in tag_map[variant] if mapped in valid_tags]
    return []


def normalize_tags(path: str, tags: list[str], valid_tags: set[str], tag_map: dict[str, list[str]]) -> list[str]:
    if path in TOPIC_TAG_OVERRIDES:
        return TOPIC_TAG_OVERRIDES[path]
    normalized: list[str] = []
    for tag in tags:
        normalized.extend(normalize_tag(tag, valid_tags, tag_map))
    deduped: list[str] = []
    for tag in normalized:
        if tag not in deduped:
            deduped.append(tag)
    return deduped


def resolve_target(
    target: str,
    alias_map: dict[str, str],
    valid_tags: set[str],
    tag_map: dict[str, list[str]],
    all_paths: set[str],
    basename_map: dict[str, list[str]],
) -> str:
    if target in all_paths:
        return target
    if target in alias_map:
        return alias_map[target]
    if "/" in target:
        basename = target.rsplit("/", 1)[-1]
        if basename in alias_map:
            return alias_map[basename]
        if basename in basename_map and len(basename_map[basename]) == 1:
            return basename_map[basename][0]
    if target in basename_map and len(basename_map[target]) == 1:
        return basename_map[target][0]

    variants = [
        target.replace("_", "-"),
        target.replace("-", "_"),
        target.lower(),
        target.lower().replace("_", "-"),
        target.lower().replace("-", "_"),
    ]
    for variant in variants:
        if variant in alias_map:
            return alias_map[variant]
        if variant in basename_map and len(basename_map[variant]) == 1:
            return basename_map[variant][0]

    for candidate in normalize_tag(target, valid_tags, tag_map):
        mapped = CANONICAL_TAG_TARGETS.get(candidate)
        if mapped:
            return mapped

    return target


def rewrite_wikilinks(
    text: str,
    alias_map: dict[str, str],
    valid_tags: set[str],
    tag_map: dict[str, list[str]],
    all_paths: set[str],
    basename_map: dict[str, list[str]],
) -> tuple[str, int]:
    replacements = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal replacements
        target = match.group(1)
        label = match.group(2) or ""
        resolved = resolve_target(target, alias_map, valid_tags, tag_map, all_paths, basename_map)
        if resolved != target:
            replacements += 1
        return f"[[{resolved}{label}]]"

    return WIKILINK_RE.sub(repl, text), replacements


def clean_bullet_lists(body: str, rel_path: str) -> tuple[str, int]:
    lines = body.splitlines()
    cleaned: list[str] = []
    removed = 0
    seen_in_block: set[str] = set()

    for line in lines:
        match = BULLET_WIKILINK_RE.match(line)
        if not match:
            cleaned.append(line)
            if line.strip() == "":
                seen_in_block = set()
            continue

        target = match.group(2)
        if target == rel_path or target in seen_in_block:
            removed += 1
            continue

        seen_in_block.add(target)
        cleaned.append(line)

    # Trim repeated blank lines introduced by removals.
    normalized: list[str] = []
    blank_pending = False
    for line in cleaned:
        if line.strip() == "":
            if blank_pending:
                continue
            blank_pending = True
        else:
            blank_pending = False
        normalized.append(line)

    return "\n".join(normalized) + ("\n" if body.endswith("\n") else ""), removed


def rebuild_index(all_paths: set[str]) -> None:
    structure: dict[str, list[str]] = defaultdict(list)
    total_wikilinks = 0
    total_size = 0

    for rel_path in sorted(all_paths):
        subdir, basename = rel_path.split("/", 1)
        file_path = os.path.join(WIKI, f"{rel_path}.md")
        structure[subdir].append(basename)
        total_size += os.path.getsize(file_path)
        with open(file_path, encoding="utf-8") as f:
            total_wikilinks += len(re.findall(r"\[\[([^\]|]+)", f.read()))

    total_pages = sum(len(items) for items in structure.values())
    lines = [
        "---",
        "title: Digital China Wiki — Master Index",
        f"generated: {datetime.now().isoformat()}",
        f"total_pages: {total_pages}",
        f"total_wikilinks: {total_wikilinks}",
        f"total_size_bytes: {total_size}",
        "---",
        "",
        "# Digital China Wiki — Master Index",
        "",
        f"**{total_pages} pages** | **{total_wikilinks} wikilinks** | **{total_size / 1024:.0f} KB**",
        "",
    ]

    for subdir in sorted(structure):
        lines.append(f"## {subdir}/ ({len(structure[subdir])} pages)")
        lines.append("")
        for basename in structure[subdir]:
            lines.append(f"- [[{subdir}/{basename}|{basename}]]")
        lines.append("")

    lines.append("---")
    lines.append(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")

    with open(os.path.join(WIKI, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def normalize_repo() -> None:
    alias_map = load_json(ALIAS_MAP_FILE)
    valid_tags, tag_map = load_build_tag_map()
    all_paths, basename_map = build_page_index()

    files_changed = 0
    link_rewrites = 0
    tag_updates = 0
    type_updates = 0
    bullet_prunes = 0

    for subdir in CONTENT_DIRS:
        dir_path = os.path.join(WIKI, subdir)
        for filename in sorted(os.listdir(dir_path)):
            if not filename.endswith(".md"):
                continue

            rel_path = f"{subdir}/{filename[:-3]}"
            file_path = os.path.join(dir_path, filename)
            with open(file_path, encoding="utf-8") as f:
                original = f.read()

            frontmatter_block, body = split_frontmatter(original)
            if frontmatter_block is None:
                continue
            data, order = parse_frontmatter(frontmatter_block)
            changed = False

            expected_type = {"topics": "topic", "institutions": "institution", "regions": "region"}.get(subdir)
            if expected_type and data.get("type") != expected_type:
                data["type"] = expected_type
                changed = True
                type_updates += 1

            if "tags" in data and isinstance(data["tags"], list):
                normalized_tags = normalize_tags(rel_path, list(data["tags"]), valid_tags, tag_map)
                if normalized_tags != data["tags"]:
                    data["tags"] = normalized_tags
                    changed = True
                    tag_updates += 1

            rewritten_body, rewritten_count = rewrite_wikilinks(
                body,
                alias_map,
                valid_tags,
                tag_map,
                all_paths,
                basename_map,
            )
            if rewritten_count:
                body = rewritten_body
                changed = True
                link_rewrites += rewritten_count

            cleaned_body, removed_bullets = clean_bullet_lists(body, rel_path)
            if removed_bullets:
                body = cleaned_body
                changed = True
                bullet_prunes += removed_bullets

            if changed:
                formatted = format_frontmatter(data, order)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"{formatted}\n{body}")
                files_changed += 1

    rebuild_index(all_paths)
    print(
        f"Normalized {files_changed} files | "
        f"type updates: {type_updates} | tag updates: {tag_updates} | wikilinks rewritten: {link_rewrites}"
        f" | duplicate/self bullets removed: {bullet_prunes}"
    )


if __name__ == "__main__":
    normalize_repo()
