# A组功能补齐 - 开发交付说明

## 项目状态

**开发目录**: `C:\Users\Tina Tang\Documents\Qoder\2026-10-11\47791e54`  
**开发时间**: 2026-10-11  
**版本**: v1.0 - 功能补齐完成  
**Git状态**: 非Git仓库（独立开发目录）

---

## 一、需求概述

根据 `A组_newbase功能补齐与交付清单.md` 要求，完成以下三个核心功能：

1. **运营专家补录** - 在活动任意阶段由运营手动补录专家
2. **容量修改** - 修改单个专家在本期活动的可带学员数
3. **退出统一链路** - 停用/退出成员时发出 `MemberParticipationChanged` 事件

---

## 二、代码变更清单

### 新增文件（6个）

| 文件路径 | 说明 | 行数 |
|---------|------|------|
| `app/schemas/manual.py` | 补录相关的数据模型定义 | 65行 |
| `app/services/manual.py` | 补录专家的核心业务逻辑 | 301行 |
| `app/api/manual.py` | 补录专家的API路由 | 45行 |
| `app/services/participation.py` | 容量修改、退出停用的业务逻辑 | 168行 |
| `app/api/participation.py` | 容量修改、退出停用的API路由 | 52行 |
| `app/tests/test_manual_participation.py` | 单元测试（6个测试用例） | 180行 |

### 修改文件（4个）

| 文件路径 | 修改内容 |
|---------|---------|
| `app/models/expert.py` | ExpertParticipation 增加 `capacity_override` 和 `version` 字段 |
| `app/api/router.py` | 注册 manual_router 和 participation_router |
| `app/schemas/__init__.py` | 导出新增的 schema 类 |
| `demo.html` | 更新演示页面，包含11步完整流程 |

---

## 三、API接口清单

### 3.1 运营专家补录（3个接口）

#### POST `/api/v1/manual/activities/{activity_id}/experts`
- **功能**: 创建补录专家
- **权限**: 仅运营 (require_operator)
- **请求体**:
  ```json
  {
    "name": "导师姓名",
    "phone": "13800138000",
    "branch": "BEIJING",
    "industries": ["TECH", "EDUCATION"],
    "topics": ["CAREER"]
  }
  ```
- **响应**: 
  ```json
  {
    "activity_member_id": "uuid",
    "user_id": "uuid",
    "role": "EXPERT"
  }
  ```

#### PATCH `/api/v1/manual/activities/{activity_id}/members/{member_id}/draft`
- **功能**: 编辑补录草稿
- **权限**: 仅运营
- **请求体**:
  ```json
  {
    "sections": {
      "experience": "经验分享",
      "supported_problems": "可支持的问题",
      "boundaries": "边界说明"
    }
  }
  ```
- **响应**: 返回更新后的成员信息和版本号

#### POST `/api/v1/manual/activities/{activity_id}/members/{member_id}/submit`
- **功能**: 提交补录专家
- **权限**: 仅运营
- **请求体**:
  ```json
  {
    "confirmation_basis": "运营确认资料完整",
    "expected_version": 2
  }
  ```
- **响应**: 返回提交状态和版本号

### 3.2 容量修改（1个接口）

#### PATCH `/api/v1/activities/{activity_id}/members/{member_id}/capacity`
- **功能**: 修改专家容量
- **权限**: 仅运营
- **请求体**:
  ```json
  {
    "capacity_override": 5,
    "reason": "该导师经验丰富，增加本期容量",
    "expected_version": 1
  }
  ```
- **响应**:
  ```json
  {
    "activity_member_id": "uuid",
    "capacity_override": 5,
    "effective_capacity": 5,
    "version": 2
  }
  ```

### 3.3 退出统一链路（2个接口）

#### POST `/api/v1/activities/{activity_id}/members/{member_id}/end`
- **功能**: 停用成员（保留记录）
- **权限**: 仅运营
- **请求体**:
  ```json
  {
    "reason": "导师主动退出本期活动"
  }
  ```
- **响应**: MemberParticipationChanged 事件对象
- **副作用**: 发出 `MEMBER_PARTICIPATION_CHANGED` OutboxEvent

#### POST `/api/v1/activities/{activity_id}/members/{member_id}/withdraw`
- **功能**: 成员主动退出
- **权限**: 仅运营
- **请求体**:
  ```json
  {
    "reason": "个人原因退出"
  }
  ```
- **响应**: MemberParticipationChanged 事件对象
- **副作用**: 发出 `MEMBER_PARTICIPATION_CHANGED` OutboxEvent

---

## 四、核心业务逻辑

### 4.1 运营专家补录流程

1. **创建专家** (`create_manual_expert`)
   - 检查活动是否存在
   - 检查是否已存在（防重复）
   - 创建或查找 User（支持占位符用户）
   - 创建 ActivityMember（状态：DRAFT/NOT_STARTED/ACTIVE）
   - 创建 MemberContact（联系方式）
   - 创建 RegistrationDraft（草稿内容）
   - **创建 ExpertParticipation**（关键：确保后续容量修改可用）
   - 记录审计日志

