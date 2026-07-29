# IDP 能力对照审计

| 文档项 | 内容 |
| --- | --- |
| 审计目标 | 确认 AIDP 完整产品范围覆盖 IDP 的关键数据、业务模型和 Agent 配置能力 |
| 参考仓库 | `kweaver-ai/kweaver-core` |
| 参考版本 | `b9b35fb245c31660127114c883e91165b42dc8f0` |
| AIDP PRD | V0.3 |
| 审计日期 | 2026-07-29 |

## 1. 审计结论

AIDP V0.3 不再以 MVP 或功能删减定义范围。IDP 中与数据接入、知识网络、业务对象、指标、Agent 数据源与能力绑定相关的核心能力均已进入 AIDP 完整产品范围。AIDP 的差异主要位于实现与部署：默认使用模块化单体和 PostgreSQL，企业规模通过 Connector/Task/Storage/Search/Graph/Runtime Provider 扩展，不照搬 IDP 的服务数量和固定中间件拓扑。

审计状态含义：

- **覆盖**：PRD 已有对应领域对象、生命周期、权限/API 或验收要求。
- **扩展**：除覆盖 IDP 语义外，AIDP 还增加文档结构化、多轮确认、Text-to-Metric 或知识库能力。
- **实现差异**：产品能力覆盖，但默认存储、服务拆分或运行组件不同。

## 2. 数据连接与资源（IDP VEGA）

| IDP 能力 | 源码参考 | AIDP 设计 | 状态 |
| --- | --- | --- | --- |
| Connector Type | `adp/vega/vega-backend/server/interfaces/connector_type.go` | ConnectorType 声明 local/remote、资源类别、配置 schema、版本和操作；提供 SDK 与契约测试 | 覆盖 |
| Connector/Catalog | `interfaces/connector.go`、`interfaces/catalog.go` | Catalog 统一数据库、文件、API、Topic、Index、Metric 连接，使用 Secret、TLS/SSH、权限、健康和审计 | 扩展 |
| 连接测试与健康 | `interfaces/catalog.go` | 保存前测试；healthy/degraded/unhealthy/offline/unchecked；定期检查、延迟和告警 | 覆盖 |
| 手工发现任务 | `interfaces/discover_task.go` | 按 database/schema/模式/类别扫描，展示状态、进度、消息、统计和失败重试 | 覆盖 |
| 定时发现 | `interfaces/discover_schedule.go` | Cron、起止时间、启停和 full-sync/create-only/cleanup-only 策略 | 覆盖 |
| 资源差异 | `interfaces/discover_task.go` | new/unchanged/updated/restored/missing；missing 先转 stale，不自动删除 | 覆盖 |
| 资源与字段元数据 | `interfaces/resource.go` | database/schema/table/view、字段类型/精度/默认值、主键、索引、外键、字符集、扩展元数据 | 覆盖 |
| 资源类别 | `interfaces/resource.go` | table、file、fileset、API、metric、topic、index、logicview、dataset | 覆盖 |
| 检索字段特征 | `interfaces/resource.go` | keyword、full-text、vector 特征进入资源字段配置 | 覆盖 |
| 逻辑视图 | `interfaces/logic_view_service.go` | derived/composite；resource/join/union/SQL/output；循环、类型与权限校验 | 覆盖 |
| 数据构建 | `interfaces/build_task.go` | batch/streaming、full/incremental、唯一/增量键、Embedding、进度、重试和位点 | 扩展 |
| 统一查询 | `interfaces/query.go`、`interfaces/resource_data.go` | 标准/流式查询、游标、取消、过滤/排序/聚合/group/having、AST 安全、配额与审计 | 扩展 |

PRD 对应章节：9.5、11.1—11.6、12、13、14、15、17、18。操作手册对应章节：6—9。

## 3. 知识网络与业务对象模型（IDP BKN）

| IDP 能力 | 源码参考 | AIDP 设计 | 状态 |
| --- | --- | --- | --- |
| 知识网络 | `adp/bkn/bkn-backend/server/interfaces/knowledge_network.go` 及相关 service | 网络、概念组、分支、基线、草稿/审批/发布、导入导出和全网校验 | 扩展 |
| 对象类 | `adp/bkn/bkn-backend/server/interfaces/object_type.go` | ID/名称/来源、数据属性、逻辑属性、主键、显示键、增量键、状态、预览与版本 | 覆盖 |
| 属性类型 | `object_type.go` | 数值、字符串/文本、日期时间、布尔、二进制、JSON、向量、点/空间形状、IP | 覆盖 |
| 数据源映射 | `object_type.go` | 对象类绑定 DataResource/LogicView/Dataset；属性保存源字段映射，不保存连接凭证 | 扩展 |
| 属性索引 | `object_type.go` | keyword/full-text/vector 及参数配置 | 覆盖 |
| 逻辑属性 | `object_type.go` | 绑定指标/算子、参数、分析维度与缓存策略 | 覆盖 |
| 关系类 | `adp/bkn/bkn-backend/server/interfaces/relation_type.go` | 源/目标对象、方向、基数、直接映射、数据视图映射、过滤交叉连接和关系属性 | 扩展 |
| 行动类 | `adp/bkn/bkn-backend/server/interfaces/action_type.go` | add/modify/delete、意图、条件、影响契约、参数、Tool/MCP、权限、确认、定时和补偿 | 扩展 |
| 指标 | `adp/bkn/bkn-backend/server/interfaces/metric.go` | 原子/派生/复合等类型、对象/子图范围、聚合、条件、分组、Having、时间和分析维度 | 扩展 |
| 模型验证 | BKN validation/import/export API | 对象、关系、行动、指标、映射、权限和依赖的单项/批量全网校验 | 覆盖 |
| 模型实例 | BKN object query/runtime APIs | 查询、关系路径、CRUD、批量导入、去重合并、字段证据、历史、行列字段和行动权限 | 扩展 |

