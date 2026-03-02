# TouchCLI vs SalesTouch 原版功能对比审计

**审计日期**: 2026-03-02
**原项目路径**: `/Users/bingbingbai/Desktop/salesTouch/`
**审计目的**: 对比原版 SalesTouch 已实现功能，审计 TouchCLI 设计中的遗漏

---

## 一、原版 SalesTouch 功能清单（AIsalesAssistHome.vue 注册）

### 已上线功能（5 个）

| # | 功能模块 | 路由 | 用户角色 | 核心能力 |
|---|---------|------|---------|---------|
| 1 | **产品信息录入** | /products | 产品部/市场部 | 产品 CRUD、PDF/媒体上传、F&B（特性与利益）AI 分析生成 |
| 2 | **产品信息浏览** | /browse | 销售 | 产品库只读浏览、查看 F&B 分析、查看文档/媒体 |
| 3 | **客户和商机** | /customers | 销售 | CRM 可视化画布、商机管道、联系人管理、互动记录、AI 对话助手 |
| 4 | **SPIN 拜访计划** | /spin-call-planner | 销售 | AI 生成 SPIN 方法论拜访计划（流式输出） |
| 5 | **销售方案生成** | /scheme-generator | 销售 | AI 生成定制化销售方案/提案（可选风格/配色/Logo） |

### 规划中功能（3 个）

| # | 功能模块 | 核心能力 |
|---|---------|---------|
| 6 | **讲师简历管理** | 管理和生成专业讲师简历 |
| 7 | **AI 演练** | 模拟真实销售场景，AI 对练（Role-play） |
| 8 | **管理者视图** | 团队销售数据、业绩分析 |

---

## 二、原版核心 AI 能力详解

### 2.1 Agent Tool Calling（9 个工具）

原版使用 Claude function calling，定义了 9 个 CRM 操作工具：

| 工具名 | 用途 | 参数 |
|--------|------|------|
| `update_customer_name` | 修改客户公司名称 | customerId, companyName |
| `update_opportunity_fields` | 更新商机字段 | opportunityId, productId, amount, department, expectedCloseDate |
| `update_contact_fields` | 更新联系人信息 | contactId, name, position, favorability(0-100), orgNeeds, personalNeeds |
| `create_opportunity` | 创建商机 | customerId, amount, department, productId, expectedCloseDate |
| `create_contact` | 创建联系人 | customerId, opportunityId, name, position, favorability, orgNeeds, personalNeeds |
| `create_interaction` | 记录互动 | contactId, interactionType(电话/邮件/会议/拜访/其他), content, interactionDate |
| `ask_user_choice` | 向用户提选择题 | question, options[] |
| `provide_sales_advice` | 生成销售建议 | focusArea(整体分析/优先级/风险识别/下一步行动) |
| `recommend_visit_plan` | 生成拜访计划 | contactId |

**关键设计模式**：
- Max iteration = 6（防止无限循环）
- Context injection：自动注入当前客户 ID
- Tool result 返回 entity type + updated fields（前端可据此刷新 UI）

### 2.2 F&B（Features & Benefits）分析

| 维度 | 说明 |
|------|------|
| 输入 | 产品上传的 PDF 文档 |
| 处理 | LLM 分析文档，提取产品特性（Feature）和客户利益（Benefit） |
| 输出 | 结构化的 F&B 分析文本，可编辑保存 |
| 用途 | 作为 SPIN 计划和销售方案的输入上下文 |
| 超时 | 120 秒 |

### 2.3 SPIN 拜访计划生成

| 维度 | 说明 |
|------|------|
| 输入模式 | 数据库模式（选客户/联系人/产品）或手动模式（输入公司+角色） |
| 上下文 | F&B 分析 + 联系人职位 + 拜访目标（承诺目标） |
| 输出 | 流式生成的 SPIN 计划（Situation/Problem/Implication/Need-payoff 四阶段提问策略） |
| 额外需求 | 用户可自定义生成指令 |

### 2.4 销售方案/提案生成

| 维度 | 说明 |
|------|------|
| 输入模式 | 数据库模式（商机+产品）或文本模式（自由输入背景信息） |
| 样式 | 3 种模板：Apple 风、商务风、国央企风 |
| 配色 | 预设色系（大地色、商务色）或自定义 4 色 |
| Logo | 支持 PNG 上传 |
| 上下文 | F&B 分析 + 商机数据 + 联系人决策链 |
| 输出 | 流式生成的完整销售提案 |

