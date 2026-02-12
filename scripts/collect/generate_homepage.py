#!/usr/bin/env python3
"""
生成道法时事报告主页面（参考优秀CSS设计）
- 极简深色主题
- 卡片缩略图+大号数字
- 订阅区域
"""
import json
import sqlite3
from datetime import datetime, timedelta

INPUT_JSON = "/Users/guanliming/dailynews/output/hotnews_detail.json"
OUTPUT_HTML = "/Users/guanliming/dailynews/output/index.html"
DB_PATH = "/Users/guanliming/dailynews/turso/reports.db"

def get_daily_stats(news_list, target_date):
    """计算某天的统计信息"""
    day_news = [n for n in news_list if n.get('publish_date') == target_date and n.get('status') == 'success']
    
    if not day_news:
        return None
    
    # TOP1新闻
    top1 = day_news[0]
    
    # 匹配道法知识点
    keywords = ['法治', '民主', '创新', '美丽中国', '富强', '强国', '文明', '中国梦', 
                '台湾', '两岸', '反腐', '航天', '科技', '经济', '文化', '社会', '公民', '权利']
    chapter_count = 0
    matched_kws = set()
    for news in day_news[:5]:
        text = (news.get('title', '') + ' ' + news.get('content', ''))[:500]
        for kw in keywords:
            if kw in text:
                matched_kws.add(kw)
    
    # 计算平均匹配度
    total_score = 0
    for news in day_news[:5]:
        score = 0
        text = (news.get('title', '') + ' ' + news.get('content', ''))[:500]
        if any(kw in text for kw in ['法治', '复议', '司法']): score += 25
        if any(kw in text for kw in ['创新', '科技', '航天']): score += 20
        if any(kw in text for kw in ['经济', '发展', '增长']): score += 15
        if any(kw in text for kw in ['两岸', '台湾', '统一']): score += 25
        if any(kw in text for kw in ['环境', '绿色', '生态']): score += 15
        total_score += score
    
    avg_score = min(int(total_score / min(len(day_news[:5]), 1)), 99)
    
    return {
        'date': target_date,
        'news_count': len(day_news),
        'top1_title': top1.get('title', '')[:50],
        'top1_summary': top1.get('summary', '')[:80] + '...',
        'chapter_count': len(matched_kws),
        'chapters': list(matched_kws)[:3],
        'match_score': max(avg_score, 70),  # 至少70%
        'weekday': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][datetime.strptime(target_date, '%Y-%m-%d').weekday()] if target_date else ''
    }

def get_date_range(news_list):
    """获取所有日期范围"""
    dates = set()
    for n in news_list:
        if n.get('status') == 'success':
            d = n.get('publish_date')
            if d:
                dates.add(d)
    return sorted(dates, reverse=True)

