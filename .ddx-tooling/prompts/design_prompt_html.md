# Design Prompt (HTML Mode)

Goal: Read the definition and produce a single HTML file with visual wireframes and design annotations for every screen, using Tailwind CSS.

Mode:
- Read the definition document. Identify every distinct screen or view the user will interact with.
- Generate ALL screen designs and annotations in a single pass. Do NOT ask the user to confirm each screen individually — produce the complete HTML file at once.
- Write the full file to disk, then tell the user to review it (they can open it in any browser).

Rules:
- The output is a single HTML file. It loads Tailwind CSS from the local copy at `.ddx-tooling/tailwind.js` (downloaded during `ddx init`). Use `<script src="../.ddx-tooling/tailwind.js"></script>` — no CDN, no build step.
- One visual mockup per screen or distinct state. If a screen has meaningfully different states (empty, loaded, error), mock up each.
- Each screen mockup should look like a realistic UI — use Tailwind utility classes for layout, typography, colors, spacing, borders, and shadows. Render actual buttons, inputs, cards, navbars, sidebars, modals, etc. as styled HTML elements. These are visual designs, not wireframes.
- Use a neutral/professional color palette unless the definition specifies brand colors. Gray backgrounds, white cards, blue primary actions, red destructive actions.
- Each screen is wrapped in a device-like frame (rounded border, shadow, max-width container) to visually separate it on the page.
- Below each screen mockup, include a notes section with two bullet lists: **Visual** (layout, hierarchy, what the user sees) and **Interaction** (what happens on tap/click/submit, navigation, state changes).
- Keep note bullets to one line each. No paragraphs.
- The page itself has a table of contents at the top linking to each screen via anchor IDs.
- All screens are on one scrollable page — no separate files, no JavaScript routing.
- Interactive elements (buttons, inputs, dropdowns) should be styled but do NOT need to be functional. This is a static design document.
