# Showroom

A simplified DocSend alternative for publishing one-page HTML decks, sharing them securely with prospects, and tracking engagement.

![Showroom](static/img/showroom-logo-final.png)

## Features

- **Upload HTML decks** - Single HTML files or ZIP bundles with assets (images, CSS, JS)
- **Email-gated sharing** - Generate unique share links per recipient; viewers enter their email to access
- **Engagement tracking** - Track who viewed, when, how long (via heartbeat), and from what device
- **Forwarding detection** - Automatically flags when a deck is viewed by someone other than the intended recipient
- **Per-deck analytics** - Dashboard with summary stats, daily view chart, and detailed viewer table
- **Enable/disable controls** - Toggle decks and individual share links on or off

## Tech Stack

- **Backend:** Python / Flask / SQLite
- **Frontend:** Jinja2 templates, vanilla JavaScript
- **Tracking:** Heartbeat pings every 5s with Page Visibility API pause detection and `sendBeacon` on unload

## Quick Start

```bash
# Clone
git clone https://github.com/FocusedDiversity/showroom.git
cd showroom

# Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python app.py
```

Open **http://localhost:5111** in your browser.

## Usage

1. **Upload a deck** - Click "+ Upload Deck" from the dashboard. Provide a title and upload an `.html` file or a `.zip` containing `index.html` and supporting assets.
2. **Create a share link** - Open a deck and enter a prospect's email to generate a unique URL.
3. **Share the link** - Copy the link and send it to your prospect. They'll enter their email to view.
4. **Track engagement** - View analytics per deck to see who viewed, for how long, and whether they forwarded it.

## Project Structure

```
showroom/
├── app.py              # Flask routes (admin, viewer, API)
├── db.py               # SQLite helpers
├── config.py           # Configuration
├── schema.sql          # Database schema
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/style.css   # Synaptiq-branded styles
│   ├── img/            # Logos and favicon
│   └── js/
│       ├── heartbeat.js    # Viewer duration tracking
│       ├── analytics.js    # Analytics dashboard rendering
│       └── admin.js        # Admin UI interactions
└── templates/
    ├── base.html
    ├── admin/          # Dashboard, deck detail, analytics
    └── viewer/         # Email gate, deck view, expired link
```

## Configuration

Environment variables (optional):

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `dev-secret-change-in-production` | Flask session secret key |

The SQLite database (`showroom.db`) and uploaded deck files (`uploads/`) are created automatically on first run and excluded from version control via `.gitignore`.

## License

MIT