2. **编辑草稿** (`patch_manual_draft`)
   - 检查是否已提交（已提交不可编辑）
   - 更新草稿的 basic/sections/structured 字段
   - 版本号 +1
   - 记录审计日志

3. **提交专家** (`submit_manual_expert`)
   - 检查是否已提交（一次性提交，不可重复）
   - 版本号乐观锁检查
   - 验证必填字段（name, phone, branch）
   - 验证必填章节（experience, supported_problems, boundaries）
   - 构建公开档案 (public_dossier)
   - 创建 RegistrationSnapshot（submission_source="OPERATOR_MANUAL"）
   - 更新成员状态：SUBMITTED/PENDING
   - 创建或查找 ExpertProfile
   - 确保 ExpertParticipation 存在
   - 记录审计日志
   - 发出 `REGISTRATION_SUBMITTED` OutboxEvent

### 4.2 容量修改逻辑

**更新专家容量** (`update_expert_capacity`)
- 检查活动和成员是否存在
- 查找 ExpertParticipation 记录
- 版本号乐观锁检查
- 更新 `capacity_override` 字段
- 计算有效容量：`capacity_override` 优先，否则使用 `activity.capacity_max`
- 版本号 +1
- 记录审计日志（包含旧值、新值、原因）

**关键点**:
- `capacity_override` 为 null 时，使用活动默认容量
- `capacity_override` 有值时，覆盖活动默认容量
- 仅影响当前活动，不影响其他活动

### 4.3 退出统一链路

**停用成员** (`end_participation`)
- 检查成员状态（仅 ACTIVE 可停用）
- 更新 `participation_status` 为 INACTIVE
- 版本号 +1
- 构建 MemberParticipationChanged 事件
- 记录审计日志
- 发出 `MEMBER_PARTICIPATION_CHANGED` OutboxEvent

**成员退出** (`withdraw_member`)
- 检查成员状态（仅 ACTIVE 可退出）
- 更新 `participation_status` 为 WITHDRAWN
- 版本号 +1
- 构建 MemberParticipationChanged 事件
- 记录审计日志
- 发出 `MEMBER_PARTICIPATION_CHANGED` OutboxEvent

**事件结构** (MemberParticipationChanged):
```json
{
  "activity_id": "seed-activity-1",
  "activity_member_id": "uuid",
  "role": "EXPERT",
  "previous_status": "ACTIVE",
  "participation_status": "INACTIVE",
  "reason": "退出原因",
  "changed_at": "2026-10-11T05:34:12.888371+00:00"
}
```

---

## 五、数据模型变更

### ExpertParticipation 表新增字段

```python
class ExpertParticipation(Base, TimestampMixin):
    __tablename__ = "expert_participations"
    
    # 原有字段
    id: Mapped[str]
    activity_member_id: Mapped[str]
    approved_snapshot_id: Mapped[str | None]
    
    # 新增字段
    capacity_override: Mapped[int | None]  # 容量覆盖值
    version: Mapped[int]                    # 乐观锁版本号
```

**迁移说明**:
- SQLite 开发环境：删除 `a_group.db` 后重新运行 `app/seeds/dev_seed.py`
- PostgreSQL 生产环境：需要执行数据库迁移
  ```sql
  ALTER TABLE expert_participations 
  ADD COLUMN capacity_override INTEGER NULL,
  ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
  ```

---

## 六、验收情况

### 6.1 单元测试

**测试文件**: `app/tests/test_manual_participation.py`  
**测试用例**: 6个

| 测试用例 | 测试内容 | 状态 |
|---------|---------|------|
| `test_create_manual_expert` | 创建补录专家 | ✅ 通过 |
| `test_patch_manual_draft` | 编辑补录草稿 | ✅ 通过 |
| `test_submit_manual_expert` | 提交补录专家 | ✅ 通过 |
| `test_update_expert_capacity` | 修改专家容量 | ✅ 通过 |
| `test_end_participation` | 停用成员 | ✅ 通过 |
| `test_withdraw_member` | 成员退出 | ✅ 通过 |

### 6.2 API接口测试

**测试时间**: 2026-10-11 05:34  
**测试环境**: localhost:8780  
**测试结果**: 全部通过

| 步骤 | 接口 | 测试内容 | 状态 |
|-----|------|---------|------|
| 1 | POST /dev/sessions | 运营登录 | ✅ 通过 |
| 2 | POST /manual/activities/{id}/experts | 创建补录专家 | ✅ 通过 |
| 3 | PATCH /activities/{id}/members/{id}/capacity | 修改专家容量 | ✅ 通过 |
| 4 | POST /activities/{id}/members/{id}/end | 停用成员 | ✅ 通过 |

**关键验证点**:
- ✅ ExpertParticipation 记录在创建专家时同步创建
- ✅ 容量修改接口可正常访问（之前因缺少 ExpertParticipation 返回 500）
- ✅ 版本号乐观锁正常工作
- ✅ 状态机转换正确（ACTIVE → INACTIVE）
- ✅ 审计日志正确记录
- ✅ OutboxEvent 正确发出

### 6.3 业务规则验证

