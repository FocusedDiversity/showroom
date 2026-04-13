# Product Definition: Showroom

## What It Is

Showroom is a presentation deck sharing and analytics platform. It lets Synaptiq team members upload HTML slide decks, generate unique share links for specific recipients, and track exactly who views each deck, for how long, how far they get, and whether they forward it to others.

## Who It's For

- **Synaptiq sales and marketing team** — the primary users who upload decks and share them with prospects, partners, and clients.
- **Deck recipients** — external viewers who receive a share link and view the presentation through a lightweight, branded viewer.

## Why It Exists

Sending a PDF or attaching a slide deck to an email is a black hole — you have no idea if anyone opened it, how far they got, or if they forwarded it. Showroom closes that gap by wrapping every shared deck in a tracked, email-gated viewer, giving the team actionable engagement data on every share.

## Core Capabilities

### 1. Deck Management
Upload HTML or ZIP slide decks through an admin dashboard. Each deck gets a unique slug, can be activated/deactivated, and has its assets stored (locally or in GCS).

### 2. Share Link Generation
Create per-recipient share links tied to an email address. Each link gets a unique token. Links can be individually enabled/disabled.

### 3. Email-Gated Viewing
Before viewing a deck, the recipient must enter their email. This captures viewer identity and detects forwarding (when the viewer's email differs from the original recipient's email).

### 4. View Tracking & Analytics
Every view records: viewer email, timestamp, duration, user agent, IP address, referrer, forwarding status, current slide, and total slides. A heartbeat pings every 5 seconds to track duration and slide progress in real time.

### 5. Analytics Dashboard
Per-deck analytics showing total views, unique viewers, average time spent, forwarded view count, daily view trends (bar chart), and a detailed table of every individual view session.

## Key Flows

1. **Upload** — Admin uploads HTML/ZIP -> deck created with slug -> assets stored -> appears on dashboard
2. **Share** — Admin enters recipient email -> unique token link generated -> link displayed for copying
3. **View** — Recipient opens link -> email gate -> enters email -> deck renders in iframe -> heartbeat tracks engagement
4. **Analyze** — Admin opens analytics for a deck -> summary stats + chart + detailed view table
