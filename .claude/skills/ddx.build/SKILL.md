---
name: ddx.build
description: Builds a capability by reading the DDX plan and executing it step by step. Writes code, creates files, and verifies each step.
disable-model-invocation: true
---

You are building a capability from its DDX documents. You will read the plan and execute it step by step.

IMPORTANT: All work happens inside the current project directory. Do NOT explore, read, or search files outside of it. Do NOT look in parent directories or other projects. Everything you need is in the DDX documents and the current project.

IMPORTANT: Use file reading/glob tools, NOT shell commands for file discovery. Do NOT use Bash to create directories — just write files directly with the Write tool and directories are created automatically. Be frictionless — if upstream docs are missing, generate them yourself rather than telling the user to run another command.

## Scope Resolution (do this FIRST)

1. Read `.ddx-tooling/config.yaml`.

2. Check if `ddx/product/definition.md` exists. If it does NOT exist, the user's request IS the product. Set scope to `product` and generate all product-level docs (definition, design, spec, plan) from the user's description. Do NOT create a capability scope when there is no product yet.

3. If the product exists, determine capability scope:
   - The user may have described what they want. Use that to infer scope.
   - Glob for `ddx/*/plan.md` files (excluding `product`).
   - If exactly one scope has a `plan.md`, that is the active scope.
   - If the user's request matches an existing scope (by content), use that scope.
   - If the user's request is something new — this is a new capability. Derive a kebab-case folder name and generate ALL upstream docs (definition, design, spec, plan) before building.
   - Only ask the user if it's genuinely ambiguous between multiple scopes.

4. Set the scope.

## Load Context

Read these documents for this scope:
- `ddx/{scope}/definition.md` — the what and why
- `ddx/{scope}/spec.md` — the architecture and technical decisions
- `ddx/{scope}/plan.md` — the ordered build steps

Also read `ddx/product/definition.md` and `ddx/product/spec.md` if they exist and scope is not `product`, for product-level context.

### Check if design is needed

Read the definition. Determine if the product has a user interface:

- **Has UI** (web app, mobile app, dashboard, portal, etc.): also read `ddx/{scope}/design.md` (or `design.html`) — the wireframes and interaction design. If missing, generate it.
- **No UI** (API, service, library, CLI, data pipeline, worker, daemon, etc.): skip design entirely. Do NOT load or generate a design document.

If any required documents are missing (definition, spec, plan — and design if UI product), generate them now (read their prompts and templates from config, use available context, write to disk) rather than stopping.

## Build

Execute the plan step by step:

1. Read the plan. Identify Step 1.
2. For each step:
   - Tell the user which step you're working on: "Building Step {N}: {step name}"
   - Read the **Build** field to know what to implement.
   - Read the **Depends on** field to understand what should already exist.
   - Read the **Verify** field to know what success looks like.
   - Implement the step — write code, create files, install dependencies, whatever the step requires. Use the spec and design documents as your reference for technical decisions and UI details.
   - After implementing, run the verification described in the **Verify** field. If it passes, move to the next step. If it fails, fix the issue before moving on.
3. After completing each step, update `ddx/{scope}/plan.md` — mark the step as done by adding `[DONE]` to the step heading.
4. Continue to the next step.

## Completion

When all steps are done:
- If this is a capability and there are more capabilities in the product plan that are not yet built, tell the user: "The {scope} capability is built. The next capability in the product plan is **{next-capability}**. Want me to run **`/ddx.build`** for it?"
- If all capabilities are built (or this is a product-level build), tell the user: "All steps in the plan are complete. The {scope} capability is built."
