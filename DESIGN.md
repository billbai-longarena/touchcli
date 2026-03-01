# TouchCLI — 纯对话式销售助手框架设计

> **一句话定义：** 没有按钮、没有表单、没有仪表盘——只有对话和语音。背后是一群 AI Agent 主动为销售人员解决问题。

---

## 0. 从 SalesTouch 到 TouchCLI：为什么要重新设计

### SalesTouch 现状总结

SalesTouch 是一个 AI 驱动的销售赋能平台，核心是 **Max Agent**——一个能"看见"用户所在页面、动态加载技能的 AI 副驾驶。当前系统：

| 维度 | 现状 |
|------|------|
| **AI 核心** | Max Agent：26+ 技能、三层记忆（会话→中期→长期）、APL 自学习、主动通知引擎 |
| **业务模块** | B2C（医美客户管理，四列布局）+ B2B/Opportunity（商机管道，三列布局） |
| **前端** | Vue 3 + Element Plus，重 GUI——表格、表单、仪表盘、卡片流、拖拽 |
| **后端** | Node.js + TypeScript + MySQL (阿里云 RDS) |
| **多 Agent** | Sensor/Strategy/Memory/Explorer/Diagnostic 五种 Agent，通过 DB 黑板协作 |
| **移动端** | 适配不完整，多列布局在手机上不可用 |

### 为什么需要 TouchCLI

1. **GUI 是瓶颈，不是价值**：SalesTouch 80% 的前端代码是表格/表单/布局，但销售人员真正需要的是"告诉我该做什么"和"帮我做"
2. **移动端体验断裂**：多列 GUI 无法在手机上工作，而销售人员 70%+ 时间在外面
3. **技能绑定页面是限制**：Max 的技能按 URL 加载，意味着用户必须先导航到正确页面才能获得帮助
4. **对话才是自然交互**：销售人员的工作本质是"说话"——跟客户说、跟团队说、跟系统说

### TouchCLI 的赌注

**砍掉所有 GUI，只留对话和语音。** 把"用户操作系统"变成"Agent 替用户操作"。

---

## 1. 产品定位与核心原则

### 定位

> **TouchCLI 是一个纯对话界面的 AI 销售助手，服务 B2B 和 B2C 销售人员。用户只需要说话或打字，背后的 Agent 群自动完成数据录入、客户跟进、商机管理、策略建议等一切操作。**

### 五条设计原则

| # | 原则 | 含义 |
|---|------|------|
| 1 | **零学习成本** | 会说话就会用。没有菜单、没有导航、没有"功能入口"的概念 |
| 2 | **Agent 先行动** | 不等用户问。Agent 主动推送：今天该联系谁、哪个商机有风险、客户刚发了朋友圈 |
| 3 | **对话即操作** | "帮我给张总创建一个 50 万的商机" = 直接创建，不是跳转到表单页 |
| 4 | **语音优先** | 开车、见客户、走路时都能用。语音输入是第一公民，文字输入是备选 |
| 5 | **全终端一致** | 手机、平板、电脑、甚至智能手表——同一个对话流，同一个体验 |

---

## 2. 用户场景

### B2B 销售（客户经理）

```
早上 8:30，开车去公司
  用户（语音）："今天有什么要注意的？"
  Agent："早上好。三件事：
    1. 华为的 200 万商机卡在方案阶段 14 天了，建议今天推进
    2. 昨天腾讯的李总看了你发的方案文档，停留 8 分钟
    3. 下午 3 点跟字节的 demo 会议，我准备了竞品对比要点

    要我展开哪个？"

  用户："展开华为那个"
  Agent："华为云存储项目，金额 200 万，3 月 15 日目标关单。
    卡在方案阶段的原因：技术评估报告还没给对方。
    你上次跟技术部王工说 2 月 25 日前给，已经超期 5 天。

    建议：给王工发一条消息催一下，然后跟华为的张总解释进度。
    要我帮你拟消息吗？"

  用户："帮我拟"
  Agent：（生成两条消息，用户语音确认后直接发送）
```

### B2C 销售（医美顾问）

```
下午 2:00，刚做完一个客户咨询
  用户（语音）："刚才那个客户叫王小美，咨询的热玛吉，28 岁，预算 2 万左右，
    她比较犹豫，怕疼。"
  Agent："好的，我帮你记录了：
    - 新客户：王小美，28 岁
    - 意向项目：热玛吉，预算 2 万
    - 顾虑：怕疼
    - 状态：已咨询/犹豫中

    根据历史数据，怕疼客户的转化关键是术后案例 + 麻醉说明。
    我创建了一个 3 天后的跟进任务，提醒你发送无痛热玛吉案例。
    需要调整吗？"

  用户："不用，就这样"
```

