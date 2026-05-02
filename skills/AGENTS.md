# skills/ — Codex Instructions

Packaged `.skill` files for Apulu Universe workflows. See root `AGENTS.md` first.

## What lives here

- `<name>.skill` — packaged skill bundles
- Source/working copies of skills also live in `~/.claude/skills/` and in `raw/skill-patches/` for in-progress edits

## Operating rules

- **Focused, not mega.** A skill should do one thing well — clear trigger condition, narrow scope, one source of truth. If a skill description starts listing 5+ unrelated capabilities, split it.
- **Triggers are contracts.** The skill's frontmatter `description` determines when it fires. Be specific about the trigger; vague descriptions cause silent misfires.
- **No hidden cross-skill coupling.** A skill should not require another skill to function. If two skills depend on shared primitives, factor those into a shared utility, not a third skill.
- **Don't bake project-specific behavior into a general skill.** A "social-content" skill that hardcodes Vawn's voice should be split into `social-content` (general) + a Vawn-specific overlay or config.
- **Patches first, then publish.** In-progress skill changes go in `raw/skill-patches/` until validated; only then update the packaged `.skill`.

## Adding a new skill

1. Use the `skill-creator` skill (`~/.claude/skills/skill-creator/`) to scaffold YAML frontmatter, structure, and the `SKILL.md` body.
2. Single-purpose `description` — one sentence, name the trigger.
3. Validate locally before packaging.
4. Drop the `.skill` here; if it supersedes an older one, note it in the commit.

## Don't touch without explicit ask

- Existing `.skill` packages — they're consumed by other workflows; renames break references.
- Skills outside `apulu-universe`'s scope (creative direction, music industry domain) belong elsewhere.
