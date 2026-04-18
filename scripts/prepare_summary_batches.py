#!/usr/bin/env python3
"""
Prepare batch summary generation tasks.
Outputs JSON batches with source text + metadata for LLM processing.
"""
import os, json, yaml
from pathlib import Path

WIKI = os.path.expanduser("~/llm-wikis/digital-china-wiki")
RESOURCES = os.path.join(WIKI, "resources")
EXTRACTED = os.path.join(WIKI, "scripts", "extracted_v2.json")

with open(EXTRACTED) as f:
    ext = json.load(f)

batch = []
for fname, entry in ext.items():
    page_path = os.path.join(RESOURCES, fname)
    if not os.path.exists(page_path):
        continue
    
    with open(page_path) as f:
        content = f.read()
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        continue
    
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except:
        continue
    
    combined = entry.get('combined_text', '')
    if not combined or len(combined) < 100:
        continue
    
    current_desc = fm.get('description', '')
    title = fm.get('title', '')
    url = fm.get('url', '')
    tags = fm.get('tags', [])
    
    batch.append({
        'file': fname,
        'title': title,
        'url': url,
        'tags': tags,
        'current_description': current_desc,
        'source_text': combined[:2500],
        'source_len': len(combined),
    })

# Split into chunks of 20 for batch processing
CHUNK_SIZE = 20
chunks_dir = os.path.join(WIKI, "scripts", "summary_batches")
os.makedirs(chunks_dir, exist_ok=True)

for i in range(0, len(batch), CHUNK_SIZE):
    chunk = batch[i:i+CHUNK_SIZE]
    chunk_file = os.path.join(chunks_dir, f"batch_{i//CHUNK_SIZE:03d}.json")
    with open(chunk_file, 'w') as f:
        json.dump(chunk, f, ensure_ascii=False, indent=2)

print(f"Total entries needing summaries: {len(batch)}")
print(f"Batch files: {(len(batch) + CHUNK_SIZE - 1) // CHUNK_SIZE}")
print(f"Saved to: {chunks_dir}/")
