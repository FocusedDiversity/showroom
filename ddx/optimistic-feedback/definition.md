# Definition: Optimistic Feedback

## Who are we building for?

- **Deck recipients (viewers)** — they expect instant feedback when submitting a comment, not a visible network delay.

## What problem are we solving for them?

Currently, after clicking Send, the viewer waits for the API round-trip before seeing their comment appear. On slow connections this creates a noticeable lag that feels unresponsive.

## What's our proposed solution?

Use optimistic UI: immediately render the comment in the panel and show the confirmation the moment the user clicks Send. Fire the API call in the background. If the API call fails, remove the optimistic entry from the cache and the DOM, and show an inline error message.

**In scope:**
- Immediate rendering of submitted comment before API response
- Rollback (remove comment) on API failure
- Inline error message on failure

**Out of scope:**
- Retry logic
- Offline queue

## How will we measure success?

- Feedback submission feels instant regardless of network latency.
- Failed submissions are cleanly rolled back with a visible error.
