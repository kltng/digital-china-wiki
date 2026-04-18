#!/usr/bin/env python3
"""Phase 1: Build the complete old-tag → controlled-vocabulary mapping."""
import os, yaml, json
from collections import Counter

WIKI = os.path.expanduser("~/llm-wikis/digital-china-wiki")

# ============================================================
# CONTROLLED VOCABULARY
# ============================================================
VALID_TAGS = {
    # Axis 1: Resource Type
    'archive', 'bibliography', 'catalog', 'database', 'dictionary',
    'ebook', 'film_video', 'full_text', 'gis', 'guide', 'map',
    'newspaper', 'organization', 'periodical', 'photo', 'platform',
    'statistical', 'tool', 'social_media', 'website',
    # Axis 2: Content Topic
    'art_history', 'book_history', 'buddhism', 'christianity', 'classics',
    'cold_war', 'colonialism', 'digital_humanities', 'economic_history',
    'epigraphy', 'film_studies', 'genealogy', 'geography',
    'intellectual_history', 'language', 'legal_history', 'literature',
    'maritime', 'medicine', 'military_history', 'music', 'museum_studies',
    'newspaper_studies', 'open_access', 'philosophy', 'political_science',
    'rare_books', 'religion', 'social_history', 'statistics',
    # Axis 3: Region
    'prc', 'taiwan', 'japan', 'hong_kong', 'korea', 'global',
}

