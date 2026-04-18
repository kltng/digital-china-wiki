#!/usr/bin/env python3
"""Phases 2-5: Flatten folders, remap tags, fix wikilinks, rebuild index."""
import os, sys, yaml, json, re, shutil
from collections import Counter, defaultdict
from datetime import datetime

WIKI = os.path.expanduser("~/llm-wikis/digital-china-wiki")

# Load tag remap data
with open(os.path.join(WIKI, 'scripts', 'tag_remap.json')) as f:
    data = json.load(f)

VALID_TAGS = set(data['valid_tags'])

# Build lookup: (subdir, filename) → new_tags
page_lookup = {}
for p in data['pages']:
    page_lookup[(p['subdir'], p['file'])] = p['new_tags']

# ============================================================
# PHASE 2: Flatten to resources/
# ============================================================
print("=" * 60)
print("PHASE 2: Flatten to resources/")
print("=" * 60)

resources_dir = os.path.join(WIKI, 'resources')
os.makedirs(resources_dir, exist_ok=True)

flatten_dirs = ['websites', 'databases', 'news', 'maps', 'tools']
moved = 0
conflicts = []

for subdir in flatten_dirs:
    src_dir = os.path.join(WIKI, subdir)
    if not os.path.isdir(src_dir):
        continue
    for f in sorted(os.listdir(src_dir)):
        if not f.endswith('.md'):
            continue
        src = os.path.join(src_dir, f)
        dst = os.path.join(resources_dir, f)
        if os.path.exists(dst):
            conflicts.append(f)
        else:
            shutil.move(src, dst)
            moved += 1

print(f"  Moved {moved} pages to resources/")
if conflicts:
    print(f"  CONFLICTS ({len(conflicts)}): {conflicts[:10]}")

# Remove empty dirs
for subdir in flatten_dirs:
    d = os.path.join(WIKI, subdir)
    if os.path.isdir(d):
        remaining = os.listdir(d)
        if not remaining:
            os.rmdir(d)
            print(f"  Removed empty dir: {subdir}/")
        else:
            print(f"  WARNING: {subdir}/ still has files: {remaining}")

# ============================================================
# PHASE 3: Remap tags, drop subjects, add resource_type
# ============================================================
print("\n" + "=" * 60)
print("PHASE 3: Remap tags on all resource pages")
print("=" * 60)

remapped = 0
tag_counter = Counter()

for f in sorted(os.listdir(resources_dir)):
    if not f.endswith('.md'):
        continue
    path = os.path.join(resources_dir, f)
    with open(path) as fh:
        content = fh.read()
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        continue
    
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except:
        continue
    
    # Figure out which subdir this came from (needed for lookup)
    # Use filename to find in page_lookup
    new_tags = None
    for subdir in flatten_dirs:
        if (subdir, f) in page_lookup:
            new_tags = page_lookup[(subdir, f)]
            break
    
    if new_tags is None:
        # Wasn't in the remap data — compute fresh
        old_tags = fm.get('tags', [])
        old_subjects = fm.get('subjects', [])
        # Just keep existing valid tags
        new_tags = [t for t in set(old_tags + old_subjects) if t in VALID_TAGS]
    
    # Update frontmatter
    fm['tags'] = new_tags
    
    # Remove subjects
    if 'subjects' in fm:
        del fm['subjects']
    
    # Remove type (was meaningless — just "website" for 800+ pages)
    if 'type' in fm:
        del fm['type']
    
    # Track tags
    for t in new_tags:
        tag_counter[t] += 1
    
    # Rebuild file
    new_fm = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False).strip()
    new_content = f"---\n{new_fm}\n---{parts[2]}"
    
    with open(path, 'w') as fh:
        fh.write(new_content)
    remapped += 1

print(f"  Remapped {remapped} pages")
print(f"  Tag distribution ({len(tag_counter)} tags):")
for t, c in tag_counter.most_common(20):
    print(f"    {t}: {c}")

# ============================================================
# PHASE 4: Fix wikilinks in topics/institutions/regions/glossary
# ============================================================
print("\n" + "=" * 60)
print("PHASE 4: Fix wikilinks for moved files")
print("=" * 60)

# Build set of resource filenames for fast lookup
resource_files = set(f for f in os.listdir(resources_dir) if f.endswith('.md'))

# Wikilink pattern: [[path/to/file|display]] or [[path/to/file]]
# Old links: [[websites/foo|bar]], [[databases/foo]], etc.
WIKILINK_RE = re.compile(r'\[\[(' + '|'.join(flatten_dirs) + r')/([^\]|]+?)(\|[^\]]+?)?\]\]')

