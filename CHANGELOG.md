# Changelog

## Unreleased

- Fix: `search_notes` failed for every query when one note had an empty `title:` in its frontmatter (common in templates), with `'NoneType' object has no attribute 'lower'`. An empty title now falls back to the file name, a numeric or date title is turned into text, and search, backlinks and links tolerate empty content.

## 0.3.0

- First-class, schema-validated Obsidian Bases (`.base`) support.
