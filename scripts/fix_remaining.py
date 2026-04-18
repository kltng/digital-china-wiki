#!/usr/bin/env python3
"""Phase 3c: Fix remaining poor summaries with domain-aware intelligent fallbacks."""
import os, yaml, re
from urllib.parse import urlparse

WIKI = os.path.expanduser("~/llm-wikis/digital-china-wiki")

# Known resource descriptions by domain or URL pattern
KNOWN_RESOURCES = {
    'afe.easia.columbia.edu': 'Asia for Educators (AFE) is an initiative of Columbia University\'s Weatherhead East Asian Institute that provides educational resources about East Asia for teachers and students. It features primary sources, teaching guides, and multimedia materials covering Chinese history, culture, literature, and society.',
    'www.chant.org': 'The CHANT (CHinese ANcient Texts) database, maintained by the Chinese University of Hong Kong, is a comprehensive digital collection of ancient Chinese texts spanning from the oracle bone inscriptions to the Six Dynasties period. It includes ancient texts, excavated materials, and bamboo and silk manuscripts.',
    'dict.revised.moe.edu.tw': 'The Revised Dictionary of Chinese Language (《重編國語辭典修訂本》) is the authoritative Chinese language dictionary published by Taiwan\'s Ministry of Education. It provides comprehensive definitions, pronunciation, and usage examples for standard Chinese characters and compounds.',
    'twitter.com/HarvardLibrary': 'Harvard Library\'s official X/Twitter account, providing updates about library services, collections, digital resources, events, and access information for Harvard University\'s extensive library system.',
    'oversea.cnki.net': 'CNKI (China National Knowledge Infrastructure) is the largest academic database in China, providing access to journal articles, dissertations, conference papers, newspapers, and reference works across all academic disciplines. The overseas portal provides English-language access to Chinese scholarly content.',
    'eastview.com': 'East View Information Services provides access to a wide range of academic databases, digital collections, and primary source materials from Russia, China, and other regions. Their products include e-Library databases for Chinese academic content, statistical yearbooks, and historical archives.',
    'newsbank.com': 'NewsBank provides access to news media databases, including the Foreign Broadcast Information Service (FBIS) Daily Reports and other historical and contemporary news archives relevant to Chinese and East Asian studies.',
    'apps.eastview.com': 'East View\'s digital platform provides access to Chinese academic databases, statistical yearbooks, historical archives, and government publications. Resources include Chinese census data, local gazetteers, and policy documents.',
    'p.udpweb.com': 'United Digital Publications (UDP) provides access to digital archives and databases covering Chinese studies, including periodicals, historical documents, and reference materials. Titles include LionArt, Repertoire of Chinese Classics, and other specialized collections.',
    'arcgis.com': 'An ArcGIS-based digital collection or mapping resource for Chinese studies, providing geospatial data, historical maps, and interactive visualizations related to China and East Asia.',
    'hollis.harvard.edu': 'HOLLIS is Harvard Library\'s online catalog and discovery system, providing access to the university\'s vast collections including books, journals, digital resources, archives, and special collections related to Chinese and East Asian studies.',
    'searchworks.stanford.edu': 'SearchWorks is Stanford University Libraries\' online catalog, providing access to books, journals, databases, digital collections, and special collections with significant holdings in Chinese and East Asian studies.',
    'web.library.yale.edu': 'Yale University Library\'s online portal provides access to one of the largest East Asian library collections in North America, including rare books, manuscripts, archival materials, and digital resources for Chinese studies.',
    'guides.library.stanford.edu': 'Stanford Libraries\' research guides provide curated information about resources for Chinese and East Asian studies, including databases, archives, digital collections, and bibliographic tools.',
    'guides.library.harvard.edu': 'Harvard Library research guides offer curated lists of resources, databases, archives, and tools for research in Chinese and East Asian studies, organized by subject and region.',
    'curiosity.lib.harvard.edu': 'Harvard Library\'s Curiosity platform provides access to digitized collections from Harvard\'s museums, libraries, and archives, including historical photographs, manuscripts, maps, and other primary sources related to China and East Asia.',
    'images.hollis.harvard.edu': 'Harvard Visual Information Access (VIA) provides access to images from Harvard\'s collections, including historical photographs, art, maps, and visual materials related to Chinese and East Asian studies.',
    'nrs.harvard.edu': 'Harvard\'s Name Resolution Service provides persistent URLs for accessing Harvard Library\'s digital resources, including online databases, digitized collections, ejournals, and archival materials.',
    'catalog.digitalarchives.tw': 'Taiwan\'s National Archives Administration provides a searchable catalog of government archives, historical documents, and official records spanning Taiwan\'s history from the Qing dynasty through the Japanese colonial period to the present.',
    'inscription.ancientbooks.cn': 'The Chinese Stone Inscription Database provides access to digitized rubbings and transcriptions of historical stone inscriptions, stele, and epigraphic materials from China, supporting research in epigraphy, paleography, and historical studies.',
    'library.harvard.edu': 'Harvard Library is one of the world\'s largest academic library systems, with extensive collections in Chinese and East Asian studies including the Harvard-Yenching Library, rare books, manuscripts, and digital resources.',
    'drnh.gov.tw': 'Academia Historica (國史館) in Taiwan holds extensive archival materials documenting Taiwan\'s history, including government records from the Qing dynasty, Japanese colonial period, and Republic of China era.',
    'th.gov.tw': 'Taiwan Historica (臺灣文獻館) preserves and provides access to historical documents and materials related to Taiwan\'s history, including local gazetteers, official records, and cultural artifacts.',
    'ncl.edu.tw': 'The National Central Library of Taiwan (國家圖書館) is the national bibliographic center, providing access to books, periodicals, digital archives, government publications, and special collections in Taiwanese and Chinese studies.',
}

