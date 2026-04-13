---
name: ddx.spec
description: Generates a Spec document that translates the Definition and Design into a technical specification.
disable-model-invocation: true
---

You are generating a Spec document. This document translates the Definition and Design into a technical specification.

IMPORTANT: Use file reading/glob tools, NOT shell commands. Do NOT use Bash to create directories — just write files directly with the Write tool and directories are created automatically. Be frictionless — if upstream docs are missing, generate them yourself rather than telling the user to run another command.

## Scope Resolution (do this FIRST)

1. Read `.ddx-tooling/config.yaml` to find the `definition`, `design`, and `spec` entries. Note prompts, templates, and output paths (contain `{scope}`).

2. Check if `ddx/product/definition.md` exists. If it does NOT exist, the user's request IS the product. Set scope to `product`. Do NOT create a capability scope when there is no product yet.

3. If the product exists, determine capability scope:
   - The user may have described what they want. Use that to infer scope.
   - Glob for existing `ddx/*/` docs. Check which scopes don't have `spec.md` yet.
   - If exactly one scope is missing `spec.md`, that is the active scope.
   - If the user's request matches an existing scope (by content), use that scope.
   - If the user's request is something new — this is a new capability. Derive a kebab-case folder name from their description.
   - Only ask the user if it's genuinely ambiguous between multiple scopes.

3. Resolve all paths: replace `{scope}` in output paths.

## Ensure Upstream Exists

Check if `ddx/{scope}/definition.md` exists. If not, generate it now:
1. Read the definition prompt and template from config.
2. Using the user's description and any product-level context (`ddx/product/*.md`), generate the definition. Fill every section — no placeholders. Ask the user brief clarifying questions ONLY if critical information is missing.
3. Write it to the appropriate path.
4. Tell the user you also created it.

### Check if design is needed

Read `ddx/{scope}/definition.md`. Determine if the product has a user interface:

- **Has UI** (web app, mobile app, dashboard, portal, etc.): check if `ddx/{scope}/design.md` (or `design.html`) exists. If not, generate it — read the design prompt and template from config, generate the document, write it, and tell the user.
- **No UI** (API, service, library, CLI, data pipeline, worker, daemon, etc.): skip design entirely. Do NOT generate a design document. Proceed with only the definition as upstream context.

## Generate

1. Read the spec prompt file.
2. Read the spec template file.
3. Read the upstream documents (Definition and Design).
4. If the output file already exists, read it — you are UPDATING.
5. Generate the complete spec document. Follow the template structure. Fill every section — no placeholders.
6. Write the complete document to the resolved output path.

## Review

Tell the user: "I've written the spec to `{output path}`. Please review it — edit anything you'd like to change. When you're done, let me know and I'll read your changes."

If the user says they've made changes or want something adjusted:
1. Re-read the file from disk.
2. Make the requested changes.
3. Write the updated file.

When the user is satisfied, tell them: "The next step is **`/ddx.plan`** to create the Plan. Want me to run it?"
