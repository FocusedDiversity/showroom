# Product Plan

## Capability Sequence

### 1. slide-feedback

**Description:** Per-slide feedback system allowing viewers to leave comments on individual slides, with admin toggle to enable/disable feedback per share link.

**Depends on:** nothing

**Status:** complete

---

### 2. shared-feedback

**Description:** Shared feedback visibility — recipients who open a share link can see aggregated feedback from other viewers on the same deck.

**Depends on:** slide-feedback

**Status:** complete

---

### 3. optimistic-feedback

**Description:** Optimistic UI for feedback submission — show feedback instantly in the UI and roll back if the server request fails.

**Depends on:** slide-feedback

**Status:** complete

---

### 4. feedback-toggle

**Description:** Admin-facing toggle to enable or disable the feedback feature per share link.

**Depends on:** slide-feedback

**Status:** complete

---

### 5. deck-authoring

**Description:** Authoring tools to generate branded HTML slide decks from structured markdown content, with theme application, AI-generated title collages via Recraft.ai, multi-variant preview, and iterative refinement before publishing to Showroom.

**Depends on:** nothing (uses existing deck management pipeline)

**Status:** complete

---

### 6. deck-design-system

**Description:** Separates color palettes from slide layouts into independently selectable dimensions. Expands slide templates from 7 to 17 types. Users preview and choose one palette + one layout before generating their deck.

**Depends on:** deck-authoring

**Status:** complete

---

### 7. pptx-import

**Description:** Upload a .pptx file to extract fonts, colors, style cues, and images into a new custom color palette and layout for use in deck generation.

**Depends on:** deck-design-system

**Status:** complete

---

### 8. font-separation

**Description:** Separates font pairings from layout collections into a third independent dimension. Users pick color palette, font pairing, and layout collection independently. Layout collections get preview UI showing their slide type layouts.

**Depends on:** deck-design-system, pptx-import

**Status:** complete
