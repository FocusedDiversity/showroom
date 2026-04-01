---
name: ddx.plan
description: Generates a Plan document. Product plans sequence capabilities in build order. Capability plans have detailed build steps.
disable-model-invocation: true
---

You are generating a Plan. The plan structure depends on whether you're planning at the PRODUCT level or the CAPABILITY level.

IMPORTANT: Use file reading/glob tools, NOT shell commands. Do NOT use Bash to create directories — just write files directly with the Write tool and directories are created automatically. Be frictionless — if upstream docs are missing, generate them yourself rather than telling the user to run another command.

## Scope Resolution (do this FIRST)

1. Read `.ddx-tooling/config.yaml` to find all document entries. Note prompts, templates, and output paths (contain `{scope}`).

2. Check if `ddx/product/definition.md` exists. If it does NOT exist, the user's request IS the product. Set scope to `product`. Do NOT create a capability scope when there is no product yet.

3. If the product exists, determine capability scope:
   - The user may have described what they want. Use that to infer scope.
   - Glob for existing `ddx/*/` docs. Check which scopes don't have `plan.md` yet.
   - If exactly one scope is missing `plan.md`, that is the active scope.
   - If the user's request matches an existing scope (by content), use that scope.
   - If the user's request is something new — this is a new capability. Derive a kebab-case folder name from their description.
   - Only ask the user if it's genuinely ambiguous between multiple scopes.

3. Resolve all paths: replace `{scope}` in output paths.

4. Determine plan type:
   - If scope is `product` → PRODUCT PLAN.
   - Otherwise → CAPABILITY PLAN.

## Ensure Upstream Exists

Check if `ddx/{scope}/definition.md` and `ddx/{scope}/spec.md` exist. For each missing doc, generate it now (read its prompt and template from config, use available context, write to disk, tell the user). Generate definition first, then spec.

### Check if design is needed

Read `ddx/{scope}/definition.md`. Determine if the product has a user interface:

- **Has UI** (web app, mobile app, dashboard, portal, etc.): check if `ddx/{scope}/design.md` (or `design.html`) exists. If not, generate it before generating spec.
- **No UI** (API, service, library, CLI, data pipeline, worker, daemon, etc.): skip design entirely. Do NOT generate a design document.

## Generate

1. Read the plan prompt file.
2. Read the plan template file.
3. Read the upstream documents — Definition, Spec, and Design (only if design exists / product has UI).
4. If the output file already exists, read it — you are UPDATING.

### Product Plan

The product plan sequences which capabilities to build and in what order. It does NOT contain implementation steps.

1. Read the product definition and spec (and design, if it exists).
2. Identify all distinct capabilities described in these documents.
3. For each capability, determine:
   - A short kebab-case name (suitable as a folder name)
   - A one-line description
   - Dependencies on other capabilities
4. Order from foundational (no dependencies) to complex (depends on earlier ones).
5. Write the plan using this structure:

```
# Product Plan

## Capability Sequence

### 1. {capability-name}
**Description:** {what this capability covers}
**Depends on:** {nothing, or earlier capabilities}
**Status:** not started

### 2. {capability-name}
...
```

### Capability Plan

Detailed build steps for a single capability.

1. Read the capability's definition and spec (and design, if it exists).
2. Also read `ddx/product/plan.md` to understand where this capability fits and what it depends on. If dependency capabilities have specs, skim them for interfaces this capability integrates with.
3. Decompose into ordered steps from low to high complexity. Each step builds on the previous.
4. Write the plan to the resolved output path using the template structure.
5. After writing, if `ddx/product/plan.md` exists, update this capability's status to `in progress` in the product plan.

## Review

Tell the user: "I've written the plan to `{output path}`. Please review it — reorder, split, or merge steps as needed. When you're done, let me know and I'll read your changes."

If the user says they've made changes or want something adjusted:
1. Re-read the file from disk.
2. Make the requested changes.
3. Write the updated file.

When the user is satisfied, tell them: "The plan is finalized. The next step is **`/ddx.build`** to start building. Want me to run it?"

### Product Plan Auto-Update

If the product plan already exists AND new capability folders have been added (glob for `ddx/*/definition.md` and compare against capabilities listed in the plan):
- Read the existing product plan.
- Read the new capability's `definition.md`.
- Add the new capability to the sequence in the appropriate position.
- Update the status of completed capabilities (those with all four docs: definition.md, design.md, spec.md, plan.md) to `complete`.
- Write the updated product plan.
