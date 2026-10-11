# A组功能模块实现总结

## 项目概述
基于 newbase 分支，为 A 组报名与资格管理系统补齐了三个核心功能模块。

## 新增功能

### 1. 运营专家补录功能
**文件位置:**
- `app/api/manual.py` - API 路由
- `app/services/manual.py` - 业务逻辑
- `app/schemas/manual.py` - 数据模型

**功能说明:**
- 允许运营人员在任意活动阶段补录专家
- 支持创建、编辑草稿、提交审核完整流程
- 复用成员唯一性、草稿、提交快照、完整性/隐私校验
- 补录提交后走统一审核流程，不自动批准

**API 端点:**
- `POST /api/v1/manual/activities/{activity_id}/experts` - 创建补录专家
- `PATCH /api/v1/manual/activities/{activity_id}/members/{member_id}/draft` - 编辑草稿
- `POST /api/v1/manual/activities/{activity_id}/members/{member_id}/submit` - 提交审核

### 2. 专家容量修改功能
**文件位置:**
- `app/api/participation.py` - API 路由
- `app/services/participation.py` - 业务逻辑
- `app/models/expert.py` - 数据模型（新增 capacity_override 字段）

**功能说明:**
- 运营可修改指定专家本期容量
- 支持容量覆盖、版本校验、占用检查
- 非空覆盖值必须为非负整数
- 清空覆盖值则恢复活动默认容量

**API 端点:**
- `PATCH /api/v1/activities/{activity_id}/members/{member_id}/capacity` - 修改容量

### 3. 退出停用统一链路
**文件位置:**
- `app/api/participation.py` - API 路由
- `app/services/participation.py` - 业务逻辑
- `app/schemas/manual.py` - MemberParticipationChanged 事件模型

**功能说明:**
- 统一所有退出和停用入口到同一条跨组链路
- 产生 MemberParticipationChanged 事件
- 包含 activityId、activityMemberId、role、previousStatus、participationStatus、reason、changedAt
- 通过 OutboxEvent 派发事件，确保一致性

**API 端点:**
- `POST /api/v1/activities/{activity_id}/members/{member_id}/end` - 停用成员
- `POST /api/v1/activities/{activity_id}/members/{member_id}/withdraw` - 退出成员

## 数据库变更

### ExpertParticipation 表新增字段
```python
capacity_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
```

## 测试覆盖

**测试文件:** `app/tests/test_manual_participation.py`

**测试用例:**
1. `test_create_manual_expert` - 创建补录专家
2. `test_patch_manual_draft` - 编辑补录草稿
3. `test_submit_manual_expert` - 提交补录专家
4. `test_update_expert_capacity` - 修改专家容量
5. `test_end_participation` - 停用成员
6. `test_withdraw_member` - 退出成员

## 运行测试

```bash
# 启动测试数据库
python scripts/docker_database.py start
python scripts/docker_database.py migrate-test

# 运行测试
python -m pytest app/tests/test_manual_participation.py -v

# 代码检查
python -m ruff check .
```

## 演示页面

打开 `demo.html` 查看完整功能演示，包含：
- 基础流程（角色列表、活动列表）
- 运营专家补录（创建、编辑、提交）
- 容量修改
- 退出停用
- 审计日志和仪表盘

## 文件清单

### 新增文件
- `app/api/manual.py`
- `app/api/participation.py`
- `app/services/manual.py`
- `app/services/participation.py`
- `app/schemas/manual.py`
- `app/tests/test_manual_participation.py`

### 修改文件
- `app/models/expert.py` - 添加 capacity_override 和 version 字段
- `app/api/router.py` - 注册新路由
- `app/schemas/__init__.py` - 导出新 schema
- `demo.html` - 更新演示页面

## 验证状态

- [x] 代码结构完整
- [x] API 端点定义
- [x] 业务逻辑实现
- [x] 数据模型更新
- [x] 测试用例编写
- [x] 演示页面更新
- [ ] 本地运行验证（需启动服务）
- [ ] 完整回归测试

## 下一步

1. 启动本地服务验证 API 功能
2. 运行完整测试套件
3. 执行代码质量检查
4. 准备 PR 提交
