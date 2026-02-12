# 📋 GitHub 部署步骤

## 1. 创建 GitHub 仓库

访问 https://github.com/new 创建新仓库，仓库名设为 `dailynews`

## 2. 推送代码

在终端执行以下命令：

```bash
cd /Users/guanliming/dailynews

# 重命名分支为 main
git branch -M main

# 添加远程仓库（将 your_username 替换为你的GitHub用户名）
git remote add origin https://github.com/你的用户名/dailynews.git

# 推送到 GitHub
git push -u main
```

## 3. 启用 GitHub Pages

1. 访问你的 GitHub 仓库页面
2. 点击 **Settings** → **Pages**
3. 在 **Source** 部分选择：
   - **Branch**: `gh-pages`
   - **Folder**: `/ (root)`
4. 点击 **Save**

## 4. 等待部署

部署完成后，访问：
```
https://你的用户名.github.io/dailynews/
```

## 5. 配置自动部署（可选）

每次推送代码后，GitHub Actions 会自动部署。

---

## 故障排除

**问题: 页面样式丢失**
- 确保 `public/pdf/` 目录包含 PDF 文件
- 检查浏览器控制台是否有 404 错误

**问题: 报告数据不显示**
- 确保 `public/data/reports/` 目录有 JSON 文件
- 检查 JSON 文件格式是否正确

---

## 项目文件说明

| 文件 | 说明 |
|------|------|
| `src/app/page.tsx` | 九宫格日历首页 |
| `src/app/report/[date]/page.tsx` | 报告详情页 |
| `scripts/daily/daily_report.py` | 每日报告生成脚本 |
| `scripts/init/init_textbook.py` | 课本初始化脚本 |
| `public/data/reports/` | 报告 JSON 数据 |
| `public/pdf/` | PDF 课本文件 |

---

## 本地开发

```bash
npm run dev
# 访问 http://localhost:3000

python3 scripts/daily/daily_report.py --date 2026-02-11
# 生成今日报告
```
