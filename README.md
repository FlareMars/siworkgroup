# SiWorkGroup

> **Si-Worker Inside** — 统一管理、权限隔离、沙盒安全的 OpenClaw 智能体工作组平台

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## 📖 项目简介

**SiWorkGroup** 是一个面向团队的 **OpenClaw 智能体工作组管理平台**。每个 *Claw* 是一个运行在受控沙盒环境中的 AI 编码智能体实例，平台提供从生命周期管理、细粒度权限控制到实时对话的完整解决方案。

### 核心能力

| 能力 | 描述 |
|------|------|
| 🦾 **Claw 生命周期管理** | 创建、启动、暂停、销毁 OpenClaw 实例，支持模板快速克隆 |
| 🔐 **细粒度权限管理** | 基于 RBAC + 策略的多维度权限控制，精确到文件系统、网络、工具调用层级 |
| 📦 **沙盒隔离** | 每个 Claw 运行在独立的 Docker 容器沙盒中，资源配额、网络策略严格隔离 |
| 💬 **实时对话** | 通过 WebSocket 与任意 Claw 进行实时流式对话，支持多会话并发 |
| 📊 **可观测性** | 实时监控 Claw 运行状态、资源使用、操作审计日志 |
| 👥 **多用户协作** | 支持团队成员对同一 Claw 进行协作，权限按角色分配 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        SiWorkGroup Platform                      │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Frontend (Next.js 14+)                  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │   │
│  │  │  Claw    │ │Permission│ │  Chat    │ │ Dashboard  │  │   │
│  │  │ Manager  │ │ Console  │ │Interface │ │ & Monitor  │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │ REST API + WebSocket               │
│  ┌──────────────────────────┼───────────────────────────────┐   │
│  │              Backend (FastAPI + Python 3.11+)             │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │   │
│  │  │  Claw    │ │   Auth   │ │   Chat   │ │   Audit    │  │   │
│  │  │  Engine  │ │  & RBAC  │ │  Engine  │ │   Logger   │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                     │
│  ┌──────────┐  ┌────────────┼──────┐  ┌────────────────────┐   │
│  │PostgreSQL│  │   Redis    │      │  │   Docker Engine    │   │
│  │(持久化)  │  │(缓存/队列) │      │  │ ┌──────┐ ┌──────┐  │   │
│  └──────────┘  └────────────┘      │  │ │Claw-1│ │Claw-2│  │   │
│                                    │  │ │Sandbox│ │Sandbox│ │   │
│                                    │  │ └──────┘ └──────┘  │   │
│                                    │  └────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 技术栈

### 后端 (Backend)

| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.11+ | 核心运行时 |
| **FastAPI** | 0.110+ | 异步 Web 框架，REST API + WebSocket |
| **SQLAlchemy** | 2.0+ | 异步 ORM |
| **Alembic** | 最新 | 数据库迁移 |
| **PostgreSQL** | 16+ | 主数据库 |
| **Redis** | 7+ | 会话缓存、消息队列、发布/订阅 |
| **Docker SDK** | 最新 | Claw 沙盒容器管理 |
| **Pydantic** | v2 | 数据验证与序列化 |
| **JWT (python-jose)** | 最新 | 身份认证 |
| **Celery** | 5+ | 异步任务队列 |
| **Structlog** | 最新 | 结构化日志 |

### 前端 (Frontend)

| 技术 | 版本 | 用途 |
|------|------|------|
| **Next.js** | 14+ (App Router) | React 全栈框架 |
| **TypeScript** | 5.0+ | 类型安全 |
| **Tailwind CSS** | 3.4+ | 原子化 CSS |
| **shadcn/ui** | 最新 | 现代化组件库 |
| **Zustand** | 最新 | 轻量全局状态管理 |
| **TanStack Query** | v5 | 服务端状态管理与缓存 |
| **Socket.IO Client** | 4+ | WebSocket 实时通信 |
| **Framer Motion** | 最新 | 动画与过渡效果 |
| **Monaco Editor** | 最新 | 内嵌代码编辑器 |
| **Recharts** | 最新 | 数据可视化 |

---

## ✨ 功能详细说明

### 1. Claw 生命周期管理

