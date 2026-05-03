# Paperclip Script Instructions

This folder manages Paperclip setup, agents, routines, IDs, and operational wiring.

## High-Risk Area

Changes here can affect autonomous agent behaviour, scheduled routines, dispatch routing, and production operations.

## Rules

- Do not change agent names, routine names, company IDs, agent IDs, or routine IDs unless explicitly asked.
- Do not regenerate setup files unless the task specifically requires it.
- Prefer read/check commands before write commands.
- Preserve the existing organisation structure unless the task is an intentional org migration.
- Before changing a script, identify:
  - what it creates or modifies
  - whether it touches the Paperclip DB
  - whether it writes IDs
  - whether it affects scheduled routines
  - what the rollback path would be

## Verification

Prefer check-only or dry-run commands first. After edits, run the smallest safe validation command available.
