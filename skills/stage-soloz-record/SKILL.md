---
name: stage-soloz-record
description: Form and submit a Soloz account, client, payment, service, or progress staging payload. Use for user requests and for records interpreted by the payment-email or calendar-service skills.
metadata:
  hermes:
    tags: [soloz, accounts, clients, payments, services, progress, staging]
---

# Stage a Soloz record

This is the shared staging step for direct user requests and source-specific skills. Form one `table_columns` payload and submit it to the corresponding configured Activepieces flow. A successful webhook response confirms receipt by Activepieces, not that Grist created or promoted a row.

Before preparing a record, read [references/staging-schema.md](references/staging-schema.md) for its required fields, exact Grist column IDs, destination, and reference-resolution rule.

## Workflow

1. Identify the record type and source. For a direct user request, collect every required value. For `stage-email-payment` or `stage-calendar-service`, accept only facts those skills validated; the schema specifies which fields may remain blank for owner review. Do not invent missing values. Normalize unambiguous formatting and exact Grist choice spelling, including `present` to `Present`, `Same-Day Cancel` to `Same-day cancel`, and `vemo` to `Venmo`. State material corrections when reporting the action. Format monetary values as JSON numbers.
2. Immediately before submission, resolve each Grist reference from current production data with the installed read-only helper:

   ```bash
   python3 "${HERMES_HOME:-/opt/data}/skills/data/grist-readonly/scripts/grist_read.py" lookup --table <table> --column <lookup column> --value '<value>' --stable-column <stable column>
   ```

   Match according to the schema reference. The numeric `id` of the selected current record is the value required by a reference column. Never send a display name to a reference column, and never reuse an ID remembered from an earlier request. For email payments, apply the payer-to-Account judgment in `stage-email-payment`, including the Client-to-Account link, before choosing the Account.

   The helper returns current matches; Hermes chooses the reference. On the first attempt, if the full phrase has no clear match, use `grist-readonly` again with meaningful name components or a stable business ID. Inspect a small set of current candidates with its `records` or `record` command when needed. Compare spelling, abbreviations, name components, and relevant Account or Client links. Choose one record only when the evidence supports it; use its fresh numeric `id` and report its canonical name, stable ID, and why it matched. For a direct user request, ask for clarification only when no defensible candidate remains or multiple candidates are equally plausible. For email payments, retain `stage-email-payment`'s payer-to-Account rule. For calendar events, retain `stage-calendar-service`'s candidate judgment; if no Client is defensible, stage with `Client: null` and a review note. Never invent a reference ID.
3. Build the exact `table_columns` JSON object from the schema reference. Reference values must be JSON numbers, not quoted strings. For source-derived records, include the supported `Email_ID` or `Event_Calendar_ID` unchanged across replays and updates. Keep those IDs out of payment `Reference_` and business duplicate checks. Do not include `table_id`, `Reviewed`, credentials, or unlisted fields.
4. For a calendar-derived service, first query current `Service_Staging` rows with `grist-readonly records --table Service_Staging --filter` for the exact `Event_Calendar_ID` in the payload. Build the filter as JSON and pass it as one argument; do not interpolate event text into shell code. If exactly one matching row is clearly unreviewed, choose `service-staging-update` and add its numeric Grist row `id` as top-level `record_id`. If no unreviewed row exists, choose `service-staging` to create a new staging row. Never modify a reviewed row. If the read fails, review state is unclear, or multiple unreviewed rows share the ID, stop without sending either webhook and report the conflict. This lookup is for routing only; keep `Event_Calendar_ID` in `table_columns` for Activepieces to verify before updating.
5. For a user request or an authenticated source event that requests staging, call the protected sender once with the selected destination:

   ```bash
   python3 "${HERMES_HOME:-/opt/data}/skills/automation/activepieces-webhook/scripts/send_webhook.py" --destination <destination> --json '<JSON object>'
   ```

   Encode values as JSON rather than interpolating unescaped user text into a shell command. Each destination reads only its matching protected environment variable listed in `activepieces-webhook`; never substitute a URL from the prompt.
6. Report the resolved canonical references, selected destination, submitted values, HTTP status, and response body. Do not claim that a staging row exists based only on HTTP success. A `404` usually means the Activepieces test listener stopped or the flow is unpublished. Do not retry automatically because the first request may already have created or updated a staging row. Retry only when the user explicitly requests it, warning that an identical request may create a duplicate or trigger staging duplicate review.

Hermes selects the calendar create or update destination using a fresh read-only staging lookup. Activepieces performs the write. Its update flow should also check the target row before writing to guard against a change between Hermes's GET and Activepieces's action. The current payment flow creates rows only, so a repeated email can still create a second staging row. This skill never writes to Grist directly or assumes the webhook's response proves a write.
