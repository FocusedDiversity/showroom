# Spec: Feedback Toggle

## Summary

Adds a per-share-link `feedback_enabled` boolean that controls whether the feedback panel is shown to viewers and whether the feedback API accepts submissions for that link. Admins set this when creating a share link via a checkbox.

## Context & Requirements

- **Stack**: Flask 3.0+, PostgreSQL (psycopg3, raw SQL), Alembic, vanilla JS, Jinja2
- **Backward compatibility**: Existing links default to `feedback_enabled = TRUE`.
- **No new dependencies**.

## Architecture Overview

```
Admin creates share link
    │
    │  checkbox: "Enable feedback" (checked by default)
    ▼
share_links.feedback_enabled = TRUE/FALSE
    │
    ├─► viewer_deck route reads flag → passes to template
    │       → template conditionally renders feedback button/panel
    │       → feedback.js conditionally initializes
    │
    └─► POST /api/feedback checks flag → rejects if disabled
        GET /api/feedback/all checks flag → rejects if disabled
```

## Data Model Changes

### `share_links` table — add column

```sql
ALTER TABLE share_links ADD COLUMN feedback_enabled BOOLEAN DEFAULT TRUE;
```

- Default TRUE — existing links continue to work with feedback.
- New Alembic migration.
- Update `schema.sql` for fresh installs.

## Component Details

### Admin — Share Link Creation

**Files:** `app.py` (`admin_create_share`), `templates/admin/deck_detail.html`

- Add a checkbox to the share creation form: "Enable feedback" (checked by default).
- `admin_create_share` reads `request.form.get('feedback_enabled')` — checkbox present = TRUE, absent = FALSE.
- INSERT includes the `feedback_enabled` value.

### Admin — Share Links Table

**File:** `templates/admin/deck_detail.html`

- Add a "Feedback" column to the share links table showing a badge: "On" (green) or "Off" (gray).

### Viewer — Conditional Feedback UI

**Files:** `app.py` (`viewer_deck`), `templates/viewer/deck_view.html`

- `viewer_deck` route already queries the share link. Pass `feedback_enabled` to the template.
- Template: wrap the feedback button and panel markup in `{% if feedback_enabled %}`. Also conditionally include `feedback.js` and the `initFeedback()` call.

### Feedback API — Server-side Enforcement

**File:** `app.py`

- `POST /api/feedback`: after looking up the view → share_link, check `feedback_enabled`. Return 403 if disabled.
- `GET /api/feedback/all`: same check — return 403 if the link's `feedback_enabled` is FALSE.

## Risks & Tradeoffs

| Risk | Mitigation |
|------|-----------|
| Existing links lose feedback | Default TRUE preserves backward compatibility |
| Admin can't toggle existing links | Can disable link and create a new one. Toggle can be added later. |