### 通用场景

```
随时随地
  Agent（主动推送）："张总（华为）刚在领英发了一条关于云原生的动态，
    他之前对你们的云存储方案感兴趣。要不要趁这个话题跟他互动一下？"

  用户："好，帮我写一条评论"
  Agent：（生成评论，用户确认后提示手动发布或自动发布）
```

---

## 3. 系统架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端 (PWA)                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│
│  │ 对话界面  │  │ 语音引擎  │  │ 通知管理  │  │ 离线消息队列     ││
│  │ (React)  │  │ (STT/TTS)│  │ (Push)   │  │ (IndexedDB)     ││
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────────────┘│
│       └──────────────┴─────────────┴─────────────┘              │
│                          WebSocket                               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│                      API Gateway (Go)                            │
│              认证 · 限流 · WebSocket 管理 · 路由                  │
└──────────┬───────────────┬───────────────┬──────────────────────┘
           │               │               │
    ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐
    │  对话服务    │ │  Agent 编排  │ │  通知服务    │
    │  (Python)   │ │  (Python)   │ │  (Go)       │
    │  会话管理    │ │  任务分发    │ │  规则引擎    │
    │  消息存储    │ │  工具执行    │ │  推送调度    │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
    ┌──────┴───────────────┴───────────────┴──────┐
    │              共享基础设施                      │
    │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────┐ │
    │  │Postgres│ │Redis │ │S3/OSS│ │ LLM网关   │ │
    │  │(主库) │  │(缓存) │ │(文件) │ │(多模型)  │ │
    │  └──────┘  └──────┘  └──────┘  └──────────┘ │
    └─────────────────────────────────────────────┘
```

---

## 4. 技术选型

### 4.1 前端：PWA (Progressive Web App)

| 选择 | 理由 |
|------|------|
| **React + TypeScript** | 生态最大，PWA 支持最成熟，对话式 UI 组件丰富 |
| **PWA（非原生 App）** | 一次开发，手机/平板/电脑/手表全覆盖。免应用商店审核。可添加到主屏幕 |
| **TailwindCSS** | 对话式 UI 极简，不需要重组件库（不再需要 Element Plus） |
| **Workbox** | Service Worker 管理，离线消息缓存，后台同步 |

**为什么不用 React Native / Flutter：**
- 对话 UI 极度简单（一个消息列表 + 一个输入框），不需要原生组件
- PWA 可以直接 `Add to Home Screen`，体验接近原生
- 避免维护 iOS/Android 双端代码
- Web Push API 已支持 Android 通知（iOS 16.4+ 也支持 PWA 推送）

**如果未来需要原生能力（如后台录音）：** 用 Capacitor 包装 PWA 为原生 App，成本极低。

### 4.2 语音引擎

```
语音输入链路：
  用户说话 → Web Speech API (实时流式) → 文本 → WebSocket → 服务端

语音输出链路：
  服务端响应文本 → TTS API (服务端) → 音频流 → WebSocket → 客户端播放
