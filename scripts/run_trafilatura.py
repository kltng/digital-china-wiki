#!/usr/bin/env python3
"""
Extract clean text from scraped_v2.json using trafilatura (CPU-fast).
Replaces MinerU-HTML which is too slow on CPU.
"""

import os, json, time
import trafilatura

WIKI = os.path.expanduser("~/llm-wikis/digital-china-wiki")
INPUT = os.path.join(WIKI, "scripts", "scraped_v2.json")
OUTPUT = os.path.join(WIKI, "scripts", "extracted_v2.json")

print("Loading scraped data...")
with open(INPUT) as f:
    data = json.load(f)
print(f"  {len(data)} entries")

# Resume support
extracted = {}
if os.path.exists(OUTPUT):
    with open(OUTPUT) as f:
        extracted = json.load(f)
    print(f"  Resuming: {len(extracted)} already done")

start = time.time()
processed = len(extracted)
total = len(data)

for i, (fname, entry) in enumerate(data.items()):
    if fname in extracted:
        continue
    
    processed += 1
    result = {
        'file': fname,
        'title': entry.get('title', ''),
        'url': entry.get('url', ''),
        'landing_text': None,
        'sub_texts': [],
        'combined_text': '',
        'combined_len': 0,
    }
    
    # Extract landing page
    html = entry.get('landing_html')
    if html and len(html) > 100:
        text = trafilatura.extract(html, include_links=False, include_tables=True,
                                    favor_precision=True, include_formatting=False)
        if text:
            result['landing_text'] = text
    
    # Extract sub-pages
    for sub in entry.get('sub_pages', []):
        sub_html = sub.get('html')
        if sub_html and len(sub_html) > 100:
            text = trafilatura.extract(sub_html, include_links=False, include_tables=True,
                                        favor_precision=True, include_formatting=False)
            if text:
                result['sub_texts'].append({
                    'url': sub.get('url', ''),
                    'text': text,
                })
    
    # Combine
    parts = []
    if result['landing_text']:
        parts.append(result['landing_text'])
    for st in result['sub_texts']:
        parts.append(st['text'])
    result['combined_text'] = '\n\n'.join(parts)
    result['combined_len'] = len(result['combined_text'])
    
    extracted[fname] = result
    
    elapsed = time.time() - start
    rate = (processed - len(extracted) + (processed - len(data.items()) + total)) / max(elapsed, 1)
    
    print(f"  [{processed}/{total}] {fname[:55]}... {result['combined_len']:,} chars ✓")
    
    # Checkpoint every 100
    if processed % 100 == 0:
        with open(OUTPUT, 'w') as f:
            json.dump(extracted, f, ensure_ascii=False)
        print(f"  [checkpoint: {processed}]")

# Final save
with open(OUTPUT, 'w') as f:
    json.dump(extracted, f, ensure_ascii=False)

elapsed = time.time() - start
ok = sum(1 for r in extracted.values() if r.get('combined_text'))
total_chars = sum(r.get('combined_len', 0) for r in extracted.values())

print(f"\n{'='*60}")
print(f"DONE: {processed} entries in {elapsed:.1f}s")
print(f"  Extracted: {ok}")
print(f"  Total text: {total_chars:,} chars ({total_chars/1024/1024:.1f} MB)")
print(f"  Saved: {OUTPUT}")
