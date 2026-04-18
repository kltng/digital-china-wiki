# Wiki Schema: Digital China Studies

## Domain
Digital resources for China studies — databases, websites, archives, tools, and platforms useful for researching Chinese history, literature, politics, society, and culture. Covers PRC, Taiwan, Hong Kong, and the global Chinese diaspora.

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `academia-sinica-digital-archives.md`)
- Every wiki page starts with YAML frontmatter (see below)
- Use `[[wikilinks]]` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- Bilingual content: include both English and 中文 summaries where applicable

## Frontmatter
```yaml
---
title: "Page Title"
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: website | database | news | maps | tool | institution | region | concept | glossary
url: canonical URL (for resources)
language: en | zh | ja | multilingual
region: prc | taiwan | hong_kong | japan | global
tags: [from taxonomy below]
subjects: [from taxonomy below]
sources: [discovery source]
---
```

## Tag Taxonomy

### Resource Types
website, database, news, maps, code_host, reference, ebook_platform, bookstore, library_catalog, video_playlist, bibliography, policy, social

### Content Domains
archives, rare_books, manuscripts, newspapers, ejournals, ebooks, government_records, primary_sources, academic_resources, digital_humanities, digital_libraries, digital_collections, digital_archive, library_services, special_collections, museum

### Disciplines
chinese_history, chinese_studies, taiwan_studies, east_asian_studies, chinese_intellectual_history, political_history, book_history, literature, philosophy, social_sciences, media_studies, library_science, research_methods, art_history, archaeology, religion, law, economics, linguistics

### Regions
prc, taiwan, hong_kong, japan, korea, southeast_asia, global

### Languages
en, zh, ja, ko, multilingual

### Access
open_access, subscription, institutional, registration_required

### Institutions
academia_sinica, harvard, yale, stanford, princeton, columbia, national_diet_library, loc, ncl_taiwan

## Page Types

### Resource Pages (websites/, databases/, news/, maps/)
One page per digital resource. Include:
- Title (English + Chinese where applicable)
- Summary / description
- 中文摘要 where applicable
- Canonical URL + access notes
- Key pages / sections of the resource
- Cross-references to [[topic]], [[region]], [[institution]] pages
- Source of discovery

### Concept Pages (concepts/, topics/)
Thematic or topical groupings. Include:
- Definition / scope
- Key resources in this area (linked)
- Related concepts
- Research methods commonly used

### Region Pages (regions/)
Geographic or political entity pages. Include:
- Overview of digital resources for this region
- Major institutions
- Key databases and archives
- Related regions

### Institution Pages (institutions/)
Universities, libraries, archives, research centers. Include:
- Overview
- Key digital collections / platforms hosted
- Related institutions and resources

### Glossary Pages (glossary/)
Chinese/English term pairs and concept definitions. Include:
- English term
- Chinese equivalent (simplified + traditional)
- Definition
- Related terms

## Page Thresholds
- **Create a page** when a resource has a unique URL and identifiable purpose
- **Add to existing page** when a resource is a subsection or feature of an already-documented resource
- **DON'T create a page** for dead links or placeholder entries
- **Split a page** when it exceeds ~200 lines
- **Archive a page** when its URL is confirmed dead and no replacement exists

## Update Policy
- New resources: create page, add to index
- URL changes: update canonical_url, note old URL
- Dead links: mark as deprecated in frontmatter, add "Status: Inactive" note
- Conflicting info: note both positions with dates and sources
