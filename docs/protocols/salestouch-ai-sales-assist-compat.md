# SalesTouch AIsalesAssist -> TouchCLI CLI Compatibility Spec

**Version**: 1.0  
**Status**: Draft (Implementation Guidance)  
**Created**: 2026-03-02  
**Source Baseline**:
- `/Users/bingbingbai/Desktop/salesTouch/frontend/src/views/AIsalesAssist/AIsalesAssistHome.vue`
- `/Users/bingbingbai/Desktop/salesTouch/frontend/src/router/index.ts`
- `/Users/bingbingbai/Desktop/salesTouch/frontend/src/composables/useAISalesAssist.ts`
- `/Users/bingbingbai/Desktop/salesTouch/frontend/src/composables/useCustomerOpportunity.ts`

---

## 1. Scope

This document defines how TouchCLI (conversation-first, no form/page interaction) should stay compatible with core business capabilities registered in legacy `AIsalesAssistHome.vue`, while upgrading output to richer structured data rendering.

Goal:
- Preserve business capability coverage.
- Standardize data compatibility contracts.
- Decouple business operations from legacy page routes.

Non-goal:
- Rebuild legacy Vue page navigation or GUI interactions.

---

## 2. Legacy Feature Registration Baseline

From `AIsalesAssistHome.vue`, enabled entries are:

1. `产品信息录入` -> `/ai-sales-assist/products`
2. `产品信息浏览` -> `/ai-sales-assist/browse`
3. `客户和商机` -> `/ai-sales-assist/customers`
4. `SPIN 拜访计划` -> `/ai-sales-assist/spin-call-planner`
5. `销售方案生成（未完成）` -> `/ai-sales-assist/scheme-generator`

Coming-soon entries:

1. `讲师简历管理`
2. `AI 演练`
3. `管理者视图`

---

## 3. TouchCLI Capability Mapping

| Legacy Route/Feature | Legacy Semantics | TouchCLI Intent Namespace | Current Status | Notes |
|---|---|---|---|---|
| `/ai-sales-assist/products` (产品录入) | 产品主数据 + 文件上传 + FAB 生成 | `product.create`, `product.update`, `product.asset.upload`, `product.fab.generate` | Gap | Requires schema expansion + tool layer |
| `/ai-sales-assist/browse` (产品浏览) | 产品资料检索/预览 | `product.list`, `product.asset.list`, `product.asset.preview` | Gap | Align with rich message entity cards |
| `/ai-sales-assist/customers` (客户和商机) | 客户、商机、联系人、互动 CRUD | `customer.*`, `opportunity.*`, `contact.*`, `interaction.*` | Partial | `customer/opportunity` exists; `contact/interaction` pending |
| `/ai-sales-assist/spin-call-planner` | 基于客户+产品上下文生成 SPIN 拜访策略 | `spin.plan.generate`, `spin.plan.refine` | Gap | Should reuse agent orchestration + memory context |
| `/ai-sales-assist/scheme-generator` | 销售方案生成/分享 | `scheme.generate`, `scheme.revise`, `scheme.share` | Gap | Depends on rich message + confirmation flow |

Decision:
- TouchCLI does not expose route-level feature entry as UI cards.
- TouchCLI maps user utterances directly to intent-level operations.

---

## 4. Data Compatibility Norms (Critical)

## 4.1 Canonical Field Convention

- API and event contracts use `snake_case`.
- Client-side internal model may keep camelCase aliases, but adapter must normalize at boundaries.
- Canonical IDs use UUID strings in TouchCLI.
- Legacy numeric IDs are supported only through compatibility adapter.

## 4.2 Legacy -> TouchCLI Entity Mapping

