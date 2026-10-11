# 代码下载清单

## 项目位置
```
C:\Users\Tina Tang\Documents\Qoder\2026-10-11\47791e54
```

## 新增文件（可直接复制）

### 1. Schema 定义
```
app/schemas/manual.py
```
- ManualExpertInput: 补录专家输入
- ManualDraftPatch: 草稿修改输入
- ManualSubmitInput: 提交输入
- CapacityUpdateInput: 容量修改输入
- CapacityUpdateView: 容量修改响应
- MemberParticipationChanged: 成员参与状态变更事件

### 2. Service 业务逻辑
```
app/services/manual.py          # 301行 - 补录专家逻辑
app/services/participation.py   # 168行 - 容量/退出逻辑
```

### 3. API 路由
```
app/api/manual.py               # 45行 - 补录API
app/api/participation.py        # 52行 - 容量/退出API
```

### 4. 测试文件
```
app/tests/test_manual_participation.py  # 180行 - 6个测试用例
```

## 修改文件（需要对比合并）

### 1. app/models/expert.py
**修改位置**: ExpertParticipation 类  
**新增字段**:
```python
capacity_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
```

### 2. app/api/router.py
**修改位置**: import 和 router 注册  
**新增内容**:
```python
from app.api.manual import router as manual_router
from app.api.participation import router as participation_router

api_router.include_router(manual_router)
api_router.include_router(participation_router)
```

### 3. app/schemas/__init__.py
**修改位置**: 导出列表  
**新增导出**:
```python
from app.schemas.manual import (
    ManualExpertInput,
    ManualDraftPatch,
    ManualSubmitInput,
    CapacityUpdateInput,
    CapacityUpdateView,
    MemberParticipationChanged,
)
```

### 4. demo.html
**修改内容**: 更新为11步演示流程，包含所有新功能

## 快速部署步骤

### Windows 开发环境
```powershell
# 1. 进入项目目录
cd "C:\Users\Tina Tang\Documents\Qoder\2026-10-11\47791e54"

# 2. 重置数据库（如果需要）
del a_group.db
.venv\Scripts\python.exe app\seeds\dev_seed.py

# 3. 启动服务器
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8780 --reload

# 4. 运行测试
.venv\Scripts\python.exe -m pytest app\tests\test_manual_participation.py -v

# 5. 打开演示页面
start demo.html
```

### Linux/Mac 开发环境
```bash
# 1. 进入项目目录
cd "/path/to/47791e54"

# 2. 重置数据库（如果需要）
rm a_group.db
.venv/bin/python app/seeds/dev_seed.py

# 3. 启动服务器
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8780 --reload

# 4. 运行测试
.venv/bin/python -m pytest app/tests/test_manual_participation.py -v
```

## 生产环境部署

### 数据库迁移（PostgreSQL）
```sql
-- 执行以下SQL添加新字段
ALTER TABLE expert_participations 
ADD COLUMN IF NOT EXISTS capacity_override INTEGER NULL,
ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

-- 验证迁移
\d expert_participations
```

### 文件部署清单
需要部署到服务器的文件：
- ✅ app/schemas/manual.py
- ✅ app/services/manual.py
- ✅ app/api/manual.py
- ✅ app/services/participation.py
- ✅ app/api/participation.py
- ✅ app/tests/test_manual_participation.py
- ✅ app/models/expert.py（修改）
- ✅ app/api/router.py（修改）
- ✅ app/schemas/__init__.py（修改）

## API 测试命令

### 1. 运营登录
```bash
curl -X POST http://localhost:8780/api/v1/dev/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": "persona-operator-1",
    "activity_id": "seed-activity-1",
    "role": "OPERATOR"
  }'
```

### 2. 创建补录专家
```bash
TOKEN="your_token_here"
curl -X POST http://localhost:8780/api/v1/manual/activities/seed-activity-1/experts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "测试导师",
    "phone": "13800138000",
    "branch": "BEIJING",
    "industries": ["TECH"],
    "topics": ["CAREER"]
  }'
```

### 3. 修改容量
```bash
MEMBER_ID="member_id_from_previous_step"
curl -X PATCH http://localhost:8780/api/v1/activities/seed-activity-1/members/$MEMBER_ID/capacity \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "capacity_override": 5,
    "reason": "增加容量",
    "expected_version": 1
  }'
```

### 4. 停用成员
```bash
curl -X POST http://localhost:8780/api/v1/activities/seed-activity-1/members/$MEMBER_ID/end \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "reason": "导师退出"
  }'
```

## 验证检查清单

- [ ] 所有新文件已复制
- [ ] 修改文件已合并
- [ ] 数据库迁移已执行（生产环境）
- [ ] 服务器启动无错误
- [ ] 单元测试全部通过
- [ ] API接口测试通过
- [ ] 演示页面可正常运行

## 常见问题

### Q1: 数据库表不存在
**解决**: 运行 `python app/seeds/dev_seed.py`

### Q2: 容量修改返回 404
**原因**: ExpertParticipation 记录不存在  
**解决**: 确保使用最新版本的 `app/services/manual.py`

### Q3: 版本号冲突
**原因**: 乐观锁检查失败  
**解决**: 获取最新版本号后重试

### Q4: 权限不足
**原因**: 非运营用户调用运营接口  
**解决**: 使用运营角色登录获取 token

## 技术支持

- **项目路径**: `C:\Users\Tina Tang\Documents\Qoder\2026-10-11\47791e54`
- **文档**: DELIVERY_NOTES.md（详细说明）
- **演示**: demo.html（可视化演示）
- **测试**: app/tests/test_manual_participation.py（单元测试）

---

**最后更新**: 2026-10-11  
**版本**: v1.0
