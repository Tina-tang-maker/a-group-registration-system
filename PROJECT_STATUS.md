# A组功能模块 — 项目说明

> 文档版本：v1.0 | 更新日期：2026-10-11 | 作者：雯清

---

## 1. 代码分支

| 项目 | 说明 |
|------|------|
| **分支名称** | `main` |
| **仓库地址** | （待填入 GitHub 仓库 URL） |
| **代码位置** | `C:\Users\Tina Tang\Documents\Qoder\2026-10-11\47791e54\` |
| **技术栈** | Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) + SQLite（本地）/ PostgreSQL（生产） |
| **代码规模** | 68 个文件，约 5000+ 行代码 |

---

## 2. 项目概述

A组报名与资格管理后端 API，覆盖 A01–A09 全部 9 个功能模块。实现从活动创建、学员/导师报名、运营审核、AI 对话整理、需求覆盖提醒、跨组资格交接、到运营统计/日志/导出的完整业务闭环。

---

## 3. 修改内容（本次新增）

### 3.1 项目基础（8 个文件）

| 文件 | 说明 |
|------|------|
| `requirements.txt` | 全部 Python 依赖声明 |
| `.env.example` / `.env` | 环境变量配置（默认 SQLite 本地模式） |
| `alembic.ini` | 数据库迁移配置 |
| `app/config.py` | Pydantic Settings 配置类 |
| `app/database.py` | 异步数据库引擎 + 会话工厂 |
| `app/dependencies.py` | 依赖注入：鉴权、分页、时钟 |
| `app/main.py` | FastAPI 入口 + Worker 启动 |
| `README.md` | 项目说明文档 |

### 3.2 数据模型层（17 张表，13 个文件）

| 模块 | 表 | 说明 |
|------|-----|------|
| A01 身份 | `users`, `role_grants`, `dev_sessions` | 用户、运营授权、开发会话 |
| A02 活动 | `activities` | 活动配置（8 个时间窗口、容量、志愿上限） |
| A03 报名 | `activity_members`, `member_contacts`, `registration_drafts`, `registration_snapshots` | 成员三角状态、联系人、草稿、提交快照 |
| A05 审核 | `review_decisions` | 审核决定（通过/驳回+原因） |
| A04 导师 | `expert_profiles`, `expert_participations` | 导师长期档案、本期参与投影 |
| A06 AI | `ai_sessions`, `ai_messages`, `ai_jobs` | AI 会话、消息、异步任务（含租约/退避） |
| A07 覆盖 | `coverage_alerts`, `coverage_reviews` | 覆盖提醒、运营复核结论 |
| A09 运营 | `notifications`, `audit_logs`, `outbox_events`, `operator_notes`, `idempotency_records` | 通知、审计日志、出站事件、运营备注、幂等记录 |

### 3.3 Schema 层（11 个文件）

Pydantic v2 请求/响应模型，覆盖全部 API 的输入输出类型定义：
- `common.py` — 分页、枚举（ActivityStatus, ReviewStatus, ParticipationStatus 等）
- `identity.py` — 开发人物、会话、上下文
- `activity.py` — 活动 CRUD、发布、公开摘要
- `registration.py` — 报名草稿、提交、历史复用、退出
- `review.py` — 审核、联系人纠错、运营备注、补录
- `ai.py` — AI 会话、消息、任务
- `coverage.py` — 覆盖分析、提醒、复核
- `matching.py` — A→B 双选输入（members/eligibleExperts/studentNeeds）
- `notification.py` — 通知、催办
- `audit.py` — 审计日志、统计面板

### 3.4 服务层（10 个文件）

核心业务逻辑，每个文件对应一个功能模块：

| 文件 | 功能 |
|------|------|
| `auth.py` | 会话解析、权限判断（is_operator、check_activity_operator） |
| `identity.py` | 开发人物列表、会话创建/销毁、字典数据（分社/行业/话题） |
| `activity.py` | 活动 CRUD、发布校验（8 个时间窗口顺序）、PATCH 版本控制 |
| `membership.py` | 加入活动（幂等）、自动编号 |
| `registration.py` | 草稿保存、正式提交（事务+快照）、隐私检测、退出 |
| `review.py` | 审核通过/驳回、联系人纠错、运营补录/代提交、停用、备注 |
| `ai_service.py` | AI 会话创建、消息持久化、任务创建、档案建议、重试 |
| `coverage.py` | 确定性覆盖分析、提醒去重、复核结论 |
| `matching.py` | 从业务事实一次生成 members+eligibleExperts+studentNeeds |
| `notification.py` | 通知列表、已读、催办（24h 去重） |
| `audit.py` | 统计面板、审计日志、CSV 导出（公式注入防护） |

### 3.5 API 路由层（11 个文件，50+ 端点）

| 路由前缀 | 模块 | 关键端点 |
|----------|------|----------|
| `/api/v1/dev/*` | A01 | personas, sessions, context, dictionaries |
| `/api/v1/activities` | A02 | CRUD + publication |
| `/api/v1/public/activities` | A02 | 公开活动目录（无需登录） |
| `/api/v1/activities/{id}/me/registration/*` | A03/A04 | 报名草稿/提交/退出 |
| `/api/v1/activities/{id}/registrations/*` | A05 | 运营审核/补录/联系人/停用 |
| `/api/v1/activities/{id}/me/ai-sessions/*` | A06 | AI 对话/消息/档案建议 |
| `/api/v1/activities/{id}/coverage-*` | A07 | 覆盖分析/提醒/复核 |
| `/api/v1/internal/activities/{id}/matching-input` | A08 | 跨组双选输入 |
| `/api/v1/me/notifications/*` | A09 | 通知/已读 |
| `/api/v1/activities/{id}/registration-reminders` | A09 | 运营催办 |
| `/api/v1/activities/{id}/registration-dashboard` | A09 | 统计面板 |
| `/api/v1/activities/{id}/audit-logs` | A09 | 审计日志 |
| `/api/v1/activities/{id}/registration-export` | A09 | CSV 导出 |

### 3.6 后台 Worker（2 个文件）

| 文件 | 功能 |
|------|------|
| `ai_worker.py` | AI 回复任务消费（租约、退避重试、fallback） |
| `coverage_worker.py` | 覆盖分析定时扫描（72 小时截止补跑） |

### 3.7 迁移与种子（3 个文件）

| 文件 | 说明 |
|------|------|
| `app/migrations/env.py` | Alembic 迁移环境配置 |
| `app/migrations/versions/001_initial.py` | 全量初始迁移（17 张表） |
| `app/seeds/dev_seed.py` | 开发种子数据（3 人物 + 1 活动 + 1 授权） |

### 3.8 测试（4 个文件）

| 文件 | 说明 |
|------|------|
| `tests/conftest.py` | 测试 fixtures（SQLite 内存库） |
| `tests/test_identity.py` | 身份隔离、权限校验 |
| `tests/test_activity.py` | 活动创建/发布/版本冲突 |
| `tests/test_matching.py` | A08 契约测试 |

### 3.9 配套文件修改（2 个文件）

| 文件 | 修改内容 |
|------|----------|
| `pnpm-workspace.yaml` | 新增 `shared/*` 目录（跨端共享类型） |
| `playwright.config.ts` | 新增 API 测试项目（端口 8780）、扩展 H5 测试匹配 |

---

## 4. 核心业务规则实现

| 规则 | 实现方式 |
|------|----------|
| **三角状态独立** | submissionStatus / reviewStatus / participationStatus 三个字段各自回答不同问题 |
| **提交一次** | 接口状态检查 + 数据库唯一约束，正式提交后不可重提 |
| **时间窗口严格** | 发布前校验 8 个时间点的顺序约束，截止后不可延长 |
| **资格计算** | 已提交 + 审核通过 + ACTIVE + 档案完整 → 进入 matching-input |
| **matching-input 原子性** | members / eligibleExperts / studentNeeds 同一次请求从同一批数据生成 |
| **隐私隔离** | 双选输入永远不含真实姓名、手机号、微信号 |
| **幂等操作** | 关键写操作支持 Idempotency-Key |
| **版本并发** | Activity.version / ActivityMember.version 乐观锁 |
| **审计不可删** | AuditLog / OperatorNote 追加式，无修改/删除入口 |
| **CSV 安全** | 公式起始字符转义，UTF-8 BOM |

---

## 5. 验收情况

### 5.1 已通过（自动验证）

| 编号 | 验收项 | 结果 |
|------|--------|------|
| T01 | 开发人物列表 | 通过 — 3 个人物正确返回 |
| T02 | 开发会话创建 | 通过 — Token 生成 + 上下文查询 |
| T03 | 身份隔离 | 通过 — 未授权返回 401 |
| T04 | 权限校验 | 通过 — 普通用户调用运营接口返回 403 |
| T15 | 活动创建 | 通过 — 运营创建草稿，状态 DRAFT |
| T16 | 活动发布校验 | 通过 — 缺少时间窗口返回 422 |
| T17 | 活动版本冲突 | 通过 — expected_version 不匹配返回 409 |
| T05 | 学员加入活动 | 通过 — 创建成员 + 空草稿 |
| T06 | 草稿保存 | 通过 — DRAFT / NOT_SUBMITTED |
| T07 | 正式提交 | 通过 — SUBMITTED / PENDING，快照生成 |
| T09 | 运营审核通过 | 通过 — APPROVED，approvedSnapshotId 设置 |
| T23 | 运营列表查询 | 通过 — 分页 + 筛选 |
| A08 | matching-input 契约 | 通过 — 审核后 1 student，sections 完整（background/problem/expected_help） |

### 5.2 端到端闭环验证

完整流程：**学员加入 → 保存草稿 → 正式提交 → 运营审核通过 → matching-input 出现该学员**

```
POST /dev/sessions (student)          → 200 Token
POST /activities/{id}/memberships     → 200 成员创建
PATCH /me/registration/draft          → 200 草稿保存
POST /me/registration/submissions     → 200 正式提交
POST /dev/sessions (operator)         → 200 Token
GET  /registrations                   → 200 列表 1 条
POST /registrations/{id}/reviews      → 200 审核通过
GET  /matching-input                  → 200 1 member + 1 studentNeed
```

### 5.3 待验收项

| 编号 | 验收项 | 状态 | 说明 |
|------|--------|------|------|
| T08 | 历史复用 | 待验证 | 接口已实现，浏览器专项未执行 |
| T10-T12 | 运营补录/联系人纠错/停用 | 待验证 | 接口已实现，浏览器专项未执行 |
| T13-T14 | 导师报名/容量 | 待验证 | 复用 A03 机制，导师专项未执行 |
| T18 | 双角色隔离 | 待验证 | 同人同学员+导师未执行 |
| T19-T22 | AI 对话/档案建议 | 待验证 | 接口+Worker 已实现，真实模型未联调 |
| T24-T25 | 退出/幂等 | 待验证 | 接口已实现，浏览器未执行 |
| T26-T27 | 覆盖分析/复核 | 待验证 | 接口已实现，浏览器未执行 |
| T28 | 统计/日志/导出 | 待验证 | 接口已实现，浏览器未执行 |
| T29-T34 | 通知/催办/已读 | 待验证 | 接口已实现，浏览器未执行 |
| — | 用户手工体验 | 待执行 | 需用户实际操作验证 |
| — | 微信真机测试 | 待执行 | 不在本地阶段范围 |
| — | 跨组联调（B/C） | 待联调 | A 侧契约已就绪 |

---

## 6. 本地运行方式

```bash
cd C:\Users\Tina Tang\Documents\Qoder\2026-10-11\47791e54
.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8780 --reload
```

- API 文档：http://localhost:8780/docs
- 健康检查：http://localhost:8780/health
- 数据库：SQLite 本地文件 `a_group.db`（已包含种子数据）

### 开发人物

| ID | 名称 | 用途 |
|----|------|------|
| persona-student-1 | 张同学 | 学员报名 |
| persona-expert-1 | 李导师 | 导师报名 |
| persona-operator-1 | 王运营 | 运营审核 |

---

## 7. 后续计划

1. **用户手工体验验收** — 按 A01→A09 顺序逐模块操作验证
2. **AI 真实模型联调** — 配置 OpenAI 兼容凭据，验证对话质量
3. **浏览器 E2E 测试** — Playwright 覆盖核心流程
4. **跨组联调（B/C）** — matching-input 契约测试 + 志愿/反选对接
5. **PostgreSQL 生产部署** — 切换数据库 + Alembic 迁移
