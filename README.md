# AIDP

AIDP 是一个开源优先、可私有部署、技术栈渐进扩展的完整智能决策平台。它既连接和治理数据库、文件、API 等现有数据，也帮助没有线上管理系统的客户，把制度、流程、表单、台账等材料通过多轮 Agent 确认转化为标准流程、业务对象模型、结构化记录、知识和指标，最终打通“数据/知识/指标/Skills/MCP/规则/行动—Agent—证据与审计”闭环。

当前阶段：产品定义。

## 文档

- [AIDP 产品需求文档（PRD）](docs/PRD.md)
- [AIDP 完整产品操作手册（设计稿）](docs/USER_GUIDE.md)
- [IDP 能力对照审计](docs/IDP_CAPABILITY_AUDIT.md)

## 核心约束

- 模块化单体优先，不以微服务数量衡量平台能力。
- Developer/Team Profile 默认只依赖 PostgreSQL；Enterprise Profile 按容量接入对象存储、任务、搜索和图 Provider。
- Docker Compose 覆盖开发与团队部署，Helm/Kubernetes 覆盖企业高可用，使用同一领域模型和 API。
- 数据、规则、工具调用和智能体结论均可追溯。
- 平台核心代码和必选依赖采用开源方案；模型既可接云端 API，也可接本地 OpenAI-compatible 服务。

> 当前仓库仅包含产品文档，技术实现将在 PRD 评审通过后启动。
