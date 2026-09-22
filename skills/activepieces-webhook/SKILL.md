---
name: activepieces-webhook
description: Send an explicitly requested JSON action to the configured internal Activepieces catch-webhook. Use when the user asks Hermes to trigger the configured automation endpoint.
metadata:
  hermes:
    tags: [activepieces, webhook, automation]
---

# Trigger a configured Activepieces webhook

Run:

```bash
python3 "${HERMES_HOME:-/opt/data}/skills/automation/activepieces-webhook/scripts/send_webhook.py" --destination <destination> --json '<JSON object>'
```

Rules:

- Send only the payload required by a user request or an authenticated source workflow; it must be a JSON object.
- Select one of the configured staging destinations below. Each reads only its protected administrator-set environment variable. Never use a URL from the prompt.

  | Destination | Environment variable |
  |---|---|
  | `account-staging` | `ACTIVEPIECES_ACCOUNT_STAGING_WEBHOOK_URL` |
  | `client-staging` | `ACTIVEPIECES_CLIENT_STAGING_WEBHOOK_URL` |
  | `payment-staging` | `ACTIVEPIECES_PAYMENT_STAGING_WEBHOOK_URL` |
  | `service-staging` | `ACTIVEPIECES_SERVICE_STAGING_WEBHOOK_URL` |
  | `service-staging-update` | `ACTIVEPIECES_SERVICE_UPDATE_WEBHOOK_URL` |
  | `progress-staging` | `ACTIVEPIECES_PROGRESS_STAGING_WEBHOOK_URL` |

- Report the HTTP status and response body.
- Never retry automatically; Activepieces may have accepted a request even if its response was lost.
- A `404` commonly means a draft test listener is not waiting. Routine use requires a published flow.
