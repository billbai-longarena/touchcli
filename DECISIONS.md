# DECISIONS.md — TouchCLI 设计决策记录

> Scout 战略审视：2026-03-02 第三轮心跳
> 由 `termite-1772385639-30853` 记录

---

## [DECISION] 实现分阶段拆解：5 个 Phase，12-16 周交付

**状态**: 🟢 **已决策**
**生效日期**: 2026-03-02
**涉及范围**: 整个 TouchCLI 应用实现

### 决策背景

DESIGN.md 提供了完整的产品与技术设计，但缺失具体的实现细节和任务分解。为避免无序施工，制定了以下分阶段计划。

### 决策内容

TouchCLI 应用实现分为 5 个 Phase，顺序依赖关系：

| Phase | 名称 | 优先级 | 工期 | 描述 |
|-------|------|--------|------|------|
| 1 | 数据与通信基础 | 🔴 HIGH | 4-6 周 | PostgreSQL schema / API 定义 / WebSocket 协议 / Redis 设计 |
| 2 | 后端基础设施 | 🔴 HIGH | 4-5 周 | Gateway (Go) / LangGraph 框架 / 工具引擎 / 错误恢复 |
| 3 | Agent 实现 | 🟡 MEDIUM | 3-4 周 | 6 个 Agent 的具体逻辑（Router / Sales / Data / Strategy / Sentinel / Memory） |
| 4 | 前端与集成 | 🟡 MEDIUM | 2-3 周 | React 19 PWA / 语音集成 / 端到端流程 |
| 5 | 优化与部署 | 🟢 LOW | 2 周 | 性能优化 / CI/CD / Docker/K8s / 监控告警 |

**总交付周期**: ~12-16 周（3-4 个月）

### 关键任务

**Phase 1 (开始优先)**:
1. Task 1.1: PostgreSQL schema 设计
   - 表：users / customers / opportunities / conversations / agent_states
   - 索引：支持快速查询和全文搜索
   - 审计列：created_at / updated_by / version

2. Task 1.2: API 接口定义 (OpenAPI 3.0)
   - POST /conversations (开始对话)
   - POST /messages (发送消息)
   - GET /opportunities (查询商机)
   - 等

3. Task 1.3: WebSocket 帧格式与心跳
   - Frame: { type: "message" | "agent-action" | "heartbeat", payload: {...} }
   - Heartbeat interval: 30s
   - Reconnection strategy: exponential backoff

4. Task 1.4: Redis 键空间设计
   - session:{session_id}: 会话状态
   - cache:customer:{id}: 客户信息缓存
   - ratelimit:{user_id}: 限流计数器

---

## [DECISION] 采用 LangGraph + PostgreSQL 的有状态 Agent 架构

**状态**: 🟢 **已决策**
**生效日期**: 2026-03-02

### 决策背景

DESIGN.md 选择了 LangGraph，但需要明确其与数据库的集成策略。

### 决策内容

- **Agent 状态存储**: LangGraph 的 checkpoint 持久化到 PostgreSQL（不使用纯内存或 Redis）
- **理由**:
  - ✅ 支持审计链（complete conversation history）
  - ✅ 支持 Agent 恢复（crash recovery）
  - ✅ 支持跨会话记忆（前 Agent 的工作可被后续 Agent 引用）
  - ✅ 满足合规性（金融/销售数据必须可追溯）

- **实现方式**:
  ```python
  # 伪代码
  from langgraph.checkpoint.postgres import PostgresSaver

  saver = PostgresSaver(connection_string="postgresql://...")
  graph.compile(checkpointer=saver)
  ```

### 影响范围

- Phase 2: LangGraph 框架集成需要 PostgreSQL driver 和 checkpoint schema
- Phase 3: 所有 Agent 都通过同一个 checkpoint 管理（支持 Agent 间的状态继承）

---

## [DECISION] WebSocket + BullMQ 混合的实时更新机制

**状态**: 🟢 **已决策**
**生效日期**: 2026-03-02

### 决策背景

TouchCLI 需要支持两类操作：(1) 实时响应（如用户输入→Agent 回复），(2) 异步任务（如邮件通知、数据同步）。

### 决策内容

- **直接推送** (低延迟): WebSocket → 用户浏览器
  - 对话消息、Agent 动作进度、即时通知
  - 延迟要求: < 500ms

- **异步队列** (高可靠): BullMQ (Redis-backed) → 后台任务
  - 邮件发送、数据导出、定时爬虫
  - 延迟要求: < 5min

### 影响范围

