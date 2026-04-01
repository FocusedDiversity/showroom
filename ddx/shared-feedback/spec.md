# Spec: Shared Feedback

## Summary

Extends the viewer feedback panel to display all feedback for the current slide from all viewers of the same deck. Adds a new API endpoint that returns deck-wide feedback scoped to the current viewer's session, and updates the frontend to render a combined comment list with visual distinction between own and others' comments.

## Context & Requirements

- **Stack**: Flask 3.0+, PostgreSQL (psycopg3, raw SQL), vanilla JS, Jinja2
- **Scale**: Low volume — dozens of viewers per deck.
- **Auth**: Viewer identity from email gate session (`viewer_email_{token}`). No login system.
- **No new dependencies**: No ORM, no frontend framework.
- **Privacy**: Display commenter email in an obfuscated form (e.g., `s***@acme.com` or first part of email before @).

## Architecture Overview

```
Feedback Panel (Browser)
    │
    │ GET /api/feedback/all?view_id=<int>
    ▼
Flask (app.py)
    │
    │ SQL: slide_feedback → views → share_links
    │       WHERE share_links.deck_id = (deck for this view)
    ▼
PostgreSQL
```

The existing `GET /api/feedback` endpoint returns only the current viewer's own feedback. A new `GET /api/feedback/all` endpoint returns all feedback for the deck, grouped by slide, with commenter emails.

## Component Details

### New API Endpoint

**File:** `app.py`

#### `GET /api/feedback/all?view_id=<int>`

```
Response: {
  "ok": true,
  "feedback": [
    {
      "id": int,
      "slide_number": int,
      "comment": string,
      "viewer_email": string,
      "is_own": boolean,
      "created_at": string (ISO 8601)
    }
  ],
  "viewer_email": string  // current viewer's email, for client-side matching
}
```

- Session validation: same as existing feedback endpoints — validates `viewer_email_{token}` session.
- Query joins `slide_feedback` → `views` → `share_links` where `share_links.deck_id` matches the deck for the given `view_id`.
- Returns ALL feedback for the deck (not just the current view), ordered by `created_at ASC`.
- Each item includes `is_own: true/false` based on whether `views.viewer_email` matches the session email.
- Viewer emails are obfuscated server-side: show first character + `***` + `@domain` (e.g., `s***@acme.com`).
- The current viewer's own email is NOT obfuscated (they see their own full email or "You").

### Frontend Changes

**File:** `static/js/feedback.js`

- Replace the call to `GET /api/feedback?view_id=` with `GET /api/feedback/all?view_id=` in `loadPriorFeedback()`.
- Update `feedbackCache` to store items with `viewer_email` and `is_own` fields.
- Update `renderPrior()`:
  - Own comments: same style as current (light background), labeled "You, {time ago}".
  - Others' comments: slightly different style (white background with subtle left border accent), labeled "{obfuscated email}, {time ago}".
- Update local cache after submit: new items get `is_own: true`.

### CSS Changes

**File:** `static/css/style.css`

- `.feedback-prior-item.is-other`: white background with a left accent border (arctic color) to distinguish from own comments.
- `.feedback-prior-author`: style for the author label (slightly bolder than timestamp).

## Integration Points

- Existing `POST /api/feedback` unchanged — submission still goes through the same endpoint.
- Existing `GET /api/feedback` unchanged — kept for backwards compatibility but no longer called by the frontend.
- Analytics API unchanged — it already shows all feedback.

## Risks & Tradeoffs

| Risk | Mitigation |
|------|-----------|
| Privacy — showing viewer emails to other viewers | Obfuscate emails server-side; only show partial email |
| Viewer sees unfamiliar names and is confused | Clear "You" label on own comments, subtle visual distinction |
| Performance — loading all deck feedback per slide | Fine at current scale; data is small |
