# A组功能补齐 - 交付报告 v1.0

**交付日期**: 2026-10-11  
**开发者**: Tina Tang  
**GitHub 仓库**: https://github.com/Tina-tang-maker/a-group-registration-system

---

## 一、代码分支信息

| 项目 | 内容 |
|-----|------|
| 当前分支 | `main` |
| 远程仓库 | `origin` → https://github.com/Tina-tang-maker/a-group-registration-system |
| 最新提交 | `99a62d5` feat: 完成A组功能补齐 - 运营专家补录、容量修改、退出统一链路 |
| 提交总数 | 1 |
| 文件总数 | 80 |
| 代码总行数 | 7,365 |

---

## 二、变更内容

### 2.1 新增功能（3个核心功能）

#### 功能一：运营专家补录
- **需求**: 在活动任意阶段，由运营手动补录专家，绕过报名窗口但走统一审核
- **实现**:
  - 运营创建专家（自动创建 User + ActivityMember + MemberContact + RegistrationDraft + ExpertParticipation）
  - 运营编辑草稿（支持 basic/sections/structured 三个区块）
  - 运营提交专家（一次性提交，不可重复，生成 RegistrationSnapshot，submission_source="OPERATOR_MANUAL"）
- **关键设计**:
  - 防重复：同一用户在同一活动只能补录一次
  - 占位符用户：支持无账号的专家，自动创建 is_placeholder=True 的 User
  - 隐私检测：自动扫描草稿中的手机号和邮箱

#### 功能二：容量修改
- **需求**: 修改单个专家在本期活动的可带学员数（capacity_override）
- **实现**:
  - 在 ExpertParticipation 上新增 `capacity_override` 字段
  - 有效容量计算：`capacity_override` 优先，为 null 时使用 `activity.capacity_max`
  - 版本号乐观锁，防止并发冲突
- **关键设计**:
  - 仅影响当前活动，不影响其他活动
  - 修改记录写入审计日志（包含旧值、新值、原因）

#### 功能三：退出统一链路
- **需求**: 停用/退出成员时，统一发出 `MemberParticipationChanged` 事件
- **实现**:
  - 停用接口（POST /end）：`participation_status` → INACTIVE
  - 退出接口（POST /withdraw）：`participation_status` → WITHDRAWN
  - 两个接口都会：
    - 检查状态机（仅 ACTIVE 可操作）
    - 版本号 +1
    - 写入审计日志
    - 发出 `MEMBER_PARTICIPATION_CHANGED` OutboxEvent

### 2.2 新增文件清单（6个）

| 文件 | 行数 | 说明 |
|------|------|------|
| `app/schemas/manual.py` | 65 | 补录/容量/退出的数据模型定义 |
| `app/services/manual.py` | 301 | 补录专家核心业务逻辑 |
| `app/api/manual.py` | 45 | 补录专家 API 路由（3个接口） |
| `app/services/participation.py` | 168 | 容量修改 + 退出停用业务逻辑 |
| `app/api/participation.py` | 52 | 容量修改 + 退出停用 API 路由（3个接口） |
| `app/tests/test_manual_participation.py` | 180 | 6个单元测试用例 |

### 2.3 修改文件清单（4个）

| 文件 | 修改内容 |
|------|---------|
| `app/models/expert.py` | ExpertParticipation 新增 `capacity_override`（容量覆盖值）和 `version`（乐观锁）字段 |
| `app/api/router.py` | 注册 `manual_router` 和 `participation_router` |
| `app/schemas/__init__.py` | 导出 ManualExpertInput、ManualDraftPatch、ManualSubmitInput、CapacityUpdateInput、CapacityUpdateView、MemberParticipationChanged |
| `demo.html` | 更新为 11 步完整流程演示页面 |

### 2.4 新增 API 接口（6个）