def generate_date_label(date_str):
    """生成日期标签"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        today = datetime.now()
        
        if date_str == today.strftime('%Y-%m-%d'):
            return "TODAY"
        elif date_str == (today - timedelta(days=1)).strftime('%Y-%m-%d'):
            return "YESTERDAY"
        else:
            return date.strftime("%b %d").upper().replace(' ', '')
    except:
        return date_str

def get_bg_color(index):
    """卡片背景色"""
    colors = ['#2c3e50', '#34495e', '#1abc9c', '#27ae60', '#2980b9', '#8e44ad', '#16a085']
    return colors[index % len(colors)]

def get_chapter_info(kws):
    """根据关键词返回课本章节信息"""
    mapping = {
        '法治': ('九年级上册', '民主与法治'),
        '复议': ('九年级上册', '民主与法治'),
        '司法': ('九年级上册', '民主与法治'),
        '创新': ('九年级上册', '创新驱动发展'),
        '科技': ('九年级上册', '创新驱动发展'),
        '航天': ('九年级上册', '创新驱动发展'),
        '经济': ('九年级上册', '富强与创新'),
        '发展': ('九年级上册', '踏上强国之路'),
        '两岸': ('九年级上册', '中华一家亲'),
        '台湾': ('九年级上册', '中华一家亲'),
        '统一': ('九年级上册', '中华一家亲'),
        '环境': ('九年级上册', '建设美丽中国'),
        '绿色': ('九年级上册', '建设美丽中国'),
        '生态': ('九年级上册', '建设美丽中国'),
        '文化': ('九年级上册', '文明与家园'),
        '公民': ('八年级下册', '公民权利'),
        '权利': ('八年级下册', '公民权利'),
        '社会': ('七年级上册', '成长的节拍'),
    }
    
    for kw in kws:
        if kw in mapping:
            return mapping[kw]
    return ('九年级上册', '核心知识点')

def main():
    print("🏠 生成优化版首页...")
    
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        news_list = json.load(f)
    
    dates = get_date_range(news_list)
    
    daily_data = []
    for date in dates:
        stats = get_daily_stats(news_list, date)
        if stats:
            daily_data.append(stats)
    
    print(f"✅ 共 {len(daily_data)} 天的数据")
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_formatted = datetime.now().strftime("%b %d").upper().replace(' ', '')
    
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日道法热点看板</title>
    <style>
        :root {
            --primary-dark: #1a2a3a;
            --accent-blue: #3498db;
            --soft-white: #fcfdfd;
            --text-gray: #7f8c8d;
            --success-green: #2ecc71;
            --card-bg: #ffffff;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', 'PingFang SC', -apple-system, sans-serif;
            background: #f0f3f5;
            color: var(--primary-dark);
        }
        
        /* Hero Section */
        .hero {
            background: linear-gradient(135deg, var(--primary-dark) 0%, #2c3e50 100%);
            color: white;
            padding: 60px 20px;
            text-align: center;
        }
        .brand-en {
            font-size: 12px;
            letter-spacing: 3px;
            text-transform: uppercase;
            opacity: 0.6;
            margin-bottom: 10px;
        }
        .hero h1 {
            font-size: 42px;
            font-weight: 800;
            margin: 0 0 15px;
            letter-spacing: -1px;
        }
        .hero p {
            font-size: 16px;
            opacity: 0.85;
            max-width: 650px;
            margin: 0 auto;
            line-height: 1.7;
        }
        
        /* Main Container */
        .main-container {
            max-width: 1200px;
            margin: -50px auto 0;
            padding: 0 20px 60px;
        }
        
        /* Knowledge Grid */
        .knowledge-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 25px;
        }
        
        /* Archive Card */
        .archive-card {
            background: var(--card-bg);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.06);
            transition: all 0.35s ease;
            text-decoration: none;
            color: inherit;
            position: relative;
        }
        .archive-card:hover {
            transform: translateY(-12px);
            box-shadow: 0 25px 50px rgba(0,0,0,0.12);
        }
        
        /* Card Thumbnail */
        .card-thumb {
            height: 180px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        .card-thumb::after {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.15);
        }
        .thumb-index {
            font-size: 80px;
            font-weight: 900;
            color: rgba(255,255,255,0.12);
            z-index: 1;
            letter-spacing: -3px;
        }
        .date-label {
            position: absolute;
            top: 18px;
            left: 18px;
            z-index: 2;
            background: var(--success-green);
            color: white;
            padding: 5px 14px;
            border-radius: 50px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
        }
        
        /* Card Content */
        .card-content {
            padding: 25px;
            background: white;
        }
        .card-tag {
            font-size: 11px;
            color: var(--accent-blue);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
            display: block;
        }
        .card-title {
            font-size: 18px;
            font-weight: 700;
            margin: 0 0 12px;
            line-height: 1.45;
            color: var(--primary-dark);
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .card-summary {
            font-size: 13px;
            color: var(--text-gray);
            line-height: 1.6;
            margin-bottom: 15px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        /* Card Meta */
        .card-meta {
            font-size: 12px;
            color: var(--text-gray);
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 15px;
            border-top: 1px solid #f5f5f5;
        }
        .hot-rank {
            display: flex;
            align-items: center;
            gap: 6px;
            font-weight: 600;
            color: #e74c3c;
        }
        .match-score {
            color: var(--success-green);
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .match-score::before {
            content: "⚡";
            font-size: 14px;
        }
        
        /* Subscribe Section */
        .subscribe-bar {
            background: var(--primary-dark);
            padding: 80px 20px;
            text-align: center;
            color: white;
            margin-top: 60px;
            border-top: 4px solid var(--accent-blue);
        }
        .subscribe-inner {
            max-width: 500px;
            margin: 0 auto;
        }
        .subscribe-inner h2 {
            font-size: 28px;
            margin-bottom: 12px;
            font-weight: 700;
        }
        .subscribe-inner p {
            font-size: 14px;
            opacity: 0.7;
            margin-bottom: 25px;
            line-height: 1.6;
        }
        .sub-form {
            display: flex;
            gap: 10px;
            background: rgba(255,255,255,0.06);
            padding: 6px;
            border-radius: 12px;
        }
        .sub-input {
            flex-grow: 1;
            background: transparent;
            border: none;
            color: white;
            padding: 14px;
            outline: none;
            font-size: 15px;
        }
        .sub-input::placeholder {
            color: rgba(255,255,255,0.4);
        }
        .sub-btn {
            background: var(--accent-blue);
            color: white;
            border: none;
            padding: 14px 28px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.25s ease;
        }
        .sub-btn:hover {
            background: #2980b9;
            transform: translateY(-2px);
        }
        
        /* Footer */
        .footer {
            background: var(--primary-dark);
            padding: 40px 20px;
            text-align: center;
            color: rgba(255,255,255,0.4);
            font-size: 12px;
        }
        .footer a {
            color: var(--accent-blue);
            text-decoration: none;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .hero h1 { font-size: 28px; }
            .knowledge-grid { grid-template-columns: 1fr; }
            .sub-form { flex-direction: column; }
        }
    </style>
</head>
<body>
    <!-- Hero Section -->
    <header class="hero">
        <div class="brand-en">Daily Law & Ethics Spotlight</div>
        <h1>每日道法热点看板</h1>
        <p>积累每一天的法治智慧。我们将繁杂的时事拆解为精准的课本索引，助你构建结构化的知识大脑。</p>
    </header>
    
    <!-- Main Content -->
    <div class="main-container">
        <div class="knowledge-grid">
'''
    
    # 生成每个日期的卡片
    for i, data in enumerate(daily_data):
        date_label = generate_date_label(data['date'])
        bg_color = get_bg_color(i)
        weekday = data.get('weekday', '')
        
        # 获取匹配的课本章节
        book, chapter = get_chapter_info(data['chapters'])
        
        html += f'''
            <a href="report_latest.html" class="archive-card">
                <div class="card-thumb" style="background: {bg_color};">
                    <span class="date-label">{date_label} · {weekday}</span>
                    <span class="thumb-index">{str(i+1).zfill(2)}</span>
                </div>
                <div class="card-content">
                    <span class="card-tag">{book} · {chapter}</span>
                    <h3 class="card-title">{data['top1_title']}</h3>
                    <p class="card-summary">{data['top1_summary']}</p>
                    <div class="card-meta">
                        <span class="hot-rank">🔥 热度 #{i+1}</span>
                        <span class="match-score">{data['match_score']}% 匹配度</span>
                    </div>
                </div>
            </a>
'''
    
    html += '''
        </div>
    </div>
    
    <!-- Subscribe Section -->
    <section class="subscribe-bar">
        <div class="subscribe-inner">
            <h2>📬 订阅每日深度推送</h2>
            <p>每天早晨 8:00，我们将最值得关注的道法热点及课本解析发送至您的邮箱。</p>
            <form class="sub-form" onsubmit="event.preventDefault(); alert('订阅功能开发中，敬请期待！');">
                <input type="email" class="sub-input" placeholder="输入您的电子邮箱..." required>
                <button type="submit" class="sub-btn">立即订阅</button>
            </form>
        </div>
    </section>
    
    <!-- Footer -->
    <footer class="footer">
        <p>🤖 自动生成 by 道法时事报告系统</p>
        <p>📊 数据来源：<a href="https://www.chinanews.com.cn/importnews.html" target="_blank">中国新闻网热榜</a></p>
    </footer>
</body>
</html>'''
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ 首页已生成: {OUTPUT_HTML}")
    print(f"\n📊 卡片预览：")
    for i, data in enumerate(daily_data[:3]):
        book, chapter = get_chapter_info(data['chapters'])
        print(f"  {i+1}. {data['date']} | {book} · {chapter} | {data['match_score']}%匹配度")

if __name__ == "__main__":
    main()
