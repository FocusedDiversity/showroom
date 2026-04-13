# Definition: Slide Feedback

## Who are we building for?

- **Synaptiq sales and marketing team** — they share decks with prospects and clients and need to understand how specific slides land, not just whether the deck was opened.
- **Deck recipients (viewers)** — external viewers who want an easy, low-friction way to react to what they're seeing while it's fresh.

## What problem are we solving for them?

Showroom tells the team *what* viewers looked at and for how long, but not *what they thought*. There's no way to capture qualitative reactions tied to specific slides — so the team can't tell which slides resonate, confuse, or need rework without scheduling a follow-up conversation.

## How do we know it's a real problem?

- Engagement analytics show *where* viewers drop off but not *why*.
- Sales follow-ups often start with "So what did you think of the deck?" — a question the tool should already answer.
- No structured feedback loop exists between deck viewing and deck improvement.

## What is the impact of the problem?

- Decks get iterated based on gut feel rather than direct viewer input.
- Sales team lacks slide-level conversation starters for follow-ups.
- Missed opportunity to capture prospect sentiment while engagement is highest (during viewing).

## What's our proposed solution?

Add a lightweight feedback input to the deck viewer that lets the recipient submit a short free-text comment on the slide they're currently viewing. Each comment is tied to the viewer's email address and slide number. Feedback surfaces in the existing analytics dashboard on a per-deck basis.

**In scope:**
- Text input field in the viewer UI (visible or toggled) for the current slide
- Comments stored per slide number + viewer email
- Feedback visible in analytics dashboard (new tab or section)

**Out of scope (v1):**
- Rating scales, emoji reactions, or structured surveys
- Real-time notifications to the Synaptiq team
- Aggregation or sentiment analysis

**Timeline:** No hard deadline — normal priority.

## How will we measure success?

- **Feedback submission rate** — percentage of viewed decks that receive at least one comment.
- **Slide coverage** — average number of distinct slides that receive feedback per deck.
- **Sales team usage** — whether feedback data is referenced in follow-up conversations.
- **Deck iteration quality** — reduction in slides with high drop-off rates after feedback-informed revisions.
