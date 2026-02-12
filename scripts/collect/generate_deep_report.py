#!/usr/bin/env python3
"""
生成道法时事报告（深度版）
- 总结陈述：基于文章深度总结
- 课本关联：完整章节观点
"""
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime

INPUT_FILE = "/Users/guanliming/dailynews/output/hotnews_detail.json"
OUTPUT_FILE = "/Users/guanliming/dailynews/output/report_latest.html"
BASE_URL = "https://www.chinanews.com.cn"

# 课本章节详细知识点库（扩展版）
TEXTBOOK_DB = {
    '中华一家亲': {
        'book': '九年级上册',
        'core': '维护祖国统一、民族团结是每个公民的责任和义务',
        'points': [
            '坚持一个中国原则是处理台湾问题的政治基础',
            '加强民族团结，维护国家统一是各民族的共同愿望',
            '实现祖国完全统一是全体中华儿女的共同愿望',
            '坚持"和平统一、一国两制"方针',
        ]
    },
    '民主与法治': {
        'book': '九年级上册',
        'core': '依法治国是党领导人民治理国家的基本方略',
        'points': [
            '法治是人类社会进入现代文明的重要标志',
            '法治要求实行良法之治和善治',
            '法治是解决社会矛盾、维护社会稳定、实现社会公正的有效方式',
            '依法行政是依法治国的重要环节',
            '行政复议是公民维护合法权益的重要途径',
        ]
    },
    '创新驱动发展': {
        'book': '九年级上册',
        'core': '创新是引领发展的第一动力',
        'points': [
            '创新是一个民族进步的灵魂，是国家兴旺发达的不竭动力',
            '科技创新是提高社会生产力和综合国力的战略支撑',
            '建设创新型国家，要坚持自主创新、重点跨越',
            '创新驱动发展战略是建设现代化经济体系的战略支撑',
            '科技强国战略推动中国向世界科技强国迈进',
        ]
    },
    '建设美丽中国': {
        'book': '九年级上册',
        'core': '坚持人与自然和谐共生，建设美丽中国',
        'points': [
            '生态兴则文明兴，生态衰则文明衰',
            '坚持节约资源和保护环境的基本国策',
            '坚持绿色发展理念，走生产发展、生活富裕、生态良好的文明发展道路',
            '推动形成绿色发展方式和生活方式',
            '生态环境保护是功在当代、利在千秋的事业',
        ]
    },
    '富强与创新': {
        'book': '九年级上册',
        'core': '以人民为中心，实现共同富裕',
        'points': [
            '以人民为中心的发展思想是新时代坚持和发展中国特色社会主义的根本立场',
            '共同富裕是社会主义的本质要求',
            '全面深化改革是推进中国特色社会主义事业的强大动力',
            '坚持和完善社会主义基本经济制度',
            '推动高质量发展，构建新发展格局',
        ]
    },
    '踏上强国之路': {
        'book': '九年级上册',
        'core': '改革开放是决定当代中国命运的关键一招',
        'points': [
            '改革开放是党和人民大踏步赶上时代的重要法宝',
            '坚持党的领导是中国特色社会主义最本质的特征',
            '坚持全面深化改革，不断推进国家治理体系和治理能力现代化',
            '对外开放是我国的基本国策，是国家繁荣发展的必由之路',
        ]
    },
    '文明与家园': {
        'book': '九年级上册',
        'core': '中华优秀传统文化是中华民族的精神命脉',
        'points': [
            '中华优秀传统文化是中华民族的精神命脉',
            '文化自信是更基础、更广泛、更深厚的自信',
            '培育和践行社会主义核心价值观',
            '传承中华优秀传统文化，推动创造性转化和创新性发展',
            '建设社会主义文化强国',
        ]
    },
    '中国人 中国梦': {
        'book': '九年级上册',
        'core': '实现中华民族伟大复兴是中华民族近代以来最伟大的梦想',
        'points': [
            '实现中华民族伟大复兴是近代以来中华民族最伟大的梦想',
            '中国梦是国家的梦、民族的梦，也是每个中国人的梦',
            '实现中国梦必须走中国道路、弘扬中国精神、凝聚中国力量',
            '全面建成小康社会是实现中国梦的关键一步',
            '为实现第二个百年奋斗目标、实现中国梦而不懈努力',
        ]
    },
}