| 规则 | 验证结果 |
|-----|---------|
| 重复补录同一用户 | ✅ 返回 409 "Expert already exists" |
| 已提交后编辑草稿 | ✅ 返回 409 "Cannot edit after submission" |
| 重复提交 | ✅ 返回 409 "Already submitted" |
| 版本号冲突 | ✅ 返回 409 "Version conflict" |
| 已停用成员再次停用 | ✅ 返回 409 "Member is INACTIVE, cannot end" |
| 必填字段校验 | ✅ 返回 422 "Missing required field" |

### 6.4 演示页面

**文件**: `demo.html`  
**功能**: 11步完整流程演示  
**状态**: ✅ 已完成

**演示流程**:
1. 获取角色列表
2. 查看公开活动
3. 运营登录
4. 创建补录专家 ⭐新功能
5. 编辑补录草稿 ⭐新功能
6. 提交补录专家 ⭐新功能
7. 修改专家容量 ⭐新功能
8. 停用成员 ⭐新功能
9. 查看报名列表
10. 查看审计日志
11. 查看运营仪表盘

**使用方法**:
```bash
# 1. 启动服务器
cd "C:\Users\Tina Tang\Documents\Qoder\2026-10-11\47791e54"
.venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8780

# 2. 打开演示页面
# 在浏览器中打开 demo.html
# 或直接双击 demo.html 文件

# 3. 点击"运行全部流程"按钮
```

---

## 七、已知问题与限制

### 7.1 已修复问题

| 问题 | 原因 | 修复方案 |
|-----|------|---------|
| 容量修改返回 500 | create_manual_expert 未创建 ExpertParticipation | 在创建专家时同步创建 ExpertParticipation 记录 |
| 重复运行演示失败 | 数据库持久化导致状态冲突 | 演示页面增加错误处理，捕获已有数据 |

### 7.2 已知限制

1. **数据库迁移**: 生产环境需要手动执行 SQL 迁移脚本
2. **事件消费**: OutboxEvent 需要下游系统消费（不在本次范围）
3. **权限粒度**: 当前仅区分 OPERATOR/非OPERATOR，未细化到具体操作

---

## 八、部署说明

### 8.1 开发环境

```bash
# 安装依赖
cd "C:\Users\Tina Tang\Documents\Qoder\2026-10-11\47791e54"
.venv/Scripts/pip.exe install -r requirements.txt

# 初始化数据库
.venv/Scripts/python.exe app/seeds/dev_seed.py

# 启动服务器
.venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8780 --reload

# 运行测试
.venv/Scripts/python.exe -m pytest app/tests/test_manual_participation.py -v
```

### 8.2 生产环境

```bash
# 1. 数据库迁移（PostgreSQL）
psql -U your_user -d your_db -c "
ALTER TABLE expert_participations 
ADD COLUMN IF NOT EXISTS capacity_override INTEGER NULL,
ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;
"

# 2. 部署代码
# 将以下新文件部署到服务器：
# - app/schemas/manual.py
# - app/services/manual.py
# - app/api/manual.py
# - app/services/participation.py
# - app/api/participation.py
# - app/tests/test_manual_participation.py

# 3. 更新路由注册
# 确保 app/api/router.py 包含：
# from app.api.manual import router as manual_router
# from app.api.participation import router as participation_router
# api_router.include_router(manual_router)
# api_router.include_router(participation_router)

# 4. 重启服务
systemctl restart your_service
```

---

## 九、代码下载

所有代码位于目录：`C:\Users\Tina Tang\Documents\Qoder\2026-10-11\47791e54`

**核心文件清单**:
```
app/
├── api/
│   ├── manual.py              # 新增：补录API路由
│   ├── participation.py       # 新增：容量/退出API路由
│   └── router.py              # 修改：注册新路由
├── schemas/
│   ├── manual.py              # 新增：数据模型定义
│   └── __init__.py            # 修改：导出新模型
├── services/
│   ├── manual.py              # 新增：补录业务逻辑
│   └── participation.py       # 新增：容量/退出业务逻辑
├── models/
│   └── expert.py              # 修改：新增字段
├── tests/
│   └── test_manual_participation.py  # 新增：单元测试
└── seeds/
    └── dev_seed.py            # 现有：种子数据

demo.html                      # 修改：演示页面
IMPLEMENTATION_SUMMARY.md      # 新增：实现总结
DELIVERY_NOTES.md              # 新增：本文档
```

---

## 十、下一步建议

1. **集成测试**: 与 newbase 分支进行集成测试，确保不冲突
2. **事件消费**: 实现 MemberParticipationChanged 事件的消费端
3. **权限细化**: 考虑更细粒度的权限控制（如：仅活动创建者可操作）
4. **文档完善**: 更新 API 文档（OpenAPI/Swagger）
5. **代码审查**: 提交代码前进行团队代码审查

---

## 联系方式

**开发者**: AI Assistant  
**完成时间**: 2026-10-11  
**项目路径**: `C:\Users\Tina Tang\Documents\Qoder\2026-10-11\47791e54`

---

**备注**: 本文档由 AI 自动生成，如有问题请联系开发者确认。
