# Spec: Slide Feedback

## Summary

Adds a lightweight feedback capability to the Showroom deck viewer, allowing recipients to submit free-text comments tied to specific slides. Comments are stored per viewer email + slide number and surfaced in the admin analytics dashboard via a new Feedback tab with filtering by slide and viewer.

## Context & Requirements

- **Stack**: Flask 3.0+, PostgreSQL (psycopg3, raw SQL), Alembic, vanilla JS, Jinja2
- **Scale**: Low volume — dozens of viewers per deck, not thousands. No performance-critical paths.
- **Latency**: Feedback submission should feel instant (<500ms round-trip).
- **Auth**: No login system. Viewer identity comes from the email gate session (`viewer_email_{token}`). Admin routes are unprotected (internal tool).
- **No new dependencies**: No ORM, no frontend framework, no external services.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Deck Viewer (Browser)               │
│                                                      │
│  ┌──────────┐   postMessage   ┌──────────────────┐  │
│  │  iframe   │ ──────────────>│  Parent Frame     │  │
│  │ (slides)  │                │  heartbeat.js     │  │
│  └──────────┘                │  feedback UI       │  │
│                               │    │               │  │
│                               └────┼───────────────┘  │
└────────────────────────────────────┼──────────────────┘
                                     │ POST /api/feedback
                                     │ GET  /api/feedback
                                     ▼
                          ┌─────────────────────┐
                          │   Flask (app.py)     │
                          │                     │
                          │  POST /api/feedback  │  ← submit
                          │  GET  /api/feedback  │  ← viewer's own
                          │  GET  /admin/api/    │
                          │    analytics/:id     │  ← extended
                          └─────────┬───────────┘
                                    │ raw SQL
                                    ▼
                          ┌─────────────────────┐
                          │    PostgreSQL        │
                          │                     │
                          │  slide_feedback      │
                          │  (view_id, slide,    │
                          │   email, comment,    │
                          │   created_at)        │
                          └─────────────────────┘
```

- **Feedback UI** — lives in the parent frame (deck_view.html), not injected into the iframe. Right-side panel (320px wide) toggled via a topbar button. Sits beside the iframe, not on top of it. Has access to `view_id` and session.
- **`POST /api/feedback`** — accepts `view_id`, `slide_number`, `comment`. Validates session, writes to `slide_feedback` table.
- **`GET /api/feedback?view_id=`** — returns the current viewer's prior comments grouped by slide, so the panel can show them when reopened.
- **Analytics API** — `/admin/api/analytics/<deck_id>` response extended with a `feedback` array containing all feedback for the deck.
- **`slide_feedback` table** — new table with FK to `views`.
- **Analytics JS** — extended to render a Feedback tab with slide and viewer filter dropdowns.

## Component Details

### Feedback UI (Frontend — Parent Frame)

**Files:** `templates/viewer/deck_view.html`, new `static/js/feedback.js`

- Topbar gains a "Feedback" pill button (right side, before Synaptiq logo)
- Clicking toggles a 320px right-side panel that sits beside the iframe (iframe shrinks horizontally):
  - Header: "Feedback for Slide N" label + close button (updates via existing `postMessage` slide tracking)
  - Scrollable middle: prior comments for this slide (fetched on open)
  - Bottom: text input + Send button (pinned)
- Submit sends `POST /api/feedback` with `view_id`, `slide_number`, `comment`
- On success: show confirmation in the panel, clear input, prepend new comment to prior list
- On error: inline error message
- Panel never overlaps/covers slide content — the iframe resizes to accommodate it
- `view_id` is already available in the template (passed to `startHeartbeat()`)

### Feedback API (Backend)

**File:** `app.py`

#### `POST /api/feedback`

```
Request:  { "view_id": int, "slide_number": int, "comment": string }
Response: { "ok": true, "feedback_id": int }
Errors:   400 (missing/invalid fields), 403 (no session), 404 (view not found)
```

- Validates: `view_id` exists, session email matches the view's `viewer_email`, comment is non-empty and ≤1000 chars, `slide_number` ≥ 1
- Inserts into `slide_feedback`

#### `GET /api/feedback?view_id=<int>`

```
Response: { "feedback": [ { "id": int, "slide_number": int, "comment": string, "created_at": string } ] }
```

- Returns only the current viewer's feedback for the given view (validated via session)
- Ordered by `created_at` ascending

### Analytics Extension (Backend + Frontend)

**Files:** `app.py`, `static/js/analytics.js`, `templates/admin/analytics.html`

#### API Changes

`GET /admin/api/analytics/<deck_id>` response gains:

```json
{
  "feedback": [
    {
      "id": 1,
      "slide_number": 3,
      "viewer_email": "sarah@acme.com",
      "comment": "This ROI breakdown is compelling",
      "created_at": "2026-03-28T14:30:00"
    }
  ],
  "feedback_count": 12
}
```

Query joins `slide_feedback` → `views` → `share_links` where `share_links.deck_id = ?`.

#### Frontend Changes

- Stat cards: add "Feedback Items" card showing `feedback_count`
- Tab navigation below stats: "Views" | "Feedback"
- Feedback tab content:
  - Filter dropdowns: slide number, viewer email (populated from data)
  - Table: Slide (pill badge), Viewer, Feedback text, Date
  - Client-side filtering (data set is small enough)
  - Empty state when no feedback exists

## Data Model & Storage

### New Table: `slide_feedback`

```sql
CREATE TABLE slide_feedback (
    id SERIAL PRIMARY KEY,
    view_id INTEGER NOT NULL,
    slide_number INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (view_id) REFERENCES views(id) ON DELETE CASCADE
);

