---
name: ddx.mandate
description: Creates or updates the project mandate — high-level identity, constraints, always-do/never-do rules, and DDX usage guidance for AI agents.
disable-model-invocation: true
---

You are creating or updating the project MANDATE. The mandate is the project-level source of truth that every AI agent reads before doing any work. It lives at `ddx/MANDATE.md` and is referenced from the project's CLAUDE.md.

IMPORTANT: Use file reading/glob tools, NOT shell commands. Do NOT use Bash to create directories — just write files directly with the Write tool and directories are created automatically.

## Check Current State

1. Read `.ddx-tooling/config.yaml` to find the `mandate` entry. Note the `prompt`, `template`, and `output` paths.

2. Check if `ddx/MANDATE.md` already exists.
   - If it exists, read it — you are UPDATING. Tell the user: "The mandate already exists. I'll walk through each section — tell me what to change or say 'skip' to keep it as-is."
   - If it does NOT exist, you are CREATING.

## Create the File Immediately (skip if updating)

1. Read the prompt file.
2. Read the template file.
3. Write the template to `ddx/MANDATE.md` RIGHT NOW — the DDX guidance sections are already filled in, the project-specific sections have placeholder text.
4. Tell the user: "I've created `ddx/MANDATE.md` with DDX guidance pre-filled. Now let's fill in the project-specific sections."

## Interview (fill the document as you go)

Follow the prompt file instructions. Walk through the project-specific sections one at a time.

CRITICAL RULE: Every time the user answers a question, you MUST:
1. FIRST — use the Edit tool or Write tool to update `ddx/MANDATE.md` with the new content. Replace the placeholder text in the relevant section(s) with real content based on the user's answer.
2. THEN — in your text response, briefly confirm what you wrote (one line) and ask the next question.

You must call the edit/write tool BEFORE responding with text. Never respond to a user's answer without updating the file. The document on disk must always reflect everything gathered so far.

If the user says they edited the file: re-read it from disk, acknowledge their changes, and continue from where you are.

Do NOT dump all questions at once.

## Finishing

When all sections are filled (or the user says "done" / "that's good"):

1. Re-read the file in case the user made final edits.
2. Do a final write to clean up any remaining placeholder text.
3. Verify that `CLAUDE.md` in the project root references the mandate. If it doesn't, add a line:
   ```
   Read and follow the project mandate: ddx/MANDATE.md
   ```
4. Tell the user: "The mandate is set. Every AI agent working in this project will read it. You can edit `ddx/MANDATE.md` directly anytime, or run `/ddx.mandate` again to update it interactively."
