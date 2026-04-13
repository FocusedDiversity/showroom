# Capability Plan: Slide Feedback

## Step 1: Database — Create `slide_feedback` table [DONE]

**Build:** Alembic migration to create the `slide_feedback` table with columns: `id` (serial PK), `view_id` (FK to views), `slide_number` (integer), `comment` (text), `created_at` (timestamp). Add index on `view_id`. Also update `schema.sql` with the new table for fresh installs.

**Depends on:** Nothing

**Verify:** Run `alembic upgrade head`, confirm table exists with `\d slide_feedback` in psql.

---

## Step 2: Backend — Feedback API endpoints [DONE]

**Build:** Add two new endpoints to `app.py`:
- `POST /api/feedback` — accepts `{ "view_id": int, "slide_number": int, "comment": string }`. Validates session email matches the view's `viewer_email`, comment is non-empty and ≤1000 chars, slide_number ≥ 1. Inserts into `slide_feedback`. Returns `{ "ok": true, "feedback_id": int }`. Errors: 400 (bad input), 403 (no session), 404 (view not found).
- `GET /api/feedback?view_id=<int>` — returns the current viewer's own feedback for the given view, ordered by `created_at` ascending. Validates session. Returns `{ "feedback": [ { "id", "slide_number", "comment", "created_at" } ] }`.

**Depends on:** Step 1

**Verify:** Use curl to submit feedback and retrieve it. Confirm session validation and input validation work.

---

## Step 3: Frontend — Feedback UI in viewer [DONE]

**Build:** Add feedback UI to the deck viewer:
- In `deck_view.html`: add a "Feedback" pill button to the topbar (right side, before Synaptiq logo). Add a 320px right-side panel container (hidden by default) that sits beside the iframe — when open, the iframe shrinks horizontally to make room. Panel has three zones: header (slide label + close), scrollable middle (prior comments), input pinned to bottom.
- Create `static/js/feedback.js`: manages panel open/close (toggling panel visibility and iframe width), tracks current slide number (reuses postMessage from iframe), fetches prior feedback on panel open (`GET /api/feedback`), submits new feedback (`POST /api/feedback`), shows confirmation on success, displays prior comments when revisiting a commented slide.
- Include `feedback.js` in `deck_view.html`.

**Depends on:** Step 2

**Verify:** Open a shared deck, click Feedback, submit a comment, see confirmation. Navigate to another slide, submit again. Reopen panel on a previously commented slide and see prior comments.

---

## Step 4: Analytics API — Extend with feedback data [DONE]

**Build:** Extend the `/admin/api/analytics/<deck_id>` endpoint in `app.py` to include feedback data. Add a query that joins `slide_feedback` → `views` → `share_links` where `share_links.deck_id = ?`. Return two new fields in the response: `feedback` (array of objects with `id`, `slide_number`, `viewer_email`, `comment`, `created_at`) and `feedback_count` (integer).

**Depends on:** Step 1

**Verify:** Submit some feedback via the viewer, then hit the analytics API and confirm feedback appears in the response.

---

## Step 5: Analytics UI — Feedback tab [DONE]

**Build:** Update the analytics frontend:
- In `analytics.html`: add tab navigation ("Views" | "Feedback") below the stat cards. Add a Feedback tab container with filter dropdowns (slide number, viewer email) and a table (columns: Slide, Viewer, Feedback, Date). Add empty state markup.
- In `analytics.js`: add "Feedback Items" stat card. Implement tab switching. Populate the feedback table from API data. Implement client-side filtering by slide and viewer. Show empty state when no feedback exists. Slide filter only shows slides with feedback; viewer filter only shows viewers who submitted feedback.

**Depends on:** Step 4

**Verify:** Open analytics for a deck with feedback — see the Feedback tab with filters working. Open analytics for a deck without feedback — see the empty state.

---
