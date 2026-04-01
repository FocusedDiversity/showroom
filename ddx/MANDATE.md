# MANDATE

## About DDX

This project uses **DDX (Document-Driven Development)**. DDX structures product decisions into a chain of documents — definition, design, spec, plan — that keep AI agents and humans aligned from idea to shipped code.

### Document Chain

```
definition  -->  design  -->  spec  -->  plan  -->  build
 (what/why)     (screens)    (how)     (steps)     (code)
```

Each document builds on the one before it. Changes cascade — updating an upstream document flags inconsistencies in everything downstream.

### How AI Agents Should Use DDX

1. **Read this mandate first.** Before any work, read `ddx/MANDATE.md` to understand the project's identity, constraints, and rules.
2. **Read relevant DDX documents before writing code.** Check `ddx/product/` for product-level context. Check `ddx/{capability}/` for the specific area you're working in.
3. **Follow the plan.** If a plan exists for the scope you're working in, follow its steps. Don't skip ahead or improvise architecture that contradicts the spec.
4. **Don't contradict upstream documents.** The definition defines *what* and *why*. The spec defines *how*. Your code should match both. If you think something should change, flag it — don't silently deviate.
5. **Use DDX skills to make changes.** Run `/ddx.update` to change documents — it handles consistency checks and cascading. Don't hand-edit DDX documents without running the update skill afterward.

### DDX Skills Reference

| Skill | Purpose |
|-------|---------|
| `/ddx.mandate` | Create or update this mandate |
| `/ddx.derive` | Analyze existing codebase and generate product docs |
| `/ddx.define` | Define a product or capability through interview |
| `/ddx.design` | Generate wireframes and interaction design |
| `/ddx.spec` | Generate technical architecture and spec |
| `/ddx.plan` | Generate ordered build steps |
| `/ddx.build` | Execute the plan — write code step by step |
| `/ddx.update` | Update any document and cascade changes |

---

## Project Identity

Showroom is a presentation deck sharing and analytics platform built by Synaptiq. It allows team members to upload HTML slide decks, generate tracked share links for specific recipients, and monitor engagement — who viewed, how long, how far they got, and whether they forwarded the link. It replaces the black hole of emailing attachments with measurable, email-gated deck delivery.

## Constraints

- **Backend**: Python / Flask, served via Gunicorn
- **Database**: PostgreSQL (via psycopg3, dict_row factory)
- **Storage**: Pluggable — local filesystem (default) or Google Cloud Storage
- **Containerization**: Docker + docker-compose (Postgres in a sidecar)
- **Migrations**: Alembic (SQLAlchemy for migration metadata only — app queries use raw SQL). After creating a new migration, run `venv/bin/alembic upgrade head` to apply it. If `init_db` (via `schema.sql`) has already created the table, use `venv/bin/alembic stamp <revision>` to sync Alembic's version tracking without re-running the DDL.
- **No auth on admin**: Admin routes are currently unprotected (no login)
- **Upload limit**: 50 MB max
- **Deck format**: HTML files or ZIP archives containing an index.html
- **Production host**: showcase.synaptiq.ai (root redirects to a specific viewer link)

## Always Do

- Use parameterized queries (`%s` placeholders) for all SQL — never string interpolation
- Use the `storage` abstraction layer for all file operations — never access the filesystem directly for deck assets
- Return `dict_row` results from all database queries
- Validate ZIP contents for path traversal (`..` and leading `/`) before extraction
- Use `slugify` for generating URL-safe deck slugs
- Keep viewer-facing pages branded with Synaptiq identity

## Never Do

- Never bypass the email gate for viewer access
- Never expose admin routes under the `/v/` viewer namespace
- Never store uploaded files outside the storage abstraction
- Never use ORM models for application queries (raw SQL only; SQLAlchemy is migration-only)
- Never commit secrets or the `showroom.db` file

## Conventions

- **File structure**: `app.py` (routes), `db.py` (connection), `config.py` (env vars), `storage.py` (file abstraction)
- **Templates**: Jinja2 in `templates/`, organized by `admin/` and `viewer/` subdirectories, extending `base.html`
- **Static assets**: `static/style.css`, `static/analytics.js`, `static/heartbeat.js`, `static/admin.js`
- **URL patterns**: Admin at `/admin/*`, viewer at `/v/<token>/*`, API at `/api/*`
- **SQL style**: Uppercase keywords, `%s` parameter placeholders, inline queries in route functions
- **Naming**: snake_case for Python, kebab-case for URL slugs
