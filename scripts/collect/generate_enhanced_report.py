#!/usr/bin/env python3
"""
生成增强版道法时事报告
- 完整内容
- 总结陈述
- 关键要点
- 课本关联（含相关度打分）
"""
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime

INPUT_FILE = "/Users/guanliming/dailynews/output/hotnews_detail.json"
OUTPUT_FILE = "/Users/guanliming/dailynews/output/report_latest.html"
BASE_URL = "https://www.chinanews.com.cn"

# 课本知识点库（包含核心内容）
TEXTBOOK_DB = {
    '中华一家亲': {
        'book': '九年级上册',
        'core': '维护祖国统一、民族团结是每个公民的责任和义务'
    },
    '民主与法治': {
        'book': '九年级上册', 
        'core': '依法治国是党领导人民治理国家的基本方略'
    },
    '创新驱动发展': {
        'book': '九年级上册',
        'core': '创新是引领发展的第一动力'
    },
    '建设美丽中国': {
        'book': '九年级上册',
        'core': '坚持人与自然和谐共生，建设美丽中国'
    },
    '富强与创新': {
        'book': '九年级上册',
        'core': '以人民为中心，实现共同富裕'
    },
    '踏上强国之路': {
        'book': '九年级上册',
        'core': '改革开放是决定当代中国命运的关键一招'
    },
    '文明与家园': {
        'book': '九年级上册',
        'core': '中华优秀传统文化是中华民族的精神命脉'
    },
    '中国人 中国梦': {
        'book': '九年级上册',
        'core': '实现中华民族伟大复兴是中华民族近代以来最伟大的梦想'
    },
}

def get_hot_rankings():
    """获取热榜前10条"""
    resp = requests.get(f"{BASE_URL}/importnews.html", timeout=15)
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    hotbox = soup.find(id="zxrb")
    hot_urls = []
    if hotbox:
        next_list = hotbox.find_next_sibling()
        if next_list:
            for link in next_list.find_all('a')[:10]:
                href = link.get('href', '')
                if href:
                    if href.startswith('//'):
                        url = 'https:' + href
                    elif href.startswith('/'):
                        url = BASE_URL + href
                    else:
                        url = href
                    parsed = urlparse(url)
                    hot_urls.append(parsed.path)
    return hot_urls

def extract_key_points(content, title):
    """提取关键要点"""
    points = []
    
    # 数字类信息
    nums = []
    for p in [r'(\d+\.\d+%)', r'(\d+万)', r'(\d+亿)', r'(\d{4}年)', r'(\d+)件', r'(\d+)人']:
        import re
        matches = re.findall(p, content)
        nums.extend([m for m in matches[:2]])
    
    if nums:
        points.append(f"📊 数据：{', '.join(nums[:2])}")
    
    # 机构
    orgs = re.findall(r'([^\s]{2,6}(部|委|局|办|政府))', content)
    for org in set([o[0] for o in orgs[:3]]):
        points.append(f"🏛️ 机构：{org}")
    
    return points

def match_chapters(text):
    """匹配课本章节（返回相关度）"""
    rules = [
        {'kws': ['台湾', '两岸', '台独', '国台办', '台海', '赖清德'], 'chapter': '中华一家亲', 'score': 90},
        {'kws': ['反腐', '违纪', '违法', '受贿', '调查', '检察院', '法治', '行政复议', '信访'], 'chapter': '民主与法治', 'score': 85},
        {'kws': ['国防', '解放军', '军队', '军事', '军营', '征兵'], 'chapter': '中华一家亲', 'score': 80},
        {'kws': ['航天', '月球', '卫星', '风光发电', '碳中和', '新能源'], 'chapter': '创新驱动发展', 'score': 85},
        {'kws': ['科技', '创新', 'AI', '互联网', '数字经济'], 'chapter': '创新驱动发展', 'score': 75},
        {'kws': ['美国', '日本', '韩国', '加拿大', '印尼', '国际'], 'chapter': '建设美丽中国', 'score': 70},
        {'kws': ['就业', '关税', '企业', '经济', '消费', '汽车', '外贸'], 'chapter': '富强与创新', 'score': 75},
        {'kws': ['旅游', '文化', '生活', '民生', '社会'], 'chapter': '建设美丽中国', 'score': 70},
        {'kws': ['交通', '安全', '事故', '环境'], 'chapter': '建设美丽中国', 'score': 72},
    ]
    
    import re
    matched = []
    for rule in rules:
        for kw in rule['kws']:
            if kw in text:
                matched.append((rule['chapter'], rule['score']))
                break
    
    # 去重并按分数排序
    seen = set()
    result = []
    for chapter, score in sorted(matched, key=lambda x: -x[1]):
        if chapter not in seen:
            seen.add(chapter)
            result.append({'chapter': chapter, 'score': score})
    
    # 只返回 >=70 分的
    return [r for r in result if r['score'] >= 70]