```

| 组件 | 选择 | 理由 |
|------|------|------|
| **STT (语音→文字)** | 优先 Web Speech API；兜底 Whisper API | 浏览器原生 STT 零延迟、免费；Whisper 准确率更高但有延迟和成本 |
| **TTS (文字→语音)** | 服务端：Azure TTS 或 minimax TTS | 中文语音质量远超浏览器原生 TTS |
| **VAD (语音活动检测)** | Silero VAD (WebAssembly) | 精确检测说话起止，避免噪音误触发 |
| **唤醒词（可选）** | Porcupine (Picovoice) | "Hey Max" 唤醒，免按钮 |

### 4.3 后端：Python + Go 双语言

| 服务 | 语言 | 理由 |
|------|------|------|
| **API Gateway** | Go | 高并发 WebSocket 连接管理、认证、限流 |
| **Agent 编排** | Python | LLM 生态最强（LangGraph/CrewAI），Agent 开发效率最高 |
| **对话服务** | Python | 与 Agent 编排共享 LLM 调用链路 |
| **通知服务** | Go | 定时任务、推送调度，对性能敏感 |

**为什么从 Node.js 切换：**
- Python 的 AI/ML 生态（LangChain, LangGraph, Transformers, Embeddings）远超 Node.js
- Go 的 WebSocket 并发能力和内存效率远超 Node.js
- 对话式产品不需要 SSR，Node.js 的前后端同构优势不再适用

### 4.4 Agent 框架：LangGraph

| 选择 | 理由 |
|------|------|
| **LangGraph** | 有状态的多 Agent 编排，支持人机协作循环（human-in-the-loop）、持久化检查点、流式输出 |
| **非 CrewAI/AutoGen** | LangGraph 更底层、更灵活，适合自定义 Agent 交互模式 |
| **非自研** | SalesTouch 自研的 text-based tool-call 系统可靠但维护成本高，LangGraph 社区支持更好 |

### 4.5 数据库：PostgreSQL

| 选择 | 理由 |
|------|------|
| **PostgreSQL** | JSONB 原生支持（Agent 记忆/黑板数据大量 JSON）、全文搜索、向量扩展 (pgvector) |
| **pgvector 扩展** | 客户/商机/对话的语义搜索，不需要额外的向量数据库 |
| **非 MySQL** | SalesTouch 在 MySQL 上遇到的 UUID 类型问题、JSON 查询性能问题，PG 原生解决 |

### 4.6 实时通信：分层协议（WebSocket + SSE）

| 选择 | 理由 |
|------|------|
| **客户端 ↔ 网关：WebSocket** | 双向实时通信，Agent 可主动推送消息，语音流传输 |
| **网关/Agent ↔ LLM Gateway：SSE** | 对接现有 `useTokenStream` 流式网关，复用统一计费与 SSO token 鉴权 |
| **Socket.IO** | WebSocket 的工程化封装，自动重连、房间管理、回退机制 |

### 4.7 缓存与消息队列

| 组件 | 选择 | 用途 |
|------|------|------|
| **Redis** | 会话状态、Agent 中间结果、速率限制、在线状态 |
| **BullMQ** (Redis-based) | Agent 任务队列、通知调度、异步工具执行 |

### 4.8 完整技术栈一览

```
前端:    React 19 + TypeScript + TailwindCSS + PWA (Workbox)
语音:    Web Speech API + Whisper API + Azure TTS + Silero VAD
通信:    Socket.IO (客户端实时) + SSE (LLM 网关流式)
网关:    Go (Gin) — 认证/限流/WS 管理
Agent:   Python (LangGraph) — 多 Agent 编排
对话:    Python (FastAPI) — 会话/消息管理
通知:    Go — 规则引擎/推送调度
数据库:  PostgreSQL 16 + pgvector
缓存:    Redis 7
队列:    BullMQ
文件:    阿里云 OSS / S3
LLM:     多模型网关 (Claude/GPT/Deepseek)
部署:    Docker + docker-compose (开发) / K8s (生产)
CI/CD:   GitHub Actions
监控:    Prometheus + Grafana + Sentry
```

---

## 5. Agent 架构设计

### 5.1 Agent 拓扑

```
                    用户输入 (文字/语音)
                           │
                    ┌──────▼──────┐
                    │  Router Agent │ ← 意图识别 + 上下文感知
                    │  (调度中枢)   │
                    └──┬───┬───┬──┘
                       │   │   │
          ┌────────────┘   │   └────────────┐
          ▼                ▼                ▼
   ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
   │ Sales Agent  │ │ Data Agent  │ │ Strategy Agent│
   │ (销售执行)   │ │ (数据操作)  │ │ (策略建议)    │
   └──────┬──────┘ └──────┬──────┘ └──────┬───────┘
          │               │               │
          ▼               ▼               ▼
   ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
   │ CRM 工具集   │ │ DB 工具集   │ │ 分析工具集    │
   └─────────────┘ └─────────────┘ └──────────────┘

   ┌─ 后台常驻 Agent（不直接对话，主动触发）─────────────┐
   │                                                     │
   │  Sentinel Agent    — 监控客户动态、商机超时、竞品变化  │
   │  Memory Agent      — 记忆整理、知识沉淀、遗忘衰减      │
   │  Coach Agent       — 分析销售行为，给出改进建议         │
   │                                                     │
   └─────────────────────────────────────────────────────┘
