# Agent Instructions for Digital China Wiki

This repository is a structured Markdown wiki for digital Chinese studies resources.
Treat it as a content and metadata repository, not as an application.

## Source of Truth

Before editing, use these files as the canonical references:

- `SCHEMA.md` for directory layout and expected frontmatter fields.
- `TAG_TAXONOMY.md` for the only allowed `tags:` values.
- `scripts/validate_wiki.py` for the validation rules the repo actually enforces.
- `scripts/normalize_wiki.py` for formatting, canonical tag targets, and link conventions.

## Repository Layout

- `resources/`: individual resource records for databases, archives, tools, maps, newspapers, platforms, and related materials.
- `topics/`: curated topic pages that group and explain related resources.
- `institutions/`: institutional profile pages.
- `regions/`: region landing pages.
- `glossary/`: glossary or redirect-style pages.
- `scripts/`: scraping, normalization, enrichment, and validation utilities.
- `index.md`: generated master index of all pages.

## Core Editing Rules

- Preserve YAML frontmatter at the top of every content page.
- Keep edits small and targeted; do not reorganize directories or rename files unless explicitly requested.
- Use concise, factual descriptions. Avoid promotional language and avoid speculation.
- Preserve existing Markdown and wikilink style.
- Do not invent new tags. Every tag must exist in `TAG_TAXONOMY.md`.
- Do not create bare wikilinks like `[[some-page]]`; use directory-qualified targets such as `[[topics/digital-humanities|Digital Humanities]]`.
- Only link to pages that already exist in the repo unless you are creating the target in the same change.

## Directory-Specific Expectations

### `resources/`

Resource pages should normally include:

- `title`
- `created`
- `updated`
- `url`
- `language`
- `region`
- `tags`
- `description`

Additional fields may appear, such as:

- `access_via_harvard`
- `site_status`
- `source_id`
- `china_relevance`

Resource pages do not require a `type` field.

Body structure should match existing pages:

- H1 title
- `URL` line
- `Region` line
- `Summary` section

### `topics/`

- Must include `type: topic`.
- Usually include `title`, `created`, and `tags`.
- Often include `resource_count`, `Key Resources`, and `Related Topics`.
- Keep topic pages curated and explanatory rather than exhaustive prose dumps.

### `institutions/`

- Must include `type: institution`.
- Usually include `title`, `url`, `tags`, and `region`.

### `regions/`

- Must include `type: region`.
- May include `aliases`.

### `glossary/`

- Follow the existing local pattern for glossary or redirect pages.
- Keep glossary entries short and navigational.

## Tags

- Tags are controlled vocabulary, not free-form labels.
- Tags usually mix resource type, subject area, and region.
- Prefer the smallest accurate set of tags rather than exhaustive tagging.
- When unsure, inspect adjacent files in the same directory and compare against `TAG_TAXONOMY.md`.

## Generated and Scripted Files

- Treat JSON, CSV, gzipped data, and batch files under `scripts/` as generated or pipeline inputs unless you confirm otherwise.
- Do not hand-edit generated artifacts unless the task explicitly requires it.
- If a content issue can be fixed either in a generated artifact or in the source Markdown page, prefer fixing the Markdown page unless the workflow clearly says otherwise.

## Validation Workflow

When changing Markdown content:

- Check that frontmatter matches the schema for that directory.
- Check that all wikilinks resolve and include directory-qualified targets.
- Check that all tags are valid.

If validation is appropriate, run:

- `python3 scripts/validate_wiki.py`

Use normalization scripts only when the task calls for broad cleanup or regeneration, not for routine small edits.

## Practical Working Style

- Prefer editing existing pages over creating duplicate pages on the same resource.
- Match the tone, formatting, and field order of nearby files.
- If you add a new resource page, ensure the slug is consistent with existing filenames and that internal links point to it correctly.
- Do not assume `index.md` is manually maintained; verify whether it should be regenerated rather than edited by hand.
