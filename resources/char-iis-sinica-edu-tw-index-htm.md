---
title: "Academia Sinica Character Missing Glyph System 缺字系統"
created: 2026-04-18
updated: '2026-04-18'
url: https://char.iis.sinica.edu.tw/index.htm
language: zh
region: taiwan
tags:
- digital_humanities
- tool
- language
- taiwan
china_relevance: null
source_id: char-iis-sinica-edu-tw-index-htm
description: Academia Sinica's Character Missing Glyph System is a lookup and API tool for querying rare or missing Chinese characters by glyph components. It supports character-form search, glyph image generation, normalization, pinyin conversion, and browser-side rendering for research and technical workflows involving non-standard characters.
---

# Academia Sinica Character Missing Glyph System 缺字系統

**URL:** https://char.iis.sinica.edu.tw/index.htm

**Language:** Chinese

**Region:** Taiwan

## Summary

Academia Sinica's 缺字系統 is a specialized tool for working with rare, variant, and missing Chinese characters. The site provides glyph-based lookup by component structure, lets users generate custom glyph images, and exposes APIs for normalization and pinyin conversion across encodings such as Big5 and Unicode.

## Notable Features

- Character-form lookup by single or multiple components
- Copyable composition formulas for missing-character notation
- Custom glyph image generation with configurable size, color, and font
- Lookup of character-form evolution and variant forms across character sets
- API support for normalization and pinyin conversion
- JavaScript tools for rendering composition formulas directly in web pages

## APIs And Technical Capabilities

The site includes a normalization API for converting user-entered composition formulas into the system's canonical representation, which is useful when a query does not match the stored formula exactly. It also exposes a pinyin conversion API that returns XML output and supports multiple romanization schemes, including Hanyu Pinyin, Wade-Giles, Yale, Tongyong Pinyin, and several Guoyu systems.

For web publishing and digital editions, the JavaScript demo shows browser-side rendering workflows using hosted scripts that replace composition formulas with generated glyph images. The documented examples include whole-page conversion, conversion within a specific DOM block, and conversion of individual strings.

## Research Value

This resource is especially useful for projects involving premodern Chinese texts, epigraphy, lexical databases, TEI/XML editions, and other corpora where rare or unsupported characters appear regularly. It helps researchers and developers bridge gaps between encoded text, character description sequences, and display-ready glyphs.
