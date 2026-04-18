#!/usr/bin/env python3
"""
Depth-2 crawl with MinerU-HTML extraction for digital-china-wiki.

Strategy:
1. Load all live resource pages with URLs
2. Fetch landing page (save raw HTML)
3. Parse landing page for same-domain "about/intro/help" links
4. Follow up to 3 such links (save raw HTML)
5. Feed all HTML through MinerU-HTML → clean Markdown
6. Generate bilingual (EN + ZH) summaries
7. Save results as scraped_v2.json
"""

import os, sys, json, re, time, yaml
from urllib.parse import urljoin, urlparse
from collections import Counter

# Use the venv python explicitly
VENV_PYTHON = os.path.expanduser("~/.hermes/hermes-agent/venv/bin/python")
WIKI = os.path.expanduser("~/llm-wikis/digital-china-wiki")

# ============================================================
# PHASE 1: Collect all live resource URLs
# ============================================================
print("=" * 60)
print("PHASE 1: Collecting live resource URLs")
print("=" * 60)

resources_dir = os.path.join(WIKI, "resources")
pages = []

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
    
    url = fm.get('url', '')
    status = fm.get('site_status', 'unknown')
    title = fm.get('title', '')
    
    if url and status in ('live', 'unknown'):
        pages.append({
            'file': f,
            'title': title,
            'url': url,
            'status': status,
            'tags': fm.get('tags', []),
            'region': fm.get('region', ''),
        })

print(f"  Found {len(pages)} pages to crawl")

# Load previous scraped data for reference
prev_scraped_path = os.path.join(WIKI, "scripts", "scraped_data.json")
prev_data = {}
if os.path.exists(prev_scraped_path):
    with open(prev_scraped_path) as f:
        prev_list = json.load(f)
    for d in prev_list:
        prev_data[d.get('file', '')] = d
    print(f"  Loaded {len(prev_data)} previous scrape records")

# ============================================================
# PHASE 2: Crawl with depth-2
# ============================================================
import requests
from selectolax.parser import HTMLParser

# Patterns for "about/intro" links (EN + ZH)
ABOUT_PATTERNS = re.compile(
    r'(about|intro|guide|overview|description|help|faq|tutorial|背景|介绍|关于|说明|概览|帮助|指引|使用|search_help|how.to.use)',
    re.IGNORECASE
)

# Skip patterns (we don't want to follow these)
SKIP_PATTERNS = re.compile(
    r'(\.(pdf|doc|xls|ppt|zip|rar|exe|dmg)|login|signin|register|signup|cart|checkout|download)',
    re.IGNORECASE
)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (compatible; DigitalChinaWiki/2.0; +https://github.com/kltng/digital-china-wiki)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
})
session.timeout = 15

def fetch_url(url):
    """Fetch a URL, return (html, final_url, error)."""
    try:
        resp = session.get(url, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        ct = resp.headers.get('content-type', '')
        if 'text/html' not in ct and 'application/xhtml' not in ct:
            return None, resp.url, f"not html: {ct}"
        return resp.text, resp.url, None
    except Exception as e:
        return None, url, str(e)[:100]

def extract_same_domain_links(html, base_url):
    """Extract about/intro links from same domain."""
    tree = HTMLParser(html)
    base_domain = urlparse(base_url).netloc
    links = []
    seen = set()
    
    for node in tree.css('a[href]'):
        href = node.attributes.get('href', '')
        if not href or href.startswith('#') or href.startswith('javascript:'):
            continue
        if SKIP_PATTERNS.search(href):
            continue
        
        full_url = urljoin(base_url, href)
        link_domain = urlparse(full_url).netloc
        
        # Same domain (or subdomain)
        if base_domain not in link_domain and link_domain not in base_domain:
            continue
        
        # Normalize
        full_url = full_url.split('#')[0].split('?')[0]
        if full_url in seen or full_url == base_url:
            continue
        seen.add(full_url)
        
        # Check if it's an "about" type link
        href_lower = href.lower()
        link_text = (node.text() or '').lower().strip()
        
        score = 0
        if ABOUT_PATTERNS.search(href_lower):
            score += 2
        if ABOUT_PATTERNS.search(link_text):
            score += 1
        
        if score > 0:
            links.append((full_url, score))
    
    # Sort by score descending, take top 3
    links.sort(key=lambda x: -x[1])
    return [l[0] for l in links[:3]]

results = {}
total = len(pages)

for i, page in enumerate(pages):
    fname = page['file']
    url = page['url']
    
    if fname in results:
        continue
    
    print(f"  [{i+1}/{total}] {fname[:60]}...", end=" ", flush=True)
    
    # Fetch landing page
    html, final_url, error = fetch_url(url)
    
    entry = {
        'file': fname,
        'title': page['title'],
        'url': url,
        'landing_html': None,
        'landing_final_url': final_url,
        'sub_pages': [],
        'crawl_error': error,
    }
    
    if html:
        entry['landing_html'] = html
        entry['landing_html_len'] = len(html)
        
        # Find about/intro sub-pages
        sub_links = extract_same_domain_links(html, final_url)
        
        for sub_url in sub_links:
            time.sleep(0.5)  # be polite
            sub_html, sub_final, sub_error = fetch_url(sub_url)
            if sub_html:
                entry['sub_pages'].append({
                    'url': sub_url,
                    'final_url': sub_final,
                    'html': sub_html,
                    'html_len': len(sub_html),
                })
                print(f"+{len(sub_html)//1024}k", end=" ", flush=True)
    
    results[fname] = entry
    
    # Rate limit
    time.sleep(1.0)
    
    # Save checkpoint every 50 pages
    if (i + 1) % 50 == 0:
        checkpoint_path = os.path.join(WIKI, "scripts", "scraped_v2_checkpoint.json")
        with open(checkpoint_path, 'w') as f:
            json.dump(results, f, ensure_ascii=False)
        print(f"\n  [checkpoint saved: {len(results)} entries]")
    else:
        print("✓" if not error else f"✗ {error[:30]}")

# Save final results
output_path = os.path.join(WIKI, "scripts", "scraped_v2.json")
with open(output_path, 'w') as f:
    json.dump(results, f, ensure_ascii=False)

print(f"\n  Saved {len(results)} entries to scraped_v2.json")

# Stats
landing_ok = sum(1 for r in results.values() if r.get('landing_html'))
has_subs = sum(1 for r in results.values() if r.get('sub_pages'))
total_subs = sum(len(r.get('sub_pages', [])) for r in results.values())
total_html_mb = sum(
    (r.get('landing_html_len', 0) or 0) + sum(s.get('html_len', 0) for s in r.get('sub_pages', []))
    for r in results.values()
) / 1024 / 1024

print(f"  Landing pages fetched: {landing_ok}/{len(results)}")
print(f"  Entries with sub-pages: {has_subs}")
print(f"  Total sub-pages: {total_subs}")
print(f"  Total HTML: {total_html_mb:.1f} MB")
