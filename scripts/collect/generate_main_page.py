#!/usr/bin/env python3
"""
生成道法时事报告主页面（九宫格布局）
- 按日期倒序排列
- 每个格子显示：日期、新闻数量、知识点数、TOP1新闻缩略
"""
import json
import sqlite3
from datetime import datetime, timedelta

INPUT_JSON = "/Users/guanliming/dailynews/output/hotnews_detail.json"
OUTPUT_HTML = "/Users/guanliming/dailynews/output/index.html"
DB_PATH = "/Users/guanliming/dailynews/turso/reports.db"

def get_daofa_chapters_for_date(date):
    """获取某天的道法知识点"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 这里可以根据需要查询道法知识点表
    cursor.execute("SELECT COUNT(*) FROM daofa_textbooks")
    total = cursor.fetchone()[0]
    conn.close()
    return total

def calculate_daily_stats(news_list, target_date):
    """计算某天的统计信息"""
    day_news = [n for n in news_list if n.get('publish_date') == target_date and n.get('status') == 'success']
    
    if not day_news:
        return None
    
    # TOP1新闻
    top1 = day_news[0]
    
    # 道法知识点匹配
    keywords = ['法治', '民主', '创新', '美丽中国', '富强', '强国', '文明', '中国梦', 
                '台湾', '两岸', '反腐', '航天', '科技', '经济', '文化', '社会']
    chapter_count = 0
    matched_kws = set()
    for news in day_news[:5]:  # 只检查前5条
        text = (news.get('title', '') + ' ' + news.get('content', ''))[:500]
        for kw in keywords:
            if kw in text:
                matched_kws.add(kw)
    
    return {
        'date': target_date,
        'news_count': len(day_news),
        'top1_title': top1.get('title', '')[:40],
        'top1_summary': top1.get('summary', '')[:100] + '...',
        'chapter_count': len(matched_kws),
        'chapters': list(matched_kws)[:5],
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
            return "今天"
        elif date_str == (today - timedelta(days=1)).strftime('%Y-%m-%d'):
            return "昨天"
        else:
            return f"{date.month}月{date.day}日"
    except:
        return date_str

def main():
    print("🏠 生成主页面（九宫格）...")
    
    # 读取新闻数据
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        news_list = json.load(f)
    
    # 获取所有日期
    dates = get_date_range(news_list)
    
    # 计算每天统计
    daily_data = []
    for date in dates:
        stats = calculate_daily_stats(news_list, date)
        if stats:
            daily_data.append(stats)
    
    print(f"✅ 共 {len(daily_data)} 天的数据")
    
    # 生成HTML
    today = datetime.now().strftime('%Y-%m-%d')
    
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>道法时事报告</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh; padding: 30px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { 
            text-align: center; 
            color: white; 
            padding: 40px 20px;
            margin-bottom: 40px;
        }
        .header h1 { font-size: 42px; margin-bottom: 15px; }
        .header p { font-size: 16px; opacity: 0.85; }
        .stats-bar { 
            background: rgba(255,255,255,0.1); 
            padding: 20px; 
            border-radius: 16px; 
            margin-bottom: 40px;
            display: flex; 
            justify-content: center; 
            gap: 50px;
            color: white;
        }
        .stat-item { text-align: center; }
        .stat-num { font-size: 28px; font-weight: bold; color: #ff6b6b; }
        .stat-label { font-size: 13px; opacity: 0.8; margin-top: 5px; }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); 
            gap: 25px; 
        }
        .card { 
            background: white; 
            border-radius: 20px; 
            overflow: hidden;
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
            transition: transform 0.3s, box-shadow 0.3s;
            cursor: pointer;
            text-decoration: none;
            color: inherit;
            display: block;
        }
        .card:hover { 
            transform: translateY(-8px); 
            box-shadow: 0 25px 60px rgba(0,0,0,0.4);
        }
        .card-header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 20px 25px;
            color: white;
        }
        .card-date { font-size: 26px; font-weight: bold; }
        .card-week { font-size: 13px; opacity: 0.85; margin-top: 5px; }
        .card-body { padding: 25px; }
        .card-stats { 
            display: flex; 
            gap: 20px; 
            margin-bottom: 20px;
        }
        .stat-pill { 
            background: #f0f4ff; 
            padding: 8px 16px; 
            border-radius: 20px;
            font-size: 13px;
            color: #667eea;
            font-weight: 600;
        }
        .card-preview { 
            background: #f8f9fa; 
            padding: 18px; 
            border-radius: 12px;
            margin-bottom: 15px;
        }
        .preview-label { 
            font-size: 12px; 
            color: #ff6b6b; 
            margin-bottom: 8px;
            font-weight: 600;
        }
        .preview-title { 
            font-size: 15px; 
            font-weight: bold; 
            color: #1a1a2e;
            margin-bottom: 8px;
            line-height: 1.4;
        }
        .preview-summary { 
            font-size: 13px; 
            color: #666; 
            line-height: 1.6;
        }
        .card-tags { 
            display: flex; 
            flex-wrap: wrap; 
            gap: 8px; 
        }
        .tag { 
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
            color: #155724;
            padding: 5px 12px; 
            border-radius: 12px;
            font-size: 12px;
        }
        .card-footer { 
            background: #f8f9fa; 
            padding: 15px 25px; 
            text-align: right;
            border-top: 1px solid #eee;
        }
        .read-more { 
            color: #667eea; 
            font-size: 14px; 
            font-weight: 600;
        }
        .empty-state { 
            text-align: center; 
            color: white; 
            padding: 60px;
            font-size: 18px;
        }
        .subscription-section {
            margin-top: 50px;
            background: white;
            border-radius: 20px;
            padding: 40px;
            text-align: center;
        }
        .subscription-section h2 { 
            font-size: 24px; 
            margin-bottom: 15px;
            color: #1a1a2e;
        }
        .subscription-section p { 
            color: #666; 
            margin-bottom: 25px;
        }
        .subscribe-btn {
            background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 30px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .subscribe-btn:hover { transform: scale(1.05); }
        .footer {
            text-align: center;
            padding: 40px;
            color: rgba(255,255,255,0.5);
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 道法时事报告</h1>
            <p>每日精选时事新闻，关联道法课本知识点</p>
        </div>
        
        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-num">''' + str(len(news_list)) + '''</div>
                <div class="stat-label">📝 新闻总数</div>
            </div>
            <div class="stat-item">
                <div class="stat-num">''' + str(len(daily_data)) + '''</div>
                <div class="stat-label">📅 报道天数</div>
            </div>
            <div class="stat-item">
                <div class="stat-num">7</div>
                <div class="stat-label">📚 道法课本</div>
            </div>
        </div>
        
        <div class="grid">
'''
    
    # 生成每个日期的卡片
    for data in daily_data:
        date_label = generate_date_label(data['date'])
        
        # 获取星期几
        try:
            week = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][datetime.strptime(data['date'], '%Y-%m-%d').weekday()]
        except:
            week = ''
        
        # 生成标签
        tags_html = ''.join([f'<span class="tag">{ch}</span>' for ch in data['chapters'][:4]])
        
        html += f'''
            <a href="report_latest.html" class="card">
                <div class="card-header">
                    <div class="card-date">{date_label}</div>
                    <div class="card-week">{data['date']}</div>
                </div>
                <div class="card-body">
                    <div class="card-stats">
                        <span class="stat-pill">📝 {data['news_count']}条新闻</span>
                        <span class="stat-pill">📚 {data['chapter_count']}个知识点</span>
                    </div>
                    <div class="card-preview">
                        <div class="preview-label">🔥 今日头条</div>
                        <div class="preview-title">{data['top1_title']}</div>
                        <div class="preview-summary">{data['top1_summary']}</div>
                    </div>
                    <div class="card-tags">
                        {tags_html}
                    </div>
                </div>
                <div class="card-footer">
                    <span class="read-more">查看详情 →</span>
                </div>
            </a>
'''
    
    html += '''
        </div>
        
        <div class="subscription-section">
            <h2>📬 订阅每日时事报告</h2>
            <p>每天自动获取最新时事新闻，智能匹配道法课本知识点</p>
            <button class="subscribe-btn" onclick="alert('订阅功能开发中，敬请期待！')">
                订阅每日报告
            </button>
        </div>
        
        <div class="footer">
            <p>🤖 自动生成 by 道法时事报告系统</p>
            <p>🔗 数据来源：<a href="https://www.chinanews.com.cn/importnews.html" style="color:#ff6b6b">中国新闻网热榜</a></p>
        </div>
    </div>
</body>
</html>'''
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ 主页面已生成: {OUTPUT_HTML}")
    print(f"\n📊 九宫格预览：")
    for data in daily_data[:3]:
        print(f"  📅 {data['date']}: {data['news_count']}条新闻, {data['chapter_count']}个知识点")

if __name__ == "__main__":
    main()
