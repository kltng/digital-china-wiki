#!/usr/bin/env python3
"""Phase 1: Check accessibility of all stub URLs in the digital-china-wiki."""
import os, csv, time, json, re
import yaml
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

WIKI = os.path.expanduser("~/llm-wikis/digital-china-wiki")
OUTPUT = os.path.join(WIKI, "scripts", "url_check_results.csv")
TIMEOUT = 15
MAX_WORKERS = 8
DELAY = 0.3  # small delay per thread

# Known geo-blocked or problematic domains to skip actual requests
SKIP_DOMAINS = set()  # we'll try them all first

def load_stubs():
    """Load all stub entries from the wiki."""
    stubs = []
    for subdir in ['websites', 'databases', 'news', 'maps', 'tools']:
        dp = os.path.join(WIKI, subdir)
        if not os.path.isdir(dp):
            continue
        for f in sorted(os.listdir(dp)):
            if not f.endswith('.md'):
                continue
            path = os.path.join(dp, f)
            with open(path) as fh:
                content = fh.read()
            if '*Awaiting full description.*' not in content:
                continue
            parts = content.split('---', 2)
            if len(parts) < 3:
                continue
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except:
                continue
            url = fm.get('url', '') or fm.get('canonical_url', '')
            if not url:
                continue
            stubs.append({
                'file': f,
                'path': path,
                'url': url,
                'title': fm.get('title', ''),
                'type': fm.get('type', ''),
                'region': fm.get('region', ''),
                'subdir': subdir,
                'language': fm.get('language', ''),
            })
    return stubs

def check_url(entry):
    """Check a single URL. Returns result dict."""
    url = entry['url']
    result = {
        'file': entry['file'],
        'subdir': entry['subdir'],
        'title': entry['title'],
        'url': url,
        'status_code': '',
        'final_url': '',
        'is_live': False,
        'category': 'unknown',
        'content_type': '',
        'redirect_url': '',
        'error': '',
        'has_ssl': url.startswith('https://'),
    }
    
    try:
        # Try GET with stream=True to avoid downloading large files
        resp = requests.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True,
            stream=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
        )
        result['status_code'] = resp.status_code
        result['final_url'] = resp.url
        result['content_type'] = resp.headers.get('Content-Type', '')
        
        if resp.status_code == 200:
            result['is_live'] = True
            # Check if it redirected
            if resp.url != url:
                result['redirect_url'] = resp.url
                result['category'] = 'live_redirect'
            else:
                result['category'] = 'live'
        elif resp.status_code in (301, 302, 303, 307, 308):
            result['category'] = 'redirect'
            result['redirect_url'] = resp.url
        elif resp.status_code == 403:
            result['category'] = 'blocked_403'
        elif resp.status_code == 404:
            result['category'] = 'dead_404'
        elif resp.status_code == 500:
            result['category'] = 'error_500'
        elif resp.status_code == 503:
            result['category'] = 'error_503'
        else:
            result['category'] = f'error_{resp.status_code}'
        
        # Close connection without reading body
        resp.close()
        
    except requests.exceptions.SSLError as e:
        result['category'] = 'ssl_error'
        result['error'] = str(e)[:200]
    except requests.exceptions.Timeout:
        result['category'] = 'timeout'
        result['error'] = 'Connection timed out'
    except requests.exceptions.ConnectionError as e:
        result['category'] = 'connection_error'
        result['error'] = str(e)[:200]
    except Exception as e:
        result['category'] = 'other_error'
        result['error'] = str(e)[:200]
    
    return result

def main():
    stubs = load_stubs()
    print(f"Loaded {len(stubs)} stub entries")
    
    results = []
    done = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_url, entry): entry for entry in stubs}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            done += 1
            if done % 50 == 0:
                print(f"  Checked {done}/{len(stubs)} URLs...")
    
    # Sort by original order
    file_order = {s['file']: i for i, s in enumerate(stubs)}
    results.sort(key=lambda r: file_order.get(r['file'], 999))
    
    # Write CSV
    fieldnames = ['file', 'subdir', 'title', 'url', 'status_code', 'final_url', 
                  'is_live', 'category', 'content_type', 'redirect_url', 'error', 'has_ssl']
    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    # Summary
    from collections import Counter
    cats = Counter(r['category'] for r in results)
    print(f"\n{'='*60}")
    print(f"RESULTS: {len(results)} URLs checked")
    print(f"{'='*60}")
    live = sum(1 for r in results if r['is_live'])
    print(f"Live (200 OK): {live}")
    for cat, count in cats.most_common():
        print(f"  {cat}: {count}")
    print(f"\nResults saved to: {OUTPUT}")
    
    # Also save a quick JSON summary for the next script
    summary = {
        'total': len(results),
        'live': live,
        'dead_or_blocked': len(results) - live,
        'categories': dict(cats),
    }
    with open(os.path.join(WIKI, "scripts", "url_check_summary.json"), 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
