# Design: Deck Authoring

## Screens

### Admin Screens

#### 1. Authoring Entry (`/admin/author`)

- **Layout**: Two-column form
- **Left column — Content Input**:
  - Dropdown: "Deliverable Model" (discovery, design, quote, kick-off, progress-report, strategy-deliverable, custom)
  - Textarea: Markdown content (pre-populated with model template when a model is selected)
  - File upload: "Or upload a .md file"
- **Right column — Theme & Collage**:
  - Dropdown: "Theme" (Synaptiq Default — soil/arctic/apricot palette, or future custom themes)
  - Theme preview: Color swatches + font samples for the selected theme
  - Radio group: "Title Slide Collage"
    - "Select existing collage" → opens collage gallery modal
    - "Generate new collage" → shows text prompt input + "Generate" button
  - Collage preview thumbnail (once selected or generated)
- **Bottom**: "Generate Previews" button (primary action)

#### 2. Collage Gallery Modal

- **Grid of existing collage images** (thumbnails with labels)
- **Search/filter bar**: Filter by keyword or tag
- **Select action**: Click a thumbnail to select, "Use This Collage" button confirms
- **Upload action**: "Upload New Collage" button to add a custom image

#### 3. Collage Generation Panel (inline, replaces collage preview area)

- **Text prompt input**: "Describe the collage you want" (e.g., "Nature and technology, botanical elements with circuit diagrams")
- **Style preset dropdown**: "Synaptiq Digital Collage" (default), "Photographic", "Abstract"
- **"Generate" button** → shows loading spinner → displays 2-3 generated options as thumbnails
- **Select action**: Click to choose one, "Use This Collage" confirms

#### 4. Preview Selection (`/admin/author/preview/<session_id>`)

- **Layout**: Horizontal carousel of 2-3 generated deck variants
- **Each variant card**:
  - Rendered slide thumbnails (first 3 slides visible, scrollable)
  - "Preview Full Deck" button → opens in a new tab at full resolution
  - "Select This Option" button
- **Variant differences**: Layout variation (e.g., card-based vs. timeline vs. split-screen for content slides), color emphasis shifts (which brand color dominates accents), collage placement/crop variations on title slide
- **Bottom**: "Back to Editor" link, "Regenerate All" button

#### 5. Refinement View (`/admin/author/refine/<session_id>`)

- **Left panel**: Full-size preview of the selected deck (slide-by-slide navigation)
- **Right panel — Feedback**:
  - Textarea: "What would you like to change?" (free-form feedback)
  - Quick-action buttons: "Adjust colors", "Change layout", "Modify title slide", "Edit content"
  - "Apply Changes" button → regenerates with feedback applied, shows updated preview
- **Top bar**: Iteration counter ("Revision 2 of 5"), "Publish to Showroom" button (primary), "Download HTML" button (secondary)
- **Publish action**: Creates the deck in Showroom's existing deck management system (same as manual upload), redirects to `/admin/deck/<id>`

### Viewer Screens

No new viewer screens — authored decks use the existing Showroom viewer.

## Interaction Patterns

- **Model template loading**: Selecting a deliverable model pre-fills the markdown textarea with the model's YAML structure converted to markdown headings and placeholder content. Sales models (discovery, quote) and delivery models (kick-off, progress-report, strategy-deliverable) each have distinct section structures.
- **Theme preview**: Changing the theme dropdown instantly updates the color swatches and font samples. No page reload.
- **Generation progress**: "Generate Previews" shows a progress bar with status messages ("Parsing content...", "Applying theme...", "Rendering slides..."). Takes 10-30 seconds.
- **Collage generation via Recraft.ai**: Shows a loading state with "Generating collage..." message. Returns 2-3 options in ~15 seconds.
- **Refinement loop**: Each "Apply Changes" cycle preserves the conversation history of feedback so the generator understands cumulative intent (e.g., "make the header bigger" followed by "actually a bit smaller" results in slightly-bigger-than-original).
- **Publish flow**: "Publish to Showroom" opens a confirmation modal with deck title (editable), description (optional), and "Publish" button. Creates the deck and redirects to the deck detail page.
- **Session persistence**: Authoring sessions are saved server-side so users can leave and return to an in-progress deck.

## Branding

- Authoring UI follows the existing Showroom admin style (same base layout, fonts, colors).
- Generated decks follow Synaptiq brand guidelines:
  - **Primary palette**: Soil (#312A29), Apricot Ink (#F7CFA5), Arctic (#A1B8CA)
  - **Secondary palette**: Mint (#C6E1D9), Sky (#B6DDED), Stone (#A59B93), Grapefruit (#E8DE90), Agave (#6A888D), Fog (#E2E1E3)
  - **Tertiary palette**: Hale Navy (#494F5B), Pine (#1D6E6F), Jasper (#CC5E58), Parchment (#F6F2D6), Blush (#F1DCD0)
  - **Fonts (Google alternatives)**: Zilla Slab (headlines), Quicksand (body/captions), Herr Von Muellerhoff (script accent), Abril Fatface (bold accent)
  - **Logo**: Butterfly logomark + wordmark, correct clear space, never on Arctic blue background
  - **Imagery**: Digital collage style (surrealist assemblage), photography inspired by history/science/literature/math/nature, hopeful/artful/thoughtful/future-forward
