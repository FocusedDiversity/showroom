# Definition: Deck Authoring

## Who are we building for?

- **Synaptiq sales and marketing team** — create prospect-facing decks (discovery, quotes, proposals) to win new business.
- **Synaptiq delivery team** — create client-facing decks throughout engagements: project kick-offs, data strategy deliverables, progress reports, executive readouts, and final handoff presentations. As a consulting company, delivery produces the highest volume of tailored decks — each engagement generates multiple decks customized to the client's context.

Both teams currently rely on manual HTML/CSS editing or external design tools and produce 20-30+ branded decks per month combined.

## What problem are we solving for them?

Creating a branded HTML slide deck today requires either design expertise and hand-coding, or a cumbersome round-trip through external design tools followed by HTML export. The team has brand guidelines, content models (discovery, design, quote, kick-off, progress report, strategy deliverable), and reusable themes, but no streamlined path from structured content to a finished, brand-compliant deck. Delivery teams feel this most acutely — they need to produce client-specific decks on tight timelines throughout every engagement.

## How do we know it's a real problem?

- Decks are the primary deliverable for both sales (every deal involves at least one) and delivery (each engagement produces 3-5+ client-facing decks: kick-off, strategy, progress, readout, handoff).
- The existing branded deck (`Synaptiq_Deck_for_Sri_Branded.html`) was hand-crafted: ~800 lines of CSS and inline SVG per deck. This is not scalable.
- Content models already exist in YAML (e.g., `deliverable-models/sales/quote.yaml`) but there is no tooling to transform them into slides.
- Brand guidelines (53-page PDF) define precise colors, fonts, imagery rules, and collage style — easy to get wrong when hand-coding.

## What is the impact of the problem?

- **Time:** Each hand-crafted deck takes hours of design and coding work.
- **Consistency:** Without automated theming, decks drift from brand guidelines (wrong colors, fonts, logo misuse).
- **Bottleneck:** Only team members with HTML/CSS skills can produce decks, creating a dependency.
- **Iteration cost:** Refining a deck (content changes, layout tweaks) requires re-editing raw HTML.

## What's our proposed solution?

An authoring toolset integrated into Showroom that:

1. **Accepts markdown content** structured against predefined deliverable models (discovery, design, quote, kick-off, progress report, strategy deliverable, etc.).
2. **Applies a brand theme** — colors, fonts, layout patterns, and logo placement derived from the Synaptiq brand guidelines.
3. **Generates a title slide collage** — either by selecting from an existing collage library or generating a new one via the Recraft.ai API with a text prompt.
4. **Produces 2-3 preview options** — varying layout, color emphasis, and collage placement so the user can compare.
5. **Supports iterative refinement** — the user selects a preferred option and provides feedback to adjust it before publishing to Showroom.

Output is a self-contained HTML deck (same format Showroom already hosts), ready for upload and sharing.

**Out of scope:** WYSIWYG drag-and-drop slide editing, real-time collaborative editing, non-HTML output formats (PDF, PPTX).

## How will we measure success?

- **Deck creation time:** From content-ready to published deck should drop from hours to under 15 minutes.
- **Brand compliance:** Generated decks pass a checklist of brand rules (correct palette, fonts, logo usage, imagery direction) without manual review.
- **Adoption:** Team uses authoring tools for >80% of new decks within 1 month of launch.
- **Iteration speed:** Refinement round-trips (select option, give feedback, regenerate) complete in under 2 minutes each.
