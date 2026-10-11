# GitHub 上传步骤

## 方法一：使用 GitHub CLI（推荐）

### 1. 安装 GitHub CLI（如果未安装）
下载地址：https://cli.github.com/

### 2. 登录 GitHub
```bash
gh auth login
```
按提示选择：
- GitHub.com
- HTTPS
- Login with a web browser

### 3. 创建仓库并推送
```bash
cd "C:\Users\Tina Tang\Documents\Qoder\2026-10-11\47791e54"

# 创建公开仓库并推送
gh repo create a-group-registration-system --public --source=. --push

# 或者创建私有仓库
gh repo create a-group-registration-system --private --source=. --push
```

完成！GitHub CLI 会自动创建仓库并推送代码。

---

## 方法二：使用 GitHub 网页（手动）

### 1. 在 GitHub 创建新仓库

1. 打开 https://github.com/new
2. 填写信息：
   - **Repository name**: `a-group-registration-system`（或其他名称）
   - **Description**: `A组报名与资格管理系统 - 运营专家补录、容量修改、退出统一链路`
   - **Public** 或 **Private**（根据需要选择）
   - **不要**勾选 "Initialize this repository with a README"
3. 点击 "Create repository"

### 2. 关联远程仓库并推送

复制 GitHub 显示的命令（类似下面），在终端执行：

```bash
cd "C:\Users\Tina Tang\Documents\Qoder\2026-10-11\47791e54"

# 添加远程仓库（替换为您的 GitHub 用户名和仓库名）
git remote add origin https://github.com/YOUR_USERNAME/a-group-registration-system.git

# 重命名分支为 main
git branch -M main

# 推送代码
git push -u origin main
```

---

## 方法三：使用 SSH（如果您配置了 SSH key）

```bash
cd "C:\Users\Tina Tang\Documents\Qoder\2026-10-11\47791e54"

# 添加远程仓库（SSH 方式）
git remote add origin git@github.com:YOUR_USERNAME/a-group-registration-system.git

# 重命名分支
git branch -M main

# 推送
git push -u origin main
```

---

## 验证上传

1. 打开 GitHub 仓库页面
2. 刷新页面，应该能看到所有文件
3. 检查文件数量：应该是 80 个文件

---

## 后续更新

当您修改代码后，可以使用以下命令推送更新：

```bash
git add .
git commit -m "描述您的更改"
git push
```

---

## 常见问题

### Q1: 推送时需要输入密码
**解决**: GitHub 不再支持密码认证，需要使用 Personal Access Token (PAT)
1. 打开 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选 `repo` 权限
4. 生成后复制 token
5. 推送时使用 token 作为密码

### Q2: 远程仓库已存在
**解决**: 如果远程仓库已有内容，需要先拉取
```bash
git pull origin main --rebase
git push -u origin main
```

### Q3: 分支名称不匹配
**解决**: 重命名本地分支
```bash
git branch -M main
git push -u origin main
```

---

## 推荐的仓库设置

创建仓库后，建议设置：

1. **Branch protection**（分支保护）
   - Settings → Branches → Add rule
   - Branch name pattern: `main`
   - 勾选 "Require pull request reviews before merging"

2. **Topics**（主题标签）
   - 添加：`python`, `fastapi`, `registration-system`, `a-group`

3. **Description**（描述）
   - `A组报名与资格管理系统 - 基于 newbase 的功能补齐`

---

## 仓库 README 建议

您的仓库已包含 README.md，GitHub 会自动显示。建议在 README 中添加：

```markdown
## 快速开始

### 本地运行
```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python app/seeds/dev_seed.py

# 启动服务器
uvicorn app.main:app --reload --port 8780

# 打开演示页面
open demo.html
```

### 文档
- [DELIVERY_NOTES.md](./DELIVERY_NOTES.md) - 详细交付说明
- [DOWNLOAD_GUIDE.md](./DOWNLOAD_GUIDE.md) - 快速部署指南
```

---

**提示**: 如果使用 GitHub CLI，整个过程只需要 3 条命令！