| 方法 | 路径 | 功能 | 权限 |
|------|------|------|------|
| POST | `/api/v1/manual/activities/{id}/experts` | 创建补录专家 | 运营 |
| PATCH | `/api/v1/manual/activities/{id}/members/{id}/draft` | 编辑补录草稿 | 运营 |
| POST | `/api/v1/manual/activities/{id}/members/{id}/submit` | 提交补录专家 | 运营 |
| PATCH | `/api/v1/activities/{id}/members/{id}/capacity` | 修改专家容量 | 运营 |
| POST | `/api/v1/activities/{id}/members/{id}/end` | 停用成员 | 运营 |
| POST | `/api/v1/activities/{id}/members/{id}/withdraw` | 成员退出 | 运营 |

---

## 三、验收情况

### 3.1 单元测试

| 测试用例 | 测试内容 | 结果 |
|---------|---------|------|
| test_create_manual_expert | 创建补录专家，验证所有关联记录 | ✅ 通过 |
| test_patch_manual_draft | 编辑草稿，验证版本号和字段更新 | ✅ 通过 |
| test_submit_manual_expert | 提交专家，验证状态转换和快照创建 | ✅ 通过 |
| test_update_expert_capacity | 修改容量，验证覆盖值和有效容量 | ✅ 通过 |
| test_end_participation | 停用成员，验证状态和事件 | ✅ 通过 |
| test_withdraw_member | 成员退出，验证状态和事件 | ✅ 通过 |

### 3.2 API 接口测试（2026-10-11 05:34）

| 步骤 | 接口 | 测试内容 | 结果 |
|-----|------|---------|------|
| 1 | POST /dev/sessions | 运营登录获取 Token | ✅ 通过 |
| 2 | POST /manual/.../experts | 创建补录专家 | ✅ 通过 |
| 3 | PATCH .../capacity | 修改专家容量（覆盖值=5） | ✅ 通过 |
| 4 | POST .../end | 停用成员（ACTIVE→INACTIVE） | ✅ 通过 |

### 3.3 业务规则验证

| 规则 | 预期行为 | 验证结果 |
|------|---------|---------|
| 重复补录同一用户 | 返回 409 "Expert already exists" | ✅ 符合预期 |
| 已提交后编辑草稿 | 返回 409 "Cannot edit after submission" | ✅ 符合预期 |
| 重复提交 | 返回 409 "Already submitted" | ✅ 符合预期 |
| 版本号冲突 | 返回 409 "Version conflict" | ✅ 符合预期 |
| 已停用成员再次停用 | 返回 409 "Member is INACTIVE, cannot end" | ✅ 符合预期 |
| 必填字段缺失 | 返回 422 "Missing required field" | ✅ 符合预期 |

### 3.4 缺陷修复记录

| 缺陷 | 根因 | 修复方案 | 状态 |
|------|------|---------|------|
| 容量修改返回 500 Internal Server Error | `create_manual_expert` 未创建 ExpertParticipation 记录，导致容量修改时查询不到 | 在 `create_manual_expert` 中同步创建 ExpertParticipation 记录 | ✅ 已修复 |

### 3.5 验收总结

| 维度 | 状态 |
|------|------|
| 功能完整性 | ✅ 3个核心功能全部实现 |
| 单元测试 | ✅ 6/6 通过 |
| API 接口测试 | ✅ 4/4 通过 |
| 业务规则 | ✅ 6/6 符合预期 |
| 缺陷修复 | ✅ 1/1 已修复 |
| 文档 | ✅ 已生成交付文档和演示页面 |

---

## 四、生产部署注意事项

### 4.1 数据库迁移
```sql
ALTER TABLE expert_participations 
ADD COLUMN IF NOT EXISTS capacity_override INTEGER NULL,
ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;
```

### 4.2 环境变量
无需新增环境变量，复用现有配置。

### 4.3 依赖
无需新增依赖，所有代码基于现有 requirements.txt。

---

## 五、后续建议

1. **集成测试**: 与 newbase 分支合并前进行集成测试
2. **事件消费**: 实现 MemberParticipationChanged 事件的下游消费
3. **权限细化**: 考虑活动级别的权限控制
4. **容量默认值**: 考虑为 capacity_override 设置业务上限

---

**报告生成时间**: 2026-10-11  
**版本**: v1.0  
**状态**: ✅ 已交付，代码已推送至 GitHub
