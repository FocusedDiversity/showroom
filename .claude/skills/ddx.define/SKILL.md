---
name: ddx.define
description: Conducts a Definition interview to create the root document in the DDX document chain. Defines the product or capability through guided questions.
disable-model-invocation: true
---

You are conducting a Definition interview. This is the ROOT document in the DDX document chain.

IMPORTANT: Use file reading/glob tools, NOT shell commands. Do NOT use Bash to create directories — just write files directly with the Write tool and directories are created automatically. Be frictionless — never block the user with choices when you can make a reasonable decision yourself.

## Scope Resolution (do this FIRST)

1. Read `.ddx-tooling/config.yaml` to find the `definition` entry. Note the `prompt`, `template`, and `output` paths. The output path contains `{scope}` — you will resolve it below.

2. Determine the current state by checking for specific files:

   **No `ddx/product/definition.md` and no other `ddx/*/definition.md` files:**
   Fresh project. Set scope to `product`.

   **`ddx/product/definition.md` exists:**
   Product is defined. The user is defining a CAPABILITY.
   - The user may have already described what they want (in the prompt that invoked this skill, or in conversation). Use that to derive a short kebab-case folder name.
   - Check existing capabilities: glob for `ddx/*/definition.md` (excluding product), read the first 10 lines of each. If the user's request clearly matches an existing capability, set scope to that capability — you are UPDATING it (append a versioned section: `## v{N} — {YYYY-MM-DD}: {what changed}`).
   - If no match, this is a new capability. Set scope to the new kebab-case name. Do NOT ask the user to confirm the name unless it's genuinely ambiguous.

   **No `ddx/product/definition.md` but other files exist outside `ddx/`:**
   Tell the user: "No product definition found. Run `/ddx.derive` first to document your existing codebase." STOP here.

3. Resolve the output path: replace `{scope}` with the determined scope.

4. If the output file already exists, read it — you are UPDATING.

## Create the File Immediately

1. Read the prompt file.
2. Read the template file.
3. Write the template to the resolved output path RIGHT NOW — with all placeholder text intact. The file must exist on disk before you ask the first question.
4. Tell the user: "I've created the file at `{output path}`. I'll fill it in as we go. You can open it and edit anytime — just tell me when you've made changes."

## Interview (fill the document as you go)

Follow the prompt instructions. Conduct a conversational interview — one question at a time.

CRITICAL RULE: Every time the user answers a question, you MUST:
1. FIRST — use the Edit tool or Write tool to update the file on disk with the new content. Replace the placeholder text in the relevant section(s) with real content based on the user's answer.
2. THEN — in your text response, briefly confirm what you wrote (one line) and ask the next question.

You must call the edit/write tool BEFORE responding with text. Never respond to a user's answer without updating the file. The document on disk must always reflect everything gathered so far.

If the user says they edited the file: re-read it from disk, acknowledge their changes, and continue from where you are.

Do NOT dump all questions at once.

## Finishing

When all sections are filled (or the user says "that's good" / "done"):

1. Re-read the file in case the user made final edits.
2. Do a final write to clean up any remaining placeholder text.
3. Determine the next step based on the definition content:
   - If the product has a user interface (web app, mobile app, dashboard, portal, etc.): tell the user: "The next step is **`/ddx.design`** to create the Design. Want me to run it?"
   - If the product is technical with no UI (API, service, library, CLI, data pipeline, worker, etc.): tell the user: "This is a technical product without a UI, so we skip design. The next step is **`/ddx.spec`** to create the Spec. Want me to run it?"