def get_domain_description(url):
    """Get a known description for a domain, or None."""
    try:
        domain = urlparse(url).netloc.lower()
        for known_domain, desc in KNOWN_RESOURCES.items():
            if known_domain in domain or domain in known_domain:
                return desc
    except:
        pass
    return None

def is_mangled_title(title):
    """Check if the title looks like it was derived from a URL slug."""
    # e.g., "Afe Easia Columbia Edu" or "Https Www Example Com"
    words = title.split()
    if len(words) >= 3:
        # Check if most words look like URL parts
        url_like = sum(1 for w in words if w.lower() in ('www', 'http', 'https', 'com', 'edu', 'org', 'net', 'gov', 'tw', 'cn') or '.' in w.lower())
        if url_like >= 2:
            return True
    return False

def clean_title(title):
    """Clean up a mangled title into something readable."""
    # Remove common URL artifacts
    title = re.sub(r'\bhttps?\b', '', title, flags=re.IGNORECASE).strip()
    title = re.sub(r'\bwww\b', '', title, flags=re.IGNORECASE).strip()
    # Remove file extensions
    title = re.sub(r'\.(html?|php|aspx?|pdf)$', '', title, flags=re.IGNORECASE)
    return title

def main():
    fixed = 0
    
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
            
            parts = content.split('---', 2)
            if len(parts) < 3:
                continue
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except:
                continue
            
            body = parts[2]
            
            # Check if needs fixing
            if '## Summary' not in body:
                continue
            
            summary_text = body.split('## Summary')[1].strip().split('\n>')[0].strip()
            
            # Detect poor summaries
            needs_fix = False
            if len(summary_text) < 30:
                needs_fix = True
            elif summary_text.startswith('Resource:'):
                needs_fix = True
            elif any(bad in summary_text for bad in ['Log In to Browse', 'JavaScript is not available', '個人帳號 - 登入', 'Dashboards', 'Web Application']):
                needs_fix = True
            # Check for garbled encoding (mojibake)
            elif any(c in summary_text for c in ['ä¸', 'å¯', 'èº', 'æ']):
                needs_fix = True
            
            if not needs_fix:
                continue
            
            url = fm.get('url', '')
            title = fm.get('title', '')
            region = fm.get('region', '')
            
            # Try to get a known description
            new_summary = get_domain_description(url)
            
            if not new_summary:
                # Generate from context
                domain = urlparse(url).netloc.lower()
                path = urlparse(url).path.lower()
                
                # Identify institution
                institution = ''
                for d, inst in [
                    ('harvard.edu', 'Harvard University'),
                    ('stanford.edu', 'Stanford University'),
                    ('yale.edu', 'Yale University'),
                    ('columbia.edu', 'Columbia University'),
                    ('sinica.edu.tw', 'Academia Sinica'),
                    ('ncl.edu.tw', 'National Central Library (Taiwan)'),
                    ('eastview.com', 'East View Information Services'),
                    ('cnki.net', 'CNKI'),
                ]:
                    if d in domain:
                        institution = inst
                        break
                
                # Identify resource type from URL path
                res_type = 'resource'
                type_map = [
                    (['census', 'population'], 'population census database'),
                    (['gazetteer', 'fangzhi', 'local'], 'local gazetteer database'),
                    (['periodical', 'magazine', 'journal'], 'periodical database'),
                    (['image', 'photo', 'picture'], 'digital image collection'),
                    (['map', 'gis'], 'digital map collection'),
                    (['inscript', 'stele', 'epigraph'], 'epigraphy database'),
                    (['newspaper', 'news'], 'newspaper database'),
                    (['statistic', 'yearbook'], 'statistical database'),
                    (['dictionary', 'dict'], 'digital dictionary'),
                    (['archive'], 'digital archive'),
                    (['catalog', 'search'], 'searchable catalog'),
                ]
                for keywords, rtype in type_map:
                    if any(k in url.lower() for k in keywords):
                        res_type = rtype
                        break
                
                # Clean title
                clean_t = title if not is_mangled_title(title) else ''
                
                parts_desc = []
                if clean_t:
                    parts_desc.append(clean_t)
                elif institution:
                    parts_desc.append(f"A {res_type} from {institution}")
                else:
                    parts_desc.append(f"A {res_type} for Chinese and East Asian studies")
                
                if institution and clean_t:
                    parts_desc.append(f"provided by {institution}")
                
                region_names = {'prc': 'mainland China', 'taiwan': 'Taiwan', 'japan': 'Japan'}
                if region in region_names:
                    parts_desc.append(f"focusing on {region_names[region]}")
                
                new_summary = '. '.join(parts_desc) + '.'
            
            if not new_summary:
                continue
            
            # Update the file
            # Replace summary section
            old_summary_match = re.search(r'(## Summary\s*\n\n)(.*?)(\n\n>|\n$|$)', body, re.DOTALL)
            if old_summary_match:
                new_body = body[:old_summary_match.start()] + f"## Summary\n\n{new_summary}" + body[old_summary_match.end():]
            else:
                # Append summary
                new_body = body + f"\n\n## Summary\n\n{new_summary}"
            
            # Update frontmatter description
            fm['description'] = new_summary[:200].rstrip()
            if len(new_summary) > 200:
                last_p = fm['description'].rfind('.')
                if last_p > 80:
                    fm['description'] = fm['description'][:last_p + 1]
                else:
                    fm['description'] += '...'
            fm['updated'] = '2026-04-18'
            
            new_fm = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
            new_content = f"---\n{new_fm}---{new_body}\n"
            
            with open(filepath, 'w', encoding='utf-8') as fh:
                fh.write(new_content)
            fixed += 1
    
    print(f"Fixed {fixed} additional pages with poor summaries")

if __name__ == '__main__':
    main()
