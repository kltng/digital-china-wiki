#!/usr/bin/env python3
"""Phase 3+4: Generate descriptions and write back enriched wiki pages.

For each of the 820 stub pages:
- If scraped data exists: use page_title, meta_description, body_text to generate summary
- If dead/blocked: generate summary from title + URL + domain context
- Enrich frontmatter: add description, update tags/subjects
- Write updated .md files
"""
import os, json, csv, re, yaml
from urllib.parse import urlparse
from collections import Counter

WIKI = os.path.expanduser("~/llm-wikis/digital-china-wiki")
SCRAPE_FILE = os.path.join(WIKI, "scripts", "scraped_data.json")
CHECK_FILE = os.path.join(WIKI, "scripts", "url_check_results.csv")

# Load scraped data
with open(SCRAPE_FILE, encoding='utf-8') as f:
    scraped_data = json.load(f)
scrape_by_file = {r['file']: r for r in scraped_data}

# Load URL check results
check_by_file = {}
with open(CHECK_FILE, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        check_by_file[row['file']] = row

# Subject mapping heuristics
SUBJECT_MAP = {
    'history': 'chinese_history',
    'dynasty': 'chinese_history',
    'imperial': 'chinese_history',
    'archive': 'archival_science',
    'manuscript': 'manuscript_studies',
    'library': 'library_science',
    'bibliograph': 'bibliography',
    'catalog': 'library_science',
    'map': 'cartography',
    'cartograph': 'cartography',
    'gis': 'gis',
    'geograph': 'geography',
    'inscript': 'epigraphy',
    'stele': 'epigraphy',
    'rubb': 'epigraphy',
    'linguist': 'linguistics',
    'language': 'linguistics',
    'dictionar': 'lexicography',
    'lexic': 'lexicography',
    'art': 'art_history',
    'painting': 'art_history',
    'calligraph': 'art_history',
    'religion': 'religion',
    'buddh': 'religion',
    'daoist': 'religion',
    'confucia': 'philosophy',
    'philosoph': 'philosophy',
    'literature': 'literature',
    'poetry': 'literature',
    'novel': 'literature',
    'medicine': 'medicine',
    'medical': 'medicine',
    'herbal': 'medicine',
    'law': 'legal_history',
    'legal': 'legal_history',
    'court': 'legal_history',
    'genealog': 'genealogy',
    'family': 'social_history',
    'clan': 'social_history',
    'newspaper': 'journalism',
    'journal': 'journalism',
    'periodical': 'journalism',
    'statistic': 'statistics',
    'census': 'demography',
    'population': 'demography',
    'archaeol': 'archaeology',
    'excavat': 'archaeology',
    'museum': 'museum_studies',
    'digit': 'digital_humanities',
    'database': 'digital_humanities',
    'digital': 'digital_humanities',
    'taiwan': 'taiwan_studies',
    'tibet': 'tibetan_studies',
    'mongol': 'mongolian_studies',
    'manchu': 'manchu_studies',
    'islam': 'islamic_studies',
    'christia': 'christianity_in_china',
    'missionar': 'christianity_in_china',
    'jesuit': 'christianity_in_china',
    'econom': 'economic_history',
    'trade': 'economic_history',
    'commer': 'economic_history',
    'politic': 'political_science',
    'govern': 'political_science',
    'militar': 'military_history',
    'war': 'military_history',
    'educat': 'education',
    'universit': 'education',
    'academic': 'education',
    'music': 'musicology',
    'theatr': 'performing_arts',
    'opera': 'performing_arts',
    'film': 'film_studies',
    'cinema': 'film_studies',
    'photograph': 'visual_studies',
    'photo': 'visual_studies',
}

def infer_subjects(title, url, body_text=''):
    """Infer academic subjects from title, URL, and body text."""
    combined = f"{title} {url} {body_text}".lower()
    subjects = set()
    for pattern, subject in SUBJECT_MAP.items():
        if pattern in combined:
            subjects.add(subject)
    # Always add east_asian_studies if China-related
    subjects.add('east_asian_studies')
    if not subjects - {'east_asian_studies'}:
        subjects.add('chinese_studies')
    return sorted(subjects)

def infer_tags(title, url, body_text='', region=''):
    """Infer content tags."""
    combined = f"{title} {url} {body_text}".lower()
    tags = set()
    
    # Type tags
    if 'database' in combined or 'catalog' in combined or 'search' in combined:
        tags.add('databases')
    if 'map' in combined or 'gis' in combined or 'cartograph' in combined:
        tags.add('maps')
    if 'archive' in combined or 'manuscript' in combined:
        tags.add('archives')
    if 'digit' in combined or 'digital' in combined:
        tags.add('digital_humanities')
    if 'librar' in combined:
        tags.add('libraries')
    if 'museum' in combined:
        tags.add('museums')
    if 'dictionar' in combined or 'encyclop' in combined:
        tags.add('reference_works')
    if 'newspaper' in combined or 'news' in combined or 'periodical' in combined:
        tags.add('periodicals')
    if 'inscript' in combined or 'stele' in combined or 'epigraph' in combined:
        tags.add('epigraphy')
    if 'statistic' in combined or 'data' in combined:
        tags.add('statistical_data')
    if 'open.access' in combined or 'free' in combined:
        tags.add('open_access')
    
    # Region tags
    if region == 'prc':
        tags.add('prc')
    elif region == 'taiwan':
        tags.add('taiwan')
    elif region == 'japan':
        tags.add('japan')
    
    return sorted(tags) if tags else ['digital_humanities']

def generate_summary_from_scrape(entry, scrape):
    """Generate a summary from scraped data."""
    parts = []
    
    title = scrape.get('page_title', '') or scrape.get('h1', '') or entry.get('title', '')
    meta_desc = scrape.get('meta_description', '')
    body_text = scrape.get('body_text', '')
    og_desc = scrape.get('og_description', '')
    
    # Use the best description source
    if meta_desc and len(meta_desc) > 30:
        summary = meta_desc.strip()
    elif og_desc and len(og_desc) > 30:
        summary = og_desc.strip()
    elif body_text and len(body_text) > 50:
        # Take first 1-2 meaningful sentences from body text
        sentences = re.split(r'(?<=[.!?])\s+', body_text)
        good_sentences = [s.strip() for s in sentences if len(s.strip()) > 20 and not s.strip().startswith(('Cookie', 'We use', 'JavaScript', 'This website'))]
        if good_sentences:
            summary = ' '.join(good_sentences[:3])
        else:
            summary = body_text[:500].strip()
    else:
        # Fallback: use title
        summary = f"Resource: {entry.get('title', 'Untitled')}."
    
    # Clean up
    summary = re.sub(r'\s+', ' ', summary).strip()
    if len(summary) > 600:
        # Truncate at last sentence boundary
        truncated = summary[:600]
        last_period = truncated.rfind('.')
        if last_period > 300:
            summary = truncated[:last_period + 1]
        else:
            summary = truncated + '...'
    
    return summary

def generate_summary_from_context(entry, check_info):
    """Generate a summary from title + URL context for dead/blocked sites."""
    title = entry.get('title', '')
    url = entry.get('url', '')
    region = entry.get('region', '')
    
    parsed = urlparse(url)
    domain = parsed.netloc
    
    # Build a contextual description
    desc_parts = []
    
    # Start with title-based description
    desc_parts.append(f"{title}")
    
    # Add domain context
    if 'harvard.edu' in domain:
        desc_parts.append("a Harvard University resource")
    elif 'stanford.edu' in domain:
        desc_parts.append("a Stanford University resource")
    elif 'yale.edu' in domain:
        desc_parts.append("a Yale University resource")
    elif 'columbia.edu' in domain:
        desc_parts.append("a Columbia University resource")
    elif 'ox.ac.uk' in domain:
        desc_parts.append("an Oxford University resource")
    elif 'sinica.edu.tw' in domain:
        desc_parts.append("an Academia Sinica (Taiwan) resource")
    elif '.gov.cn' in domain:
        desc_parts.append("a Chinese government resource")
    elif '.edu.cn' in domain:
        desc_parts.append("a Chinese academic institution resource")
    elif 'cnki' in domain:
        desc_parts.append("a CNKI (China National Knowledge Infrastructure) resource")
    
    # Region context
    if region == 'prc':
        desc_parts.append("focusing on mainland China")
    elif region == 'taiwan':
        desc_parts.append("focusing on Taiwan")
    elif region == 'japan':
        desc_parts.append("related to Japan and East Asian studies")
    
    # Status note
    category = check_info.get('category', '')
    if 'dead' in category or '404' in category:
        desc_parts.append("The original site appears to be no longer available (404 error)")
    elif 'blocked' in category or '403' in category:
        desc_parts.append("The site blocks automated access")
    elif 'timeout' in category or 'connection' in category:
        desc_parts.append("The site may be intermittently unavailable or geo-restricted")
    
    summary = '. '.join(desc_parts) + '.'
    return summary

def update_wiki_file(filepath, entry, summary, tags, subjects, description, site_status='live'):
    """Update a wiki markdown file with enriched content."""
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return False
    
    # Parse frontmatter
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except:
        return False
    
    # Update frontmatter
    fm['description'] = description
    if tags:
        existing_tags = fm.get('tags', [])
        if isinstance(existing_tags, list):
            merged = sorted(set(existing_tags + tags))
        else:
            merged = sorted(set(tags))
        fm['tags'] = merged
    if subjects:
        existing_subjects = fm.get('subjects', [])
        if isinstance(existing_subjects, list):
            merged = sorted(set(existing_subjects + subjects))
        else:
            merged = sorted(set(subjects))
        fm['subjects'] = merged
    
    if site_status != 'live':
        fm['site_status'] = site_status
    
    fm['updated'] = '2026-04-18'
    
    # Reconstruct file
    new_fm = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    # Build body
    url = fm.get('url', '') or fm.get('canonical_url', '')
    lang = fm.get('language', '')
    region_label = {'prc': 'China', 'taiwan': 'Taiwan', 'japan': 'Japan', 'global': 'Global'}.get(fm.get('region', ''), fm.get('region', ''))
    lang_label = {'zh': 'Chinese', 'en': 'English', 'ja': 'Japanese', 'zh_en': 'Chinese/English', 'multi': 'Multilingual'}.get(lang, lang)
    
    body = f"\n# {fm.get('title', 'Untitled')}\n\n"
    body += f"**URL:** {url}\n\n"
    if lang_label:
        body += f"**Language:** {lang_label.title()}\n\n"
    if region_label:
        body += f"**Region:** {region_label}\n\n"
    
    # Add Harvard proxy link if available
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
            if '*Awaiting full description.*' not in content:
                continue
            
            parts = content.split('---', 2)
            if len(parts) < 3:
                continue
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except:
                continue
            
            entry = {
                'file': f,
                'path': filepath,
                'url': fm.get('url', ''),
                'title': fm.get('title', ''),
                'type': fm.get('type', ''),
                'region': fm.get('region', ''),
                'language': fm.get('language', ''),
            }
            
            check_info = check_by_file.get(f, {})
            scrape_info = scrape_by_file.get(f, {})
            scrape_status = scrape_info.get('scrape_status', '')
            
            # Determine site status
            category = check_info.get('category', 'unknown')
            is_live = check_info.get('is_live', 'False') == 'True'
            
            if is_live and scrape_status == 'success':
                site_status = 'live'
                summary = generate_summary_from_scrape(entry, scrape_info)
                body_for_inference = scrape_info.get('body_text', '')
            elif is_live and scrape_status in ('not_html',):
                site_status = 'live'
                # Use what we have from the title
                summary = f"{entry['title']}. This resource provides non-HTML content (possibly a data API or file download)."
                body_for_inference = ''
            else:
                # Dead/blocked
                if 'dead' in category or '404' in category:
                    site_status = 'dead'
                elif 'blocked' in category or '403' in category:
                    site_status = 'access_restricted'
                elif 'timeout' in category:
                    site_status = 'unreachable'
                elif 'connection' in category:
                    site_status = 'unreachable'
                else:
                    site_status = 'unknown'
                summary = generate_summary_from_context(entry, check_info)
                body_for_inference = ''
            
            # Generate tags and subjects
            tags = infer_tags(entry['title'], entry['url'], body_for_inference, entry.get('region', ''))
            subjects = infer_subjects(entry['title'], entry['url'], body_for_inference)
            
            # Short description for frontmatter (first ~200 chars of summary)
            description = summary[:200].rstrip()
            if len(summary) > 200:
                # Don't cut mid-sentence in frontmatter
                last_period = description.rfind('.')
                if last_period > 100:
                    description = description[:last_period + 1]
                else:
                    description += '...'
            
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
    print(f"ENRICHMENT COMPLETE")
    print(f"{'='*60}")
    print(f"Updated: {updated} pages")
    print(f"  Live (scraped): {updated_live}")
    print(f"  Dead/blocked (context-generated): {updated_dead}")
    print(f"  Errors: {errors}")

if __name__ == '__main__':
    main()