- **创建 Claw**：通过 Web 界面或 API 创建新的 OpenClaw 实例，支持配置模型、工具集、工作目录、资源配额
- **模板克隆**：基于现有 Claw 配置快速创建副本
- **状态管理**：启动 / 暂停 / 恢复 / 销毁，实时状态面板
- **删除 Claw**：级联清理容器、会话、文件系统，支持数据导出后删除

### 2. 权限管理 (RBAC + Policy)

```
权限层级
├── 平台级
│   ├── 超级管理员 (Super Admin)
│   └── 普通用户 (User)
│
├── Claw 级
│   ├── 所有者 (Owner)     — 全部操作权限
│   ├── 协作者 (Collaborator) — 对话 + 查看
│   └── 观察者 (Viewer)    — 只读审计日志
│
└── 资源策略
    ├── 文件系统白名单/黑名单路径
    ├── 网络出口策略（域名白名单）
    ├── 可用工具集（工具级别开关）
    └── 执行命令黑名单正则
```

- **操作审计**：所有权限变更、Claw 操作、对话内容均写入不可篡改的审计日志
- **API Key 管理**：为每个 Claw 生成独立 API Key，支持作用域限制与过期设置

### 3. 沙盒管理

每个 Claw 运行在独立的 **Docker 容器**中，提供以下隔离保障：

| 隔离维度 | 实现方式 |
|----------|----------|
| **进程隔离** | Linux PID Namespace |
| **文件系统隔离** | Overlay FS + 挂载点白名单 |
| **网络隔离** | 独立 Docker 网络，出口规则由 `iptables` 策略控制 |
| **资源配额** | cgroups v2：CPU、内存、磁盘 I/O 限制 |
| **系统调用过滤** | Seccomp Profile 限制危险系统调用 |

沙盒配置示例：
```json
{
  "sandbox": {
    "cpu_limit": "2.0",
    "memory_limit": "4g",
    "disk_quota": "20g",
    "network_policy": {
      "egress_whitelist": ["api.openai.com", "github.com"],
      "allow_localhost": true
    },
    "fs_policy": {
      "writable_paths": ["/workspace"],
      "readonly_paths": ["/etc", "/usr"],
      "blocked_paths": ["/proc/sys"]
    }
  }
}
```

### 4. 实时对话

- **流式响应**：基于 WebSocket + Server-Sent Events，Claw 的思考过程与输出实时流式渲染
- **多会话管理**：一个 Claw 支持多个并发会话，会话间上下文独立
- **历史记录**：完整对话历史持久化，支持搜索与导出
- **工具调用可视化**：Claw 调用工具时，前端实时展示调用详情、入参与返回结果
- **文件拖拽**：支持向 Claw 拖拽文件作为上下文输入
- **Markdown 渲染**：消息内容支持完整 Markdown + 代码高亮

---

## 📁 项目结构

```
siworkgroup/
├── backend/                    # Python 后端
│   ├── app/
│   │   ├── api/                # API 路由层
│   │   │   ├── v1/
│   │   │   │   ├── claws.py    # Claw CRUD 接口
│   │   │   │   ├── auth.py     # 认证接口
│   │   │   │   ├── permissions.py  # 权限管理接口
│   │   │   │   ├── sandbox.py  # 沙盒配置接口
│   │   │   │   └── chat.py     # 对话接口
│   │   │   └── ws/
│   │   │       └── chat_ws.py  # WebSocket 对话端点
│   │   ├── core/               # 核心配置
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── deps.py
│   │   ├── models/             # 数据库模型
│   │   │   ├── claw.py
│   │   │   ├── user.py
│   │   │   ├── permission.py
│   │   │   ├── session.py
│   │   │   └── audit.py
│   │   ├── services/           # 业务逻辑层
│   │   │   ├── claw_service.py
│   │   │   ├── sandbox_service.py
│   │   │   ├── permission_service.py
│   │   │   └── chat_service.py
│   │   ├── sandbox/            # 沙盒引擎
│   │   │   ├── docker_manager.py
│   │   │   ├── network_policy.py
│   │   │   └── seccomp_profile.json
│   │   └── main.py
│   ├── alembic/                # 数据库迁移
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/                   # Next.js 前端
│   ├── app/
│   │   ├── (auth)/
│   │   │   └── login/
│   │   ├── dashboard/
│   │   ├── claws/
│   │   │   ├── [id]/
│   │   │   │   ├── chat/       # 对话界面
│   │   │   │   ├── permissions/# 权限管理
│   │   │   │   └── sandbox/    # 沙盒配置
│   │   │   └── new/            # 创建 Claw
│   │   └── layout.tsx
│   ├── components/
│   │   ├── ui/                 # shadcn/ui 基础组件
│   │   ├── claw/               # Claw 相关组件
│   │   ├── chat/               # 对话相关组件
│   │   └── permission/         # 权限相关组件
│   ├── lib/
│   │   ├── api/                # API 客户端
│   │   ├── store/              # Zustand 状态
│   │   └── socket/             # WebSocket 客户端
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml          # 本地开发编排
├── docker-compose.prod.yml     # 生产部署编排
├── .env.example
└── README.md
```

