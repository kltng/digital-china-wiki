---
title: Digital China Wiki — Schema
type: schema
---

# Digital China Wiki — Schema

A structured knowledge base of digital resources for Chinese studies.

## Directory Structure

```
digital-china-wiki/
├── resources/        # 916 resource pages (databases, archives, tools, etc.)
├── topics/           # 25 conceptual/topic pages (e.g., digital humanities in China)
├── institutions/     # 14 institutional profiles
├── regions/          # 5 region pages (PRC, Taiwan, Hong Kong, Japan, Korea)
├── glossary/         # 10 glossary redirect pages
├── index.md          # Master index
├── SCHEMA.md         # This file
├── TAG_TAXONOMY.md   # Controlled tag vocabulary
└── scripts/          # Utility scripts
```

## Page Frontmatter

### Resource Pages (`resources/`)

```yaml
---
title: "Full Title"
url: https://example.com
description: Brief description of the resource.
language: zh          # ISO 639-1
region: prc           # from Region axis
tags: [database, statistical, prc]
created: 2026-04-18
updated: 2026-04-18
---
```

**Fields:**
- `title` (required) — Full display name
- `url` (required) — Canonical URL
- `description` (required) — 1-3 sentence summary
- `language` — Primary language(s) of the resource
- `region` — Primary geographic focus
- `tags` — Controlled vocabulary (see below). Min 1, typically 2-4 tags.
- `created` / `updated` — ISO date
- `access_via_harvard` — Harvard EZProxy URL (if applicable)
- `site_status` — `live` | `dead` | `unreachable` | `restricted` | `unknown`
- `source_id` — Original ID from source data

### Topic Pages (`topics/`)

```yaml
---
title: "Topic Name"
type: topic
tags: [digital_humanities, prc]
created: 2026-04-18
---
```

### Institution Pages (`institutions/`)

```yaml
---
title: "Institution Name"
type: institution
url: https://example.edu
tags: [catalog]
region: prc
---
```

### Region Pages (`regions/`)

```yaml
---
title: "Region Name"
type: region
aliases: [alias1, alias2]
---
```

## Tag Taxonomy

Tags follow a 3-axis controlled vocabulary. All tags must come from the
validated set in `TAG_TAXONOMY.md`.

### Axis 1: Resource Type (20 tags)
`archive` · `bibliography` · `catalog` · `database` · `dictionary` ·
`ebook` · `film_video` · `full_text` · `gis` · `guide` · `map` ·
`newspaper` · `organization` · `periodical` · `photo` · `platform` ·
`statistical` · `tool` · `social_media` · `website`

### Axis 2: Content Topic (30 tags)
`art_history` · `book_history` · `buddhism` · `christianity` · `classics` ·
`cold_war` · `colonialism` · `digital_humanities` · `economic_history` ·
`epigraphy` · `film_studies` · `genealogy` · `geography` ·
`intellectual_history` · `language` · `legal_history` · `literature` ·
`maritime` · `medicine` · `military_history` · `music` · `museum_studies` ·
`newspaper_studies` · `open_access` · `philosophy` · `political_science` ·
`rare_books` · `religion` · `social_history` · `statistics`

### Axis 3: Region (6 tags)
`prc` · `taiwan` · `japan` · `hong_kong` · `korea` · `global`

## Wikilinks

Pages link to each other using `[[dir/filename|display text]]` syntax.
Only link to existing pages. No free-form tags — use only the controlled vocabulary above.
