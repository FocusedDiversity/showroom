# Definition: Shared Feedback

## Who are we building for?

- **Deck recipients (viewers)** — external viewers who want to see what others thought about specific slides, creating a richer, more conversational feedback experience.
- **Synaptiq sales and marketing team** — they benefit when viewers engage more deeply with decks by reading and reacting to others' comments.

## What problem are we solving for them?

Currently, each viewer's feedback is siloed — they can only see their own prior comments in the feedback panel. There's no way to see what other viewers said about the same slide, even though that social context would encourage more engagement and richer feedback.

## How do we know it's a real problem?

- Viewers have no visibility into whether others found a slide compelling or confusing.
- The feedback panel feels like a one-way form rather than a conversation.
- Showing others' comments creates social proof and prompts more thoughtful responses.

## What is the impact of the problem?

- Lower feedback volume because there's no social signal encouraging participation.
- Missed opportunity to create a lightweight discussion thread around individual slides.
- Sales team gets fewer data points because viewers don't see (and react to) others' perspectives.

## What's our proposed solution?

Extend the viewer feedback panel to show all feedback for the current slide from all viewers of the same deck — not just the current viewer's own comments. Each comment shows the commenter's name/email and timestamp. The current viewer's own comments are visually distinguished from others'.

**In scope:**
- New API endpoint to return all feedback for a deck's slides (across all viewers)
- Updated feedback panel to show all comments, with visual distinction for own vs. others'
- Obfuscated email display (first name or partial email) for privacy

**Out of scope (v1):**
- Reply/threading on individual comments
- Upvoting or reacting to others' comments
- Real-time updates (new comments from others appear on next panel open/slide change)

**Timeline:** No hard deadline — normal priority.

## How will we measure success?

- **Feedback volume increase** — more comments per deck after viewers can see others' feedback.
- **Return engagement** — viewers who see others' comments are more likely to submit their own.
