# TouchCLI i18n & Multi-language Plan (S-004)

## Scope

This document closes signal `S-004` by defining:

1. when i18n should be introduced in delivery phases
2. how language handling should work in Agent workflows
3. frontend/backend ownership boundaries

## Decision Summary

- Introduce i18n architecture in **Phase 3 (frontend start)**.
- Activate production-grade multi-language behavior in **Phase 4**.
- Use **i18next** on frontend and **message-catalog templates** on backend.
- Agent language handling is **locale-aware prompt routing**, not separate models per language.

## Phase Placement

### Phase 3 (Now / frontend implementation)

- define locale contract in API and WebSocket payloads
- add locale persistence in user profile/session context
- implement frontend i18next wiring and base dictionaries (`en-US`, `zh-CN`)

### Phase 4 (voice + advanced integrations)

- expand translation coverage for workflow messages and notifications
- add localized voice configuration (STT/TTS language mapping)
- add language-specific prompt templates for strategy/sales agents

### Phase 5 (optimization/deployment)

- add missing key detection and translation coverage checks in CI
- add locale-specific performance/error dashboards

## Frontend / Backend Split

### Frontend responsibilities

- source of truth for UI string rendering
- i18next namespace management (`common`, `conversation`, `opportunity`, `errors`)
- user locale selection and fallback behavior
- sending `locale` in request headers and WebSocket init frame

### Backend responsibilities

- persist preferred locale in user/session context
- return structured response codes + default message keys
- provide localized system templates for agent/system messages
- keep business logic locale-neutral (no hard-coded language branches in core rules)

## Agent Language Strategy

### Input handling

- detect language from:
  1. explicit user preference (highest priority)
  2. request/session locale
  3. lightweight detection fallback

### Prompt routing

- maintain shared intent schema across languages
- route to locale-specific prompt template packs
- keep tool-call schema identical across languages

### Output policy

- output language defaults to user preferred locale
- include optional secondary language hint only when confidence is low
- log locale decisions for audit and debugging

## Contract Changes

### HTTP

- required header: `Accept-Language` (fallback to user profile locale)
- optional query/body field: `locale`

### WebSocket

- connection init frame should include:
  - `locale`
  - `timezone`
  - `client_language_preferences`

## Minimal Data Model Additions

- `users.preferred_locale` (e.g., `en-US`, `zh-CN`)
- `conversations.locale` (snapshot at conversation start)
- optional `messages.locale` for mixed-language threads

## Acceptance Criteria (S-004 Closure)

- i18n introduction phase is explicitly decided
- agent-level language routing strategy is defined
- frontend/backend responsibility boundary is explicit
- API/WebSocket locale contract is documented

All criteria are satisfied by this document.

## Next Implementation Tasks

1. add locale fields to OpenAPI schemas
2. add frontend i18next bootstrap with `en-US` + `zh-CN`
3. add backend locale resolver middleware/dependency
4. add two prompt template packs (`en-US`, `zh-CN`) for Router and Sales agents