```

### 5.2 Agent 职责定义

#### Router Agent（调度中枢）

**角色：** 所有用户输入的第一个接触点。负责理解意图、识别上下文、分发给专业 Agent。

```
输入："帮我创建一个华为的商机，金额 200 万"
Router 判断：
  - 意图：创建商机 → Data Agent
  - 实体：客户=华为，金额=200万
  - 上下文：用户是 B2B 销售
  → 分发给 Data Agent，附带结构化参数
```

```
输入："华为那个项目你觉得能不能成？"
Router 判断：
  - 意图：策略分析 → Strategy Agent
  - 实体：客户=华为，关联最近的商机
  - 需要数据：先让 Data Agent 查询商机详情，再交给 Strategy Agent 分析
  → 编排：Data Agent (查) → Strategy Agent (分析) → 组合回复
```

#### Sales Agent（销售执行）

**角色：** 帮用户完成销售动作——拟消息、生成方案、准备话术、跟进提醒。

**工具：**
- `draft_message` — 拟定给客户的消息（微信/邮件/短信）
- `prepare_talking_points` — 根据客户画像和商机阶段生成话术
- `create_follow_up` — 创建跟进计划（含自动提醒）
- `generate_proposal` — 生成简版方案/报价（Markdown 格式，可导出 PDF）
- `role_play` — 模拟客户进行对话练习

#### Data Agent（数据操作）

**角色：** 一切 CRM 数据的 CRUD。用户说一句话，它完成数据录入。

**工具：**
- `manage_customer` — 客户增删改查
- `manage_opportunity` — 商机增删改查（含阶段推进）
- `manage_contact` — 联系人增删改查
- `log_interaction` — 记录拜访/电话/微信沟通
- `search` — 语义搜索（客户、商机、联系人、历史对话）
- `query_stats` — 查询统计数据（漏斗、转化率、预测）

#### Strategy Agent（策略建议）

**角色：** 分析局势，给出建议。不执行操作，只输出思考。

**工具：**
- `analyze_opportunity` — 分析商机赢率、风险点、关键路径
- `competitive_intel` — 竞品对比分析
- `stakeholder_map` — 决策链分析（关键人、影响力、态度）
- `next_best_action` — 基于当前状态推荐下一步
- `forecast` — 销售预测（个人/团队/区域）

#### Sentinel Agent（后台哨兵，常驻）

**角色：** 7×24 监控，发现异常主动通知用户。

**触发规则（示例）：**

| 规则 | 触发条件 | 通知内容 |
|------|----------|----------|
| 商机停滞 | 同一阶段 > 7 天 | "华为项目在方案阶段停了 10 天，要不要推进？" |
| 客户沉默 | 最后互动 > 14 天 | "张总已经 14 天没联系了，发条消息保持关系？" |
| 商机到期 | 预期关单日 < 7 天 | "腾讯项目 3 天后到期，当前还在谈判阶段" |
| 新线索 | 外部数据源推送 | "你关注的字节跳动刚发了招聘 XX 岗位（可能有采购需求）" |
| 客户动态 | 社交媒体/新闻 | "华为张总刚发了朋友圈..." |

#### Memory Agent（后台记忆员，常驻）

**角色：** 管理对话和行为中产出的知识。

**职责：**
- **抽取**：从每次对话中提取关键事实（客户偏好、承诺、反对意见）
- **整合**：跨对话合并同一客户/商机的信息
- **衰减**：过时信息自动降权（30 天前的"客户说下周开会"已过期）
- **组织级沉淀**：多个销售反馈同一客户特征 → 升级为组织知识

#### Coach Agent（后台教练，常驻）

**角色：** 分析销售行为，给出改进建议。

**触发：**
- 每周一早上推送周报："上周你跟进了 12 个客户，4 个推进了，你在'技术评估'阶段的转化率偏低..."
- 检测到低效模式："你最近 3 个丢失的商机都卡在同一阶段，是不是 XX 环节有问题？"

### 5.3 Agent 间通信

```python
# 使用 LangGraph 的 State 机制实现 Agent 间通信

class ConversationState(TypedDict):
    messages: list[Message]          # 对话历史
    current_intent: str              # 当前意图
    entities: dict                   # 识别出的实体
    agent_results: dict              # 各 Agent 返回结果
    pending_confirmation: dict | None # 等待用户确认的操作
    user_context: UserContext        # 用户画像 + 当前状态

