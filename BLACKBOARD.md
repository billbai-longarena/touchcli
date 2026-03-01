# BLACKBOARD.md — touchcli

> Refined on 2026-03-02 during scout exploration of `S-001`.

## Project Summary

- **Type**: Termite Protocol field-infrastructure repository with TouchCLI product design documentation.
- **Primary Stack**: Bash scripts + SQLite state store (`.termite.db`).
- **Build Tool**: none detected (no `package.json`, `go.mod`, `pyproject.toml`, `Cargo.toml`, or `Makefile`).
- **Runtime Dependencies**: `bash`, `sqlite3` (required), `shellcheck` (optional).

## Project Structure (Verified)

- `scripts/`: protocol lifecycle scripts (`field-arrive`, `field-cycle`, `field-claim`, `field-deposit`, DB helpers, audit helpers).
- `scripts/hooks/`: Git hook templates and installer.
- `signals/`: DB-exported snapshots (`active/`, `observations/`, `rules/`, `claims/`, `archive/`).
- Root protocol/docs: `AGENTS.md`, `CLAUDE.md`, `TERMITE_PROTOCOL.md`, `QUICKSTART.md`, `UPGRADE_NOTES.md`, `DESIGN.md`.

## Colony Health

| Dimension | Status | Trend | Last Verified |
|-----------|--------|-------|---------------|
| Build     | pass (script syntax and metabolism cycle) | stable | 2026-03-02 |
| Tests     | not configured (no test harness detected) | stable | 2026-03-02 |
| Docs      | present (protocol + design docs) | improving | 2026-03-02 |

## Signals

| ID | Type | Title | Weight | TTL | Status | Owner |
|----|------|-------|--------|-----|--------|-------|
| S-001 | EXPLORE | Map unknown project — verify build, test, document structure | 32 | 14d | open | unassigned |

## Hotspot Areas

- `scripts/`: automation correctness and portability.
- `.termite.db` + `signals/active/`: single source of truth and exported snapshots.

## Notes for AI

- Use `./scripts/field-arrive.sh` as entrypoint for each session.
- Keep DB-first flow; treat `signals/active/*.yaml` as snapshots.
- If adding CI, start with shell validation (`bash -n`, then `shellcheck` where available).

## Known Limitations

- No language package manager or app runtime scaffold in this repository yet.
- No automated test suite configured.

## Immune Log

- 2026-03-02: `bash -n scripts/*.sh` passed.
- 2026-03-02: `./scripts/field-cycle.sh` completed successfully.
- 2026-03-02: `shellcheck` warnings detected (non-blocking; no fatal lint errors).
