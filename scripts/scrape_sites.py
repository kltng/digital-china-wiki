#!/usr/bin/env python3
"""Phase 2: Scrape live sites and extract metadata for wiki enrichment."""
import os, csv, json, time, re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

WIKI = os.path.expanduser("~/llm-wikis/digital-china-wiki")
CHECK_RESULTS = os.path.join(WIKI, "scripts", "url_check_results.csv")
OUTPUT = os.path.join(WIKI, "scripts", "scraped_data.json")
TIMEOUT = 20
MAX_WORKERS = 6
MAX_BODY_CHARS = 3000  # limit extracted text per page

def load_live_entries():
    """Load entries that were marked as live from the URL check."""
    entries = []
    with open(CHECK_RESULTS, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['is_live'] == 'True':
                entries.append(row)
    return entries

def extract_metadata(soup, url):
    """Extract structured metadata from a BeautifulSoup parsed page."""
    meta = {
        'page_title': '',
        'meta_description': '',
        'meta_keywords': '',
        'og_title': '',
        'og_description': '',
        'og_type': '',
        'h1': '',
        'body_text': '',
        'language': '',
        'links_count': 0,
        'has_search': False,
        'has_database': False,
        'nav_items': [],
    }
    
    # Title
    if soup.title and soup.title.string:
        meta['page_title'] = soup.title.string.strip()[:300]
    
    # Meta description
    desc = soup.find('meta', attrs={'name': 'description'})
    if desc and desc.get('content'):
        meta['meta_description'] = desc['content'].strip()[:500]
    
    # Meta keywords
    kw = soup.find('meta', attrs={'name': 'keywords'})
    if kw and kw.get('content'):
        meta['meta_keywords'] = kw['content'].strip()[:300]
    
    # Open Graph
    for prop in ['og:title', 'og:description', 'og:type']:
        tag = soup.find('meta', attrs={'property': prop})
        if tag and tag.get('content'):
            key = prop.replace('og:', 'og_')
            meta[key] = tag['content'].strip()[:500]
    
    # H1
    h1 = soup.find('h1')
    if h1:
        meta['h1'] = h1.get_text(strip=True)[:300]
    
    # Language
    html_tag = soup.find('html')
    if html_tag and html_tag.get('lang'):
        meta['language'] = html_tag['lang']
    
    # Body text extraction — get meaningful paragraphs
    body = soup.find('body')
    if body:
        # Remove script, style, nav, footer, header elements
        for tag in body.find_all(['script', 'style', 'nav', 'footer', 'header', 'noscript']):
            tag.decompose()
        
        # Get text from paragraphs, lists, divs with substantial content
        texts = []
        for el in body.find_all(['p', 'li', 'dd', 'dt', 'td', 'blockquote']):
            text = el.get_text(strip=True)
            if len(text) > 20 and not text.startswith(('Cookie', 'We use cookies', 'This site uses', 'JavaScript is required')):
                texts.append(text)
        
        combined = ' '.join(texts)
        if len(combined) > MAX_BODY_CHARS:
            combined = combined[:MAX_BODY_CHARS] + '...'
        meta['body_text'] = combined
    
    # Count links
    if body:
        meta['links_count'] = len(body.find_all('a', href=True))
    
    # Detect search functionality
    search_inputs = soup.find_all('input', attrs={'type': 'search'})
    search_forms = soup.find_all('form', attrs={'role': 'search'})
    meta['has_search'] = bool(search_inputs or search_forms)
    
    # Detect database-like features
    db_keywords = ['database', 'search', 'catalog', 'archive', 'repository', 'collection', 'digital archive']
    page_text_lower = (meta['body_text'] + ' ' + meta['meta_description']).lower()
    meta['has_database'] = any(kw in page_text_lower for kw in db_keywords)
    
    return meta

def scrape_entry(entry):
    """Scrape a single live entry."""
    url = entry.get('final_url') or entry['url']
    if not url.startswith('http'):
        url = entry['url']
    
    result = {
        'file': entry['file'],
        'subdir': entry['subdir'],
        'title': entry['title'],
        'original_url': entry['url'],
        'fetched_url': url,
        'scrape_status': 'unknown',
        'error': '',
    }
    
    try:
        resp = requests.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            }
        )
        
        result['final_url'] = resp.url
        content_type = resp.headers.get('Content-Type', '')
        
        if resp.status_code != 200:
            result['scrape_status'] = f'http_{resp.status_code}'
            return result
        
        # Only parse HTML
        if 'text/html' not in content_type and 'application/xhtml' not in content_type:
            result['scrape_status'] = 'not_html'
            result['content_type'] = content_type
            return result
        
        # Parse
        soup = BeautifulSoup(resp.text, 'lxml')
        meta = extract_metadata(soup, url)
        result.update(meta)
        result['scrape_status'] = 'success'
        
    except requests.exceptions.Timeout:
        result['scrape_status'] = 'timeout'
        result['error'] = 'Connection timed out'
    except requests.exceptions.ConnectionError as e:
        result['scrape_status'] = 'connection_error'
        result['error'] = str(e)[:200]
    except Exception as e:
        result['scrape_status'] = 'error'
        result['error'] = str(e)[:200]
    
    return result

def main():
    entries = load_live_entries()
    print(f"Loaded {len(entries)} live entries to scrape")
    
    results = []
    done = 0
    success = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(scrape_entry, entry): entry for entry in entries}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            done += 1
            if result['scrape_status'] == 'success':
                success += 1
            if done % 50 == 0:
                print(f"  Scraped {done}/{len(entries)} ({success} successful)")
    
    # Sort by file order
    results.sort(key=lambda r: (r['subdir'], r['file']))
    
    # Save
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    
    # Summary
    from collections import Counter
    statuses = Counter(r['scrape_status'] for r in results)
    print(f"\n{'='*60}")
    print(f"SCRAPE RESULTS: {len(results)} attempted")
    print(f"{'='*60}")
    for status, count in statuses.most_common():
        print(f"  {status}: {count}")
    
    # Sample a successful scrape
    successful = [r for r in results if r['scrape_status'] == 'success']
    if successful:
        print(f"\nSample successful scrape: {successful[0]['file']}")
        print(f"  Title: {successful[0].get('page_title', 'N/A')[:80]}")
        print(f"  Meta desc: {successful[0].get('meta_description', 'N/A')[:120]}")
        print(f"  Body text ({len(successful[0].get('body_text', ''))} chars): {successful[0].get('body_text', '')[:200]}...")
    
    print(f"\nResults saved to: {OUTPUT}")

if __name__ == '__main__':
    main()
