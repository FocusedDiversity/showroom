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

*(What is this project? One paragraph: what it does, who it's for, and why it exists. No implementation details.)*

## Constraints

*(Non-negotiable rules. Technology choices, architectural boundaries, compliance requirements, performance targets, dependencies that must or must not be used. Be specific.)*

## Always Do

*(Rules the AI must always follow when working in this project. Examples: "always write tests for new functions", "always use the project's error handling pattern", "always check for existing utilities before writing new ones".)*

## Never Do

*(Things the AI must never do. Examples: "never use any", "never add dependencies without asking", "never modify migration files directly", "never commit .env files".)*

## Conventions

*(Coding style, naming patterns, file organization, commit message format, PR conventions — anything that keeps the codebase consistent.)*
