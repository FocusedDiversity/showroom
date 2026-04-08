# Definition: Deck Design System

## Who are we building for?

Same users as deck-authoring: **Synaptiq sales and delivery teams** creating branded slide decks. They now have a working authoring pipeline (markdown → deck) but need more visual variety and creative control — specifically, independent choice over color treatment and slide layout style.

## What problem are we solving for them?

The current authoring system bundles color emphasis and layout variation into opaque "variants" (Arctic Focus, Apricot Focus, Warm Tones). Users cannot independently choose a color palette or a layout style — they pick from 3 pre-baked combinations and hope one fits. Additionally, the system only supports 7 slide types, leaving many common presentation needs (agenda, comparison, matrix, quote, table) unserved.

## How do we know it's a real problem?

- Users requested the ability to pick colors independently from layouts during internal feedback on the authoring tool.
- The 7 current slide types force workarounds — a comparison is shoehorned into cards, an agenda into a text slide, a 2×2 matrix cannot be represented at all.
- Consulting deliverables require diverse slide types (McKinsey-style matrices, data tables, testimonial quotes) that the current system cannot produce.

## What is the impact of the problem?

- **Creative constraint:** 3 coupled variants means 3 total options. Separating palette × layout yields 9+ combinations from the same 3×3 matrix.
- **Content gaps:** 10 common slide types have no template, forcing manual HTML editing or awkward substitutions.
- **Brand underuse:** The Synaptiq brand guideline defines a rich palette (15+ colors) and 4 font families, but only a fraction is expressed through the current templates.

## What's our proposed solution?

Refactor the authoring system into two independently selectable dimensions:

1. **Color Palettes** (≥3 options) — Named combinations of brand colors (backgrounds, accents, gradients, text colors) derived from the Synaptiq brand guideline. Each palette uses the same HTML templates but applies different CSS color variables.

2. **Slide Layouts** (≥3 options) — Named layout packages, each providing a complete set of templates for all 17 slide types. Each layout has a distinct font pairing (title font ≠ content font) and a characteristic visual style (spacing, decorative elements, card shapes, etc.).

3. **Expanded Slide Types** (17 total):
   - Title slide
   - Section divider slide
   - Agenda / roadmap slide
   - Problem / context slide
   - Key message slide
   - Content / detail slide
   - Data / chart slide
   - Comparison slide
   - Process / timeline slide
   - Visual / image-driven slide
   - Quote / testimonial slide
   - Summary / key takeaway slide
   - Call to action / recommendations slide
   - 2×2 matrix slide
   - Table slide
   - Closing / thank you slide
   - Blank slide

4. **Preview & Selection UI** — Users preview color palettes (swatches + sample slide) and layout packages (rendered sample slides) independently, then select one palette + one layout to generate their deck.

**Out of scope:** Custom palette creation, drag-and-drop layout editing, per-slide palette/layout overrides.

## How will we measure success?

- **Variety:** Generated decks show noticeably different visual styles across palette × layout combinations.
- **Slide coverage:** All 17 slide types render correctly in every palette × layout combination (17 × 3 × 3 = 153 combinations).
- **Selection time:** Users pick palette + layout in under 2 minutes via the preview UI.
- **Adoption:** >90% of authored decks use the new palette/layout selector (vs. falling back to old variant flow).
