# Repository Guidelines (Codex / Gemini)

## 致人类开发者 (Note to Human Developers)

> 本文件 (`AGENTS.md`) 是 Codex / Gemini 等非交互平台的入口文件。
> "白蚁协议"是心跳指令——收到后自动执行节律，自主判断并行动。
> 完整协议规范在 `TERMITE_PROTOCOL.md`，本文件足够驱动日常行动。

<!-- termite-kernel:v10.0 -->
## 白蚁协议 — 最小内核 v10.0

> **"白蚁协议"四个字 = 启动心跳，自动执行。**
> **终极目标：维持三丘（开发丘·产品丘·客户丘）的持续发展与繁荣。**

### 协议语法（9 条不可化约规则）

```
1. ARRIVE→SENSE→STATE        到达后感知环境，建立态势
2. STATE→CASTE→PERMISSIONS   态势决定种姓，种姓决定权限
3. ACTION∈PERMISSIONS→DO     在权限内行动
4. DO→DEPOSIT(signal,weight,TTL,location)  行动后沉积信息素
5. weight<threshold→EVAPORATE 低权重信号自动挥发
6. weight>threshold→ESCALATE  高权重信号升级为热点
7. count(agents,same_signal)≥3→EMERGE  ≥3条独立观察→涌现为规则
8. context>80%→MOLT           上下文将满→蜕皮（写WIP+.pheromone，结束会话）
9. DO(generate_agent)→SEED  生成Agent系统时注入协议种子（参见TERMITE_SEED.md）
```

### 执行流程

```
IF 可执行脚本（scripts/field-arrive.sh 存在且可执行）:
  运行 ./scripts/field-arrive.sh → 读 .birth → 按 .birth 中的种姓和规则干活
IF 不可执行:
  检查 ALARM.md（有→兵蚁，立即修复）
  → 检查 WIP.md（新鲜→工蚁，接力前任）
  → 判定种姓（默认探路蚁）→ 干活
  → 沉积观察到 signals/observations/（回退: BLACKBOARD.md）
```

**信号通道**: "白蚁协议"单独 = 心跳通道（完全自主）；附带任务描述 = 指令通道（高权重信号注入）。心跳自足，指令加速。

### 安全网底线（4 条）
1. commit message 说清楚改了什么、为什么改
2. 不要删除任何 .md 文件
3. 改动超过 50 行就 commit 一次（`[WIP]` 标签）
4. 看到 ALARM.md → 停下来读它

> 做到这四点，你就是一只有用的白蚁。完整协议规范参阅 `TERMITE_PROTOCOL.md`。

---

## 非交互 Agent 扩展（Claim/Verify/Release）

> 非交互式 Agent 无法与用户实时沟通，因此使用信号认领机制实现自主协作。

**核心循环：**
1. **Claim**: 读 `signals/active/*.yaml`（回退: `BLACKBOARD.md`）→ 按权重选最高 → `./scripts/field-claim.sh claim S-xxx work <owner>`
2. **Work**: 最小原子动作 → 自检 → 偏离则回判断
3. **Deposit**: 更新信号状态/权重 → 沉积观察 → `./scripts/field-claim.sh release S-xxx work`

**互斥规则**: work⊥audit，review 不阻塞。冲突时跳过，选其他信号。
**容错**: 失败必须写 HOLE + Next 指引。多步任务先写 Plan。
**微探索**: 至少 5% 行动预算用于 EXPLORE 信号。

---

## 按需查阅索引

| 遇到什么 | 读哪里 |
|----------|--------|
| 种姓判定规则 | `TERMITE_PROTOCOL.md` Part II |
| 种姓详解与权限 | `TERMITE_PROTOCOL.md` Part III |
| 信号 YAML 格式 | `signals/README.md` |
| 并发认领冲突 | `TERMITE_PROTOCOL.md` Part II |
| 三丘哲学 | `TERMITE_PROTOCOL.md` Part III |
| 降级运行 | `TERMITE_PROTOCOL.md` Part II |
| 免疫系统 | `TERMITE_PROTOCOL.md` Part III |
| 协议升级变更 | `UPGRADE_NOTES.md` |

---

## Host Project Overview

