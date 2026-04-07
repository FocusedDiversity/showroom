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