# ============================================================
# MAPPING: old tag → list of new tags
# ============================================================
TAG_MAP = {
    # --- Resource Type mappings ---
    'databases': ['database'],
    'database': ['database'],
    'academic_database': ['database'],
    'academic_databases': ['database'],
    'libraries': ['catalog'],
    'library_science': ['catalog'],
    'library_services': ['catalog'],
    'academic_libraries': ['catalog'],
    'digital_libraries': ['database'],
    'digital_library': ['database'],
    'catalog': ['catalog'],
    'catalogs': ['catalog'],
    'library_catalog': ['catalog'],
    'searchworks': ['catalog'],
    'bibliographic_records': ['bibliography'],
    'bibliographic_databases': ['bibliography'],
    'bibliographic_search': ['bibliography'],
    'bibliographic_studies': ['bibliography'],
    'bibliographic_access': ['bibliography'],
    'bibliographic_resources': ['bibliography'],
    'bibliography': ['bibliography'],
    'bibliometrics': ['bibliography'],
    'citation_index': ['bibliography'],
    'archives': ['archive'],
    'digital_archives': ['archive'],
    'digital_archive': ['archive'],
    'digital-archive': ['archive'],
    'historical_archives': ['archive'],
    'archival_search': ['archive'],
    'archival_documents': ['archive'],
    'archival_records': ['archive'],
    'historical_documents': ['archive'],
    'historical-document': ['archive'],
    'historical_documentation': ['archive'],
    'primary_sources': ['archive'],
    'primary-sources': ['archive'],
    'primary_sources': ['archive'],
    'manuscripts': ['rare_books'],
    'maps': ['map'],
    'cartography': ['map'],
    'museums': ['museum_studies'],
    'museum': ['museum_studies'],
    'reference_works': ['dictionary'],
    'reference_work': ['dictionary'],
    'reference_books': ['dictionary'],
    'reference_tools': ['dictionary'],
    'reference_services': ['guide'],
    'reference_studies': ['dictionary'],
    'reference_list': ['guide'],
    'online_dictionaries': ['dictionary'],
    'online_encyclopedias': ['dictionary'],
    'chinese_dictionary': ['dictionary'],
    'chinese_dictionaries': ['dictionary'],
    'dictionary': ['dictionary'],
    'periodicals': ['periodical'],
    'ejournals': ['periodical'],
    'academic_journals': ['periodical'],
    'journal_search': ['periodical'],
    'newspapers': ['newspaper'],
    'newspaper_archive': ['newspaper'],
    'newspaper_archives': ['newspaper'],
    'newspaper_studies': ['newspaper'],
    'historical_newspapers': ['newspaper'],
    'epigraphy': ['epigraphy'],
    'rare_books': ['rare_books'],
    'rare-books': ['rare_books'],
    'chinese_rare_books': ['rare_books'],
    'ancient_books': ['rare_books'],
    'ebooks': ['ebook'],
    'ebook_platform': ['ebook'],
    'digital_publishing': ['ebook'],
    'digital_reading': ['ebook'],
    'book_search': ['catalog'],
    'book_reviews': ['guide'],
    'book_history': ['book_history'],
    'book_sales': ['ebook'],
    'chinese_books': ['full_text'],
    'taiwanese_books': ['full_text'],
    'academic_books': ['full_text'],
    'online_bookstores': ['ebook'],
    'bookstore': ['ebook'],
    'social_cataloging': ['catalog'],
    'full_text_search': ['full_text'],
    'chinese_digital_library': ['full_text'],
    'chinese_classics': ['classics'],
    'classical_chinese': ['classics'],
    'premodern_texts': ['full_text'],
    'text_corpora': ['full_text'],
    'text_mining': ['tool'],
    'text-analysis': ['tool'],
    'research-tools': ['tool'],
    'tools': ['tool'],
    'research': ['guide'],
    'natural_language_processing': ['tool'],
    'chinese_word_segmentation': ['tool'],
    'computational_linguistics': ['tool'],
    'chinese_language_processing': ['tool'],
    'ocr': ['tool'],
    'text_recognition': ['tool'],
    'tutorials': ['guide'],
    'tutorial': ['guide'],
    'research_guides': ['guide'],
    'research_guide': ['guide'],
    'research_methods': ['guide'],
    'research-methods': ['guide'],
    'research_support': ['guide'],
    'academic_support': ['guide'],
    'academic_resources': ['guide'],
    'academic_research': ['guide'],
    'digital_collections': ['database'],
    'digital_collection': ['database'],
    'digital-collection': ['database'],
    'university_collections': ['database'],
    'digital-resources': ['database'],
    'digital_images': ['photo'],
    'digital_images': ['photo'],
    'digital_collections': ['database'],
    'statistical_data': ['statistical'],
    'statistics': ['statistical'],
    'government_data': ['statistical'],
    'open_data': ['statistical'],
    'survey_data': ['statistical'],
    'census_database': ['statistical'],
    'economic_data': ['statistical'],
    'company_data': ['statistical'],
    'stock_market': ['statistical'],
    'news_data': ['statistical'],
    'social_media': ['social_media'],
    'social-media': ['social_media'],
    'community': ['social_media'],
    'youtube': ['social_media'],
    'digital-humanities': ['digital_humanities'],
    'digital_humanities': ['digital_humanities'],
    'digital_scholarship': ['digital_humanities'],
    'data_science': ['digital_humanities'],
    'computational_research': ['digital_humanities'],
    'computational_methods': ['digital_humanities'],
    'computational_analysis': ['digital_humanities'],
    'gis': ['gis'],
    'historical_geography': ['gis'],
    'film_video': ['film_video'],
    'portal': ['website'],
    'gateway': ['website'],
    'institutional_services': ['organization'],
    'institutional_info': ['organization'],
    'research_center': ['organization'],
    'research_centers': ['organization'],
    'academic-community': ['organization'],
    'research_lab': ['organization'],
    'academic_institutions': ['organization'],
    'academic_discourse': ['organization'],
    'academic_publishing': ['organization'],
    'scholarship': ['organization'],
    'humanities': ['organization'],
    
    # --- Content Topic mappings ---
    'chinese_studies': ['digital_humanities'],
    'chinese_thought': ['intellectual_history'],
    'chinese_history': ['social_history'],
    'china_history': ['social_history'],
    'asian_studies': ['digital_humanities'],
    'asian_studies': ['digital_humanities'],
    'asian-history': ['art_history'],
    'asian-art': ['art_history'],
    'east_asian_studies': ['digital_humanities'],
    'east-asian-studies': ['digital_humanities'],
    'china-studies': ['digital_humanities'],
    'china_studies': ['digital_humanities'],
    'oriental_studies': ['digital_humanities'],
    'chinese_art': ['art_history'],
    'art': ['art_history'],
    'ceramics': ['art_history'],
    'arts': ['art_history'],
    'arts_and_humanities': ['digital_humanities'],
    'women-studies': ['social_history'],
    'gender-studies': ['social_history'],
    'social_sciences': ['social_history'],
    'social_sciences': ['social_history'],
    'sociology': ['social_history'],
    'social_research': ['social_history'],
    'buddhism': ['buddhism'],
    'buddhist_studies': ['buddhism'],
    'religion': ['religion'],
    'religious_studies': ['religion'],
    'chinese_religion': ['religion'],
    'philosophy': ['philosophy'],
    'chinese_philosophy': ['philosophy'],
    'political_science': ['political_science'],
    'chinese_politics': ['political_science'],
    'political_communication': ['political_science'],
    'political_analysis': ['political_science'],
    'political_thought': ['intellectual_history'],
    'political_history': ['political_science'],
    'political_risk': ['political_science'],
    'political_parties': ['political_science'],
    'government_documents': ['political_science'],
    'government_records': ['political_science'],
    'government_media': ['political_science'],
    'official_documents': ['political_science'],
    'official_statements': ['political_science'],
    'policy_documents': ['political_science'],
    'chinese_government': ['political_science'],
    'administrative': ['political_science'],
    'administrative_records': ['political_science'],
    'chinese_law': ['legal_history'],
    'legal_studies': ['legal_history'],
    'legal_research': ['legal_history'],
    'intellectual_property': ['legal_history'],
    'copyright': ['legal_history'],
    'copyright_law': ['legal_history'],
    'open_license': ['open_access'],
    'open_licensing': ['open_access'],
    'creative_commons': ['open_access'],
    'attribution': ['open_access'],
    'open-source': ['open_access'],
    'public_domain': ['open_access'],
    'literature': ['literature'],
    'chinese_literature': ['literature'],
    'literary_terms': ['literature'],
    'language_and_literature': ['literature'],
    'linguistics': ['language'],
    'chinese_language': ['language'],
    'literary_terms': ['literature'],
    'comparative_linguistics': ['language'],
    'romanization': ['language'],
    'transliteration': ['language'],
    'military_history': ['military_history'],
    'chinese_military': ['military_history'],
    'military_news': ['military_history'],
    'maritime_customs': ['maritime'],
    'customs_records': ['maritime'],
    'customs_history': ['maritime'],
    'foreign_trade': ['maritime'],
    'chinese_economy': ['economic_history'],
    'economics': ['economic_history'],
    'economics_and_management': ['economic_history'],
    'economic_analysis': ['economic_history'],
    'country_reports': ['economic_history'],
    'colonial_history': ['colonialism'],
    'colonial_history': ['colonialism'],
    'imperial_china': ['colonialism'],
    'imperial_maps': ['map'],
    'modern_china': ['social_history'],
    'modern_china_history': ['social_history'],
    'modern_chinese_history': ['social_history'],
    'modern_history': ['social_history'],
    'republican_china': ['social_history'],
    '19th_20th_century': ['social_history'],
    '1940s': ['social_history'],
    'qing_dynasty': ['social_history'],
    'qing_history': ['social_history'],
    'tang_dynasty': ['classics'],
    'tang_history': ['classics'],
    'ming_dynasty': ['classics'],
    'qin_dynasty': ['classics'],
    'imperial_mausoleums': ['classics'],
    'archaeological_studies': ['museum_studies'],
    'archaeological-site': ['museum_studies'],
    'cultural-heritage': ['museum_studies'],
    'chinese_diaspora': ['social_history'],
    'genealogy': ['genealogy'],
    'chinese_intellectual_history': ['intellectual_history'],
    'intellectual_discourse': ['intellectual_history'],
    'local_history': ['social_history'],
    'cold_war': ['cold_war'],
    'ccp_history': ['cold_war'],
    'party_history': ['cold_war'],
    'sino_us_relations': ['cold_war'],
    'chinese_civil_war': ['cold_war'],
    'marshall_mission': ['cold_war'],
    'diplomatic_history': ['cold_war'],
    'diplomatic_records': ['cold_war'],
    'international_relations': ['cold_war'],
    'foreign_policy': ['political_science'],
    'human_rights': ['political_science'],
    'social_policy': ['political_science'],
    'media_studies': ['newspaper_studies'],
    'media_history': ['newspaper_studies'],
    'chinese_media': ['newspaper_studies'],
    'german-research': ['website'],
    'germany': ['website'],
    'information-science': ['digital_humanities'],
    'history': ['social_history'],
    'historical_research': ['digital_humanities'],
    'history_philology': ['classics'],
    'philology': ['classics'],
    'chinese_philology': ['classics'],
    'paleography': ['classics'],
    'periodical': ['periodical'],
    'articles': ['periodical'],
    'conference_papers': ['periodical'],
    'conference_proceedings': ['periodical'],
    'theses': ['database'],
    'china': ['prc'],
    'voa': ['newspaper'],
    'national_library': ['catalog'],
    'national_diet_library': ['catalog'],
    'multidisciplinary': ['digital_humanities'],
    'sciences': ['digital_humanities'],
    'ancient_china': ['classics'],
    'ancient_chinese_studies': ['classics'],
    'western_languages': ['language'],
    'chinese_politics': ['political_science'],
    'productivity': ['tool'],
    'academic-tools': ['tool'],
    'access': ['guide'],
    'policies': ['guide'],
    'university_policy': ['guide'],
    'staff_resources': ['guide'],
    'contact_information': ['guide'],
    'access_information': ['guide'],
    'document_delivery': ['guide'],
    'interlibrary_loan': ['guide'],
    'reproduction_services': ['guide'],
    'library_directory': ['catalog'],
    'library_resources': ['catalog'],
    'library_studies': ['catalog'],
    'special_collections': ['archive'],
    'university_archives': ['archive'],
    'government_documents': ['archive'],
    'special_collections': ['archive'],
    'voa': ['newspaper'],
    'taiwan_history': ['social_history'],
    'taiwan_studies': ['taiwan'],
    'taiwan_government': ['taiwan'],
    'hong_kong': ['hong_kong'],
    'stanford': ['catalog'],
    'stanford_university': ['catalog'],
    'harvard_university': ['catalog'],
    'apabi': ['database'],
    'airiti': ['database'],
    'academia-sinica': ['catalog'],
    'academia_sinica': ['catalog'],
    'concepts': ['guide'],
    'commercial_resources': ['database'],
    'general': ['website'],
    'general_academic': ['website'],
    'general_reference': ['dictionary'],
    'culture': ['social_history'],
    'cultural_sciences': ['digital_humanities'],
    'political_and_legal_studies': ['political_science'],
    'philosophy_and_religion': ['philosophy'],
    'arts': ['art_history'],
    'history_and_geography': ['social_history'],
    'trademark': ['website'],
    'university_governance': ['website'],
    'brand_management': ['website'],
    'institutional_identity': ['website'],
    'news_data': ['newspaper'],
    'museum-of-fine-arts-boston': ['museum_studies'],
    'university_of_tokyo': ['catalog'],
    'bavarian-state-library': ['catalog'],
    'librarians': ['guide'],
    'open_access': ['open_access'],
    'gazetteers': ['full_text'],
    'academic_publishing': ['periodical'],
    'acoustic': ['music'],
    'photos': ['photo'],
}

