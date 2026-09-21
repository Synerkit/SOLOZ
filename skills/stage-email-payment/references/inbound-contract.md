# Inbound payment-email contract

Activepieces sends the original payment-notification email to the authenticated Hermes route `/webhooks/ap-push`.

## Preferred raw body

Use HTTP `Body Type: Raw` and insert only Gmail's plain-text message body. Do not manually construct JSON and do not include an instruction in the body. Forwarded provider headers and content must remain intact so Hermes can validate the provider and subject.

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
- Set `X-Request-ID` to the stable Gmail message ID. Hermes uses it as the delivery ID and ignores repeats for its idempotency window.
- Hermes returns `202 Accepted` when the agent run starts. This response does not mean the Payment staging webhook succeeded; the run is asynchronous.
- `Reference_` provides the downstream duplicate key. Use the provider transaction ID when available, otherwise the Gmail message ID.

The route prompt should render the raw webhook body through `{__raw__}` while binding the `stage-email-payment` skill. The skill—not arbitrary email content—controls validation and side effects.