**项目名称**: TouchCLI — 纯对话式 AI 销售助手框架

**核心定位**: 砍掉所有 GUI，用对话和语音替代表格、表单、仪表盘。Agent 主动为销售人员完成数据录入、客户跟进、商机管理和策略建议。

**背景**: 从 SalesTouch（Vue 3 重 GUI 平台）衍生，面向 B2B（客户经理）和 B2C（医美顾问）销售人员。用户需要"告诉我该做什么"和"帮我做"，而不是"教我怎么用"。

**核心原则**:
1. 零学习成本 — 会说话就会用
2. Agent 先行动 — 主动推送任务和建议
3. 对话即操作 — 语音指令直接创建/更新数据
4. 语音优先 — 开车、见客户时可用
5. 全终端一致 — 手机、平板、电脑同体验

**设计参考**: `DESIGN.md` (第 1-5 节，用户场景、架构总览、技术选型、Agent 设计)

## Host Project Structure & Module Organization

本仓库既是 **Termite Protocol 框架库本身**，又是 **TouchCLI 项目的设计与规划库**。当前阶段纯文档驱动，分为两层：

**第一层 — 协议框架 (已完成)**:
- `TERMITE_PROTOCOL.md` — 完整的多 Agent 协作协议规范
- `CLAUDE.md` / `AGENTS.md` — 入口文件与心跳内核
- `scripts/` — 10+ 生命周期脚本（到达、代谢、沉积、认领）
- `.termite.db` — SQLite 信号存储与状态管理

**第二层 — 应用设计 (规划中)**:
- `DESIGN.md` — TouchCLI 完整设计文档（产品定位、用户场景、技术栈、Agent 拓扑）
- `QUICKSTART.md` — 协议快速上手（安装、配置、创世）
- `BLACKBOARD.md` — 蚁丘健康状态与信号库存
- `UPGRADE_NOTES.md` — 协议版本变更记录

**模块对应** (见 CLAUDE.md 路由表):
- `DESIGN.md` → 产品与应用架构
- `AGENTS.md` → Agent 开发与非交互扩展
- `TERMITE_PROTOCOL.md` → 协议规范与术语
- `scripts/` → 场基础设施与工具
- `signals/` + `BLACKBOARD.md` → 信号与观察

---

## 场基础设施 / Field Infrastructure

| 工具/文件 | 作用 | 说明 |
|----------|------|------|
| `scripts/field-arrive.sh` | 到达仪式 | 每个会话开始时运行，生成 `.birth`（≤800 tokens），感知蚁丘脉搏 |
| `scripts/field-cycle.sh` | 完整代谢循环 | 衰减过期信号、排水归档、更新蚁丘脉搏，由 post-commit hook 自动触发 |
| `scripts/field-deposit.sh` | 信息素沉积 | 记录观察 (Observation)、个体信息素 (.pheromone)、规则争议 |
| `scripts/field-export-audit.sh` | 审计包导出 | 导出不含项目源码的蚁丘协议产物，供协议源仓库的 Protocol Nurse 分析 |
| `scripts/field-claim.sh` | 认领与释放 | 互斥锁机制，claim/release/check/list/expired 子命令，支持多 Agent 并发 |
| `signals/rules/*.yaml` | 触发-动作规则 | 由 field-arrive.sh 注入 `.birth`；规则来自协议规范和通过"涌现"产生 |
| `signals/active/*.yaml` | 活跃信号导出 | `.termite.db` 中 active 信号的 YAML 快照，用于人类阅读和审计 |
| `.pheromone` | 信息素痕迹 | JSON 格式，记录会话结束时的完成项、未解决项、交接质量，chain 成时间序列 |
| `.birth` | 出生证明 | 本次会话的完整态势（种姓、信号、规则、权限、预算），由 field-arrive.sh 生成 |
| `.termite.db` | 主存储 | SQLite WAL 模式，所有信号、观察、规则、认领的单一事实源，支持并发多 Agent |

---

## 路由表：任务 → 局部黑板

