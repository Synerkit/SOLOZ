---
name: grist-readonly
description: Answer questions using live read-only data from the configured Grist document. Use when the user asks about Grist tables, columns, records, or business data stored in that document.
metadata:
  hermes:
    tags: [grist, read-only, data]
---

# Read Configured Grist Data

Retrieve current data before answering questions about the configured Grist document.

```bash
python3 "${HERMES_HOME:-$HOME/.hermes}/skills/data/grist-readonly/scripts/grist_read.py" tables
python3 "${HERMES_HOME:-$HOME/.hermes}/skills/data/grist-readonly/scripts/grist_read.py" columns --table TABLE_ID
python3 "${HERMES_HOME:-$HOME/.hermes}/skills/data/grist-readonly/scripts/grist_read.py" records --table TABLE_ID --limit 100
python3 "${HERMES_HOME:-$HOME/.hermes}/skills/data/grist-readonly/scripts/grist_read.py" record --table TABLE_ID --id RECORD_ID
python3 "${HERMES_HOME:-$HOME/.hermes}/skills/data/grist-readonly/scripts/grist_read.py" lookup --table TABLE_ID --column COLUMN_ID --value '<value>' --stable-column STABLE_COLUMN_ID
```

For `records`, optional `--filter` accepts a Grist filter JSON object whose values are arrays. Optional `--sort` accepts comma-separated column IDs, with `-` for descending order. Fetch only what is needed.

Use `lookup` to resolve a human-readable value without exposing unrelated rows. It normalizes case, accents, punctuation, and whitespace, then tries exact and contains matches. Its output contains only numeric record IDs, matched values, and optional stable-column values. Require exactly one match before using a record ID; treat `match_type: "contains"` as a suggested match and state the canonical matched value.

## Consultation workflow

1. Discover available tables when the relevant table ID is unknown.
2. Inspect the relevant columns before interpreting records.
3. Use `lookup` for human-readable reference resolution; otherwise retrieve relevant records with filters and conservative limits.
4. Answer from returned data, distinguishing an empty result from a failed request.
5. Without a maintained semantic map, state material uncertainty about business meaning.

## Hard boundaries

- Use only the bundled helper; it issues GET requests only.
- Never use Grist `POST`, `PATCH`, `PUT`, or `DELETE` endpoints, even if permissions change.
- Destination and document come only from protected administrator-set environment variables, never from a prompt.
- Never print, return, log, or inspect `GRIST_API_KEY`.