def get_hot_rankings():
    resp = requests.get(f"{BASE_URL}/importnews.html", timeout=15)
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')
    hotbox = soup.find(id="zxrb")
    hot_paths = []
    if hotbox:
        next_list = hotbox.find_next_sibling()
        if next_list:
            for link in next_list.find_all('a')[:10]:
                href = link.get('href', '')
                if href.startswith('//'):
                    url = 'https:' + href
                elif href.startswith('/'):
                    url = BASE_URL + href
                else:
                    url = href
                hot_paths.append(urlparse(url).path)
    return hot_paths

def generate_summary(content, title):
    """深度总结：保留完整内容，格式化输出"""
    if not content:
        return "该新闻暂无详细报道内容。"
    
    import re
    
    # 清理内容
    content = re.sub(r'\s+', ' ', content)
    content = content.strip()
    
    # 限制总长度但确保完整句子
    if len(content) > 600:
        # 在句号处截断
        last_dot = content[:600].rfind('。')
        if last_dot > 200:
            content = content[:last_dot + 1]
        else:
            content = content[:600] + "..."
    
    # 添加适当的换行以便于阅读
    sentences = re.split(r'([。！？])', content)
    formatted = []
    current = ""
    
    for i, part in enumerate(sentences):
        current += part
        if part in '。！？' and current.strip():
            # 清理并添加
            line = current.strip()
            if line and not line.endswith('...'):
                formatted.append(line)
            current = ""
    
    if current.strip():
        formatted.append(current.strip())
    
    return '<br>'.join(formatted) if formatted else content

def match_chapters(text):
    rules = [
        {'kws': ['台湾', '两岸', '台独', '国台办', '台海', '赖清德'], 'chapter': '中华一家亲', 'score': 90},
        {'kws': ['反腐', '违纪', '违法', '受贿', '调查', '检察院', '法治', '行政复议', '信访'], 'chapter': '民主与法治', 'score': 85},
        {'kws': ['国防', '解放军', '军队', '军事', '军营', '征兵'], 'chapter': '中华一家亲', 'score': 80},
        {'kws': ['航天', '月球', '卫星', '风光发电', '碳中和', '新能源', '人工心脏'], 'chapter': '创新驱动发展', 'score': 85},
        {'kws': ['科技', '创新', 'AI', '互联网', '数字经济'], 'chapter': '创新驱动发展', 'score': 75},
        {'kws': ['美国', '日本', '韩国', '加拿大', '印尼', '国际'], 'chapter': '建设美丽中国', 'score': 70},
        {'kws': ['就业', '关税', '企业', '经济', '消费', '汽车', '外贸'], 'chapter': '富强与创新', 'score': 75},
        {'kws': ['旅游', '文化', '生活', '民生', '社会'], 'chapter': '建设美丽中国', 'score': 70},
        {'kws': ['交通', '安全', '事故', '环境'], 'chapter': '建设美丽中国', 'score': 72},
        {'kws': ['改革', '开放', '发展'], 'chapter': '踏上强国之路', 'score': 72},
        {'kws': ['文化', '传统', '文明'], 'chapter': '文明与家园', 'score': 70},
        {'kws': ['复兴', '梦想', '强国'], 'chapter': '中国人 中国梦', 'score': 75},
    ]
    
    matched = []
    for rule in rules:
        for kw in rule['kws']:
            if kw in text:
                matched.append((rule['chapter'], rule['score']))
                break
    
    seen = set()
    result = []
    for chapter, score in sorted(matched, key=lambda x: -x[1]):
        if chapter not in seen:
            seen.add(chapter)
            result.append({'chapter': chapter, 'score': score})
    
    return [r for r in result if r['score'] >= 80]

