#!/usr/bin/env python3
"""Phase 3b: Re-enrich pages with better summary generation.

Fixes:
1. Better body text extraction — try multiple strategies
2. Use page_title (available for 507/615) as a real description source
3. Smarter sentence selection from body text
4. Chinese language body text handling
5. Title cleanup — many page titles are just the domain name, but the wiki title is better
"""
import os, json, csv, re, yaml
from urllib.parse import urlparse
from collections import Counter

WIKI = os.path.expanduser("~/llm-wikis/digital-china-wiki")
SCRAPE_FILE = os.path.join(WIKI, "scripts", "scraped_data.json")
CHECK_FILE = os.path.join(WIKI, "scripts", "url_check_results.csv")

with open(SCRAPE_FILE, encoding='utf-8') as f:
    scraped_data = json.load(f)
scrape_by_file = {r['file']: r for r in scraped_data}

check_by_file = {}
with open(CHECK_FILE, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        check_by_file[row['file']] = row

def clean_text(text):
    """Clean extracted text."""
    if not text:
        return ''
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove common web boilerplate
    boilerplate = [
        r'Cookie[s]?\s*(?:preferences|settings|policy|notice)?',
        r'We use cookies',
        r'This site uses cookies',
        r'JavaScript is (required|disabled)',
        r'Please enable JavaScript',
        r'Skip to (?:main )?content',
        r'Toggle navigation',
        r'Menu\s*$',
        r'Search\s*$',
        r'Close\s*$',
        r'Home\s*$',
    ]
    for bp in boilerplate:
        text = re.sub(bp, '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_sentences(text, max_chars=500):
    """Extract best sentences from text, up to max_chars."""
    if not text:
        return ''
    text = clean_text(text)
    if not text:
        return ''
    
    # Split into sentences — handle both Western and Chinese punctuation
    sentences = re.split(r'(?<=[.!?。！？])\s+', text)
    if len(sentences) <= 1:
        # Try splitting by newlines or double spaces
        sentences = re.split(r'\n+', text)
    
    good = []
    total_len = 0
    for s in sentences:
        s = s.strip()
        if len(s) < 15:
            continue
        # Skip boilerplate
        lower = s.lower()
        if any(skip in lower for skip in ['cookie', 'javascript', 'browser', 'skip to', 'toggle', 'subscribe', 'sign up', 'newsletter', 'copyright ©']):
            continue
        if total_len + len(s) > max_chars:
            # Try to fit a truncated version
            remaining = max_chars - total_len
            if remaining > 50:
                good.append(s[:remaining] + '...')
            break
        good.append(s)
        total_len += len(s)
    
    return ' '.join(good) if good else text[:max_chars]

def is_good_title(title, wiki_title=''):
    """Check if the scraped page title is meaningful (not just a domain name)."""
    if not title:
        return False
    title = title.strip()
    # If it's just the wiki title (which came from the filename), it's not useful
    if title.lower().replace(' ', '') == wiki_title.lower().replace(' ', ''):
        return False
    # Very short titles are usually not useful
    if len(title) < 10:
        return False
    return True

def generate_summary(entry, scrape_info, check_info):
    """Generate the best possible summary for an entry."""
    wiki_title = entry.get('title', '')
    url = entry.get('url', '')
    region = entry.get('region', '')
    
    scrape_status = scrape_info.get('scrape_status', '')
    
    # For live, successfully scraped pages
    if scrape_status == 'success':
        meta_desc = clean_text(scrape_info.get('meta_description', ''))
        og_desc = clean_text(scrape_info.get('og_description', ''))
        body_text = scrape_info.get('body_text', '')
        page_title = clean_text(scrape_info.get('page_title', ''))
        h1 = clean_text(scrape_info.get('h1', ''))
        
        # Strategy 1: meta description (if substantial)
        if meta_desc and len(meta_desc) > 40:
            return clean_summary(meta_desc)
        
        # Strategy 2: og_description
        if og_desc and len(og_desc) > 40:
            return clean_summary(og_desc)
        
        # Strategy 3: Extract sentences from body text
        if body_text and len(body_text) > 50:
            sentences = extract_sentences(body_text, max_chars=500)
            if len(sentences) > 40:
                return clean_summary(sentences)
        
        # Strategy 4: Use page title + h1 as context for a description
        # Clean up page title (often has site name appended)
        clean_page_title = page_title
        if clean_page_title:
            # Remove common suffixes like " - Stanford Libraries" etc
            for sep in [' - ', ' | ', ' — ', ' :: ']:
                parts = clean_page_title.split(sep)
                if len(parts) >= 2 and len(parts[0]) > 10:
                    clean_page_title = parts[0].strip()
                    break
        
        if clean_page_title and len(clean_page_title) > 15 and clean_page_title.lower() != wiki_title.lower():
            return clean_summary(f"{clean_page_title}.")
        
        # Strategy 5: Use h1
        if h1 and len(h1) > 15 and h1.lower() != wiki_title.lower():
            return clean_summary(f"{h1}.")
    
    # For non-HTML responses
    if scrape_status == 'not_html':
        return f"{wiki_title}. This resource provides data or file-based content accessible through its web interface."
    
    # For dead/blocked/unreachable — generate from context
    return generate_context_summary(entry, check_info)

def generate_context_summary(entry, check_info):
    """Generate summary from contextual clues for dead/blocked sites."""
    wiki_title = entry.get('title', '')
    url = entry.get('url', '')
    region = entry.get('region', '')
    domain = urlparse(url).netloc.lower()
    category = check_info.get('category', 'unknown')
    
    parts = []
    
    # Clean up wiki title if it's a mangled domain name
    # e.g. "Afe Easia Columbia Edu" -> use the URL instead
    clean_title = wiki_title
    if re.match(r'^[a-z0-9-]+ [a-z0-9-]+ [a-z0-9-]+$', wiki_title, re.IGNORECASE):
        # This looks like a mangled domain name — reconstruct from URL
        clean_title = ''
    
    if clean_title:
        parts.append(clean_title)
    
    # Domain-based context
    domain_context = {
        'harvard.edu': 'Harvard University',
        'stanford.edu': 'Stanford University',
        'yale.edu': 'Yale University',
        'columbia.edu': 'Columbia University',
        'princeton.edu': 'Princeton University',
        'ox.ac.uk': 'University of Oxford',
        'cam.ac.uk': 'University of Cambridge',
        'sinica.edu.tw': 'Academia Sinica, Taiwan',
        'ncl.edu.tw': 'National Central Library, Taiwan',
        'th.gov.tw': 'Taiwan Historica',
        'drnh.gov.tw': 'Academia Historica, Taiwan',
        'gov.tw': 'Taiwan government',
        'gov.cn': 'Chinese government',
        'cnki.net': 'CNKI (China National Knowledge Infrastructure)',
        'douban.com': 'Douban (Chinese social platform)',
        'archive.org': 'Internet Archive',
    }
    
    org = ''
    for d, name in domain_context.items():
        if d in domain:
            org = name
            break
    
    # URL path context
    path_lower = url.lower()
    type_desc = ''
    if any(w in path_lower for w in ['database', 'db']):
        type_desc = 'database'
    elif any(w in path_lower for w in ['catalog', 'search', 'find']):
        type_desc = 'catalog'
    elif any(w in path_lower for w in ['archive', 'collection']):
        type_desc = 'digital collection'
    elif any(w in path_lower for w in ['map', 'gis']):
        type_desc = 'map resource'
    elif any(w in path_lower for w in ['dictionary', 'dict', 'glossary']):
        type_desc = 'dictionary'
    elif any(w in path_lower for w in ['librar', 'guides', 'libguide']):
        type_desc = 'library resource'
    elif any(w in path_lower for w in ['inscription', 'epigraph', 'stele', 'rubb']):
        type_desc = 'epigraphy resource'
    elif any(w in path_lower for w in ['news', 'journal', 'periodical']):
        type_desc = 'periodical resource'
    
    # Build description
    desc = ''
    if clean_title and org:
        desc = f"{clean_title}, provided by {org}"
    elif clean_title:
        desc = clean_title
    elif org:
        desc = f"A {type_desc or 'resource'} from {org}"
    else:
        desc = f"A {type_desc or 'resource'} for Chinese and East Asian studies"
    
    if type_desc and org and clean_title:
        desc += f", is a {type_desc}"
    
    # Region
    region_map = {'prc': 'mainland China', 'taiwan': 'Taiwan', 'japan': 'Japan', 'global': 'global scope'}
    if region in region_map:
        desc += f" with a focus on {region_map[region]}"
    
    desc += '.'
    
    # Status note
    if 'dead' in category or '404' in category:
        desc += ' The site may no longer be available at this URL.'
    elif 'blocked' in category or '403' in category:
        desc += ' The site may require authentication or block automated access.'
    elif 'timeout' in category or 'connection' in category:
        desc += ' The site may be intermittently unavailable or geo-restricted.'
    
    return desc

def clean_summary(text):
    """Final cleanup of a summary."""
    text = clean_text(text)
    # Ensure it ends with a period
    if text and text[-1] not in '.!?':
        text += '.'
    return text

def infer_subjects(title, url, body_text=''):
    combined = f"{title} {url} {body_text}".lower()
    subjects = set()
    SUBJECT_MAP = {
        'history': 'chinese_history', 'dynasty': 'chinese_history', 'imperial': 'chinese_history',
        'archive': 'archival_science', 'manuscript': 'manuscript_studies',
        'library': 'library_science', 'bibliograph': 'bibliography', 'catalog': 'library_science',
        'map': 'cartography', 'cartograph': 'cartography', 'gis': 'gis', 'geograph': 'geography',
        'inscript': 'epigraphy', 'stele': 'epigraphy', 'rubb': 'epigraphy',
        'linguist': 'linguistics', 'dictionar': 'lexicography', 'lexic': 'lexicography',
        'art': 'art_history', 'painting': 'art_history', 'calligraph': 'art_history',
        'religion': 'religion', 'buddh': 'religion', 'daoist': 'religion',
        'literature': 'literature', 'poetry': 'literature', 'novel': 'literature',
        'medicine': 'medicine', 'herbal': 'medicine',
        'law': 'legal_history', 'legal': 'legal_history', 'court': 'legal_history',
        'genealog': 'genealogy',
        'newspaper': 'journalism', 'journal': 'journalism',
        'archaeol': 'archaeology', 'museum': 'museum_studies',
        'digit': 'digital_humanities', 'database': 'digital_humanities',
        'taiwan': 'taiwan_studies', 'tibet': 'tibetan_studies', 'mongol': 'mongolian_studies',
        'econom': 'economic_history', 'trade': 'economic_history',
        'politic': 'political_science', 'govern': 'political_science',
        'militar': 'military_history', 'educat': 'education', 'universit': 'education',
        'music': 'musicology', 'film': 'film_studies', 'cinema': 'film_studies',
        'photograph': 'visual_studies', 'photo': 'visual_studies',
    }
    for pattern, subject in SUBJECT_MAP.items():
        if pattern in combined:
            subjects.add(subject)
    subjects.add('east_asian_studies')
    if not subjects - {'east_asian_studies'}:
        subjects.add('chinese_studies')
    return sorted(subjects)

def infer_tags(title, url, body_text='', region=''):
    combined = f"{title} {url} {body_text}".lower()
    tags = set()
    TAG_PATTERNS = {
        'databases': ['database', 'catalog', 'search engine'],
        'maps': ['map', 'gis', 'cartograph'],
        'archives': ['archive', 'manuscript', 'special collection'],
        'digital_humanities': ['digital', 'digitiz'],
        'libraries': ['librar'],
        'museums': ['museum'],
        'reference_works': ['dictionar', 'encyclop', 'glossary', 'handbook'],
        'periodicals': ['newspaper', 'news', 'journal', 'periodical', 'magazine'],
        'epigraphy': ['inscript', 'stele', 'epigraph', 'rubb'],
        'statistical_data': ['statistic', 'census', 'data'],
        'open_access': ['open access', 'free access', 'oai'],
        'primary_sources': ['primary source', 'historical document', 'original document'],
    }
    for tag, patterns in TAG_PATTERNS.items():
        if any(p in combined for p in patterns):
            tags.add(tag)
    region_tags = {'prc': 'prc', 'taiwan': 'taiwan', 'japan': 'japan'}
    if region in region_tags:
        tags.add(region_tags[region])
    return sorted(tags) if tags else ['digital_humanities']

def update_wiki_file(filepath, entry, summary, tags, subjects, description, site_status='live'):
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return False
    
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except:
        return False
    
    fm['description'] = description
    existing_tags = fm.get('tags', [])
    if isinstance(existing_tags, list):
        fm['tags'] = sorted(set(existing_tags + tags))
    else:
        fm['tags'] = sorted(tags)
    existing_subjects = fm.get('subjects', [])
    if isinstance(existing_subjects, list):
        fm['subjects'] = sorted(set(existing_subjects + subjects))
    else:
        fm['subjects'] = sorted(subjects)
    
    if site_status != 'live':
        fm['site_status'] = site_status
    elif 'site_status' in fm:
        del fm['site_status']
    
    fm['updated'] = '2026-04-18'
    
    new_fm = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    url = fm.get('url', '') or fm.get('canonical_url', '')
    lang = fm.get('language', '')
    region = fm.get('region', '')
    region_label = {'prc': 'China', 'taiwan': 'Taiwan', 'japan': 'Japan', 'global': 'Global'}.get(region, region)
    lang_map = {'zh': 'Chinese', 'en': 'English', 'ja': 'Japanese', 'zh_en': 'Chinese/English', 'multi': 'Multilingual'}
    lang_label = lang_map.get(lang, lang)
    
    body = f"\n# {fm.get('title', 'Untitled')}\n\n"
    body += f"**URL:** {url}\n\n"
    if lang_label:
        body += f"**Language:** {lang_label.title()}\n\n"
    if region_label and region_label != region:
        body += f"**Region:** {region_label}\n\n"
    
    proxy = fm.get('access_via_harvard', '')
    if proxy:
        body += f"**Harvard Access:** {proxy}\n\n"
    
    body += f"## Summary\n\n{summary}\n"
    
    if site_status != 'live':
        body += f"\n> ⚠️ **Note:** This resource may be currently unavailable or require special access. "
        if 'harvard' in url.lower() or 'hollis' in url.lower():
            body += "Try accessing through a university library portal.\n"
        elif '.gov.cn' in url or '.edu.cn' in url:
            body += "Chinese government and academic sites may be geo-restricted.\n"
        else:
            body += "The original URL may have changed or the resource has been archived.\n"
    
    new_content = f"---\n{new_fm}---{body}\n"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True

def main():
    updated = 0
    updated_live = 0
    updated_dead = 0
    errors = 0
    short_summaries = 0
    
    for subdir in ['websites', 'databases', 'news', 'maps', 'tools']:
        dp = os.path.join(WIKI, subdir)
        if not os.path.isdir(dp):
            continue
        for f in sorted(os.listdir(dp)):
            if not f.endswith('.md'):
                continue
            filepath = os.path.join(dp, f)
            with open(filepath, encoding='utf-8') as fh:
                content = fh.read()
            # Process ALL stubs (still have the marker) or previously enriched with bad summaries
            parts = content.split('---', 2)
            if len(parts) < 3:
                continue
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except:
                continue
            
            body = parts[2]
            # Check if this needs enrichment
            has_stub_marker = '*Awaiting full description.*' in body
            has_short_summary = False
            if '## Summary' in body:
                summary_section = body.split('## Summary')[1].strip().split('\n')[0]
                if len(summary_section) < 30 or summary_section.startswith('Resource:'):
                    has_short_summary = True
            
            if not has_stub_marker and not has_short_summary:
                continue
            
            entry = {
                'file': f, 'path': filepath,
                'url': fm.get('url', ''), 'title': fm.get('title', ''),
                'type': fm.get('type', ''), 'region': fm.get('region', ''),
                'language': fm.get('language', ''),
            }
            
            check_info = check_by_file.get(f, {})
            scrape_info = scrape_by_file.get(f, {})
            
            category = check_info.get('category', 'unknown')
            is_live = check_info.get('is_live', 'False') == 'True'
            scrape_status = scrape_info.get('scrape_status', '')
            
            if is_live and scrape_status == 'success':
                site_status = 'live'
            elif is_live and scrape_status == 'not_html':
                site_status = 'live'
            elif 'dead' in category or '404' in category:
                site_status = 'dead'
            elif 'blocked' in category or '403' in category:
                site_status = 'access_restricted'
            elif 'timeout' in category or 'connection' in category:
                site_status = 'unreachable'
            else:
                site_status = 'unknown'
            
            body_for_inference = scrape_info.get('body_text', '') if scrape_status == 'success' else ''
            summary = generate_summary(entry, scrape_info, check_info)
            tags = infer_tags(entry['title'], entry['url'], body_for_inference, entry.get('region', ''))
            subjects = infer_subjects(entry['title'], entry['url'], body_for_inference)
            
            description = summary[:200].rstrip()
            if len(summary) > 200:
                last_period = description.rfind('.')
                if last_period > 80:
                    description = description[:last_period + 1]
                else:
                    description += '...'
            
            if len(summary) < 30:
                short_summaries += 1
            
            ok = update_wiki_file(filepath, entry, summary, tags, subjects, description, site_status)
            if ok:
                updated += 1
                if site_status == 'live':
                    updated_live += 1
                else:
                    updated_dead += 1
            else:
                errors += 1
    
    print(f"{'='*60}")
    print(f"RE-ENRICHMENT COMPLETE")
    print(f"{'='*60}")
    print(f"Updated: {updated} pages")
    print(f"  Live: {updated_live}")
    print(f"  Dead/blocked: {updated_dead}")
    print(f"  Short summaries (<30 chars): {short_summaries}")
    print(f"  Errors: {errors}")

if __name__ == '__main__':
    main()
