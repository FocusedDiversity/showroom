---
name: ddx.derive
description: Derives product documentation from an existing codebase. Analyzes source code, README, and manifest files to generate definition, design, and spec documents.
disable-model-invocation: true
---

You are deriving product docs from an existing codebase.

## Preconditions

1. Check that `.ddx-tooling/config.yaml` exists. If not, tell the user to run `/ddx.init` first and stop.
2. Check if `ddx/product/definition.md` already exists. If it does, tell the user: "Product docs already exist. Nothing to derive." and stop.
3. Check if the project has source code (look for `src/`, `app/`, `lib/`, `package.json`, `Cargo.toml`, `go.mod`, `requirements.txt`, etc.). If no source code found, tell the user: "No source code detected. Run `/ddx.define` to define the product from scratch." and stop.

## Derive

IMPORTANT: Do NOT use Bash to create directories — just write files directly with the Write tool and directories are created automatically.

1. Read `.ddx-tooling/config.yaml`. Note the `definition`, `design`, and `spec` entries. Replace `{scope}` with `product` in all output paths.
2. Read each document's template file.
3. Scan the project:
   - Read README, manifest files (package.json, Cargo.toml, etc.)
   - Read main entry points and directory structure
   - Skim key source files to understand the architecture
4. Generate `ddx/product/definition.md` using the definition template — fill sections from what you can infer. Be factual, only include what the code evidence supports.
5. Determine if the product has a user interface based on what you found in the codebase:
   - **Has UI** (web app, mobile app, dashboard, portal, frontend code, templates, views, etc.): generate `ddx/product/design.md` using the design template — describe the screens/interfaces that exist as ASCII wireframes.
   - **No UI** (API, service, library, CLI, data pipeline, worker, daemon, etc.): skip design entirely. Do NOT generate a design document.
6. Generate `ddx/product/spec.md` using the spec template — describe the architecture as-built with an ASCII diagram.
7. Tell the user: "I've derived product docs from your codebase. Please review the files in `ddx/product/` and edit them. When you're satisfied, the next step is **`/ddx.define`** to start defining your first capability. Want me to run it?"

If you cannot confidently fill the templates (codebase is too ambiguous), tell the user: "I couldn't confidently derive product docs from your codebase. Run `/ddx.define` to define the product from scratch."
