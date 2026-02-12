# 📚 道法时事报告系统

## 一、需求设计

### 1.1 产品概述
一个自动采集中国新闻网时政新闻，匹配道法课本知识点，生成九宫格展示的时事报告系统。

### 1.2 功能需求

#### 1.2.1 新闻采集
- 从中国新闻网时政频道获取顶部焦点新闻
- 下钻详情页提取完整内容
- 自动提取关键要点（人物、机构、事件）
- 按日期存储，支持历史查询

#### 1.2.2 内容处理
- AI专业总结（新闻综述、关键要点、道法关联、思考问题）
- 智能匹配道法课本知识点（7-9年级）
- 支持同标题覆盖更新

#### 1.2.3 前端展示
- 九宫格首页（按日期展示卡片）
- 点击卡片展开当日新闻详情
- 响应式设计，支持移动端

### 1.3 数据结构

#### 新闻表 (news_articles)
```sql
CREATE TABLE news_articles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL UNIQUE,
  url TEXT UNIQUE,
  source TEXT,
  publish_date DATE,
  content TEXT,
  summary TEXT,
  category TEXT,
  channel TEXT,
  key_points TEXT,        -- JSON数组
  ai_summary TEXT,         -- AI专业总结
  metadata TEXT,           -- JSON元数据
  created_at DATETIME,
  updated_at DATETIME
)
```

#### 课本表 (textbook_chapters)
```sql
CREATE TABLE textbook_chapters (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book_name TEXT NOT NULL,
  chapter_title TEXT NOT NULL,
  section_title TEXT,
  page_range TEXT,
  content TEXT,
  content_summary TEXT,
  keywords TEXT,
  embedding BLOB,
  metadata TEXT,
  created_at DATETIME,
  updated_at DATETIME
)
```

## 二、技术架构

### 2.1 技术栈
- **前端**: Next.js 14 + Tailwind CSS
- **后端**: Python + Flask (轻量级API)
- **数据库**: SQLite (Turso)
- **新闻采集**: Python requests + BeautifulSoup
- **部署**: Vercel / 本地运行

### 2.2 系统架构
```
┌─────────────────────────────────────────────────────┐
│                   前端 (Next.js)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  九宫格首页  │  │  新闻详情页 │  │    API调用   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└────────────────────────┬────────────────────────────────┐
                         │ fetch('/api/news')
                         ▼
┌─────────────────────────────────────────────────────┐
│                   API (Flask)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  /api/dates │  │  /api/news  │  │  /api/crawl │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────┐
│                 数据库 (SQLite)                      │
│  ┌─────────────────┐  ┌─────────────────────┐    │
│  │  news_articles  │  │  textbook_chapters   │    │
│  └─────────────────┘  └─────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## 三、开发实现

### 3.1 新闻采集模块
- [x] `scripts/collect/chinanews_fetcher.py` - 新闻采集器

### 3.2 API接口
- [ ] `/api/dates` - 获取日期列表
- [ ] `/api/news?date=YYYY-MM-DD` - 获取指定日期新闻
- [ ] `/api/crawl` - 触发采集

### 3.3 前端页面
- [x] `src/app/page.tsx` - 九宫格首页
- [ ] `src/app/report/[date]/page.tsx` - 日期详情页

## 四、测试用例

### 4.1 采集测试
```bash
# 测试新闻采集
python3 scripts/collect/chinanews_fetcher.py "https://www.chinanews.com.cn/china/"
```

### 4.2 API测试
```bash
# 测试API
curl http://localhost:5000/api/dates
curl http://localhost:5000/api/news?date=2026-02-11
```

### 4.3 前端测试
访问 http://localhost:3000
- 检查九宫格展示
- 测试卡片点击
- 检查响应式布局

## 五、输出模板

### 5.1 新闻详情模板

```
1. 标题 分类 来源 · 发布时间
内容摘要...

📌 关键要点
- 涉及人物：XXX
- 涉及机构：XXX

📚 课本关联
九年级上册 · 创新驱动发展
内容摘要...
匹配：创新、发展

📖 AI总结
【新闻综述】
...
【核心要点】
...
【道法关联】
...
【思考问题】
...
```

### 5.2 九宫格卡片模板

```tsx
<div className="card">
  <h3>{date}</h3>
  <p>{newsCount}条新闻</p>
  <span className="tag">{category}</span>
</div>
```

## 六、运行指南

### 6.1 安装依赖
```bash
# Python依赖
pip install requests beautifulsoup4 tavily-python

# Node依赖
npm install
```

### 6.2 启动服务
```bash
# 启动后端API
python3 api/server.py

# 启动前端
npm run dev
```

### 6.3 定时采集
```bash
# 每天早上7点自动采集
crontab -e
0 7 * * * cd /path/to/dailynews && python3 scripts/collect/chinanews_fetcher.py
```
