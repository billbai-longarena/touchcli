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
| Framework | ✅ **READY** | stable | 2026-03-02 Scout x3 |
| Documentation | ✅ **COMPLETE** | ↗️ improving | 2026-03-02 (CLAUDE/AGENTS/DECISIONS) |
| Foundation Genesis | ✅ **VERIFIED** | ✅ ready for Worker | 2026-03-02 (涌现规则确认) |
| Build     | pass (script syntax and metabolism cycle) | stable | 2026-03-02 |
| Tests     | not configured (no test harness detected) | stable | 2026-03-02 |
| Phase 1   | ✅ **IMPLEMENTATION COMPLETE** (schema, API, WebSocket, Redis design) | ✓ complete | 2026-03-02 Worker |
| Backend   | 🟡 FRAMEWORK READY (FastAPI/Go scaffold + dependencies) | ✓ framework | Ready for Phase 2 |
| Phase 2   | ⏳ IN PREPARATION (S-003 HOLE w:49, ready for next Worker) | waiting for implementation | Next |

## Signals (5 Active) — After Decay Cycle

| ID | Type | Title | Weight | TTL | Status | Owner | Source |
|----|------|-------|--------|-----|--------|-------|--------|
| S-003 | HOLE | Phase 2: Backend Infrastructure (4-5 weeks, 7-task plan) | 49 | 30d | open | unassigned | scout-strategic |
| S-002 | IMPLEMENT | Phase 1: COMPLETE ✓ (PostgreSQL schema, REST API, WebSocket, Redis) | 46 | 21d | completed | worker-phase1 | emergent |
| S-005 | PROBE | EXPLORE: Performance Benchmarks & SLA Definition | 32 | 21d | open | unassigned | scout-decision |
| S-001 | EXPLORE | Map unknown project (decaying, archive when w≤20) | 27 | 14d | claimed | scout | autonomous |
| S-004 | PROBE | EXPLORE: Internationalization & Multi-language Support | 22 | 21d | open | unassigned | scout-decision |

## Emerged Rules

| ID | Trigger | Action | Source | Hit Count | Created |
|----|---------|--------|--------|-----------|---------|
| R-001 | ≥3 Scout observations confirm: protocol framework stable, project type identified, docs complete, routing resolved | Foundation Genesis Verified → Worker phase ready. Maintain S-001 until weight ≤ 20, then archive. | 5 observations | 1 | 2026-03-02 |

## Hotspot Areas

- `scripts/`: automation correctness and portability.
- `.termite.db` + `signals/active/`: single source of truth and exported snapshots.

## Notes for AI

- **Phase Transition**: Foundation Genesis → Worker Implementation (Rule R-001 emerged, active in .birth)
- **DECISIONS.md**: Strategic planning complete (5 Phase breakdown, 12-16 week timeline, 8 core decisions + 2 EXPLORE items)
- **Signal Hierarchy**:
  - S-003 (w:55, HOLE) — Phase 2, depends on S-002 completion
  - S-002 (w:49, IMPLEMENT) — Phase 1, priority for Worker caste
  - S-005 (w:35, PROBE) — Performance SLA research (medium priority)
  - S-001 (w:30, EXPLORE) — Genesis EXPLORE, decaying, archive when w≤20
  - S-004 (w:25, PROBE) — i18n research (low priority)
- **Scout Completions**:
  1. Foundation Genesis verified (4 Scout sessions, Rule R-001 emerged)
  2. DECISIONS.md with 5-phase strategic plan
  3. S-002/S-003 phase task signals created
  4. S-004/S-005 research exploration signals created
- **Data Consistency**: All signals now synced to .termite.db (S-003 fixed from YAML)
- **Phase 1 COMPLETE** — All 4 Tasks Delivered (2026-03-02 Worker, 1887 lines):
  1. ✅ Task 1.1: db/001_initial_schema.sql (290 lines)
     - 11 core tables: users, customers, opportunities, conversations, messages, agent_states, activity_log, session_snapshots, batch_jobs
     - Indexes, constraints, triggers, full-text search, pgvector support
  2. ✅ Task 1.2: docs/api/openapi.yaml (636 lines)
     - 11 REST endpoints (POST/GET/PATCH)
     - Complete OpenAPI 3.0 specification with schema definitions
  3. ✅ Task 1.3: docs/protocols/websocket-protocol.md (454 lines)
     - 6 frame types: message, agent-action, agent-state, audio, heartbeat, error, system
     - Message flows, error handling, authentication, security
  4. ✅ Task 1.4: docs/redis-keyspace-design.md (507 lines)
     - 7 key namespaces: sessions, cache, locks, rate limit, batch jobs, secondary index
     - Memory estimation, monitoring, eviction policy
- **Phase 1 Framework**: PHASE_1.md (planning), backend/python/main.py, backend/go/main.go (code scaffold)
- **Phase 2 Ready**: S-003 (w:49 HOLE) prepared with PHASE_2_PLAN.md (7-task breakdown)

## Known Limitations

- No language package manager or app runtime scaffold in this repository yet.
- No automated test suite configured.

## Immune Log

- 2026-03-02: `bash -n scripts/*.sh` passed.
- 2026-03-02: `./scripts/field-cycle.sh` completed successfully.
- 2026-03-02: `shellcheck` warnings detected (non-blocking; no fatal lint errors).