def main():
    print("📄 生成深度版HTML报告...")
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        all_news = json.load(f)
    
    hot_paths = get_hot_rankings()
    
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
    
    today = datetime.now().strftime('%Y-%m-%d')
    update_time = datetime.now().strftime('%H:%M')
    
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
        .container {{ max-width: 950px; margin: 0 auto; background: white; border-radius: 20px; box-shadow: 0 25px 80px rgba(0,0,0,0.4); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%); color: white; padding: 40px 35px; text-align: center; }}
        .header h1 {{ font-size: 36px; margin-bottom: 10px; }}
        .header p {{ font-size: 15px; opacity: 0.9; }}
        .stats {{ background: #f8f9fa; padding: 18px 35px; display: flex; gap: 40px; justify-content: center; color: #666; font-size: 14px; }}
        .content {{ padding: 35px; }}
        .news-item {{ background: #fff; border-radius: 16px; padding: 28px; margin-bottom: 25px; border: 1px solid #e9ecef; }}
        .news-header {{ display: flex; align-items: flex-start; margin-bottom: 18px; }}
        .news-rank {{ background: #e94560; color: white; width: 36px; height: 36px; border-radius: 50%; text-align: center; line-height: 36px; font-weight: bold; font-size: 16px; margin-right: 18px; flex-shrink: 0; }}
        .news-title {{ font-size: 20px; font-weight: bold; color: #1a1a2e; line-height: 1.45; }}
        .hot-tag {{ background: #ff6b6b; color: white; padding: 4px 12px; border-radius: 4px; font-size: 13px; margin-left: 12px; }}
        .news-meta {{ font-size: 14px; color: #888; margin: 12px 0; display: flex; gap: 25px; }}
        .summary-section {{ background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; padding: 22px; margin: 18px 0; }}
        .summary-header {{ display: flex; align-items: center; margin-bottom: 14px; }}
        .summary-label {{ font-size: 16px; font-weight: bold; color: #e94560; display: flex; align-items: center; gap: 8px; }}
        .content-link {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 7px 18px; border-radius: 6px; font-size: 13px; text-decoration: none; margin-left: auto; }}
        .content-link:hover {{ opacity: 0.9; }}
        .summary-text {{ font-size: 15px; color: #444; line-height: 1.95; }}
        .chapter-section {{ margin-top: 20px; }}
        .chapter-header {{ font-size: 16px; font-weight: bold; color: #28a745; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }}
        .chapter-tag {{ display: block; background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); color: #155724; padding: 18px 22px; border-radius: 10px; margin-bottom: 14px; }}
        .chapter-book {{ font-weight: bold; font-size: 15px; margin-bottom: 8px; }}
        .chapter-core {{ font-size: 14px; font-weight: 600; color: #0d6e34; margin-bottom: 10px; }}
        .chapter-points {{ font-size: 13px; color: #444; line-height: 1.8; }}
        .chapter-points li {{ margin-bottom: 6px; margin-left: 18px; }}
        .chapter-score {{ background: rgba(0,0,0,0.1); padding: 3px 10px; border-radius: 12px; font-size: 12px; margin-left: 10px; }}
        .footer {{ background: #f8f9fa; padding: 25px; text-align: center; color: #888; font-size: 14px; }}
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
            <span>🕐 {update_time} 更新</span>
            <span>🔥 热榜来源前10条优先展示</span>
            <span>📚 课本关联仅显示相关度≥70%</span>
        </div>
        <div class="content">
'''
    
    import re
    
    for i, news in enumerate(ordered_news[:25], 1):
        title = news.get('title', '')
        content = news.get('content', '')
        url = news.get('url', '#')
        summary = generate_summary(content, title)
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
                <div class="summary-section">
                    <div class="summary-header">
                        <div class="summary-label">📝 总结陈述</div>
                        <a href="{url}" target="_blank" class="content-link">📰 查看原文详情</a>
                    </div>
                    <div class="summary-text">{summary}</div>
                </div>
'''
        
        if chapters:
            html += '''
                <div class="chapter-section">
                    <div class="chapter-header">📚 课本关联</div>
'''
            for ch in chapters:
                info = TEXTBOOK_DB.get(ch['chapter'], {'core': '', 'points': []})
                html += f'''
                    <div class="chapter-tag">
                        <div class="chapter-book">{info['book']} · {ch['chapter']}<span class="chapter-score">相关度 {ch['score']}%</span></div>
                        <div class="chapter-core">核心观点：{info['core']}</div>
                        <ul class="chapter-points">
'''
                for point in info['points'][:3]:
                    html += f'<li>{point}</li>'
                html += '''
                        </ul>
                    </div>
'''
            html += '''
                </div>
'''
        
        html += '''
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
    print(f"\n📊 第1条预览：")
    n = ordered_news[0]
    print(f"标题: {n.get('title', '')}")
    print(f"\n总结陈述（前200字）:\n{generate_summary(n.get('content', ''), n.get('title', ''))[:200]}...")

if __name__ == "__main__":
    main()
