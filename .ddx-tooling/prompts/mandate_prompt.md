# Mandate Interview

You are gathering project-specific mandate information. The DDX sections are already filled in — focus on the project-specific sections.

## Interview Flow

Walk through these sections one at a time. Ask one question, wait for the answer, update the file, then ask the next.

### 1. Project Identity
Ask: "What is this project? Give me a one-paragraph summary — what it does, who it's for, and why it exists."

### 2. Constraints
Ask: "What are the non-negotiable constraints? Think about: required technologies, architectural boundaries, things that must or must not be used, performance requirements, compliance rules."

If the user gives a short answer, probe once: "Any other constraints? Think about dependencies, deployment targets, or compatibility requirements."

### 3. Always Do
Ask: "What rules should an AI always follow when working in this project? For example: always write tests, always use a specific pattern, always check for existing code before writing new code."

### 4. Never Do
Ask: "What should an AI never do in this project? For example: never use certain patterns, never add dependencies without asking, never modify certain files."

### 5. Conventions
Ask: "Any coding conventions to follow? Think about: naming patterns, file organization, commit message format, code style preferences."

## Guidelines

- If the user says "skip" or "none" for a section, remove the placeholder text and write "None specified." instead.
- If the user gives bullet points, format them as a clean markdown list.
- Keep language direct and actionable — mandates are instructions, not prose.
- Don't add your own constraints or suggestions. Only write what the user tells you.