CREATE INDEX idx_slide_feedback_view_id ON slide_feedback(view_id);
```

- `view_id` FK to `views` — gives us viewer email, share link, and deck via joins
- No separate `email` column needed — derived from `views.viewer_email`
- `comment` is TEXT (validated to ≤1000 chars at the API layer)
- `ON DELETE CASCADE` — if a view is deleted, its feedback goes too
- One index on `view_id` for the viewer-side query; analytics query joins through `views` → `share_links`

### Migration

New Alembic migration: `add_slide_feedback_table`

```python
def upgrade():
    op.execute("""
        CREATE TABLE slide_feedback (
            id SERIAL PRIMARY KEY,
            view_id INTEGER NOT NULL,
            slide_number INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (view_id) REFERENCES views(id) ON DELETE CASCADE
        );
        CREATE INDEX idx_slide_feedback_view_id ON slide_feedback(view_id);
    """)

def downgrade():
    op.execute("DROP TABLE IF EXISTS slide_feedback;")
```

Also add the CREATE TABLE to `schema.sql` for fresh installs.

## Integration Points

- **Existing heartbeat.js** — feedback.js reuses the same `postMessage` listener pattern to track current slide number. No changes needed to heartbeat.js itself.
- **Existing slide tracking injection** — no changes needed. The iframe already posts slide changes to the parent.
- **Session** — feedback API relies on the existing Flask session (`viewer_email_{token}`) set during email gate. No new auth mechanism.
- **Analytics API** — extended, not replaced. Existing fields unchanged. New `feedback` and `feedback_count` fields are additive.

## Operational Considerations

- **Migration**: Run `alembic upgrade head` on deploy. Non-destructive (new table only).
- **Rollback**: `alembic downgrade -1` drops the table. Feedback data would be lost, but no other tables are affected.
- **Logging**: Standard Flask request logging covers the new endpoints. No special instrumentation needed.
- **Storage**: Text comments are small. Even at 1000 chars × 1000 comments = ~1MB. No storage concerns.

## Risks & Tradeoffs

| Risk | Mitigation |
|------|-----------|
| Spam / abuse via feedback input | 1000-char limit, rate limiting can be added later if needed |
| Viewer ignores the feedback button | Low-friction design (one click to open). Acceptable — feedback is opt-in |
| No email column in `slide_feedback` | By design — email comes from the `views` join. If views are purged, feedback loses attribution. Acceptable for v1 |
| Client-side filtering in analytics | Fine for current scale. If feedback volume grows significantly, move filtering to the API with query params |
| No edit/delete for viewers | Intentional for v1 simplicity. Can add later if requested |
