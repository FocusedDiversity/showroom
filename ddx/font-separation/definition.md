# Definition: Font Separation

## Who are we building for?

Same users as deck-authoring: Synaptiq sales and delivery teams creating branded decks. They want finer-grained creative control — specifically, picking fonts independently from slide layout structure.

## What problem are we solving for them?

Fonts are currently embedded inside the `Layout` object. Choosing "Bold" means you get Abril Fatface titles — always. If a user wants Abril Fatface titles but with the Editorial slide structure, they can't. The 3 layouts × 3 palettes matrix gives 9 combos, but fonts are locked to layouts so there's no way to mix and match.

## How do we know it's a real problem?

- PPTX-imported layouts inherit fonts from the source file but are locked to a base template set. Users can't reuse imported fonts with a different layout collection.
- The Synaptiq brand guide has 4 font families, but only 3 pairings are available — tied to specific layouts.

## What is the impact of the problem?

- **Limited combos:** 3 palettes × 3 layouts = 9 combos. Separating fonts adds a third axis: 3 palettes × 3+ fonts × 3 layout collections = 27+ combos.
- **Creative rigidity:** Users who like Editorial's whitespace but want Bold's display fonts are stuck.

## What's our proposed solution?

1. **Extract font pairing from Layout into a new `FontPairing` dataclass** — title font, content font, Google Fonts import URL.
2. **Rename "Layout" to "Layout Collection"** throughout the UI (the code can keep `Layout` internally but the user-facing label becomes "Layout Collection").
3. **Add a Font Pairing selector** to the authoring form — the user picks palette, font pairing, and layout collection independently.
4. **Layout Collection preview** — user can preview the various slide type layouts within each collection (title, content, comparison, matrix, etc.) rendered with their selected palette + font.
5. **Update the generator** to accept three inputs: palette + font_pairing + layout_collection.
6. **Update PPTX import** to create a separate font pairing alongside the palette and layout collection.

**Out of scope:** Per-slide font overrides, font upload (custom non-Google fonts), WYSIWYG font editing.

## How will we measure success?

- **Combos:** 3+ font pairings × 3+ palettes × 3+ layout collections = 27+ distinct deck styles.
- **User satisfaction:** Users can mix any font with any layout collection.
- **Layout preview:** Users understand what each layout collection looks like before selecting it.
