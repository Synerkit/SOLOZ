---
name: stage-soloz-record
description: Stage an account, client, payment, service, or progress record in Soloz. Use when the user asks to add one of these records through its configured staging workflow.
metadata:
  hermes:
    tags: [soloz, accounts, clients, payments, services, progress, staging]
---

# Stage a Soloz record

Submit one record to the requested Soloz staging flow. A successful webhook response confirms receipt by Activepieces, not that Grist created or promoted a row.

Before preparing a record, read [references/staging-schema.md](references/staging-schema.md) for its required fields, exact Grist column IDs, destination, and reference-resolution rule.

## Workflow

1. Identify the record type and collect every required value. Ask for missing or ambiguous business values; do not invent them. Normalize unambiguous formatting and known choice spelling, including dates such as `09/20/26` to `2026-09-20`, `present` to `Present`, and `vemo` to `Venmo`. State any correction when reporting the action. Format monetary values as JSON numbers.
2. Immediately before submission, resolve each Grist reference from current production data with the installed read-only helper:

   ```bash
   python3 "${HERMES_HOME:-/opt/data}/skills/data/grist-readonly/scripts/grist_read.py" lookup --table <table> --column <lookup column> --value '<value>' --stable-column <stable column>
   ```

   Match according to the schema reference. The numeric `id` of the single returned match is the value required by a reference column. Never send a display name to a reference column, and never reuse an ID remembered from an earlier request.

   The helper performs exact, case-insensitive, and unique partial-name discovery while returning only minimal match data. If there is no match, stop and report it. If multiple records match, stop and ask the user to disambiguate with the stable business ID shown in the schema. A single partial match is acceptable; report the canonical matched name and stable ID. Never guess.
3. Build the exact `table_columns` JSON object from the schema reference. Reference values must be JSON numbers, not quoted strings. Do not include `table_id`, `Reviewed`, credentials, formula columns, or extra fields.
4. When the user has requested submission, call the protected sender once with the schema's destination:

   ```bash
   python3 "${HERMES_HOME:-/opt/data}/skills/automation/activepieces-webhook/scripts/send_webhook.py" --destination <destination> --json '<JSON object>'
   ```

   Encode values as JSON rather than interpolating unescaped user text into a shell command. Each destination reads only its matching protected `ACTIVEPIECES_*_STAGING_WEBHOOK_URL`; never substitute a URL from the prompt.
5. Report the resolved canonical references, submitted values, HTTP status, and response body. Do not claim that a staging row exists based only on HTTP success. A `404` usually means the Activepieces test listener stopped or the flow is unpublished. Do not retry automatically because the first request may already have created a staging row. Retry only when the user explicitly requests it, warning that an identical request may create a duplicate or trigger staging duplicate review.
