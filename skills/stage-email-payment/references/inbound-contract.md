# Inbound payment-email contract

Activepieces sends the original payment-notification email to the authenticated Hermes route `/webhooks/ap-push`.

## Preferred raw body

Use HTTP `Body Type: Raw` and insert only Gmail's plain-text message body. Do not manually construct JSON, prepend Gmail fields, or include an instruction in the body. Activepieces' Payment router must check the Gmail sender and subject before dispatching to this authenticated route; Hermes then checks the body for a coherent provider-authored payment notification. Forwarded provider headers and content, when present in the text, remain useful corroboration. A direct Bank of America/Zelle body need not contain `From:` or `Subject:` lines.

Set `Content-Type: text/plain; charset=utf-8`.

## Optional structured body

The route also accepts this JSON envelope for compatibility and direct testing:

```json
{
  "event_type": "payment_email",
  "prompt": "Parse this payment notification and stage one Soloz payment.",
  "email": {
    "message_id": "<stable Gmail message ID>",
    "from": "<sender name and address>",
    "subject": "<subject>",
    "received_at": "<ISO-8601 timestamp>",
    "text": "<plain-text body>",
    "html": "<optional HTML body>"
  }
}
```

For structured delivery, required fields are `event_type`, `email.message_id`, `email.from`, `email.subject`, `email.received_at`, and at least one of `email.text` or `email.html`; `prompt` is optional. Preserve the provider's original content. Do not have Activepieces precompute the payer, amount, or transaction reference unless it also includes the original email fields for verification.

## Delivery and replay protection

- Authenticate with the secret header already configured for the Hermes route. Keep the secret outside the JSON body and logs.
- Use `Content-Type: text/plain; charset=utf-8` for the preferred raw body or `application/json` for the optional envelope.
- Set `X-Request-ID` to the stable Gmail message ID. Hermes uses it only as the delivery ID and ignores repeats for its idempotency window. It is not a payment transaction reference and must never be placed in `Reference_`.
- Hermes returns `202 Accepted` when the agent run starts. This response does not mean the Payment staging webhook succeeded; the run is asynchronous.
- `Reference_`, when present, is the provider's actual transaction/reference number. Grist uses it for strong transaction-duplicate checks. If the email does not identify one, omit `Reference_` from the staging payload; neither Hermes' delivery ID nor a notification/tracking token is an acceptable substitute. A missing reference or date leaves `Payments_Staging.Validation_Status` invalid for promotion until the owner reviews and completes it, but does not block provisional staging of a credible payment.
- For a direct Bank of America/Zelle body saying a named payer sent a positive amount but offering only an unlabeled number (such as `9212026`), stage the payer/account, amount, and method if otherwise supported. Do not force the unlabeled number into `Payment_Date` or `Reference_`; preserve it with a short explanation in `Payments_Staging.Notes` for owner review. Do not copy the whole message or tracking links into Notes.

The route binds the `stage-email-payment` skill and renders its parsed payload through `{__raw__}`. The current Hermes gateway parses a non-JSON raw body as form data and may show fragments as JSON keys/values; this representation is not a structured email envelope. The skill—not arbitrary email content—controls validation and side effects. Correcting gateway raw-text parsing is a separate change.