PRD 对应章节：9.4、9.7、12、13、14、17、18。操作手册对应章节：8、9、13—17。

## 4. Agent 配置与能力绑定（IDP Decision Agent）

| IDP 能力 | 源码参考 | AIDP 设计 | 状态 |
| --- | --- | --- | --- |
| Agent 总配置 | `decision-agent/.../daconfvalobj/config.go` | AgentManifest 统一 Runtime、模型、数据、能力、输出、记忆、预算和模式 | 覆盖 |
| 数据源绑定 | `daconfvalobj/datasourcevalobj/` | 绑定数据资源/数据集、知识网络及对象范围、文档、知识库、指标与规则的固定版本 | 扩展 |
| Tool 绑定 | `daconfvalobj/skillvalobj/` | 版本、输入映射、超时、结果处理、人工确认与字段/行动权限 | 扩展 |
| MCP 绑定 | `daconfvalobj/skillvalobj/` | Server 连接、tools/prompts/resources 同步、工具白名单、权限和版本 | 覆盖 |
| Skill 绑定 | `daconfvalobj/skillvalobj/` | `SKILL.md` 包、版本、参考文件、兼容 `.agents/skills` 导入导出 | 扩展 |
| 子 Agent | `daconfvalobj/skillvalobj/` | 固定发布版本、输入映射、超时、最大嵌套和干预策略 | 覆盖 |
| LLM、历史与记忆 | `daconfvalobj/config.go` | 多模型路由、会话历史、记忆策略、输出 schema、步骤/时间/token 预算 | 覆盖 |

PRD 对应章节：9.9—9.13、11、12、13、17、18。操作手册对应章节：18—24。

## 5. AIDP 补充的完整能力

以下能力不是对 IDP 概念的简单复刻，而是 AIDP 必须完整交付的补充：

1. 文档结构化 Agent：多类型上传、Document IR、标准流程、持久多轮确认、证据、ChangeSet 和事务发布。
2. Text-to-Metric：自然语言生成可治理指标的 Author 模式，以及只查询已发布指标的 Query 模式。
3. 完整知识库：内置全文/向量混合检索、权限过滤、评测与引用，同时提供 RAGFlow Provider。
4. 数据质量和字段级血缘：把源字段变化传递到对象、指标、知识和 Agent 的影响分析。
5. 渐进部署：Developer、Team、Enterprise、Offline Profile 使用相同领域模型和 API。
6. OpenCode Runtime Provider：复用持久会话、Question/Permission、Skills/MCP 生态，同时由 AIDP 掌握资源、权限、版本和审计。

## 6. 不照搬的实现

下列差异是有意的架构选择，不代表功能缺失：

- 不以 IDP 的微服务数量作为产品边界；AIDP 先按模块化单体交付，按容量和安全域拆分。
- 不强制 MariaDB、OpenSearch、Redis、Kafka、对象存储或图数据库同时存在；默认 Provider 使用 PostgreSQL，Enterprise Profile 可替换。
- 不让 OpenCode 成为项目、数据、确认或版本的权威存储；它只承担受限 Agent Runtime。
- 不让大模型直接生成并执行任意 SQL；Text-to-Metric 生成中间表示，再由确定性编译器与权限策略执行。
- 不把数据库凭证复制到对象模型或 Agent Prompt；所有访问经 Catalog、Secret 与资源权限完成。

## 7. 后续工程门禁

研发开始前必须把本对照表转成可执行追踪矩阵：每项能力关联 PRD 编号、领域 schema、API、页面、迁移、权限用例、契约测试和端到端验收。任何被标为“覆盖”或“扩展”的能力，在设计调整时都不能无记录删除；如实现方式改变，需要 ADR 说明能力等价性和迁移方案。

## 8. 源码链接

- [KWeaver Core](https://github.com/kweaver-ai/kweaver-core/tree/b9b35fb245c31660127114c883e91165b42dc8f0)
- [VEGA interfaces](https://github.com/kweaver-ai/kweaver-core/tree/b9b35fb245c31660127114c883e91165b42dc8f0/adp/vega/vega-backend/server/interfaces)
- [BKN backend](https://github.com/kweaver-ai/kweaver-core/tree/b9b35fb245c31660127114c883e91165b42dc8f0/adp/bkn)
- [Decision Agent config](https://github.com/kweaver-ai/kweaver-core/tree/b9b35fb245c31660127114c883e91165b42dc8f0/decision-agent/agent-backend/agent-factory/src/domain/valueobject/daconfvalobj)