def generate_summary(content, title):
    """生成总结陈述"""
    if not content:
        return "暂无详细内容"
    
    # 提取关键句子
    import re
    sentences = re.split(r'[。！？]', content)
    important = []
    for s in sentences:
        if any(kw in s for kw in ['表示', '指出', '强调', '据', '通过', '实现', '达到', '完成']):
            important.append(s.strip())
        if len(important) >= 2:
            break
    
    if important:
        return important[0] + '。'
    return content[:200] + ('...' if len(content) > 200 else '')

def main():
    print("📄 生成增强版HTML报告...")
    
    # 读取JSON
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        all_news = json.load(f)
    
    # 获取热榜排名
    hot_paths = get_hot_rankings()
    
    # 排序
    ordered_news = []
    seen_paths = set()
    
    for hot_path in hot_paths:
        for news in all_news:
            if news.get('status') != 'success':
                continue
            path = urlparse(news.get('url', '')).path
            if path == hot_path and path not in seen_paths:
                ordered_news.append(news)
                seen_paths.add(path)
                break
    
    for news in all_news:
        if news.get('status') != 'success':
            continue
        path = urlparse(news.get('url', '')).path
        if path not in seen_paths:
            ordered_news.append(news)
            seen_paths.add(path)
    
    print(f"✅ 共 {len(ordered_news)} 条新闻")
    
    # 生成HTML
    today = datetime.now().strftime('%Y-%m-%d')
    
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
        .stats {{ background: #f8f9fa; padding: 15px 30px; display: flex; gap: 30px; justify-content: center; color: #666; }}
        .content {{ padding: 30px; }}
        .date-section {{ margin-bottom: 40px; }}
        .date-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 20px; border-radius: 10px; margin-bottom: 20px; font-size: 16px; font-weight: bold; }}
        .news-item {{ background: #fff; border-radius: 16px; padding: 24px; margin-bottom: 20px; border: 1px solid #e9ecef; }}
        .news-item:hover {{ box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
        .news-header {{ display: flex; align-items: flex-start; margin-bottom: 15px; }}
        .news-rank {{ background: #e94560; color: white; width: 32px; height: 32px; border-radius: 50%; text-align: center; line-height: 32px; font-weight: bold; margin-right: 15px; flex-shrink: 0; }}
        .news-title {{ font-size: 18px; font-weight: bold; color: #1a1a2e; line-height: 1.4; }}
        .hot-tag {{ background: #ff6b6b; color: white; padding: 3px 10px; border-radius: 4px; font-size: 12px; margin-left: 10px; }}
        .news-meta {{ font-size: 13px; color: #888; margin: 10px 0; display: flex; gap: 20px; }}
        .news-content {{ background: #f8f9fa; padding: 20px; border-radius: 12px; margin: 15px 0; }}
        .content-block {{ margin-bottom: 15px; }}
        .content-block:last-child {{ margin-bottom: 0; }}
        .block-label {{ font-size: 13px; font-weight: bold; color: #e94560; margin-bottom: 8px; }}
        .content-text {{ font-size: 14px; color: #444; line-height: 1.8; }}
        .key-points {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }}
        .key-point {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 6px 14px; border-radius: 20px; font-size: 13px; }}
        .chapter-tags {{ margin-top: 15px; }}
        .chapter-tag {{ display: inline-block; background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); color: #155724; padding: 10px 16px; border-radius: 8px; margin-right: 10px; margin-bottom: 10px; }}
        .chapter-name {{ font-weight: bold; font-size: 14px; }}
        .chapter-core {{ font-size: 12px; margin-top: 5px; opacity: 0.8; }}
        .chapter-score {{ background: rgba(0,0,0,0.1); padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-left: 8px; }}
        .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #888; font-size: 13px; }}
        .footer a {{ color: #e94560; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 道法时事报告</h1>
            <p>{today} · {len(ordered_news)}条新闻 · 数据来源：中国新闻网热榜</p>
        </div>
        <div class="stats">
            <span>📅 {datetime.now().strftime('%H:%M')} 更新</span>
            <span>🔥 热榜来源前10条</span>
        </div>
        <div class="content">
'''
    
    import re
    
    for i, news in enumerate(ordered_news[:20], 1):
        title = news.get('title', '')
        content = news.get('content', '')
        summary = generate_summary(content, title)
        key_points = extract_key_points(content, title)
        chapters = match_chapters(title + ' ' + content[:1000])
        
        hot_tag = '<span class="hot-tag">🔥 热榜</span>' if i <= 10 else ''
        
        html += f'''
            <div class="news-item">
                <div class="news-header">
                    <div class="news-rank">{i}</div>
                    <div class="news-title">{title}</div>
                    {hot_tag}
                </div>
                <div class="news-meta">
                    <span>📎 {news.get("source", "中国新闻网")}</span>
                    <span>📅 {news.get("time", "")}</span>
                    <span>📂 {news.get("channel", "要闻")}</span>
                </div>
                <div class="news-content">
'''
        
        # 完整内容
        html += f'''
                    <div class="content-block">
                        <div class="block-label">📰 新闻内容</div>
                        <div class="content-text">{content[:500]}{"..." if len(content) > 500 else ""}</div>
                    </div>
'''
        
        # 总结陈述
        html += f'''
                    <div class="content-block">
                        <div class="block-label">📝 总结陈述</div>
                        <div class="content-text">{summary}</div>
                    </div>
'''
        
        # 关键要点
        if key_points:
            html += '''
                    <div class="content-block">
                        <div class="block-label">🎯 关键要点</div>
                        <div class="key-points">
'''
            for point in key_points:
                html += f'<span class="key-point">{point}</span>'
            html += '''
                        </div>
                    </div>
'''
        
        # 课本关联
        if chapters:
            html += '''
                    <div class="chapter-tags">
                        <div class="block-label">📚 课本关联</div>
'''
            for ch in chapters:
                info = TEXTBOOK_DB.get(ch['chapter'], {'core': ''})
                html += f'''
                        <div class="chapter-tag">
                            <div class="chapter-name">{info['book']} · {ch['chapter']}<span class="chapter-score">相关度 {ch['score']}%</span></div>
                            <div class="chapter-core">💡 {info['core']}</div>
                        </div>
'''
            html += '''
                    </div>
'''
        
        html += '''
                </div>
            </div>
'''
    
    html += '''
        </div>
        <div class="footer">
            <p>🤖 自动生成 by 道法时事报告系统</p>
            <p>🔗 <a href="https://www.chinanews.com.cn/importnews.html">中国新闻网热榜</a></p>
        </div>
    </div>
</body>
</html>'''
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ 报告已生成: {OUTPUT_FILE}")
    print(f"📊 前3条预览：")
    for i, n in enumerate(ordered_news[:3], 1):
        chapters = match_chapters(n.get('title', '') + ' ' + n.get('content', '')[:500])
        print(f"  {i}. {n.get('title', '')[:35]}...")
        print(f"     课本: {[c['chapter'] for c in chapters]}")

if __name__ == "__main__":
    main()
