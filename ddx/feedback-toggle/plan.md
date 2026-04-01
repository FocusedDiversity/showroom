# Capability Plan: Feedback Toggle

## Step 1: Database — Add `feedback_enabled` column [DONE]

**Build:** Create Alembic migration to add `feedback_enabled BOOLEAN DEFAULT TRUE` to `share_links`. Update `schema.sql` with the new column for fresh installs.

**Depends on:** Nothing.

**Verify:** Run `alembic upgrade head`, confirm column exists with `SELECT feedback_enabled FROM share_links LIMIT 1`.

---

## Step 2: Admin — Share link creation with feedback checkbox [DONE]

**Build:**
- Update `templates/admin/deck_detail.html`: add a labeled checkbox "Enable feedback" (checked by default) to the share link creation form, next to the email input and Create button.
- Update `app.py` `admin_create_share`: read `feedback_enabled` from the form (checkbox: present = TRUE, absent = FALSE). Pass it to the INSERT query.
- Add a "Feedback" column to the share links table showing a badge: "On" (green/active) or "Off" (gray/inactive).

**Depends on:** Step 1.

**Verify:** Create a share link with feedback enabled — see "On" badge. Create one without — see "Off" badge.

---

## Step 3: Viewer — Conditionally render feedback UI [DONE]

**Build:**
- Update `app.py` `viewer_deck`: pass `feedback_enabled` (from the share link row) to the template context.
- Update `templates/viewer/deck_view.html`: wrap the feedback toggle button, feedback panel div, `feedback.js` script tag, and `initFeedback()` call inside `{% if feedback_enabled %}`.

**Depends on:** Step 1.

**Verify:** Open a feedback-enabled link — feedback button visible. Open a feedback-disabled link — no feedback button, no panel.

---

## Step 4: Backend — Enforce feedback_enabled on API endpoints [DONE]

**Build:** Update `app.py`:
- `POST /api/feedback`: after looking up the share link for the view, check `feedback_enabled`. If FALSE, return `{"ok": false, "error": "Feedback is not enabled for this link"}` with status 403.
- `GET /api/feedback/all`: same check — return 403 if `feedback_enabled` is FALSE.

**Depends on:** Step 1.

**Verify:** Attempt to POST feedback via curl for a disabled link — get 403. Attempt GET /api/feedback/all — get 403.

---

## Step 5: Tests — Unit and integration tests [DONE]

**Build:** Add tests:
- Migration test: confirm column exists and defaults to TRUE.
- Admin: test creating links with and without feedback enabled.
- Viewer: test that `feedback_enabled` is passed to the template.
- API: test that POST /api/feedback returns 403 for feedback-disabled links. Test GET /api/feedback/all returns 403 for disabled links.

**Depends on:** Steps 1-4.

**Verify:** Run `pytest tests/ -v` — all tests pass.

---