---

## 🛠️ 开发环境准备

> 本节列出运行本项目所需的全部工具及安装命令，适用于本地开发（非 Docker 模式）。

### 工具清单

| 工具 | 最低版本 | 用途 |
|------|----------|------|
| **Git** | 2.x | 代码版本控制 |
| **Python** | 3.11 | 后端运行时 |
| **pip / venv** | 随 Python 3.11 自带 | 虚拟环境与包管理 |
| **Node.js** | 20 LTS | 前端运行时 |
| **npm** | 10+（随 Node.js 自带）| 前端包管理 |
| **PostgreSQL** | 16 | 主数据库 |
| **Redis** | 7 | 缓存 / 任务队列 |
| **Docker** | 24+（可选）| 沙盒容器 & 一键启动 |
| **Docker Compose** | v2（可选）| 服务编排 |
| **Homebrew** | 最新（macOS）| macOS 包管理器 |

---

### macOS 安装命令

#### 1. Homebrew（如未安装）

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. Git

```bash
brew install git
git --version   # 验证
```

#### 3. Python 3.11+

```bash
brew install python@3.11
python3.11 --version   # 验证：Python 3.11.x
```

> 也可使用 [pyenv](https://github.com/pyenv/pyenv) 管理多版本：
> ```bash
> brew install pyenv
> pyenv install 3.11
> pyenv global 3.11
> ```

#### 4. Node.js 20 LTS

```bash
brew install node@20
echo 'export PATH="$(brew --prefix)/opt/node@20/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
node --version   # 验证：v20.x.x
npm --version    # 验证：10.x.x
```

#### 5. PostgreSQL 16

```bash
brew install postgresql@16
echo 'export PATH="$(brew --prefix)/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
brew services start postgresql@16
pg_isready   # 验证：localhost:5432 - accepting connections
```

#### 6. Redis 7

```bash
brew install redis
brew services start redis
redis-cli ping   # 验证：PONG
```

#### 7. Docker Desktop（可选，用于沙盒或一键启动）

从 [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/) 下载安装，或：

```bash
brew install --cask docker
docker --version          # 验证
docker compose version    # 验证
```

---

### Linux（Ubuntu/Debian）安装命令

#### Git

```bash
sudo apt update && sudo apt install -y git
```

#### Python 3.11+

```bash
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

#### Node.js 20 LTS

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

#### PostgreSQL 16

```bash
sudo apt install -y postgresql-16 postgresql-client-16
sudo systemctl enable --now postgresql
```

#### Redis 7

```bash
sudo apt install -y redis-server
sudo systemctl enable --now redis-server
```

#### Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # 无需 sudo 运行 docker
```

---

### 一键安装（macOS，推荐）

项目提供了自动化脚本，会完成上述所有安装并初始化数据库：

```bash
bash scripts/local-setup.sh
```

脚本执行内容：
1. 通过 Homebrew 安装 PostgreSQL 16、Redis、Node.js 20
2. 启动 PostgreSQL 和 Redis 服务
3. 创建数据库用户 `siuser` 和数据库 `siworkgroup`
4. 创建 Python 虚拟环境并安装后端依赖
5. 执行 Alembic 数据库迁移
6. 安装前端 npm 依赖
7. 从 `.env.example` 生成 `.env`

---

## 🚀 快速开始

### 前置要求

- Docker 24+ & Docker Compose v2
- Python 3.11+（本地开发）
- Node.js 20 LTS+（本地开发）
- Git

### 1. 克隆项目

```bash
git clone https://github.com/FlareMars/siworkgroup.git
cd siworkgroup
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写必要配置
```

`.env` 主要配置项：

```dotenv
# 数据库
DATABASE_URL=postgresql+asyncpg://siuser:sipass@localhost:5432/siworkgroup

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# OpenAI / 模型服务
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1

# Docker
DOCKER_HOST=unix:///var/run/docker.sock
SANDBOX_IMAGE=siworkgroup/claw-sandbox:latest
```

### 3. 一键启动（Docker Compose）

```bash
docker compose up -d
```

服务启动后访问：

| 服务 | 地址 |
|------|------|
| 前端 Web | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

### 4. 本地开发模式

**后端：**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端：**

```bash
cd frontend
npm install
npm run dev
```

---

## 📡 API 概览

### 认证

```
POST   /api/v1/auth/register     注册
POST   /api/v1/auth/login        登录，返回 JWT
POST   /api/v1/auth/refresh      刷新 Token
POST   /api/v1/auth/logout       注销
```

### Claw 管理

```
GET    /api/v1/claws             获取 Claw 列表
POST   /api/v1/claws             创建新 Claw
GET    /api/v1/claws/{id}        获取 Claw 详情
PATCH  /api/v1/claws/{id}        更新 Claw 配置
DELETE /api/v1/claws/{id}        删除 Claw
POST   /api/v1/claws/{id}/start  启动 Claw
POST   /api/v1/claws/{id}/stop   停止 Claw
GET    /api/v1/claws/{id}/stats  获取资源统计
```

### 权限管理

```
GET    /api/v1/claws/{id}/permissions          获取权限列表
POST   /api/v1/claws/{id}/permissions          添加成员权限
PATCH  /api/v1/claws/{id}/permissions/{uid}    修改成员角色
DELETE /api/v1/claws/{id}/permissions/{uid}    移除成员
GET    /api/v1/claws/{id}/policies             获取资源策略
PUT    /api/v1/claws/{id}/policies             更新资源策略
GET    /api/v1/claws/{id}/audit-logs           获取审计日志
```

### 沙盒

```
GET    /api/v1/claws/{id}/sandbox              获取沙盒配置
PUT    /api/v1/claws/{id}/sandbox              更新沙盒配置
POST   /api/v1/claws/{id}/sandbox/reset        重置沙盒环境
GET    /api/v1/claws/{id}/sandbox/filesystem   浏览沙盒文件系统
```

### 对话

```
GET    /api/v1/claws/{id}/sessions             获取会话列表
POST   /api/v1/claws/{id}/sessions             创建新会话
GET    /api/v1/claws/{id}/sessions/{sid}/messages  获取消息历史
DELETE /api/v1/claws/{id}/sessions/{sid}       删除会话

# WebSocket 实时对话
WS     /ws/claws/{id}/sessions/{sid}/chat      实时对话端点
```

---

## 🔒 安全设计

1. **最小权限原则**：每个 Claw 默认无任何外部访问权限，需显式授权
2. **沙盒逃逸防护**：Seccomp + AppArmor Profile 限制危险系统调用，禁止 `ptrace`、`mount` 等操作
3. **网络隔离**：容器默认无网络，按白名单策略开放出口
4. **审计不可篡改**：审计日志写入后追加不可修改（PostgreSQL IMMUTABLE 策略）
5. **密钥轮换**：支持 API Key 零停机轮换
6. **输入校验**：所有 API 输入经 Pydantic v2 严格校验，防止注入

---

## 🧪 测试

```bash
# 后端单元测试 + 集成测试
cd backend
pytest --cov=app --cov-report=html

# 前端类型检查
cd frontend
npm run type-check

# 前端测试
npm run test
```

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feat/your-feature`
3. 提交变更：`git commit -m 'feat: add some feature'`（遵循 [Conventional Commits](https://www.conventionalcommits.org/)）
4. 推送分支：`git push origin feat/your-feature`
5. 提交 Pull Request

---

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

---

<div align="center">
  <sub>Built with ❤️ by FlareMars · Powered by OpenClaw</sub>
</div>