---
name: release-note-captain
description: Use this skill when a project is finished, shipped, deployed, published, or released and the user wants a release note created or updated in Obsidian. It covers collecting release facts, choosing the note path, writing a concise release summary, updating existing notes safely, and preserving follow-up actions.
---

# Release Note Captain

Create or update an Obsidian release note when a project is deployed, published, or finished.

## Destination

Default folder:

```text
Release Notes/
```

Default filename:

```text
YYYY-MM-DD — Project Name.md
```

Use vault-relative paths only. If the release note already exists, read it first and update it instead of creating a duplicate.

## Required Fields

Include these sections unless the user asks for a different format:

- Project
- Date
- Status
- Repo URL
- Live URL, if available
- Summary
- What Shipped
- Verification
- SEO/GEO or Distribution Notes
- Follow-Ups

## Workflow

1. Gather release facts from the conversation, repo, deploy output, GitHub, or local files.
2. Use `list_notes` or `get_note` to check whether a release note already exists.
3. Create the folder `Release Notes` if missing.
4. Create or update the release note.
5. Keep wording useful for both public release history and private project memory.
6. End with the note path and any missing details that still need the user.

## Style

- Clear and compact.
- Prefer bullets for shipped changes and verification.
- Include exact URLs and commit hashes when available.
- Avoid hype. State what shipped and why it matters.
- Preserve unfinished follow-ups instead of burying them.

## Template

Use `templates/release-note.md` as the base structure when creating a new note.

