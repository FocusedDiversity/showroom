# Capability Plan: Optimistic Feedback

## Step 1: Frontend — Optimistic submit in feedback.js [DONE]

**Build:** Rewrite `submitFeedback()` in `static/js/feedback.js` to:
- Generate a temp ID, add optimistic entry to cache with `_pending: true`
- Immediately render, clear input, show confirmation
- Fire API in background
- On success: update temp ID to real ID, clear `_pending`
- On failure: remove optimistic entry from cache, re-render, show error via `showError()`

Also update `renderPrior()` to add `is-pending` CSS class to items with `_pending: true`.

Add `showError(message)` function that creates/shows an error div below the input row, auto-dismissing after 4 seconds.

**Depends on:** Existing feedback.js.

**Verify:** Submit feedback — it appears instantly. Simulate a failure (e.g., invalid view_id) — comment is removed and error shown.

---

## Step 2: CSS — Pending and error styles [DONE] [DONE]

**Build:** Add to `static/css/style.css`:
- `.feedback-prior-item.is-pending` — `opacity: 0.7` to indicate in-flight
- `.feedback-error` — error message styling: red text, small font, padding below input row

**Depends on:** Step 1.

**Verify:** Visually confirm pending items have reduced opacity and error messages are styled correctly.

---

## Step 3: Tests — Verify optimistic behavior [DONE]

**Build:** Add/update tests to verify:
- Comment appears in DOM before API response completes
- On API failure, comment is removed from DOM
- Error message appears on failure

**Depends on:** Steps 1-2.

**Verify:** Run all tests — pass.

---
