# Pipeline Instructions

This folder contains the configurable Apulu content pipeline.

Respect the pipeline stages:

- `discovery/` = platform scraping and trend intake.
- `ideation/` = competitive analysis and content ideas.
- `scripting/` = hooks, outlines, titles.
- `cascade/` = platform-specific post adaptation.
- `prompt-research/` = AI video prompt research.
- `brain/` = health monitor and daily briefing logic.
- `bridge.py` = exports pipeline intelligence into Vawn posting context.
- `config/` = project config and content rules.

## Rules

- Do not mix stages unless the current architecture already does.
- Do not hardcode one project into shared pipeline helpers.
- Preserve dry-run flags and other CLI options.
- Preserve output formats consumed by downstream scripts.
- Before editing, identify which downstream file or scheduled process consumes the output.
- Protect state files and generated outputs from accidental deletion.
- When changing platform copy rules, check `content_rules.json` and related config first.

## Pre-change Checklist

For any non-trivial pipeline edits:

1. Identify the entry point script and how it's invoked (CLI or schedule).
2. Determine input files and state files touched (e.g., queue, DLQ, status files).
3. Determine where outputs go and which downstream processes consume them.
4. Check for retry logic, circuit breakers, deduplication, and health checks, and ensure these behaviours remain intact.
5. Run the pipeline or stage in dry-run mode to verify changes before full execution.

## Verification

Prefer:

- Run with `--dry-run` if supported.
- Run the specific stage command, not the whole pipeline, unless needed.
- Check generated output shape before claiming success.
