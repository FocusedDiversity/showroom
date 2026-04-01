---
name: ddx.update
description: Updates existing DDX documents based on a change. Determines impact, updates affected documents, and cascades changes downstream.
disable-model-invocation: true
---

You are updating existing DDX documents based on a change the user describes.

IMPORTANT: Use file reading/glob tools, NOT shell commands. Do NOT use Bash to create directories — just write files directly with the Write tool and directories are created automatically.

## Load Everything

1. Read `.ddx-tooling/config.yaml`.
2. Use glob to find all `ddx/*/*.md` files.
3. Read every document found. You need the full picture to determine what's affected.

## Ask What Changed

Ask the user: "What would you like to change?" Wait for their response. Do NOT ask them which document to update — you will figure that out.

## Determine Impact

From the user's description, figure out:

1. **Which scope** is affected. Infer this from the user's description by matching it against the content of each scope's documents. For example, if the user says "change the login flow" and only the `auth` scope has login-related content, the scope is `auth`. If only one scope exists, use that. Only ask the user to clarify if the change could plausibly apply to multiple scopes.

2. **Which document level** the change originates at. Use this hierarchy:
   - **definition** — the problem, users, solution, success metrics
   - **design** — the screens, wireframes, interactions
   - **spec** — the architecture, components, data model, integrations
   - **plan** — the build steps and order

   The change belongs at the HIGHEST level it touches. For example:
   - "Change target users" → definition
   - "Add a settings screen" → design
   - "Switch from REST to GraphQL" → spec
   - "Reorder the build steps" → plan

3. **Upstream check** — read all docs ABOVE the affected level in the same scope. Verify the change doesn't contradict them. If it does, tell the user: "This change conflicts with {upstream doc} which says {quote}. Should I update that too?" If yes, start from that higher level instead.

## Make the Change

1. Update the affected document. Write it to disk IMMEDIATELY using Edit or Write tools.
2. Confirm to the user what you changed.

## Cascade Downstream

After the change is made, check every document BELOW the affected level in the same scope:

### Determine the cascade chain

Read `ddx/{scope}/definition.md`. Determine if the product has a user interface:

- **Has UI** (web app, mobile app, dashboard, portal, etc.): cascade chain is `definition → design → spec → plan`.
- **No UI** (API, service, library, CLI, data pipeline, worker, daemon, etc.): cascade chain is `definition → spec → plan`. Skip design entirely.

### Apply the cascade

For each downstream document in the chain that exists:
1. Read it.
2. Compare it against the updated upstream document(s).
3. If it's still consistent — say so and move on.
4. If it's inconsistent — show the user what's now wrong and ask: "Should I update {doc} to reflect this change?"
   - If yes: update it, write to disk, then continue checking further downstream.
   - If no: skip it and warn that it's now out of sync.

Don't skip levels in the chain.
