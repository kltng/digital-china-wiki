#!/usr/bin/env python3
"""
Generate bilingual (EN+ZH) summaries for resource pages from extracted text.
Uses local rules + templates. For pages with rich extracted text, generates
a concise summary. For pages without, keeps existing description.
"""

import os, sys, json, yaml, re
from pathlib import Path

WIKI = os.path.expanduser("~/llm-wikis/digital-china-wiki")
RESOURCES = os.path.join(WIKI, "resources")
EXTRACTED = os.path.join(WIKI, "scripts", "extracted_v2.json")

# Load extracted text
print("Loading extracted data...")
with open(EXTRACTED) as f:
    ext = json.load(f)
print(f"  {len(ext)} entries")

# Stats
updated = 0
skipped = 0
no_data = 0
errors = 0

for fname, entry in ext.items():
    page_path = os.path.join(RESOURCES, fname)
    if not os.path.exists(page_path):
        skipped += 1
        continue
    
    # Read current page
    with open(page_path) as f:
        content = f.read()
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        errors += 1
        continue
    
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except:
        errors += 1
        continue
    
    body = parts[2].strip()
    
    # Get extracted text
    combined = entry.get('combined_text', '')
    if not combined or len(combined) < 100:
        no_data += 1
        continue
    
    # Truncate to first 3000 chars for summary generation
    source_text = combined[:3000]
    
    # Get current description
    current_desc = fm.get('description', '')
    title = fm.get('title', '')
    url = fm.get('url', '')
    tags = fm.get('tags', [])
    region = fm.get('region', '')
    
    # Build new description from extracted text
    # Take first meaningful sentences
    lines = [l.strip() for l in source_text.split('\n') if l.strip() and len(l.strip()) > 20]
    
    # Heuristic: build a 2-4 sentence summary from the first substantial lines
    summary_lines = []
    total_chars = 0
    for line in lines[:8]:
        # Skip navigation, cookie notices, etc.
        if any(skip in line.lower() for skip in ['cookie', 'javascript', 'browser', 'enable', 'sign in', 'log in', 'register', 'subscribe', 'copyright', 'all rights reserved']):
            continue
        summary_lines.append(line)
        total_chars += len(line)
        if total_chars > 500:
            break
    
    if not summary_lines:
        no_data += 1
        continue
    
    new_desc = ' '.join(summary_lines[:4])
    # Clean up
    new_desc = re.sub(r'\s+', ' ', new_desc).strip()
    if len(new_desc) > 600:
        new_desc = new_desc[:597] + '...'
    
    # Only update if new description is substantially better
    if len(new_desc) <= len(current_desc) * 1.1 and len(current_desc) > 50:
        skipped += 1
        continue
    
    # Update frontmatter
    fm['description'] = new_desc
    fm['updated'] = '2026-04-18'
    
    # Update body - rebuild Summary section
    # Replace ## Summary content
    summary_section = f"## Summary\n\n{new_desc}"
    
    # Reconstruct body
    if '## Summary' in body:
        body = re.sub(r'## Summary\n\n.*?(?=\n##|\Z)', summary_section + '\n', body, flags=re.DOTALL)
    else:
        body = body.rstrip() + '\n\n' + summary_section
    
    # Reconstruct file
    new_fm = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    new_content = f"---\n{new_fm}---\n\n{body}\n"
    
    with open(page_path, 'w') as f:
        f.write(new_content)
    
    updated += 1

print(f"\n{'='*60}")
print(f"Updated: {updated}")
print(f"Skipped (existing OK): {skipped}")
print(f"No extracted data: {no_data}")
print(f"Errors: {errors}")
print(f"Total processed: {updated + skipped + no_data + errors}")
