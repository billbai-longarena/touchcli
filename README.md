# TouchCLI — 纯对话式 AI 销售助手

> 没有按钮、没有表单、没有仪表盘——只有对话和语音。背后是一群 AI Agent 主动为销售人员完成一切操作。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/billbai-longarena/touchcli/actions/workflows/ci.yml/badge.svg)](https://github.com/billbai-longarena/touchcli/actions)

---

## 项目简介

TouchCLI 是一个 **纯对话界面的 AI 销售助手框架**，服务 B2B 和 B2C 销售人员。用户只需说话或打字，背后的 Agent 群自动完成数据录入、客户跟进、商机管理、策略建议等一切操作。

### 核心设计原则

| # | 原则 | 含义 |
|---|------|------|
| 1 | **零学习成本** | 会说话就会用，没有菜单、导航和功能入口 |
| 2 | **Agent 先行动** | 不等用户问，主动推送任务和建议 |
| 3 | **对话即操作** | 语音/文字指令直接创建/更新数据，无需跳转表单 |
| 4 | **语音优先** | 开车、见客户时也能用 |
| 5 | **全终端一致** | 手机、平板、电脑同一对话流 |

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 18 + TypeScript + Vite + WebSocket |
| API 网关 | Go (Gin) |
| 业务后端 | Python 3.11 + FastAPI + SQLAlchemy |
| 数据库 | PostgreSQL 15 + Alembic 迁移 |
| 缓存/队列 | Redis 7 + Celery |
| AI 框架 | LangGraph + OpenAI |
| 容器化 | Docker + docker-compose + Kubernetes |

---

## 快速开始

### 前提条件

- Node.js 18+
- Python 3.11+
- Docker & docker-compose（推荐）

### 1. 克隆仓库

```bash
git clone https://github.com/billbai-longarena/touchcli.git
cd touchcli
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填写 OPENAI_API_KEY 等必要配置
```

### 3. 使用 Docker 启动（推荐）

```bash
docker-compose up -d
```

### 4. 手动启动（开发模式）

```bash
# 安装前端依赖
npm install

# 安装后端依赖
cd backend/python && pip install -r requirements.txt && cd ../..

# 运行数据库迁移
./scripts/migrate-db.sh

# 终端 1：前端
npm run dev

# 终端 2：Python 后端
cd backend/python && uvicorn main:app --reload

# 终端 3：Go 网关
cd backend/go && go run main.go
```

### 5. 访问应用

- 前端：http://localhost:3000
- API 文档：http://localhost:8080/docs

---

## 项目结构

```
touchcli/
├── frontend/          # React 前端（Vite + TypeScript）
├── backend/
│   ├── python/        # FastAPI 业务后端
│   └── go/            # Go API 网关
├── db/                # 数据库迁移与种子数据
├── k8s/               # Kubernetes 部署配置
├── scripts/           # 自动化脚本（含白蚁协议基础设施）
├── signals/           # 白蚁协议信号存储
├── docs/              # 补充文档
├── .env.example       # 环境变量模板
├── docker-compose.yml # 本地全栈编排
└── openapi.yaml       # API 规范
```

---

## 文档

| 文档 | 说明 |
|------|------|
| [DESIGN.md](DESIGN.md) | 产品定位、用户场景、技术架构、Agent 拓扑 |
| [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md) | 开发者完整上手指南 |
| [ENVIRONMENT_CONFIGURATION.md](ENVIRONMENT_CONFIGURATION.md) | 所有环境变量说明 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 部署架构与操作流程 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构详解 |
| [openapi.yaml](openapi.yaml) | REST API 完整规范 |

---

## 白蚁协议（Termite Protocol）

本项目内嵌了 **白蚁协议** ——一套多 Agent 并发协作框架，用于驱动项目持续演进。

- 协议规范：[TERMITE_PROTOCOL.md](TERMITE_PROTOCOL.md)
- 快速上手：[QUICKSTART.md](QUICKSTART.md)
- 心跳内核：[AGENTS.md](AGENTS.md)

---

## 贡献

欢迎 Issue 和 Pull Request。请先阅读 [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md) 了解开发环境配置。

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交变更：`git commit -m "feat: add your feature"`
4. 推送分支：`git push origin feature/your-feature`
5. 发起 Pull Request

---

## License

[MIT](LICENSE) © 2026 billbai-longarena
