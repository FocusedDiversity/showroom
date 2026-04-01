# Capability Plan: Shared Feedback

## Step 1: Backend — Add `/api/feedback/all` endpoint [DONE]

**Build:** Add a new `GET /api/feedback/all?view_id=<int>` endpoint to `app.py`. This endpoint:
- Validates the viewer session (same pattern as existing feedback endpoints).
- Looks up the deck_id for the given view_id via `views` → `share_links`.
- Queries ALL feedback for that deck: `slide_feedback` → `views` → `share_links` WHERE `share_links.deck_id = ?`.
- Returns each item with: `id`, `slide_number`, `comment`, `viewer_email` (obfuscated for others), `is_own` (boolean), `created_at`.
- Obfuscation: for other viewers' emails, show `first_char***@domain`. For own email, return "You".
- Order by `created_at ASC`.

**Depends on:** Existing `slide_feedback` table and session auth.

**Verify:** Use curl to call the endpoint. Confirm it returns feedback from multiple viewers with proper obfuscation and `is_own` flags.

---

## Step 2: Frontend — Update feedback.js to show all feedback [DONE]

**Build:** Update `static/js/feedback.js`:
- Change `loadPriorFeedback()` to call `GET /api/feedback/all?view_id=` instead of `GET /api/feedback?view_id=`.
- Update `feedbackCache` to store items with `viewer_email` and `is_own` fields.
- Update `renderPrior()`:
  - Own comments: existing gray background style, labeled "You · {time ago}".
  - Others' comments: add CSS class `is-other`, labeled "{obfuscated email} · {time ago}".
  - Comments are interleaved chronologically.
- When adding a new comment to the local cache after submit, set `is_own: true` and `viewer_email: 'You'`.
- Update placeholder logic: show "Add another comment..." if the viewer has any own comments on this slide, otherwise "Share your thoughts on this slide...".

**Depends on:** Step 1.

**Verify:** Open a shared deck, submit feedback, see it labeled "You". Have a second viewer submit feedback on the same slide. Reopen the panel and see both comments with correct styling.

---

## Step 3: CSS — Style distinction for own vs. others' comments [DONE]

**Build:** Add CSS to `static/css/style.css`:
- `.feedback-prior-item.is-other`: white background, left border accent in arctic color (`var(--arctic)`), to distinguish from own comments.
- `.feedback-prior-author`: bold text style for the author name/email portion.
- Ensure both styles work within the right-side panel layout.

**Depends on:** Step 2.

**Verify:** Visually confirm own comments have gray background and others' have white background with arctic left border.

---

## Step 4: Tests — Unit and integration tests for shared feedback [DONE]

**Build:** Add tests:
- Unit tests in `tests/test_feedback_unit.py`: test the new `/api/feedback/all` endpoint — missing view_id, nonexistent view, no session, correct session returns all feedback.
- Integration tests in `tests/test_feedback_integration.py`: create two viewers with feedback on the same deck, call `/api/feedback/all`, verify both viewers' feedback appears with correct `is_own` flags, verify email obfuscation.

**Depends on:** Steps 1-3.

**Verify:** Run `pytest tests/test_feedback_unit.py tests/test_feedback_integration.py -v` — all tests pass.

---
