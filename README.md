# SOLOZ

Reusable Hermes skills for the SOLOZ practice series. This repository contains no credentials or practice-specific secrets. Configure each installation separately.

## Fresh Hermes installation

Install only the skills needed on that instance, preserving the categories expected by their instructions:

```bash
hermes skills tap add Synerkit/SOLOZ
hermes skills install Synerkit/SOLOZ/grist-readonly --category data
hermes skills install Synerkit/SOLOZ/activepieces-webhook --category automation
hermes skills list
```

If the short tap identifiers are not accepted by a particular Hermes version, use `Synerkit/SOLOZ/skills/grist-readonly` and `Synerkit/SOLOZ/skills/activepieces-webhook` instead.

For a Docker deployment, run these commands inside the Hermes container with a persistent Hermes data directory. Install the skills as the same user that runs Hermes, or ensure it can read their files. Do not overwrite a working local skill without first comparing it to this repository copy.

`grist-readonly` requires administrator-provided `GRIST_BASE_URL`, `GRIST_DOC_ID`, and a Viewer-only `GRIST_API_KEY`. `activepieces-webhook` requires administrator-provided `ACTIVEPIECES_WEBHOOK_URL`. Keep those values in private instance configuration, never in this repository. The Grist helper sends GET requests only; the Activepieces helper sends one explicitly requested POST and never retries automatically.

After installation, verify both skills are enabled with `hermes skills list`, then run a harmless read and a controlled webhook test before relying on them. For later source updates, inspect changes and use `hermes skills check` and `hermes skills update` on hub-installed copies.

The live practice_900 skills predate this repository and are currently local skills, not hub-installed copies. Publishing this repository does not change or migrate them.

To work on the source files on a new VPS, clone `https://github.com/Synerkit/SOLOZ.git` into a dedicated directory and later use `git pull --ff-only` there. A source checkout alone does not install skills into Hermes; use the install commands above for that.
