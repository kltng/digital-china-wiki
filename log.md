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
