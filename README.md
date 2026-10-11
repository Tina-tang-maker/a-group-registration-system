# A组报名与资格管理后端 API

基于 FastAPI + PostgreSQL 的完整后端实现，覆盖A组全部9个功能模块。

## 功能模块

| 编号 | 功能 | API 路由前缀 |
|------|------|-------------|
| A01 | 身份与活动成员 | `/api/v1/dev/*`, `/api/v1/me/context`, `/api/v1/dictionaries/*` |
| A02 | 活动与报名窗口 | `/api/v1/activities/*`, `/api/v1/public/activities` |
| A03 | 学员报名与需求档案 | `/api/v1/activities/{id}/me/registration/*` |
| A04 | 导师档案与本期报名 | 复用 A03 接口，role=EXPERT |
| A05 | 运营审核与报名管理 | `/api/v1/activities/{id}/registrations/*` |
| A06 | AI对话与资料整理 | `/api/v1/activities/{id}/me/ai-sessions/*`, `/api/v1/jobs/*` |
| A07 | 需求覆盖提醒 | `/api/v1/activities/{id}/coverage-*` |
| A08 | 跨组资格交接 | `/api/v1/internal/activities/{id}/matching-input` |
| A09 | 运营统计/日志/导出 | `/api/v1/activities/{id}/registration-dashboard`, `audit-logs`, `registration-export` |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，设置 DATABASE_URL
```

### 3. 创建数据库并运行迁移

```bash
# 确保 PostgreSQL 正在运行
createdb a_group  # 或使用 psql 创建

# 运行数据库迁移
alembic upgrade head
```

### 4. 灌入种子数据

```bash
python -m app.seeds.dev_seed
```

### 5. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问 API 文档

打开浏览器访问 http://localhost:8000/docs

## 开发身份系统

本地开发环境提供简化身份入口：

```bash
# 1. 查看可用开发人物
GET /api/v1/dev/personas

# 2. 选择人物创建会话
POST /api/v1/dev/sessions
{
  "persona_id": "persona-operator-1",
  "activity_id": "seed-activity-1",
  "role": "OPERATOR"
}
# 响应头 X-Dev-Token 包含 token

# 3. 后续请求携带 token
Authorization: Bearer <token>
```

### 预置开发人物

| ID | 名称 | 用途 |
|----|------|------|
| persona-student-1 | 张同学 | 学员报名 |
| persona-expert-1 | 李导师 | 导师报名 |
| persona-operator-1 | 王运营 | 运营审核 |

## 核心业务规则

1. **三角状态独立**: submissionStatus / reviewStatus / participationStatus 各自回答不同问题
2. **提交一次**: 正式提交后不可重提，不可修改专业资料
3. **时间窗口严格**: 发布前必须配置完整时间且满足顺序约束
4. **资格计算**: 已提交 + 审核通过 + ACTIVE + 档案完整 → 进入 matching-input
5. **matching-input 原子性**: members/eligibleExperts/studentNeeds 同一请求生成
6. **隐私隔离**: 双选输入永远不含真实姓名、手机号、微信号
7. **幂等**: 关键写操作支持 Idempotency-Key
8. **版本并发**: Activity.version, ActivityMember.version 用于乐观锁

## 运行测试

```bash
pip install pytest pytest-asyncio aiosqlite
pytest app/tests/ -v
```

## 项目结构

```
app/
├── main.py              # FastAPI 入口 + Worker 启动
├── config.py            # 环境变量配置
├── database.py          # 异步数据库引擎
├── dependencies.py      # 依赖注入（鉴权、分页）
├── models/              # SQLAlchemy 数据模型（17张表）
├── schemas/             # Pydantic 请求/响应模型
├── services/            # 业务逻辑层
├── api/                 # API 路由层
├── workers/             # 后台 Worker（AI回复、覆盖分析）
├── migrations/          # Alembic 数据库迁移
├── seeds/               # 开发种子数据
└── tests/               # 测试用例
```