# Now load all pages and build the complete mapping
all_old_tags = Counter()
all_new_tags = Counter()
unmapped = Counter()

pages = []
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
        parts = content.split('---', 2)
        if len(parts) < 3:
            continue
        try:
            fm = yaml.safe_load(parts[1]) or {}
        except:
            continue
        
        old_tags = fm.get('tags', [])
        old_subjects = fm.get('subjects', [])
        
        # Merge tags + subjects → new tags
        combined_input = list(set(old_tags + old_subjects))
        new_tags = set()
        
        for t in combined_input:
            all_old_tags[t] += 1
            if t in VALID_TAGS:
                new_tags.add(t)
            elif t in TAG_MAP:
                for nt in TAG_MAP[t]:
                    new_tags.add(nt)
            else:
                unmapped[t] += 1
                # Try fuzzy match
                t_lower = t.lower().replace('-', '_').replace(' ', '_')
                if t_lower in VALID_TAGS:
                    new_tags.add(t_lower)
                elif t_lower in TAG_MAP:
                    for nt in TAG_MAP[t_lower]:
                        new_tags.add(nt)
                # else: truly unmapped, will be handled below
        
        for nt in new_tags:
            all_new_tags[nt] += 1
        
        pages.append({
            'file': f, 'subdir': subdir, 'path': path,
            'old_tags': old_tags, 'old_subjects': old_subjects,
            'new_tags': sorted(new_tags),
        })

print(f"Processed {len(pages)} pages")
print(f"\nOld tags: {len(all_old_tags)} unique")
print(f"New tags: {len(all_new_tags)} unique")
print(f"Unmapped tags: {len(unmapped)}")

if unmapped:
    print(f"\nUNMAPPED TAGS (need manual mapping):")
    for t, c in unmapped.most_common():
        print(f"  {t}: {c}")

print(f"\nNEW TAG DISTRIBUTION:")
for t, c in all_new_tags.most_common():
    in_vocab = "✓" if t in VALID_TAGS else "✗ NOT IN VOCAB"
    print(f"  {t}: {c} {in_vocab}")

# Save mapping for next script
mapping_data = {
    'pages': pages,
    'valid_tags': sorted(VALID_TAGS),
    'unmapped': dict(unmapped),
}
with open(os.path.join(WIKI, 'scripts', 'tag_remap.json'), 'w') as f:
    json.dump(mapping_data, f, ensure_ascii=False, indent=1)
print(f"\nSaved remap data to scripts/tag_remap.json")
