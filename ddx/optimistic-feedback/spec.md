# Spec: Optimistic Feedback

## Summary

Converts the feedback submission flow from wait-for-response to optimistic-update. The comment appears instantly in the panel, and the API call runs in the background. On failure, the comment is removed and an error is shown.

## Current Flow

1. User clicks Send → button disabled
2. `POST /api/feedback` fires
3. Wait for response
4. On success: add to cache, clear input, show confirmation, re-render after 3s
5. On failure: re-enable button (no user feedback)

## New Flow

1. User clicks Send → clear input immediately
2. Generate a temporary client-side ID (`_temp_<random>`)
3. Add optimistic entry to `feedbackCache[currentSlide]` with `_pending: true`
4. Call `renderPrior()` — comment appears instantly
5. Show confirmation immediately
6. Fire `POST /api/feedback` in background
7. **On success**: replace temp ID with real `feedback_id`, remove `_pending` flag
8. **On failure**: remove the optimistic entry from cache, re-render, show inline error

## Component Details

### `feedback.js` — `submitFeedback()`

- Generate `tempId = '_temp_' + Math.random().toString(36).slice(2)`
- Create optimistic cache entry: `{ id: tempId, comment, viewer_email: 'You', is_own: true, created_at: new Date().toISOString(), _pending: true }`
- Push to cache, clear input, render, show confirmation
- Fire fetch — on success: find entry by `tempId`, update `id` to `data.feedback_id`, remove `_pending`
- On failure: filter out entry with `tempId` from cache, re-render, show error

### `feedback.js` — `renderPrior()`

- Pending items get an additional CSS class `is-pending` for subtle visual distinction (slightly lower opacity)

### `feedback.js` — error display

- Add a `showError(message)` function that shows a brief inline error below the input area
- Auto-dismiss after 4 seconds

### CSS — `style.css`

- `.feedback-prior-item.is-pending` — slightly reduced opacity (0.7) to indicate in-flight state
- `.feedback-error` — error message styling (red text, small font, below input row)

## No backend changes required.