- Phase 2: Go Gateway 需要 WebSocket 支持和 BullMQ 消费者
- Phase 3: Agent 的工具执行选择合适的通道（实时 vs 异步）

---

## [DECISION] 兼容 SalesTouch SSO，采用 OAuth 2.0 + JWT

**状态**: 🟢 **已决策**
**生效日期**: 2026-03-02

### 决策背景

TouchCLI 作为 SalesTouch 的演进版本，需要复用现有的认鉴基础设施。

### 决策内容

- **协议**: OAuth 2.0 (Authorization Code Flow) + JWT
- **令牌**:
  - Access Token: 有效期 1 小时，包含用户身份和权限
  - Refresh Token: 有效期 7 天，用于更新 Access Token
  - 签名算法: RS256 (RSA，公钥发布在 `/.well-known/jwks.json`)

- **权限模型**: 基于角色 (RBAC)
  - `sales:read` / `sales:write` — 销售数据权限
  - `customers:read` / `customers:write` — 客户信息权限
  - 等

### 影响范围

- Phase 2: Gateway 需要集成 OAuth 鉴权中间件（验证 JWT）
- 所有后端 API 都需要权限检查

---

## [DECISION] PostgreSQL migration 工具：采用 Alembic（Python）

**状态**: 🟢 **已决策**
**生效日期**: 2026-03-02

### 决策背景

数据库 schema 演变需要版本控制和可回滚的迁移。

### 决策内容

- **工具**: SQLAlchemy 的 Alembic
- **理由**:
  - 与 LangGraph checkpoint 集成友好（都是 Python 生态）
  - 支持自动检测 schema 变更（`alembic revision --autogenerate`）
  - 支持分支迁移和冲突解决
  - 支持 rollback

- **工作流**:
  ```bash
  alembic revision --autogenerate -m "Add customers table"
  alembic upgrade head  # Apply in dev
  alembic downgrade -1  # Rollback if needed
  ```

### 影响范围

- Phase 1: 初始 schema 设计时建立迁移流程
- CI/CD: 部署前自动运行 `alembic upgrade head`

---

## [DECISION] 预估 Team 规模：4-5 人，3-4 个月交付

**状态**: 🟢 **已决策**
**生效日期**: 2026-03-02

### 决策内容

| 角色 | 数量 | 职责 |
|------|------|------|
| 后端 (Go) | 1 人 | Gateway / 网络通信 / 权限管理 |
| 后端 (Python) | 1 人 | LangGraph Agent 框架 / 工具引擎 |
| 前端 (React) | 1 人 | PWA UI / 语音集成 / 端到端测试 |
| DevOps (兼职) | 0.5 人 | CI/CD 流水线 / 部署配置 / 监控 |
| QA (兼职) | 0.5 人 | 自动化测试 / 集成测试 / 性能测试 |

**总成本**: ~4.5 人-月 * 3.5 月 = ~15-16 人-月

---

## [EXPLORE] 国际化与多语言支持 (TBD)

**状态**: 🟡 **待研究**
**优先级**: LOW

### 问题

- 应该在哪一个 Phase 引入多语言支持？
- 是否需要在 Agent 层面支持多语言（如中文、英文意图识别差异）？
- 前端与后端的国际化分工？

### 建议

- 在 Phase 4（前端集成）之前定义 i18n 架构
- 考虑使用 i18next (JavaScript) + gettext (Python) 来分离
- 后端的 Agent 可能需要针对不同语言的 prompt 模板

---

## [EXPLORE] 性能基准与 SLA (TBD)

**状态**: 🟡 **待研究**
**优先级**: MEDIUM

### 关键指标（待定）

1. **Agent 响应时间**: 目标 < 500ms（从用户输入到 Agent 回复）
2. **WebSocket 消息延迟**: 目标 < 100ms（网络往返）
3. **数据库查询**: 目标 < 50ms（p99）
4. **并发连接**: 目标 > 1000 同时用户
5. **可用性**: 目标 99.5%（月可用时间 > 99.5%）

### 建议

- Phase 2 完成后进行基准测试（baseline）
- Phase 5 进行负载测试与性能优化

---

## 后续行动

1. ✅ DECISIONS.md 已沉积（本文件）
2. ⏳ 等待人类指令或 Worker Agent 接力
3. ⏳ Task 卡详细化（每个 Phase 的具体交付物清单）
4. ⏳ 技术规范编写（API 详细设计、数据库 ER 图、消息格式）

---

**签名**: `[termite:2026-03-02:scout]`
**记录者**: Scout (termite-1772385639-30853)
**协议版本**: termite-kernel:v10.0
