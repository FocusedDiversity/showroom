# Definition: Feedback Toggle

## Who are we building for?

- **Synaptiq sales and marketing team (admins)** — they need control over which share links allow feedback and which are view-only. Some recipients (e.g., board members, casual forwards) shouldn't see the feedback UI.

## What problem are we solving for them?

Every share link currently exposes the feedback panel. Admins have no way to share a "clean" view-only link alongside a feedback-enabled one. This means they either accept feedback from everyone or from no one.

## How do we know it's a real problem?

- Some decks are shared with audiences who shouldn't be prompted for feedback (e.g., executive briefings, public-facing links).
- Admins want to control the feedback experience per-recipient without creating separate deck copies.

## What's our proposed solution?

Add a `feedback_enabled` boolean to each share link (defaulting to TRUE for backward compatibility). When creating a share link, the admin chooses whether feedback is enabled. The viewer template conditionally renders the feedback button and panel based on this flag. The feedback API endpoints also enforce this flag server-side.

**In scope:**
- New `feedback_enabled` column on `share_links` table
- Checkbox on the share link creation form
- Feedback badge visible in the share links table
- Conditional rendering of feedback UI in the viewer
- Server-side enforcement on feedback API endpoints

**Out of scope (v1):**
- Toggling feedback on/off for existing links (admin can disable and recreate)
- Per-slide feedback control

**Timeline:** No hard deadline — normal priority.

## How will we measure success?

- Admins create both feedback-enabled and view-only links for the same deck.
- Feedback API rejects submissions from view-only links.