### 2.5 CRM 可视化画布

| 维度 | 说明 |
|------|------|
| 技术 | SVG 渲染，非传统表格 |
| 布局 | 中心客户圆 → 放射状商机圆（大小=金额，颜色=阶段） |
| 交互 | 点击编辑、拖拽定位、hover 效果 |
| 视图切换 | 商机视图 ↔ 联系人视图 |
| 表格备选 | CustomerTableView 提供传统表格视图 |

### 2.6 联系人深度模型

原版联系人字段远比 TouchCLI 设计丰富：

| 字段 | 说明 | TouchCLI DESIGN.md |
|------|------|-------------------|
| name | 姓名 | ✅ 有 |
| position | 职位 | ✅ 有 (title) |
| **favorability** | 好感度 0-100 | ❌ 缺失（只有 attitude: supportive/neutral/negative） |
| **orgNeeds** | 组织需求 | ❌ 缺失 |
| **personalNeeds** | 个人需求 | ❌ 缺失 |
| interactions[] | 互动历史 | ✅ 有（interactions 表） |

### 2.7 Case Study 系统（案例学习）

原版有完整的案例学习子系统（useCaseAssist.ts, 733 行）：

| 子功能 | 说明 |
|--------|------|
| 智能案例阅读 | 从 PDF 自动生成交互式故事章节、测验、分支叙事 |
| 思维导图 | 生成层次化概念图（背景→问题→利益相关方→方案→成果→启示） |
| 测验生成 | 从案例材料自动生成可定制的测试题 |
| 剧本生成 | SSE 流式创建音频叙述脚本 |
| 音频合成 | TTS 将脚本转为语音（10 分钟超时） |

---

## 三、差距分析：原版有但 TouchCLI 设计遗漏的功能

### 3.1 完全遗漏（DESIGN.md 未提及）

| 遗漏功能 | 原版实现 | 对 TouchCLI 的意义 | 优先级 |
|----------|---------|-------------------|--------|
| **产品知识库** | products 表 + PDF/媒体上传 + F&B 分析 | 🔴 **核心**：Agent 需要产品知识才能回答产品相关问题、生成方案 | P1 |
| **F&B 分析引擎** | LLM 分析产品文档 → 结构化特性/利益 | 🔴 **核心**：SPIN 计划和方案生成的基础数据 | P1 |
| **SPIN 拜访计划** | 流式生成 SPIN 方法论拜访策略 | 🟠 **重要**：销售人员的高频使用场景 | P1 |
| **销售方案/提案生成** | 多模板 + 配色 + Logo + 流式生成 | 🟠 **重要**：直接产出物，对成交有直接影响 | P1 |
| **AI 演练/Role-play** | 模拟客户进行对话练习 | 🟡 **差异化**：Sales Agent 的 role_play 只是一行描述 | P2 |
| **管理者视图** | 团队数据、业绩分析 | 🟡 **差异化**：B2B 场景下管理层需求 | P2 |
| **案例学习系统** | 案例阅读/思维导图/测验/音频 | ⚪ **增值**：销售培训场景，非核心 CRM 功能 | P3 |

### 3.2 设计有但字段缺失

| 模块 | 缺失字段 | 原版实现 | 建议 |
|------|---------|---------|------|
| **contacts** | favorability (0-100) | 好感度滑块 | 补充到 contacts 表设计 |
| **contacts** | orgNeeds | 组织需求文本 | 补充到 contacts 表设计 |
| **contacts** | personalNeeds | 个人需求文本 | 补充到 contacts 表设计 |
| **products** | 整张表 | products + files + F&B | 新增 products 实体到数据模型 |

### 3.3 设计有但实现参考缺失

| 功能 | DESIGN.md 描述 | 原版提供的参考 |
|------|---------------|---------------|
| Agent 工具调用 | 5.2 节各 Agent 工具列表 | agentTools.ts: 9 个具体工具定义 + 参数 schema + 执行逻辑 |
| 人机协作确认 | 5.4 节 L0-L4 操作分级 | ask_user_choice 工具 + 前端 options 渲染 |
| Sales Agent role_play | 5.2 节一行描述 | 原版 "AI 演练" 规划为独立模块 |
| Strategy Agent | 5.2 节工具列表 | provide_sales_advice 工具 + focusArea 参数 |

---

## 四、补充设计建议

### 4.1 产品知识库（新增实体）

TouchCLI 的对话式交互**必须**有产品知识作为支撑。建议新增：