# Agent 间不直接通信，通过 State 传递
# Router 写入 intent/entities → 专业 Agent 读取并执行 → 结果写回 State
```

### 5.4 人机协作模式

在纯对话界面中，所有"确认"都通过对话完成：

```
Agent: "我准备创建以下商机：
  客户：华为
  项目：云存储升级
  金额：200 万
  阶段：需求分析
  预计关单：2026-05-01

  确认创建吗？"

用户: "金额改成 180 万，其他没问题"

Agent: "好的，金额调整为 180 万，已创建。商机编号 OPP-2026-0342。"
```

**操作分级：**

| 级别 | 操作类型 | 是否需要确认 |
|------|----------|-------------|
| **L0** | 查询类（查客户、查商机） | 不需要 |
| **L1** | 记录类（记拜访、加备注） | 不需要，事后可撤销 |
| **L2** | 创建/修改类（建商机、改阶段） | 摘要确认 |
| **L3** | 发送类（给客户发消息） | 逐字确认 |
| **L4** | 删除类（删客户、删商机） | 二次确认 |

---

## 6. 数据模型

### 6.1 核心实体

```sql
-- 用户与组织（SSO-only：不存本地注册凭据）
users (
  id UUID PRIMARY KEY,
  sso_subject TEXT UNIQUE NOT NULL,  -- IdP subject/sub
  org_id UUID NOT NULL,
  role TEXT NOT NULL,
  display_name TEXT,
  avatar_url TEXT,
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
)
organizations (id, name, plan, settings JSONB, created_at)

