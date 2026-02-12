#!/usr/bin/env python3
"""
生成中新热榜HTML报告
"""
import json
from datetime import datetime

# 配置
INPUT_FILE = "/Users/guanliming/dailynews/output/hotnews_detail.json"
OUTPUT_FILE = "/Users/guanliming/dailynews/output/report_latest.html"

def match_chapter(title, content):
    """匹配道法课本章节"""
    text = title + ' ' + (content[:500] if content else '')
    
    rules = [
        {'kws': ['台湾', '两岸', '台独', '国台办', '台海', '赖清德'], 'book': '九年级上册', 'chapter': '中华一家亲'},
        {'kws': ['反腐', '违纪', '违法', '受贿', '调查', '检察院', '法治', '行政复议'], 'book': '九年级上册', 'chapter': '民主与法治'},
        {'kws': ['国防', '解放军', '军队', '军事', '军营'], 'book': '九年级上册', 'chapter': '中华一家亲'},
        {'kws': ['航天', '月球', '卫星', '科技', '创新', 'AI', '风光发电', '人工心脏'], 'book': '九年级上册', 'chapter': '创新驱动发展'},
        {'kws': ['美国', '日本', '韩国', '国际', '加拿大', '印尼'], 'book': '九年级上册', 'chapter': '建设美丽中国'},
        {'kws': ['就业', '经济', '关税', '企业', '外贸', '消费', '金价', '汽车'], 'book': '九年级上册', 'chapter': '富强与创新'},
        {'kws': ['生活', '民生', '旅游', '文化', '教育', '学校'], 'book': '九年级上册', 'chapter': '建设美丽中国'},
        {'kws': ['交通', '安全', '事故', '环境'], 'book': '九年级上册', 'chapter': '建设美丽中国'},
    ]
    
    for rule in rules:
        for kw in rule['kws']:
            if kw in text:
                return f"{rule['book']} · {rule['chapter']}"
    
    return "九年级上册 · 民主与法治"

def main():
    print("📄 生成HTML报告...")
    
    # 读取JSON
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        news_list = json.load(f)
    
    # 按日期分组
    date_groups = {}
    for news in news_list:
        if news.get('status') != 'success':
            continue
        date = news.get('publish_date', '2026-02-12')
        if date not in date_groups:
            date_groups[date] = []
        date_groups[date].append(news)
    
    # 排序日期
    sorted_dates = sorted(date_groups.keys(), reverse=True)
    
    # 生成HTML
    today = datetime.now().strftime('%Y-%m-%d')
    total = sum(len(v) for v in date_groups.values())
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>道法时事报告 - {today}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh; padding: 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 20px; box-shadow: 0 25px 80px rgba(0,0,0,0.4); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%); color: white; padding: 35px; text-align: center; }}
        .header h1 {{ font-size: 32px; margin-bottom: 8px; }}
        .header p {{ opacity: 0.9; font-size: 14px; }}
        .stats {{ background: #f8f9fa; padding: 15px 30px; display: flex; gap: 30px; justify-content: center; font-size: 14px; color: #666; }}
        .content {{ padding: 30px; }}
        .date-section {{ margin-bottom: 40px; }}
        .date-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 20px; border-radius: 10px; margin-bottom: 20px; font-size: 16px; font-weight: bold; }}
        .news-item {{ background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 16px; padding: 24px; margin-bottom: 16px; border-left: 5px solid #e94560; }}
        .news-item:hover {{ transform: translateX(5px); transition: transform 0.2s; }}
        .news-top {{ display: flex; align-items: flex-start; margin-bottom: 12px; }}
        .news-rank {{ display: inline-block; background: #e94560; color: white; width: 28px; height: 28px; border-radius: 50%; text-align: center; line-height: 28px; font-size: 14px; font-weight: bold; margin-right: 12px; flex-shrink: 0; }}
        .news-title {{ font-size: 17px; font-weight: bold; color: #1a1a2e; line-height: 1.4; }}
        .news-meta {{ font-size: 12px; color: #666; margin: 10px 0; display: flex; gap: 15px; flex-wrap: wrap; }}
        .news-meta span {{ background: #e9ecef; padding: 4px 12px; border-radius: 15px; }}
        .news-summary {{ color: #444; line-height: 1.7; font-size: 14px; margin: 12px 0; }}
        .chapter-tag {{ display: inline-block; background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); color: #155724; padding: 8px 16px; border-radius: 8px; font-size: 13px; margin-top: 10px; }}
        .footer {{ text-align: center; padding: 20px; background: #f8f9fa; color: #666; font-size: 12px; }}
        .footer a {{ color: #e94560; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 道法时事报告</h1>
            <p>{today} · 共{total}条新闻 · 数据来源：中国新闻网热榜</p>
        </div>
        <div class="stats">
            <span>📊 日期：{len(date_groups)}天</span>
            <span>📝 新闻：{total}条</span>
            <span>📅 更新：{datetime.now().strftime('%H:%M')}</span>
        </div>
        <div class="content">
'''
    
    for date in sorted_dates:
        items = date_groups[date]
        html += f'''
            <div class="date-section">
                <div class="date-header">📅 {date}</div>
'''
        for i, news in enumerate(items, 1):
            chapter = match_chapter(news.get('title', ''), news.get('content', ''))
            html += f'''
                <div class="news-item">
                    <div class="news-top">
                        <span class="news-rank">{i}</span>
                        <span class="news-title">{news.get('title', '')}</span>
                    </div>
                    <div class="news-meta">
                        <span>📎 {news.get('source', '中国新闻网')}</span>
                        <span>📅 {news.get('time', date)}</span>
                        <span>📂 {news.get('channel', '要闻')}</span>
                    </div>
                    <div class="news-summary">{news.get('summary', '')[:200]}...</div>
                    <div class="chapter-tag">📚 {chapter}</div>
                </div>
'''
        html += '''
            </div>
'''
    
    html += '''
        </div>
        <div class="footer">
            <p>🤖 自动生成 by News Collector</p>
            <p>🔗 <a href="https://www.chinanews.com.cn/importnews.html">中国新闻网热榜</a></p>
        </div>
    </div>
</body>
</html>'''
    
    # 保存
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 报告已生成: {OUTPUT_FILE}")
    print(f"📊 包含 {total} 条新闻，{len(date_groups)} 个日期")

if __name__ == "__main__":
    main()