```sql
-- 产品表
products (
  id UUID PRIMARY KEY,
  org_id UUID NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  category TEXT,           -- 产品分类
  tags TEXT[],
  extra JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 产品文档表
product_documents (
  id UUID PRIMARY KEY,
  product_id UUID NOT NULL,
  filename TEXT NOT NULL,
  original_name TEXT NOT NULL,
  file_path TEXT NOT NULL,  -- S3/OSS 路径
  file_size BIGINT,
  file_type TEXT,           -- pdf/image/video/audio
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- F&B 分析结果表
product_fab_analyses (
  id UUID PRIMARY KEY,
  product_id UUID NOT NULL,
  fab_content TEXT NOT NULL,   -- LLM 生成的特性/利益分析
  embedding VECTOR(1536),      -- 用于语义搜索
  prompt TEXT,                 -- 生成时使用的 prompt
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.2 Contact 模型增强

```sql
-- 在现有 contacts 设计基础上增加：
ALTER TABLE contacts ADD COLUMN favorability INT DEFAULT 50 CHECK (favorability BETWEEN 0 AND 100);
ALTER TABLE contacts ADD COLUMN org_needs TEXT;       -- 组织需求
ALTER TABLE contacts ADD COLUMN personal_needs TEXT;  -- 个人需求
```

### 4.3 Agent 工具定义参考

TouchCLI 的 Agent 应参考原版 9 个工具定义，在 LangGraph 中实现为 tool nodes：

**CRM 操作工具（Data Agent）**：
- `manage_customer` → 参考 update_customer_name
- `manage_opportunity` → 参考 update_opportunity_fields + create_opportunity
- `manage_contact` → 参考 update_contact_fields + create_contact（含 favorability/needs）
- `log_interaction` → 参考 create_interaction（含 interactionType 枚举）

**交互工具（Router Agent）**：
- `ask_user_choice` → 直接复用（对应 S-011 人机协作）

**分析工具（Strategy Agent）**：
- `provide_sales_advice` → 参考 focusArea 参数（整体分析/优先级/风险/下一步）
- `recommend_visit_plan` → 参考联系人 + 商机 + 产品上下文拼装

**生成工具（Sales Agent，新增）**：
- `generate_spin_plan` → SPIN 方法论拜访计划
- `generate_proposal` → 销售方案/提案生成
- `generate_fab_analysis` → F&B 分析生成

### 4.4 TouchCLI 中的对话式实现方式

原版这些功能是独立页面（GUI），TouchCLI 应转化为**对话式触发**：

| 原版 GUI | TouchCLI 对话触发 | Agent |
|---------|-------------------|-------|
| 产品录入页面 | "上传华为云存储的产品手册" → Agent 引导上传流程 | Data Agent |
| F&B 分析按钮 | "分析一下华为云存储的产品特性" → Agent 调用 F&B 生成 | Data Agent |
| SPIN 计划页面 | "帮我准备跟华为张总的拜访计划" → Agent 生成 SPIN 计划 | Sales Agent |
| 方案生成页面 | "帮我给华为写一个方案，用商务风格" → Agent 生成提案 | Sales Agent |
| AI 演练页面 | "模拟华为的采购经理，跟我练一下" → Agent 进入 role-play | Sales Agent |
| 管理者视图 | "看一下本周团队的销售数据" → Agent 查询汇总 | Strategy Agent |

---

## 五、新增信号分配

| 信号 | 标题 | 权重 | 优先级 | 依赖 |
|------|------|------|--------|------|
| **S-019** | 产品知识库 + 文档管理 + F&B 分析引擎 | 65 | P1 | S-007 |
| **S-020** | SPIN 拜访计划生成（Sales Agent 新工具） | 45 | P1 | S-007, S-019 |
| **S-021** | 销售方案/提案生成器（多模板 + 流式输出） | 42 | P1 | S-007, S-019 |
| **S-022** | AI 演练/Role-play 模拟（销售场景对练） | 28 | P2 | S-007 |
| **S-023** | 管理者视图（团队数据仪表盘 + 业绩分析） | 22 | P3 | S-009 |

同时更新：
- **S-009** 补充：contacts 增加 favorability/orgNeeds/personalNeeds；新增 products 相关表
- **S-007** 补充：Agent 工具定义参考原版 agentTools.ts 的 9 个工具 schema

---

*审计完成。5 个新信号 + 2 个信号更新，覆盖原版所有已上线 + 规划中功能。*
