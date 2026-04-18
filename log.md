# Wiki Log

> Chronological record of all wiki actions. Append-only.
> Format: `## [YYYY-MM-DD] action | subject`
> Actions: ingest, update, query, lint, create, archive, delete

## [2026-04-18] create | Wiki initialized
- Domain: Digital resources for China studies
- Source: kltng/digital-china-list repo (932 entries)
- Structure: websites, databases, news, maps, concepts, regions, institutions, tools, glossary, topics

## [2026-04-18] ingest | Bulk page generation from digital-china-list
- 932 source entries parsed from YAML frontmatter
- 823 website pages + 72 database + 13 news + 10 maps + 14 tools = 932 resource pages
- 25 concept/topic pages (chinese-history, digital-humanities, taiwan-studies, etc.)
- 5 region pages (prc, taiwan, hong-kong, japan, global)
- 14 institution pages (academia-sinica, harvard-yenching, yale-library, etc.)
- 10 glossary redirect pages for common wikilink targets
- Master index.md created
- Total: 986 pages, 2,113 wikilinks, 0.7 MB
- 150 broken links (110 single-occurrence tag links, 40 resolved with glossary redirects)

## [2026-04-18] update | Rewrote 27 EZProxy URLs to canonical form
- Preserved proxy URL in new `access_via_harvard:` frontmatter field
- 0 skipped for manual review

## [2026-04-18] update | Phase 1: URL accessibility check
- Ran `scripts/check_urls.py` on 820 stub URLs
- Results: 615 live, 205 dead/blocked/unreachable

## [2026-04-18] update | Phase 2: Live site scraping
- Ran `scripts/scrape_sites.py` — scraped 605/615 live sites
- Extracted meta tags + body text for content enrichment

## [2026-04-18] update | Phase 3: Content enrichment
- Ran `scripts/enrich_pages_v2.py` + `scripts/fix_remaining.py`
- Generated descriptions for all 920+ pages (avg 288 chars)
- Final site_status breakdown: 723 live / 44 dead / 44 restricted / 74 unreachable

## [2026-04-18] delete | Deduplication pass
- Found 11 true duplicate pairs (mangled-title vs proper-title pages)
- Found 4 WeChat QR junk pages
- Deleted 16 pages total, fixed 12 files with broken wikilinks
- Post-dedup: 969 pages, commit `e33bc25`

## [2026-04-18] update | Restructure: flatten + controlled tag taxonomy
- Flattened websites/ databases/ news/ maps/ tools/ → single `resources/` (916 pages)
- Renamed concepts/ → topics/ (25 pages)
- Mapped 381 unique old tags → 52 controlled tags (3-axis taxonomy)
  - Axis 1: Resource Type (20 tags) — archive, database, catalog, tool, etc.
  - Axis 2: Content Topic (30 tags) — art_history, cold_war, digital_humanities, etc.
  - Axis 3: Region (6 tags) — prc, taiwan, japan, hong_kong, korea, global
- Dropped `subjects` and `type` fields from all pages
- Added TAG_TAXONOMY.md, updated SCHEMA.md
- Rebuilt index.md (970 pages, 1034 wikilinks, 1038 KB)
- Top tags: digital_humanities (847), database (386), catalog (269), statistical (224), prc (190)
- Commit `f12c2cf`, pushed to kltng/digital-china-wiki
