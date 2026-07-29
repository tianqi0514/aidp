# AIDP 开发与架构说明

## 1. 技术栈

- 前端：Vue 3、TypeScript、Vite、Pinia、Vue Router、Element Plus。
- 后端：Python 3.12、FastAPI、Pydantic、SQLAlchemy 2、Alembic。
- 数据库：PostgreSQL 16；轻量检索阶段使用 pgvector。
- 测试：pytest、FastAPI TestClient、Vitest、Vue Test Utils；真实 PostgreSQL 连接器集成测试。
- 部署：Docker Compose；后续 Enterprise Profile 增加 Helm/Kubernetes。

## 2. 仓库结构

```text
aidp/
├── apps/
│   ├── server/
│   │   ├── aidp/core/                # 配置、数据库、错误和共享 schema
│   │   ├── aidp/modules/             # 模块化单体领域模块
│   │   ├── migrations/               # Alembic 迁移
│   │   └── tests/                    # 单元、API、契约和集成测试
│   └── web/
│       ├── src/api/                   # 类型与 API Client
│       ├── src/stores/                # Pinia 状态
│       └── src/views/                 # 与后端模块成对交付的页面
├── docs/
├── docker-compose.yml
└── Makefile
```

## 3. 模块交付顺序

| 顺序 | 模块 | 状态 | 依赖原因 |
| --- | --- | --- | --- |
| 1 | 工程底座、项目、成员、Secret | 已实现首个切片 | 形成租户、权限和凭证边界 |
| 2 | Connector、Catalog、连接测试、资源发现 | PostgreSQL 纵向切片已实现 | 后续对象、指标和知识都引用 DataResource |
| 3 | 知识网络、对象类、关系类、行动类 | 首个纵向切片已实现 | Agent 和指标的共同语义底座 |
| 4 | 文档、Document IR、结构化 Case、多轮确认 | 待开发 | 可复用对象模型和 Evidence 契约 |
| 5 | 知识库、指标、规则 | 待开发 | 依赖数据资源、对象和文档 |
| 6 | Skills、MCP、Tools、AgentManifest | 待开发 | 在统一 Capability Runtime 上组装能力 |
| 7 | 内置 Agent、评测、发布与企业运维 | 待开发 | 调用前述稳定版本化资源 |

“已实现首个切片”表示该模块已经形成可运行的前后端、数据库迁移、Agent 能力和测试，不表示 PRD 中该模块的全部高级功能已经完成。后续迭代在同一模块内继续补齐连接器类型、调度、版本、权限和治理能力。

## 4. Agent 可调用能力契约

后台业务能力不能只写在 FastAPI Router 中。每个操作必须遵循以下路径：

```text
Vue / REST API ─┐
                ├─> Application Service ─> Domain Model / Provider
Built-in Agent ─┘               └────────> Audit Event
```

一个模块的写操作只有同时满足以下条件才允许合并：

1. 业务逻辑位于 Application Service，Router 只负责 HTTP 输入输出。
2. 在 `modules/capabilities/definitions.py` 注册稳定能力名、模块、说明和风险级别。
3. 输入和输出均使用 Pydantic 模型，Capability 目录自动发布 JSON Schema。
4. `read` 能力可以直接执行；`write` 与 `high` 能力必须先 preview，再显式确认。
5. 每次执行写入 `capability_invocations`，保存调用者、脱敏输入、输出、状态和错误。
6. 非幂等能力必须声明 `idempotent=false`；后续任务编排器为其生成幂等键。
7. API 测试和 Capability 测试必须调用同一 Service，防止两套逻辑漂移。

当前目录接口：

- `GET /api/v1/agent/capabilities`：列出能力和输入/输出 schema。
- `POST /api/v1/agent/capabilities/validate-plan`：在执行前校验多步骤计划、参数和确认要求。
- `POST /api/v1/agent/capabilities/{name}:invoke`：preview 或受控执行能力。

当前注册能力覆盖项目创建、Catalog 创建/测试/发现，以及知识网络、对象、关系、行动、全网校验和发布。文档、知识、指标、规则、Skills、MCP 和 Agent 模块必须沿用同一契约。

## 5. 开发命令

后端：

```bash
cd apps/server
uv sync
uv run alembic upgrade head
uv run uvicorn aidp.main:app --reload
```

前端：

```bash
cd apps/web
pnpm install
pnpm dev
```

完整检查：

```bash
make lint
make test
make test-integration
make build
```

`make test-integration` 会创建隔离的 PostgreSQL Compose 项目，运行真实连接/发现测试，最后删除该测试容器、网络和数据卷。

## 6. 数据库迁移要求

- 只允许通过 Alembic 修改正式数据库结构。
- 每个迁移必须在 PostgreSQL 上验证 upgrade、downgrade、再次 upgrade。
- 不可逆的数据迁移必须在文件头说明恢复方案，不能提供虚假的 downgrade。
- 迁移与领域代码在同一提交内评审。
- 测试可使用 SQLite 加速领域/API 测试，但 Connector、方言、迁移和事务语义必须在 PostgreSQL 上复测。

## 7. 模块完成定义

- 后端 model/schema/service/router/capability/audit 完整；
- Vue 页面可创建、查看、校验和处理错误；
- PostgreSQL 迁移可正向和回退；
- 单元、API、权限、失败路径、Capability 和真实数据库测试通过；
- OpenAPI、操作手册和本文件同步更新；
- `ruff`、`vue-tsc`、Vitest 与生产构建全部通过。
