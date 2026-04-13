# Design Prompt

Goal: Read the definition and produce wireframes with design annotations that fully describe the user experience.

Mode:
- Read the definition document. Identify every distinct screen or view the user will interact with.
- Generate ALL wireframes and annotations in a single pass. Do NOT ask the user to confirm each screen individually — produce the complete design document at once.
- Write the full document to disk, then tell the user to review it.

Rules:
- One wireframe per screen or distinct state. If a screen has meaningfully different states (empty, loaded, error), wireframe each.
- Wireframes use ASCII box-drawing. Use `+`, `-`, `|` for borders. Use `[ Button ]` for actions, `( radio )` for radios, `[x]` for checkboxes, `[ input field___ ]` for inputs, `---` for dividers. Keep proportions readable — no wider than 72 characters.
- Each wireframe is immediately followed by its annotations — no separation.
- Annotations are two short bullet lists: **Visual** (layout, hierarchy, what the user sees) and **Interaction** (what happens on tap/click/submit, navigation, state changes).
- Keep bullets to one line each. No paragraphs.