-- 客户（B2B + B2C 统一模型）
customers (
  id UUID PRIMARY KEY,
  org_id UUID NOT NULL,
  owner_id UUID NOT NULL,          -- 归属销售
  name TEXT NOT NULL,
  type TEXT CHECK (type IN ('company', 'individual')),  -- B2B=company, B2C=individual

  -- 通用字段
  phone TEXT, email TEXT, address TEXT,
  source TEXT,                      -- 来源渠道
  tags TEXT[],                      -- 标签

  -- B2B 字段 (type='company')
  industry TEXT, company_size TEXT, website TEXT,

  -- B2C 字段 (type='individual')
  age INT, gender TEXT, budget_range TEXT, concerns TEXT[],

  -- 状态
  status TEXT DEFAULT 'new',        -- new/contacting/visiting/deal/loyal/lost
  last_interaction_at TIMESTAMPTZ,

  -- 元数据
  extra JSONB DEFAULT '{}',         -- 灵活扩展
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 商机 (B2B 专用)
opportunities (
  id UUID PRIMARY KEY,
  org_id UUID, customer_id UUID, owner_id UUID,
  name TEXT, amount NUMERIC,
  stage TEXT,                       -- discovery/analysis/proposal/negotiation/closing/won/lost
  expected_close_date DATE,
  probability INT,                  -- 赢率 0-100
  competitors TEXT[],
  loss_reason TEXT,
  extra JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
);

-- 联系人
contacts (
  id UUID, org_id UUID, customer_id UUID,
  name TEXT, title TEXT, phone TEXT, email TEXT,
  role TEXT,                        -- decision_maker/influencer/champion/blocker/user
  attitude TEXT,                    -- supportive/neutral/negative/unknown
  extra JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ
);

-- 互动记录
interactions (
  id UUID, org_id UUID, customer_id UUID, opportunity_id UUID,
  user_id UUID,                     -- 记录人
  type TEXT,                        -- call/visit/wechat/email/meeting
  summary TEXT,                     -- AI 生成的摘要
  raw_content TEXT,                 -- 原始内容（用户口述的录音转文字等）
  sentiment TEXT,                   -- positive/neutral/negative
  next_action TEXT,                 -- 下一步
  extra JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ
);

-- 对话（与 AI 的对话）
conversations (
  id UUID, user_id UUID, org_id UUID,
  title TEXT,                       -- AI 自动生成的对话标题
  summary TEXT,                     -- 对话摘要
  status TEXT DEFAULT 'active',     -- active/archived
  created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
);

messages (
  id UUID, conversation_id UUID,
  role TEXT,                        -- user/assistant/system/tool
  content TEXT,
  content_type TEXT DEFAULT 'text', -- text/voice_transcript/card/action_result
  metadata JSONB DEFAULT '{}',      -- 工具调用结果、语音原始URL等
  created_at TIMESTAMPTZ
);

-- Agent 记忆
memories (
  id UUID, org_id UUID, user_id UUID,
  scope TEXT,                       -- user/customer/org
  target_id UUID,                   -- 关联的客户/商机 ID (scope=customer 时)
  content TEXT,                     -- 记忆内容
  embedding VECTOR(1536),           -- 用于语义搜索
  importance FLOAT DEFAULT 0.5,     -- 重要度 0-1
  decay_rate FLOAT DEFAULT 0.02,    -- 每天衰减率
  source TEXT,                      -- conversation/observation/synthesis
  created_at TIMESTAMPTZ,
  last_accessed_at TIMESTAMPTZ
);

-- 通知队列
notifications (
  id UUID, user_id UUID, org_id UUID,
  type TEXT,                        -- alert/insight/reminder/coach
  priority TEXT,                    -- P0/P1/P2/P3
  title TEXT, body TEXT,
  related_entity_type TEXT,         -- customer/opportunity/interaction
  related_entity_id UUID,
  status TEXT DEFAULT 'pending',    -- pending/delivered/read/dismissed
  scheduled_at TIMESTAMPTZ,
  delivered_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ
);
```

### 6.2 索引策略

```sql
-- 高频查询路径
CREATE INDEX idx_customers_org_owner ON customers(org_id, owner_id);
CREATE INDEX idx_customers_last_interaction ON customers(org_id, last_interaction_at);
CREATE INDEX idx_opportunities_org_stage ON opportunities(org_id, stage);
CREATE INDEX idx_interactions_customer ON interactions(customer_id, created_at DESC);
CREATE INDEX idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_memories_scope ON memories(scope, target_id, importance DESC);
CREATE INDEX idx_notifications_user_status ON notifications(user_id, status, scheduled_at);
```

---

## 7. 前端设计

### 7.1 界面结构

整个 App 只有一个页面：**对话页**。

```
┌─────────────────────────────────────────┐
│  TouchCLI                    [👤] [⚙]  │  ← 极简顶栏：品牌 + 用户头像 + 设置
├─────────────────────────────────────────┤
│                                         │
│  ┌─ Agent 消息 ──────────────────────┐ │
│  │ 早上好！今天有 3 件事需要关注：    │ │
│  │ 1. 华为商机停滞 14 天              │ │
│  │ 2. 腾讯李总看了方案               │ │
│  │ 3. 下午 3 点字节 demo              │ │
│  │                                   │ │
│  │ 要我展开哪个？                     │ │
│  └───────────────────────────────────┘ │
│                                         │
│         ┌─ 用户消息 ──────────┐        │
│         │ 展开华为那个         │        │
│         └─────────────────────┘        │
│                                         │
│  ┌─ Agent 消息 ──────────────────────┐ │
│  │ 华为云存储项目：                   │ │
│  │ ┌──────────────────────────────┐  │ │  ← 内嵌卡片（唯一的"GUI"元素）
│  │ │ 💰 200万  📅 3/15  ⚠️ 超期   │  │ │
│  │ └──────────────────────────────┘  │ │
│  │ 建议：给王工发消息催技术报告...    │ │
│  └───────────────────────────────────┘ │
│                                         │
├─────────────────────────────────────────┤
│  [🎤]  输入消息...              [发送]  │  ← 输入栏：麦克风 + 文字输入
└─────────────────────────────────────────┘
```

### 7.2 消息类型

对话中的消息不全是纯文本，可以包含**轻量级内嵌卡片**：

| 类型 | 用途 | 渲染方式 |
|------|------|----------|
| **text** | 普通文本对话 | Markdown 渲染 |
| **entity_card** | 客户/商机/联系人摘要 | 紧凑卡片（名称+关键指标） |
| **action_result** | 操作结果（已创建/已修改） | 成功/失败状态 + 实体摘要 |
| **confirmation** | 等待用户确认的操作 | 操作详情 + 确认/取消按钮 |
| **quick_replies** | 建议回复选项 | 可点击的 chip 列表 |
| **chart_mini** | 简易数据可视化 | 内嵌迷你图（漏斗/趋势/占比） |
| **voice_note** | 语音消息 | 播放条 + 转写文字 |

### 7.3 响应式策略

```
手机 (< 640px):
  - 全屏对话
  - 底部输入栏固定
  - 语音按钮放大（大拇指友好）
  - 卡片铺满宽度

平板 (640px - 1024px):
  - 左侧：会话列表（可收起）
  - 右侧：对话区

桌面 (> 1024px):
  - 左侧：会话列表（固定展示）
  - 中间：对话区
  - 右侧：快速操作面板（可选，显示当前实体详情）
```

### 7.4 离线支持

```
Service Worker 策略:
  - 对话历史: Cache First (IndexedDB 存储)
  - 用户输入: 离线队列 (IndexedDB 暂存 → 联网后同步)
  - 语音输入: 本地录音 → 联网后 STT → 发送
  - 通知: Web Push (后台推送，无需 App 在前台)
```

---

## 8. 语音交互设计

### 8.1 语音输入模式

| 模式 | 触发方式 | 适用场景 |
|------|----------|----------|
| **按住说话** | 长按麦克风按钮 | 嘈杂环境、精确控制 |
| **点击切换** | 点击麦克风开/关 | 安静环境、长段语音 |
| **免唤醒（可选）** | VAD 自动检测说话 | 开车、做饭等双手不方便时 |
| **唤醒词（可选）** | "Hey Max" | 完全免触屏交互 |

### 8.2 语音 UX 细节

```
用户按住麦克风：
  → 麦克风图标变为脉动波纹动画
  → 实时显示语音识别的文字（流式）
  → 用户松开：发送
  → 用户上滑：取消

Agent 回复：
  → 自动朗读（可设置默认开/关）
  → 用户可中断朗读（点击任意位置或说"停"）
  → 朗读时高亮当前句子
```

### 8.3 语音特有能力

```
"帮我记一下，刚才跟华为张总聊了 40 分钟，他同意下周来看 demo，
 但是采购流程要走 3 个月，让我准备一份 ROI 分析。
 对了，他们技术总监李工对我们的方案有顾虑，觉得集成复杂度高。"

Agent 自动结构化：
  → 创建互动记录（客户=华为，类型=会议，时长=40min）
  → 提取关键信息：
    - 张总同意 demo（态度: supportive）
    - 采购周期 3 个月
    - 需要 ROI 分析文档
  → 创建跟进任务：准备 ROI 分析（截止：本周五）
  → 更新联系人：李工，技术总监，态度=有顾虑，顾虑=集成复杂度
  → 回复用户确认摘要
```

---

## 9. 通知与主动推送

### 9.1 推送通道

| 通道 | 技术 | 适用场景 |
|------|------|----------|
| **App 内消息** | WebSocket 实时推送 | App 在前台时 |
| **Web Push** | Web Push API + VAPID | App 在后台或关闭时 |
| **短信（可选）** | 阿里云短信 API | 紧急事项（P0 级别） |
| **企业微信/钉钉（可选）** | 对应 API | 企业内部集成 |

### 9.2 推送策略

```
通知优先级：
  P0 (紧急): 商机即将到期、客户投诉 → 即时推送 + 震动
  P1 (重要): 商机停滞、客户回复 → 即时推送
  P2 (建议): 跟进提醒、行为建议 → 汇总推送（早/晚各一次）
  P3 (参考): 行业新闻、竞品动态 → 每日摘要

防打扰：
  - 勿扰时间段（默认 22:00 - 08:00）可自定义
  - 同一事项 24 小时内最多提醒 2 次
  - 用户连续忽略 3 次 → 自动降级优先级
```

---

## 10. 安全设计

### 10.1 认证

```
SSO (OIDC/SAML) + JWT:
  - 所有用户身份由企业 IdP 管理，不提供本地注册/找回密码流程
  - Access Token: 15 分钟有效（由 SSO/网关签发）
  - Refresh Token: 7 天有效，Redis 黑名单
  - 服务端只保留最小身份映射（sso_subject、org_id、role）
```

### 10.2 多租户隔离

```
所有 DB 查询强制 org_id 过滤：
  - PostgreSQL RLS (Row Level Security) 作为最后防线
  - API 层中间件注入 org_id，业务代码无法绕过
```

### 10.3 AI 安全

```
- Agent 操作审计日志（谁在什么时候通过 AI 做了什么）
- Prompt injection 防护（用户输入消毒）
- LLM 输出检查（不泄露其他租户数据、不编造数据）
- Token 用量计量和余额控制
```

---

## 11. 部署架构

```
开发环境:
  docker-compose up
  → PostgreSQL + Redis + API Gateway + Agent Service + Notification Service

生产环境:
  Kubernetes:
  ┌─────────────────────────────────────────────────┐
  │  Ingress (Nginx) + TLS                          │
  ├─────────────────────────────────────────────────┤
  │  API Gateway (Go)        × 2-4 pods             │
  │  Agent Service (Python)  × 2-4 pods             │
  │  Notification (Go)       × 1-2 pods             │
  ├─────────────────────────────────────────────────┤
  │  PostgreSQL (阿里云 RDS)                         │
  │  Redis (阿里云 Redis)                            │
  │  OSS (文件存储)                                  │
  └─────────────────────────────────────────────────┘

  前端 PWA: CDN 静态托管（阿里云 CDN）
```

---

## 12. 开发路线图

### Phase 1：核心对话 (4 周)

- [ ] 项目脚手架（monorepo: frontend + gateway + agent + notification）
- [ ] 用户认证（SSO/OIDC 登录 + JWT 鉴权）
- [ ] 对话服务（创建会话、发消息、历史查询）
- [ ] Router Agent + Data Agent（基础 CRM 操作）
- [ ] 前端对话 UI（消息列表 + 文字输入 + 实体卡片渲染）
- [ ] WebSocket 实时通信

### Phase 2：语音 + 智能 (3 周)

- [ ] 语音输入（Web Speech API + Whisper 兜底）
- [ ] 语音输出（TTS 集成）
- [ ] Sales Agent（消息拟写、话术准备）
- [ ] Strategy Agent（商机分析、赢率预测）
- [ ] Memory Agent（对话记忆抽取和整合）

### Phase 3：主动推送 (3 周)

- [ ] Sentinel Agent（监控规则引擎）
- [ ] Web Push 通知
- [ ] Coach Agent（周报、行为分析）
- [ ] 通知偏好设置

### Phase 4：打磨 + 扩展 (2 周)

- [ ] PWA 离线支持
- [ ] 移动端语音体验优化
- [ ] 迷你图表卡片
- [ ] 性能优化（首屏 < 2s）
- [ ] 多语言支持

---

## 13. 与 SalesTouch 的关系

### 可复用的资产

| SalesTouch 组件 | TouchCLI 复用方式 |
|-----------------|-------------------|
| Max 的技能知识 | Agent prompt 中的领域知识 |
| 三层记忆模型 | Memory Agent 的衰减/整合逻辑 |
| 主动通知规则 | Sentinel Agent 的规则引擎 |
| 测试框架 Layer 2-3 | Agent 对话测试的评估方法 |
| 多租户数据模型 | 核心 CRM 表结构 |
| LLM Gateway | 多模型切换和计费逻辑 |

### 不复用的部分

| SalesTouch 组件 | 原因 |
|-----------------|------|
| Vue 3 前端 | 全部重写为 React PWA |
| Node.js 后端 | 换为 Python (Agent) + Go (Gateway) |
| MySQL 数据库 | 换为 PostgreSQL + pgvector |
| 前端实时通道 | 换为 WebSocket（客户端↔网关） |
| LLM 调用链路 | 保留 SSE（网关/Agent↔LLM Gateway） |
| 页面绑定技能系统 | 不再有"页面"概念，改为意图路由 |
| Element Plus 组件 | 不再有重 GUI，改为 TailwindCSS 极简 UI |

---

## 14. 关键设计决策记录

| 决策 | 选择 | 否决方案 | 理由 |
|------|------|----------|------|
| 跨平台方案 | PWA | React Native, Flutter, Electron | 对话 UI 极简无需原生组件；一次开发全端运行 |
| Agent 框架 | LangGraph | CrewAI, AutoGen, 自研 | 有状态编排 + 人机协作 + 持久化检查点 |
| 后端语言 | Python + Go | Node.js, Rust | Python=AI 生态最强, Go=高并发网关 |
| 数据库 | PostgreSQL | MySQL | JSONB 原生, pgvector 向量搜索, RLS 行级安全 |
| 实时通信 | 分层协议：WebSocket + SSE | Long Polling, 纯 SSE | 客户端语音/推送需双向；LLM 网关复用既有 SSE 流式接口 |
| 语音 STT | Web Speech API + Whisper | 纯 Whisper, Google STT | 浏览器原生零延迟免费，Whisper 作高精度兜底 |
| 前端框架 | React | Vue 3 | React PWA 生态更成熟，Next.js 可选 SSR |

---

> **TouchCLI 的本质：** 把 SalesTouch 的 Max Agent 从"页面副驾驶"升级为"对话主驾驶"。不是砍功能，是换交互范式——从"用户操作 GUI，AI 辅助"变成"用户说话，Agent 群自主执行"。
