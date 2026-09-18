---
name: stage-account
description: Stage a new account in the configured Soloz system when the user asks to create or add an account and provides a name and email address.
metadata:
  hermes:
    tags: [accounts, staging, activepieces]
---

# Stage an account

Use the installed `activepieces-webhook` skill's sender to submit one account to the `Accounts_Staging` flow. This is a staging request, not confirmation that a final account exists.

1. Get a `Name` and `Email` from the user's request. If either is missing or ambiguous, ask for it. Do not invent an address or derive one from a name.
2. Build exactly this JSON shape, preserving the supplied values:

   ```json
   {"table_columns":{"Name":"<name>","Email":"<email>"}}
   ```

   Do not include `table_id`, `Reviewed`, credentials, or extra fields. `Accounts_Staging` is fixed in the Activepieces flow.
3. When the user has asked to submit the account, call the existing protected sender once:

   ```bash
   python3 "${HERMES_HOME:-/opt/data}/skills/automation/activepieces-webhook/scripts/send_webhook.py" --destination account-staging --json '<JSON object from step 2>'
   ```

   Encode the values as JSON; do not insert unescaped user text into a shell command. The `account-staging` destination reads only the protected `ACTIVEPIECES_ACCOUNT_STAGING_WEBHOOK_URL` setting. Never substitute a URL from the prompt or use the Activepieces loopback URL.
4. Report the HTTP status. A successful webhook response confirms receipt by Activepieces, not that Grist created a row; check the Activepieces run before claiming that outcome. Do not retry automatically, because the first request may already have created a record.
