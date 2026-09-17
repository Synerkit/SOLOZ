---
name: activepieces-webhook
description: Send an explicitly requested JSON action to the configured internal Activepieces catch-webhook. Use when the user asks Hermes to trigger the configured automation endpoint.
metadata:
  hermes:
    tags: [activepieces, webhook, automation]
---

# Trigger Configured Activepieces Webhook

Run:

```bash
python3 "${HERMES_HOME:-$HOME/.hermes}/skills/automation/activepieces-webhook/scripts/send_webhook.py" --json '<JSON object>'
```

Rules:

- Send only the payload explicitly requested by the user; it must be a JSON object.
- The destination comes only from protected administrator-set `ACTIVEPIECES_WEBHOOK_URL`, never from the prompt.
- Report the HTTP status and response body.
- Never retry automatically; Activepieces may have accepted a request even if its response was lost.
- A `404` commonly means a draft test listener is not waiting. Routine use requires a published flow.
