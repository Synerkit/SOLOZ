# SOLOZ

Reusable Hermes skills for the SOLOZ practice series. This repository contains no credentials or practice-specific secrets. Configure each installation separately.

## Fresh Hermes installation

Install only the skills needed on that instance, preserving the categories expected by their instructions:

```bash
hermes skills tap add Synerkit/SOLOZ
hermes skills install Synerkit/SOLOZ/grist-readonly --category data
hermes skills install Synerkit/SOLOZ/activepieces-webhook --category automation
hermes skills install Synerkit/SOLOZ/stage-soloz-record --category automation
hermes skills install Synerkit/SOLOZ/stage-email-payment --category automation
hermes skills install Synerkit/SOLOZ/stage-calendar-service --category automation
hermes skills list
```

If the short tap identifiers are not accepted by a particular Hermes version, use the corresponding `Synerkit/SOLOZ/skills/<skill-name>` path instead.

For a Docker deployment, run these commands inside the Hermes container with a persistent Hermes data directory. Install the skills as the same user that runs Hermes, or ensure it can read their files. Do not overwrite a working local skill without first comparing it to this repository copy.

`grist-readonly` requires administrator-provided `GRIST_BASE_URL`, `GRIST_DOC_ID`, and a Viewer-only `GRIST_API_KEY`. The five create destinations and the service update destination require their corresponding protected `ACTIVEPIECES_*_WEBHOOK_URL` values. Keep those values in private instance configuration, never in this repository. The Grist helper sends GET requests only; the Activepieces helper sends one explicitly requested POST and never retries automatically.

After installation, verify the installed skills are enabled with `hermes skills list`, then run a harmless read and a controlled webhook test before relying on them. For later source updates, inspect changes and use `hermes skills check` and `hermes skills update` on hub-installed copies.

The live practice_900 skills predate this repository and are currently local skills, not hub-installed copies. Publishing this repository does not change or migrate them.

## Practice_900 staging roles

Grist holds production and staging tables. Hermes interprets payment emails and calendar events, resolves current references, and uses `stage-soloz-record` to form the common staging payload. `activepieces-webhook` sends that payload once to the configured Activepieces flow; Activepieces performs the deterministic staging write. `grist-readonly` is the GET-only read capability.

`stage-email-payment` supplies `Payments_Staging.Email_ID` from the source email. `stage-calendar-service` supplies `Service_Staging.Event_Calendar_ID` from the source event. These identify repeated deliveries or updates to the same source item; they are separate from payment transaction duplicate checks and the business service duplicate checks. Calendar services use a fresh read-only staging lookup to choose the existing Activepieces create webhook or the independent service update webhook. Payment staging remains create-only. A webhook acceptance alone does not prove that a Grist row was created or updated.

The inbound Hermes `/webhooks/ap-push` route is reserved for `stage-email-payment`. Practice_900 has a separate `/webhooks/ap-calendar-service` route bound to `stage-calendar-service`, which calls the shared `stage-soloz-record` workflow. The calendar Activepieces HTTP action must target that route and use its separate protected `X-Gitlab-Token` secret. The protected `ACTIVEPIECES_*_WEBHOOK_URL` values are outbound Hermes-to-Activepieces destinations and do not select an inbound Hermes skill.

Both inbound routes accept the concatenator output as a raw UTF-8 HTTP body. The practice_900 gateway wraps it in a `data` field for the skill; an existing JSON body with a `data` string also works. The gateway override and its pinned image version are documented in the practice_900 Hermes Docker directory.

To work on the source files on a new VPS, clone `https://github.com/Synerkit/SOLOZ.git` into a dedicated directory and later use `git pull --ff-only` there. A source checkout alone does not install skills into Hermes; use the install commands above for that.