| Legacy Entity | Legacy Key Fields | TouchCLI Canonical Entity | Mapping Rule |
|---|---|---|---|
| `Product` | `id:number`, `productName`, `description`, `fileCount` | `product` | `legacy_product_id` kept in metadata, canonical `id` is UUID |
| `PDFFile` | `productId`, `filename`, `filePath`, `fileSize` | `product_asset` | `productId -> product_id`, preserve filename/file_size |
| `Customer` | `companyName` | `customer.name` | `companyName -> name`; optional `type=company` |
| `Opportunity` | `customerId`, `productId`, `amount`, `department`, `expectedCloseDate` | `opportunity` | `customerId -> customer_id`, `expectedCloseDate -> close_date` |
| `Contact` | `favorability`, `orgNeeds`, `personalNeeds` | `contact` | move semantic fields under structured columns or metadata |
| `Interaction` | `interactionType`, `content`, `interactionDate` | `interaction` | `interactionType -> type`, `interactionDate -> occurred_at` |

## 4.3 Envelope Compatibility

Legacy API often returns:
- `{ success: true, data: ... }`

TouchCLI current style returns:
- plain object/array

Norm:
- Internal service boundary uses plain typed payload.
- Compatibility adapter accepts both shapes:
  - if `success/data` exists -> unwrap `data`
  - else treat payload as canonical response

## 4.4 Stage/Status Compatibility

Canonical opportunity stage enum:
- `prospecting`
- `discovery`
- `proposal`
- `negotiation`
- `closed_won`
- `closed_lost`

Normalization rules:
- `closed`, `closed won`, `won` -> `closed_won`
- `closed lost`, `lost` -> `closed_lost`
- unknown values -> `prospecting` + warning log

## 4.5 Message Type Compatibility (for Rich Display, No GUI Form Interaction)

To support richer data presentation in CLI conversation stream, define canonical `content_type`:

- `text`
- `entity_card`
- `action_result`
- `confirmation`
- `quick_replies`
- `chart_mini`
- `voice_note` (reserved)

Compatibility rule:
- legacy plain text defaults to `text`
- structured metadata must contain `schema_version` and `entity_type` where relevant

Minimal metadata contract:

```json
{
  "schema_version": "1.0",
  "entity_type": "customer|opportunity|product|contact|plan|scheme",
  "legacy_ref": {
    "source": "salestouch",
    "id": "optional legacy id"
  }
}
```

## 4.6 Time/Currency Compatibility

- time fields must be ISO 8601 UTC strings (`2026-03-02T13:00:00Z`)
- currency amount persisted as decimal number in canonical `amount`
- optional metadata key `currency` defaults to `CNY`

---

## 5. Intent-Level Contract (Routeless CLI)

Legacy routes are converted to intent contracts:

1. `product.*` for product knowledge management
2. `customer.*` + `opportunity.*` + `contact.*` + `interaction.*` for CRM core
3. `spin.*` for visit planning
4. `scheme.*` for proposal generation and sharing

Each intent execution should produce one of:
- `action_result` (executed)
- `confirmation` (requires approval, see S-011)
- `entity_card` (read/display only)

---

## 6. Implementation Guardrails

1. Keep compatibility conversion in adapter layer; do not leak legacy shape into core agent state.
2. Add explicit schema versions for all structured messages.
3. Never require UI-only interactions (button-only workflows); all actions must be executable by natural-language reply.
4. For missing legacy modules, keep stable placeholder intents with clear "not implemented" action_result payload.

---

## 7. Acceptance Checklist

- [ ] Mapping table approved for all 5 enabled legacy entries.
- [ ] Adapter supports both plain payload and `{success,data}` payload.
- [ ] Field normalization covers `customerId/customer_id`, `companyName/name`, `expectedCloseDate/close_date`.
- [ ] Opportunity stage normalization implemented and tested.
- [ ] Structured message `content_type` expanded beyond `text`.
- [ ] At least one end-to-end scenario validates: "legacy customer+opportunity data -> TouchCLI rich message output".

---

## 8. Signal Linkage

This spec directly supports:
- `S-009` (Data Model Expansion)
- `S-010` (Rich Message Types)
- `S-011` (Human-in-the-Loop confirmation)

Recommended execution order:
1. `S-009` finalize entity compatibility columns/metadata
2. `S-010` finalize structured message renderer and schemas
3. `S-011` wire confirmation cards to intent execution

