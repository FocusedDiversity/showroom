# Definition: PPTX Import

## Who are we building for?

Same users as deck-authoring: **Synaptiq sales and delivery teams**. They have existing PowerPoint decks — from clients, from previous engagements, from other design tools — and want to bring those visual identities into Showroom's authoring system without manually recreating palettes and layouts.

## What problem are we solving for them?

The deck design system currently offers 3 built-in palettes and 3 built-in layouts. Teams working with a client's brand or repurposing an existing PPTX deck must manually eyedropper colors, identify fonts, and pick the closest built-in option. There's no way to create custom palettes or layouts, and no way to import visual identity from an existing file.

## How do we know it's a real problem?

- Delivery teams regularly receive client-branded PPTX files and need to produce Showroom decks matching that brand.
- Sales teams sometimes adapt decks from previous engagements but must start from scratch visually.
- The 3 built-in palettes only cover Synaptiq brand variations — there's no option for client brands.

## What is the impact of the problem?

- **Manual effort:** Extracting colors and fonts from a PPTX takes 15-30 minutes and is error-prone.
- **Limited options:** Only 3 palettes × 3 layouts = 9 combinations. Client work needs more.
- **Inconsistency:** Manually picked colors often don't match the source exactly.

## What's our proposed solution?

Add a PPTX upload endpoint to the authoring admin. When a user uploads a `.pptx` file:

1. **Extract the color scheme** from the slide master/theme — map the theme colors (dk1, dk2, lt1, lt2, accent1-6) to the `Palette` dataclass fields (background_dark, accent_primary, etc.).
2. **Extract font families** from the slide master — the heading font and body font become `font_title` and `font_content` on a new `Layout`. Map to the closest Google Fonts equivalent.
3. **Extract style cues** — approximate border-radius, spacing, and accent styles from the PPTX theme to populate `style_metadata`.
4. **Extract images** from slides — store as collage candidates in the collage library.
5. **User provides names** — the user names both the new palette and the new layout before saving.
6. **Persist** — save the new palette and layout so they appear in the authoring form alongside the built-in options.

The new layout reuses one of the existing template directories (editorial/bold/elegant — closest match) but with the extracted fonts and style metadata. No new HTML templates are generated.

**Out of scope:** Converting PPTX slide content into markdown, importing slide animations, importing PPTX charts as live data, creating new HTML template sets per import.

## How will we measure success?

- **Extraction accuracy:** Imported palette colors match the source PPTX theme within visual tolerance.
- **Time savings:** Creating a custom palette + layout from a PPTX takes under 2 minutes (vs 15-30 minutes manually).
- **Adoption:** Users create custom palettes/layouts for >50% of client-branded decks.