| 任务关键词 | 局部黑板 | 模块 |
| ---------- | -------- | ---- |
| `design` / `product` / `touchcli` / `对话` / `Agent 架构` | `DESIGN.md` | TouchCLI 产品定位与技术架构 |
| `agent` / `framework` / `白蚁` / `协议` / `非交互` | `AGENTS.md` | 非交互 Agent 扩展与框架入口 |
| `protocol` / `termite` / `规范` / `术语` / `种姓` | `TERMITE_PROTOCOL.md` | 完整协议规范（9 语法规则 + 4 安全网） |
| `script` / `场基础设施` / `field-*` / `shell` | `scripts/` | 生命周期工具、代谢循环、认领机制 |
| `signal` / `信息素` / `pheromone` / `观察` | `signals/` + `BLACKBOARD.md` | 活跃信号与观察库 |
| `config` / `配置` / `分支` / `governance` | `CLAUDE.md` | 项目配置、分支治理、技术栈 |

---

## Build, Test, and Development Commands

| 操作 | 命令 | 说明 |
| ---- | ---- | ---- |
| 到达仪式 | `./scripts/field-arrive.sh` | 每个会话开始时运行，生成 `.birth`，设置态势 |
| 信息素沉积 | `./scripts/field-deposit.sh --pattern '...' --context '...'` | 会话结束时沉积观察、信息素、规则争议 |
| 脚本语法检查 | `bash -n scripts/field-*.sh` | 所有 shell 脚本通过语法检查 |
| 代码风格检查 | `shellcheck scripts/` | 可选，检查常见 shell 反模式（如需） |
| 数据库检查 | `sqlite3 .termite.db ".tables"` | 验证 SQLite 表结构（signals、observations、rules、claims 等） |
| 信号导出同步 | `ls signals/active/ && sqlite3 .termite.db "SELECT id FROM signals WHERE status='open'"` | 快照与数据库一致性检查 |
| Git 提交 | `git add . && git commit -m "[termite:YYYY-MM-DD:caste] ..."` | 所有改动必须带 termite 签名 |

---

## 验证清单

| 改动类型 | 验证方式 |
| -------- | -------- |
<!-- | 后端代码 | 构建通过，无报错 | -->
<!-- | 前端代码 | 构建通过，无报错 | -->

---

## Configuration & Secrets

<!-- 在此说明环境变量和配置文件结构，不要包含实际密钥值 -->

## 分支治理（固定）

```
swarm ──(人类挑拣稳定功能)──▶ uat ──(测试通过后合并)──▶ master
▲ AI 白蚁常驻开发分支             ▲ 用户测试分支                 ▲ 生产分支
```

| 分支 | 用途 | 写入规则 |
|------|------|----------|
| `swarm` | 持续开发主分支 | AI 白蚁开发与心跳信号任务默认只在此分支提交与合并 |
| `uat` | 用户测试 | 仅在需要提测时由人类主导从 `swarm` 合并 |
| `master` | 生产发布 | 仅人类工程师操作，作为生产基线 |

约束：
- 白蚁心跳信号开发默认在 `swarm`。
- 所有开发完成后合并到 `swarm`。
- 未经人类明确指令，不直接提交到 `uat` / `master`。

<!-- ### 分支治理 — 三分支流水线

```
<dev-branch> ──(人类挑拣稳定功能)──▶ <staging-branch> ──(测试通过后合并)──▶ <production-branch>
 ▲ AI 白蚁工作区                      ▲ 开发服务器                          ▲ 生产环境
```

| 分支 | 谁写入 | 部署 |
|------|--------|------|
| `<dev-branch>` | AI 白蚁（所有 commit 只到这里） | 不部署 |
| `<staging-branch>` | 人类工程师主导 | 自动发布到开发服务器 |
| `<production-branch>` | 仅人类工程师 | 手动发布到生产环境 |

自主模式：只允许操作 `<dev-branch>` 和 `feature/*`。
人类指挥模式：人类明确指令时可操作 `<staging-branch>`，操作前复述指令并请求确认。
`<production-branch>` 即使人类指挥也不允许白蚁操作。 -->

---

## 已知限制

> 动态状态在 `BLACKBOARD.md`。

---

## 黑板索引

| 黑板 | 路径 |
| ---- | ---- |
<!-- | 模块 A | `path/to/module-a/BLACKBOARD.md` | -->
