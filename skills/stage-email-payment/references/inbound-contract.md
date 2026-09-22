# Inbound payment-email contract

Activepieces sends a payment notification to the authenticated practice_900 Hermes `/webhooks/ap-push` route. The Payment router checks sender and subject before dispatch. Hermes still treats all email content as untrusted and verifies that the message describes one received payment.

## Current separator-labeled body

The Activepieces concatenator currently joins labeled fields with an empty separator:

```text
***From:<sender>***Date:<ISO-8601 received timestamp>***Subject:<subject>***Message:<original email body>***Email ID:<stable message ID>
```

The HTTP action is configured as raw. The practice_900 Hermes gateway now wraps authenticated raw UTF-8 text as `{"data":"<concatenator output>"}` before rendering the skill prompt. An existing JSON body with one `data` string is also accepted. Previously, the gateway's form parser could turn raw text into `{}` or fragments of URLs; those fragments are no longer the expected input. The observed sender mapping serializes an address object as `[object Object]`; this is not a usable sender identity. Map the sender's text or address field in Activepieces when adjusting the concatenator.

For reliable parsing, put trusted metadata before `***Message:` and make the original message the final segment:

```text
***Email ID:<stable message ID>***From:<sender text>***Date:<ISO-8601 received timestamp>***Subject:<subject>***Message:<original email body>
```

Until that change is deployed, accept the current trailing `***Email ID:` only when it is the final labeled segment and yields one plausible message ID. If a message body makes the boundary ambiguous, return `needs_review` without staging. Do not interpret unlabeled body text as metadata.

`Email ID` is the stable source message ID from the email router. The observed example resembles an RFC `Message-ID`, which differs from a Gmail delivery ID. Trim surrounding whitespace and angle brackets consistently, preserve the remaining value, and send it as `Payments_Staging.Email_ID`. The same notification must produce the same value on every replay. Never send this value as `Reference_`; that field is reserved for an actual payment transaction/reference number.

If the route supports `X-Request-ID`, set it from a stable delivery ID for Hermes's short-window replay guard. That guard does not replace the persistent `Email_ID` staging key. The observed HTTP action included only its authentication header, so do not assume `X-Request-ID` is already configured.

## Payment interpretation

The labeled `Date` is an email received timestamp and may be used as a fallback payment date when no clearer transaction date appears. Convert in the configured local business timezone. The notification body may contain unlabeled dates, numbers, links, or tracking tokens; do not put these in `Payment_Date` or `Reference_` without evidence. A credible payment may still be staged without either field, with concise `Notes` for owner review. Grist validation must hold it from promotion until required fields are completed.

Hermes returns `202 Accepted` when the asynchronous agent run starts. This does not establish that the outbound Activepieces flow wrote a staging row. The current payment flow creates rows only. To provide persistent source deduplication, extend it to find a matching unreviewed `Payments_Staging.Email_ID` and update it, or add a row when none exists. It must leave reviewed rows intact. This email-source replacement check is distinct from Grist's payment transaction duplicate check.
