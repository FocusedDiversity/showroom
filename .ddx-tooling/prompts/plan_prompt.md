# Plan Prompt

Goal: Break the spec and design into ordered implementation steps that an AI coding agent can follow.

Mode:
- Read the upstream documents. Identify every component, screen, and integration from the spec and design.
- Decompose the work into steps ordered from low complexity to high complexity. Each step must build on the previous — never reference something that hasn't been built in an earlier step.
- Present the proposed steps to the user. For each step show: what gets built, what it depends on from earlier steps, and what the user can verify when it's done.
- Ask the user to confirm, reorder, split, or merge steps before writing the document. Show this instruction: "I will write the plan. Please review it — reorder, split, or merge steps as needed. When you're done, let me know and I'll read your changes."
- When user tells you they're done, read the document and ask if they want you to change anything.

Rules:
- Each step is a self-contained task. An AI agent should be able to read one step and execute it without reading ahead.
- Steps must be ordered so earlier steps are simpler and later steps build on them. Foundation first, integrations last.
- Each step must have a clear verification — what the user can see or test to confirm the step is done.
- No guessing. If the spec is ambiguous about build order or dependencies, ask.
- If you're showing options, use numbered bullet points.
- Prefer closed questions. Minimize cognitive load.
