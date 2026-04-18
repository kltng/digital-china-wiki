#!/usr/bin/env python3
"""
Run MinerU-HTML (Transformers/CPU backend) on scraped_v2.json HTML data.
Extracts clean main content from raw HTML pages.
"""

import os, sys, json, time
from pathlib import Path

WIKI = os.path.expanduser("~/llm-wikis/digital-china-wiki")
INPUT = os.path.join(WIKI, "scripts", "scraped_v2.json")
OUTPUT = os.path.join(WIKI, "scripts", "mineru_extracted.json")

print("Loading scraped data...")
with open(INPUT) as f:
    data = json.load(f)
print(f"  {len(data)} entries loaded")

# Check if we have a partial results file to resume
extracted = {}
if os.path.exists(OUTPUT):
    with open(OUTPUT) as f:
        extracted = json.load(f)
    print(f"  Resuming from {len(extracted)} already processed entries")

# Initialize MinerU-HTML with Transformers (CPU) backend
print("Initializing MinerU-HTML (Transformers/CPU, 0.5B model)...")
from mineru_html import MinerUHTML_Transformers

miner = MinerUHTML_Transformers(
    model_init_kwargs={
        'device_map': 'auto',
        'dtype': 'auto',
    }
)
print("  Model loaded!")

# Process each entry
total = len(data)
processed = len(extracted)
errors = 0
start = time.time()

for i, (fname, entry) in enumerate(data.items()):
    if fname in extracted:
        continue
    
    processed += 1
    pages_done = 0
    pages_total = 1 + len(entry.get('sub_pages', []))
    
    result = {
        'file': fname,
        'title': entry.get('title', ''),
        'url': entry.get('url', ''),
        'landing_text': None,
        'sub_texts': [],
        'combined_text': '',
    }
    
    try:
        # Process landing page
        html = entry.get('landing_html')
        if html and len(html) > 100:
            texts = miner.process(html)
            if texts and texts[0].output_data and texts[0].output_data.main_html:
                from selectolax.parser import HTMLParser
                tree = HTMLParser(texts[0].output_data.main_html)
                result['landing_text'] = tree.body.text(separator='\n', strip=True)
            pages_done += 1
        
        # Process sub-pages
        for sub in entry.get('sub_pages', []):
            sub_html = sub.get('html')
            if sub_html and len(sub_html) > 100:
                texts = miner.process(sub_html)
                if texts and texts[0].output_data and texts[0].output_data.main_html:
                    from selectolax.parser import HTMLParser
                    tree = HTMLParser(texts[0].output_data.main_html)
                    sub_text = tree.body.text(separator='\n', strip=True)
                    result['sub_texts'].append({
                        'url': sub.get('url', ''),
                        'text': sub_text,
                    })
                pages_done += 1
        
        # Combine all extracted text
        parts = []
        if result['landing_text']:
            parts.append(result['landing_text'])
        for st in result['sub_texts']:
            parts.append(st['text'])
        result['combined_text'] = '\n\n'.join(parts)
        result['combined_len'] = len(result['combined_text'])
        
    except Exception as e:
        result['error'] = str(e)[:200]
        errors += 1
    
    extracted[fname] = result
    
    # Progress
    elapsed = time.time() - start
    rate = processed / max(elapsed, 1)
    eta = (total - processed) / max(rate, 0.1)
    
    status = "✓" if not result.get('error') else f"✗ {result.get('error', '')[:30]}"
    print(f"  [{processed}/{total}] {fname[:50]}... ({pages_done}/{pages_total} pages) {result.get('combined_len', 0)} chars {status} ETA: {eta/60:.0f}m")
    
    # Checkpoint every 25 entries
    if processed % 25 == 0:
        with open(OUTPUT, 'w') as f:
            json.dump(extracted, f, ensure_ascii=False)
        print(f"  [checkpoint: {processed} entries saved]")

# Final save
with open(OUTPUT, 'w') as f:
    json.dump(extracted, f, ensure_ascii=False)

elapsed = time.time() - start
ok = sum(1 for r in extracted.values() if r.get('combined_text'))
total_chars = sum(r.get('combined_len', 0) for r in extracted.values())

print(f"\n{'='*60}")
print(f"DONE: {processed} entries in {elapsed/60:.1f} min")
print(f"  Extracted: {ok}")
print(f"  Errors: {errors}")
print(f"  Total text: {total_chars:,} chars ({total_chars/1024/1024:.1f} MB)")
print(f"  Saved to: {OUTPUT}")
