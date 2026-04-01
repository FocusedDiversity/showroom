---
name: ddx.design
description: Generates a Design document that translates the Definition into wireframes and interaction design.
disable-model-invocation: true
---

You are generating a Design document. This document translates the Definition into wireframes and interaction design.

IMPORTANT: Use file reading/glob tools, NOT shell commands. Do NOT use Bash to create directories — just write files directly with the Write tool and directories are created automatically. Be frictionless — if upstream docs are missing, generate them yourself rather than telling the user to run another command.

## Scope Resolution (do this FIRST)

1. Read `.ddx-tooling/config.yaml` to find the `definition` and `design` entries. Note prompts, templates, and output paths (contain `{scope}`). Also note the `mode` field under `design` — it will be `"ascii"` or `"html"`.

2. Check if `ddx/product/definition.md` exists. If it does NOT exist, the user's request IS the product. Set scope to `product`. Do NOT create a capability scope when there is no product yet.

3. If the product exists, determine capability scope:
   - The user may have described what they want. Use that to infer scope.
   - Glob for `ddx/*/definition.md`. Check which scopes don't have a design file yet (check for both `design.md` and `design.html` depending on mode).
   - If exactly one scope is missing a design file, that is the active scope.
   - If the user's request matches an existing scope (by content), use that scope.
   - If the user's request is something new — this is a new capability. Derive a kebab-case folder name from their description.
   - Only ask the user if it's genuinely ambiguous between multiple scopes.

3. Resolve all paths: replace `{scope}` in output paths.

## Determine Design Mode

Read the `mode` field from the `design` entry in config:

- If `mode` is `"ascii"` (default): use the `prompt`, `template`, and `output` fields.
- If `mode` is `"html"`: use the `html_prompt`, `html_template`, and `html_output` fields.

This determines which prompt instructions, template structure, and output file path you will use.

## Ensure Upstream Exists

Check if `ddx/{scope}/definition.md` exists.

If it does NOT exist — generate it now:
1. Read the definition prompt and template from config.
2. Using the user's description and any product-level context (`ddx/product/definition.md` if it exists), generate a complete definition document. Fill every section — no placeholders. Ask the user brief clarifying questions ONLY if critical information is missing.
3. Write it to `ddx/{scope}/definition.md`.
4. Tell the user: "I've also created the definition at `ddx/{scope}/definition.md`."

## Technical Product Detection

Read `ddx/{scope}/definition.md`. Based on the proposed solution and the overall product description, determine if this product has a user interface:

- **Needs design** (has UI): web apps, mobile apps, desktop apps, dashboards, portals, browser extensions, or anything with screens that end-users directly see and interact with visually.
- **Skip design** (no UI): APIs, services, libraries, SDKs, CLIs, data pipelines, ETL jobs, workers, daemons, infrastructure tools, message brokers, or any product where the primary interface is code, configuration, or command-line — not visual screens.

If the product does NOT need a user interface:
1. Tell the user: "This is a technical product without a user interface — the design phase is not needed. The next step is **`/ddx.spec`** to create the Spec. Want me to run it?"
2. **STOP here. Do not generate a design document.**

## Generate

1. Read the design prompt file (ascii or html, based on mode).
2. Read the design template file (ascii or html, based on mode).
3. Read the upstream Definition.
4. If the output file already exists, read it — you are UPDATING.
5. Generate the complete design document following the prompt instructions and template structure. Fill every section — no placeholders.
6. Write the complete document to the resolved output path.

### HTML Mode Notes

When generating in HTML mode:
- The output is a single `.html` file the user can open in any browser.
- It loads Tailwind CSS from the local copy at `.ddx-tooling/tailwind.js` (downloaded during `ddx init`). Use `<script src="../.ddx-tooling/tailwind.js"></script>`.
- Build realistic-looking UI mockups with styled HTML elements (buttons, inputs, cards, navbars, etc.) — not ASCII wireframes.
- Each screen is wrapped in a device-like frame and includes Visual + Interaction notes below it.
- All screens are on one scrollable page with a table of contents at the top.
- Interactive elements should be styled but do NOT need to be functional.

## Review

Tell the user: "I've written the design to `{output path}`. Please review it — edit anything you'd like to change. When you're done, let me know and I'll read your changes."

For HTML mode, also tell them: "You can open this file directly in your browser to preview the designs."

If the user says they've made changes or want something adjusted:
1. Re-read the file from disk.
2. Make the requested changes.
3. Write the updated file.

When the user is satisfied, tell them: "The next step is **`/ddx.spec`** to create the Spec. Want me to run it?"