link_dirs = ['topics', 'institutions', 'regions', 'glossary', 'concepts']
total_fixed = 0
files_fixed = 0

for link_dir in link_dirs:
    dp = os.path.join(WIKI, link_dir)
    if not os.path.isdir(dp):
        # Try renamed dir
        if link_dir == 'topics' and os.path.isdir(os.path.join(WIKI, 'concepts')):
            dp = os.path.join(WIKI, 'concepts')
        else:
            continue
    
    for f in sorted(os.listdir(dp)):
        if not f.endswith('.md'):
            continue
        path = os.path.join(dp, f)
        with open(path) as fh:
            content = fh.read()
        
        original = content
        # Replace old dir prefixes in wikilinks with resources/
        content = WIKILINK_RE.sub(r'[[resources/\2\3]]', content)
        
        if content != original:
            with open(path, 'w') as fh:
                fh.write(content)
            files_fixed += 1
            diff = sum(1 for a, b in zip(original, content) if a != b)
            total_fixed += content.count('[[resources/') - original.count('[[resources/')

print(f"  Fixed {total_fixed} wikilinks across {files_fixed} files")

# ============================================================
# Rename concepts/ → topics/
# ============================================================
print("\n" + "=" * 60)
print("Rename concepts/ → topics/")
print("=" * 60)

concepts_dir = os.path.join(WIKI, 'concepts')
topics_dir = os.path.join(WIKI, 'topics')
if os.path.isdir(concepts_dir) and not os.path.isdir(topics_dir):
    shutil.move(concepts_dir, topics_dir)
    print("  Renamed concepts/ → topics/")
    
    # Fix wikilinks referencing concepts/
    CONCEPT_LINK_RE = re.compile(r'\[\[concepts/([^\]|]+?)(\|[^\]]+?)?\]\]')
    for link_dir in ['institutions', 'regions', 'glossary', 'resources', 'topics']:
        dp = os.path.join(WIKI, link_dir)
        if not os.path.isdir(dp):
            continue
        for f in os.listdir(dp):
            if not f.endswith('.md'):
                continue
            path = os.path.join(dp, f)
            with open(path) as fh:
                content = fh.read()
            new_content = CONCEPT_LINK_RE.sub(r'[[topics/\1\2]]', content)
            if new_content != content:
                with open(path, 'w') as fh:
                    fh.write(new_content)
    print("  Fixed wikilinks: concepts/ → topics/")
elif os.path.isdir(topics_dir):
    print("  topics/ already exists, skipping")

# ============================================================
# PHASE 5: Rebuild index.md
# ============================================================
print("\n" + "=" * 60)
print("PHASE 5: Rebuild index.md")
print("=" * 60)

# Scan all dirs for pages
structure = defaultdict(list)
all_wikilinks = 0
total_size = 0

for item in sorted(os.listdir(WIKI)):
    dp = os.path.join(WIKI, item)
    if not os.path.isdir(dp) or item.startswith('.') or item == 'scripts':
        continue
    for f in sorted(os.listdir(dp)):
        if not f.endswith('.md'):
            continue
        fp = os.path.join(dp, f)
        size = os.path.getsize(fp)
        total_size += size
        with open(fp) as fh:
            text = fh.read()
        links = re.findall(r'\[\[([^\]|]+)', text)
        all_wikilinks += len(links)
        structure[item].append(f[:-3])  # strip .md

total_pages = sum(len(v) for v in structure.values())

lines = [
    "---",
    "title: Digital China Wiki — Master Index",
    f"generated: {datetime.now().isoformat()}",
    f"total_pages: {total_pages}",
    f"total_wikilinks: {all_wikilinks}",
    f"total_size_bytes: {total_size}",
    "---",
    "",
    "# Digital China Wiki — Master Index",
    "",
    f"**{total_pages} pages** | **{all_wikilinks} wikilinks** | **{total_size / 1024:.0f} KB**",
    "",
]

for section in sorted(structure.keys()):
    pages = structure[section]
    lines.append(f"## {section}/ ({len(pages)} pages)")
    lines.append("")
    for p in pages:
        lines.append(f"- [[{section}/{p}|{p}]]")
    lines.append("")

lines.append("---")
lines.append(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
lines.append("")

index_path = os.path.join(WIKI, 'index.md')
with open(index_path, 'w') as f:
    f.write('\n'.join(lines))

print(f"  Total pages: {total_pages}")
print(f"  Total wikilinks: {all_wikilinks}")
print(f"  Total size: {total_size / 1024:.0f} KB")
print(f"  Sections: {dict((k, len(v)) for k, v in sorted(structure.items()))}")

print("\n✅ Phases 2-5 complete!")
