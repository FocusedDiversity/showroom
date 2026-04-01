# Product Design: Showroom

## Screens

### Admin Screens

#### 1. Dashboard (`/admin`)
- **Layout**: Grid of deck cards
- **Each card shows**: Title, description (truncated), link count, view count, creation date
- **Actions**: "Upload Deck" button opens modal
- **Upload modal**: Title (required), description (optional), file input (HTML or ZIP), submit button
- **Empty state**: Message prompting first upload

#### 2. Deck Detail (`/admin/deck/<id>`)
- **Header**: Deck title, status badge (active/inactive), breadcrumb back to dashboard
- **Actions**: Enable/Disable toggle, Delete button, View Analytics link
- **Share section**: Email input + "Create Share Link" button
- **Share links table**: Recipient email, shareable URL with copy button, view count, status badge, created date, enable/disable action

#### 3. Analytics (`/admin/deck/<id>/analytics`)
- **Stat cards row**: Total Views, Unique Viewers, Avg Time Spent, Forwarded Views
- **Chart**: Bar chart of daily view counts
- **Detail table**: Viewer email, shared with (original recipient), forwarded badge, duration, last slide viewed, timestamp, device type

### Viewer Screens

#### 4. Email Gate (`/v/<token>`)
- **Centered card**: Synaptiq logo, deck title, subtitle text, email input, submit button
- **Error state**: Inline error message above form

#### 5. Deck Viewer (`/v/<token>/view`)
- **Top bar**: Deck title (left), slide indicator (center), Synaptiq logo (right)
- **Content area**: Full-width iframe loading the raw deck HTML
- **Background**: Heartbeat JS pings server every 5 seconds with duration + slide position

#### 6. Link Expired (`/v/<token>` when invalid)
- **Centered message**: "Link Unavailable" heading, explanation text
- **Footer**: Synaptiq branding

## Interaction Patterns

- **Flash messages**: Success/error toasts auto-dismiss after 5 seconds
- **Copy to clipboard**: Share link URLs have a click-to-copy button
- **Slide tracking**: Injected JS in iframe detects slide changes via multiple heuristics (active slide class, slide indicator text, global variable) and posts messages to parent window
- **Forwarding detection**: Automatic — compares viewer-entered email against the share link's intended recipient
- **Tab visibility**: Heartbeat pauses when tab is hidden, resumes on focus

## Branding

- Synaptiq color palette: soil (dark brown), apricot, arctic (blue), mint, coconut (white)
- Synaptiq logo in viewer screens
- Clean, card-based UI with responsive breakpoints
