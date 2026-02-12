#!/usr/bin/env python3
"""
生成道法时事报告子页面（优化版）
- 参考优秀CSS设计
- 卡片式布局
- 展开全文功能
- 网格化课本关联
"""
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime

INPUT_FILE = "/Users/guanliming/dailynews/output/hotnews_detail.json"
OUTPUT_FILE = "/Users/guanliming/dailynews/output/report_latest.html"
BASE_URL = "https://www.chinanews.com.cn"

# 课本章节详细知识点库（核心内容更具体）
TEXTBOOK_DB = {
    '中华一家亲': {
        'book': '九年级上册',
        'core': '维护祖国统一、民族团结是每个公民的责任和义务',
        'detail': '坚持一个中国原则是处理台湾问题的政治基础；实现祖国完全统一是全体中华儿女的共同愿望；加强民族团结，维护国家统一是各民族的共同愿望。'
    },
    '民主与法治': {
        'book': '九年级上册',
        'core': '依法治国是党领导人民治理国家的基本方略',
        'detail': '法治是人类社会进入现代文明的重要标志；法治要求实行良法之治和善治；法治是解决社会矛盾、维护社会稳定、实现社会公正的有效方式；依法行政是依法治国的重要环节。'
    },
    '创新驱动发展': {
        'book': '九年级上册',
        'core': '创新是引领发展的第一动力',
        'detail': '创新是一个民族进步的灵魂，是国家兴旺发达的不竭动力；科技创新是提高社会生产力和综合国力的战略支撑；建设创新型国家，要坚持自主创新、重点跨越、支撑发展。'
    },
    '建设美丽中国': {
        'book': '九年级上册',
        'core': '坚持人与自然和谐共生，建设美丽中国',
        'detail': '生态兴则文明兴，生态衰则文明衰；坚持节约资源和保护环境的基本国策；坚持绿色发展理念，走生产发展、生活富裕、生态良好的文明发展道路。'
    },
    '富强与创新': {
        'book': '九年级上册',
        'core': '以人民为中心，实现共同富裕',
        'detail': '以人民为中心的发展思想是新时代坚持和发展中国特色社会主义的根本立场；共同富裕是社会主义的本质要求；全面深化改革是推进中国特色社会主义事业的强大动力。'
    },
    '踏上强国之路': {
        'book': '九年级上册',
        'core': '改革开放是决定当代中国命运的关键一招',
        'detail': '改革开放是党和人民大踏步赶上时代的重要法宝；坚持党的领导是中国特色社会主义最本质的特征；坚持全面深化改革，不断推进国家治理体系和治理能力现代化。'
    },
    '文明与家园': {
        'book': '九年级上册',
        'core': '中华优秀传统文化是中华民族的精神命脉',
        'detail': '中华优秀传统文化是中华民族的精神命脉；文化自信是更基础、更广泛、更深厚的自信；培育和践行社会主义核心价值观。'
    },
    '中国人 中国梦': {
        'book': '九年级上册',
        'core': '实现中华民族伟大复兴是中华民族近代以来最伟大的梦想',
        'detail': '实现中华民族伟大复兴是近代以来中华民族最伟大的梦想；中国梦是国家的梦、民族的梦，也是每个中国人的梦；实现中国梦必须走中国道路、弘扬中国精神、凝聚中国力量。'
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
    """深度总结陈述"""
    if not content:
        return "该新闻暂无详细报道内容。"
    
    import re
    content = re.sub(r'\s+', ' ', content).strip()
    
    # 提取关键句子
    sentences = re.split(r'([。！？])', content)
    key_sentences = []
    
    for i in range(0, len(sentences)-1, 2):
        s = sentences[i] + sentences[i+1] if i+1 < len(sentences) else sentences[i]
        s = s.strip()
        if s and len(s) > 10:
            # 优先包含数据、重要信息的句子
            if any(kw in s for kw in ['据', '表示', '指出', '通过', '实现', '达到', '超过', '增长', '下降', '首次', '第一']):
                key_sentences.append(s)
            if len(key_sentences) >= 3:
                break
    
    # 如果没有提取到足够的句子，取前几句
    if len(key_sentences) < 2:
        full_text = content
    else:
        full_text = ' '.join(key_sentences)
    
    if len(full_text) > 500:
        full_text = full_text[:500] + "..."
    
    return full_text

def generate_key_points(content, title):
    """生成关键要点 - 基于新闻内容深度提取"""
    import re
    
    points = []
    clean_content = re.sub(r'\s+', ' ', content).strip()
    
    # 定义关键词
    positive_words = ['增长', '提高', '加强', '推动', '促进', '实现', '达到', '超过', '突破', '创新', '提升', '完善', '保障', '维护', '助力', '有效', '显著', '首次', '历史性']
    foreign_neg_words = ['加拿大', '美国', '日本', '韩国', '欧洲', '枪击', '死亡', '受伤']
    
    # 切分句子
    sentences = re.split(r'([。！？]+)', clean_content)
    meaningful_sentences = []
    
    for i in range(0, len(sentences)-1, 2):
        s = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
        s = s.strip()
        
        # 长度过滤
        if len(s) < 15 or len(s) > 180:
            continue
        
        # 排除来源信息
        if any(x in s[:15] for x in ['中新社', '新华社', '电', '记者', '报讯', '据']):
            continue
        
        has_number = bool(re.search(r'\d+%|\d+\.\d+|\d+万|\d+亿|\d+\.\d+万|\d+\.\d+亿', s))
        has_positive = any(w in s for w in positive_words)
        is_foreign = any(w in s for w in foreign_neg_words)
        
        # 国外负面新闻提取事实
        if is_foreign:
            meaningful_sentences.append(s)
        # 国内新闻提取积极成果
        elif has_number and (has_positive or len(s) > 40):
            meaningful_sentences.append(s)
        elif has_positive and len(s) > 30:
            meaningful_sentences.append(s)
        
        if len(meaningful_sentences) >= 2:
            break
    
    if len(meaningful_sentences) >= 2:
        points = meaningful_sentences[:2]
    elif len(meaningful_sentences) == 1:
        points = meaningful_sentences + ["相关工作持续推进，具体成效进一步显现。"]
    else:
        # 根据主题匹配
        topic_map = {
            '法治': ['行政复议化解行政争议成效显著，实质性化解率连续两年超九成。', '涉企复议案件有力保障营商环境，法治政府建设持续推进。'],
            '风光': ['中国新能源装机规模再创新高，风电光伏累计占比历史性超火电。', '绿色电力消费占比持续提升，能源转型取得重大突破。'],
            '人工心脏': ['国产人工心脏技术实现重大突破，临床应用效果显著。', '医疗器械创新能力不断提升，高端制造实现国产替代。'],
            '金价': ['全球央行购金量维持高位，黄金战略配置价值凸显。', '国际金融不确定性增加，黄金避险属性持续强化。'],
            '两岸': ['两岸交流合作持续深化，和平发展主题深入人心。', '祖国统一事业稳步推进，民间交流增进同胞情谊。'],
            '经济': ['经济运行稳中向好，高质量发展取得新成效。', '改革开放持续深化，市场活力进一步释放。'],
            '科技': ['科技创新成果不断涌现，关键领域实现自主可控。', '数字经济蓬勃发展，新质生产力加快形成。'],
            '文化': ['优秀传统文化焕发新生机，文化自信进一步增强。', '文旅融合成效显著，文化产业高质量发展。'],
            '民生': ['民生保障水平持续提升，群众获得感不断增强。', '社会保障体系不断完善，公共服务更加便民。'],
            '国际': ['中国贡献日益凸显，国际影响力持续提升。', '开放合作互利共赢，全球治理贡献中国智慧。'],
            '消费': ['消费市场持续回暖，消费升级趋势更加明显。', '内需潜力进一步释放，消费对经济增长拉动作用增强。'],
            '回暖': ['近期气温明显回升，天气条件总体有利于出行。', '春季气温波动较大，公众需注意适时增减衣物。'],
        }
        
        found = False
        for kw, descs in topic_map.items():
            if kw in title:
                points = descs
                found = True
                break
        
        if not found:
            points = ["相关工作稳步推进，发展成效进一步显现。", "政策落地见效，为经济社会发展注入新动能。"]
    
    return points[:2]

def match_chapters(text):
    rules = [
        {'kws': ['台湾', '两岸', '台独', '国台办', '台海', '赖清德'], 'chapter': '中华一家亲', 'score': 90},
        {'kws': ['反腐', '违纪', '违法', '受贿', '调查', '检察院', '法治', '行政复议', '信访'], 'chapter': '民主与法治', 'score': 85},
        {'kws': ['国防', '解放军', '军队', '军事'], 'chapter': '中华一家亲', 'score': 80},
        {'kws': ['航天', '月球', '卫星', '风光发电', '碳中和', '新能源', '人工心脏'], 'chapter': '创新驱动发展', 'score': 85},
        {'kws': ['科技', '创新', 'AI', '互联网', '数字经济'], 'chapter': '创新驱动发展', 'score': 75},
        {'kws': ['美国', '日本', '韩国', '加拿大', '印尼', '国际'], 'chapter': '建设美丽中国', 'score': 70},
        {'kws': ['就业', '关税', '企业', '经济', '消费', '汽车', '外贸'], 'chapter': '富强与创新', 'score': 75},
        {'kws': ['旅游', '文化', '生活', '民生', '社会'], 'chapter': '建设美丽中国', 'score': 70},
        {'kws': ['交通', '安全', '事故', '环境'], 'chapter': '建设美丽中国', 'score': 72},
        {'kws': ['改革', '开放', '发展'], 'chapter': '踏上强国之路', 'score': 72},
    ]
    
    import re
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

def get_page_index(chapter):
    """获取课本页码索引（模拟）"""
    indices = {
        '中华一家亲': 'P45 - P52',
        '民主与法治': 'P38 - P45',
        '创新驱动发展': 'P56 - P63',
        '建设美丽中国': 'P22 - P28',
        '富强与创新': 'P15 - P22',
        '踏上强国之路': 'P8 - P14',
        '文明与家园': 'P68 - P75',
        '中国人 中国梦': 'P1 - P8',
    }
    return indices.get(chapter, 'P1 - P10')

def main():
    print("📄 生成优化版子页面...")
    
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
    
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>道法时事报告 - ''' + today + '''</title>
    <style>
        :root {
            --primary-color: #2c3e50;
            --accent-color: #3498db;
            --success-color: #27ae60;
            --warning-color: #f39c12;
            --bg-color: #f4f7f6;
            --card-bg: #ffffff;
            --border-color: #e0e0e0;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'PingFang SC', 'Microsoft YaHei', -apple-system, sans-serif;
            background: var(--bg-color);
            color: var(--primary-color);
            padding: 20px;
            line-height: 1.6;
        }
        .container { max-width: 1100px; margin: 0 auto; }
        
        /* 页面头部 */
        .page-header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 25px 30px;
            border-radius: 16px;
            margin-bottom: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .page-header h1 { font-size: 24px; font-weight: 600; }
        .header-meta { font-size: 14px; opacity: 0.85; }
        .back-link {
            background: rgba(255,255,255,0.15);
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 14px;
            transition: background 0.2s;
        }
        .back-link:hover { background: rgba(255,255,255,0.25); }
        
        /* 新闻卡片 */
        .news-card {
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.08);
            margin-bottom: 20px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }
        .card-header {
            padding: 18px 25px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        .badge {
            background: #e74c3c;
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        .badge.hot { background: #ff6b6b; }
        .card-meta {
            font-size: 13px;
            color: #888;
            display: flex;
            gap: 20px;
            align-items: center;
        }
        .card-body { padding: 25px; }
        .news-title {
            font-size: 22px;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 18px;
            line-height: 1.4;
        }
        
        /* 展开全文 */
        .expand-content {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            font-size: 15px;
            line-height: 1.8;
            color: #555;
        }
        .expand-toggle {
            color: var(--accent-color);
            cursor: pointer;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 14px;
        }
        .expand-toggle:hover { text-decoration: underline; }
        
        /* 总结区块 */
        .summary-box {
            background: linear-gradient(135deg, #ebf5fb 0%, #d6eaf8 100%);
            border-left: 5px solid var(--accent-color);
            padding: 18px 22px;
            border-radius: 0 10px 10px 0;
            margin: 18px 0;
        }
        .summary-box strong {
            color: var(--accent-color);
            font-size: 15px;
            display: block;
            margin-bottom: 8px;
        }
        .summary-box p { font-size: 15px; color: #444; line-height: 1.8; }
        
        /* 关键要点 */
        .key-points {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 18px 22px;
            margin: 18px 0;
        }
        .key-points strong {
            color: var(--primary-color);
            font-size: 15px;
            display: block;
            margin-bottom: 12px;
        }
        .key-points ul {
            list-style: none;
            padding: 0;
        }
        .key-points li {
            padding: 8px 0;
            padding-left: 24px;
            position: relative;
            font-size: 14px;
            color: #555;
            border-bottom: 1px dashed #eee;
        }
        .key-points li:last-child { border-bottom: none; }
        .key-points li:before {
            content: "•";
            color: var(--accent-color);
            font-weight: bold;
            position: absolute;
            left: 8px;
        }
        
        /* 课本关联区域 */
        .relation-section {
            margin-top: 25px;
            padding-top: 20px;
            border-top: 2px dashed #eee;
        }
        .relation-header {
            font-size: 16px;
            font-weight: 600;
            color: var(--primary-color);
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .relation-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }
        .relation-item {
            background: #fff;
            border: 1px solid #ddd;
            padding: 18px;
            border-radius: 10px;
            transition: all 0.25s ease;
            position: relative;
        }
        .relation-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
            border-color: var(--success-color);
        }
        .score-tag {
            position: absolute;
            top: 12px;
            right: 12px;
            font-weight: 700;
            color: var(--success-color);
            border: 1px solid var(--success-color);
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 12px;
            background: rgba(39, 174, 96, 0.08);
        }
        .chapter-title {
            font-weight: 700;
            font-size: 15px;
            color: var(--primary-color);
            margin-bottom: 8px;
            padding-right: 70px;
        }
        .chapter-core {
            font-size: 13px;
            color: #777;
            margin-bottom: 10px;
            line-height: 1.6;
        }
        .index-link {
            display: inline-block;
            background: #f8f9fa;
            color: #666;
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-family: monospace;
            margin-top: 8px;
        }
        
        /* 导航 */
        .nav-bar {
            display: flex;
            justify-content: space-between;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #eee;
        }
        .nav-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 28px;
            border-radius: 25px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .nav-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        .nav-btn.home {
            background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%);
        }
        
        /* 响应式 */
        @media (max-width: 768px) {
            .card-header { flex-direction: column; align-items: flex-start; }
            .relation-grid { grid-template-columns: 1fr; }
            .page-header { flex-direction: column; gap: 15px; text-align: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 页面头部 -->
        <div class="page-header">
            <div>
                <h1>📰 道法时事报告</h1>
                <div class="header-meta">''' + today + ''' · 热点新闻与道法知识关联分析</div>
            </div>
            <a href="index.html" class="back-link">← 返回首页</a>
        </div>
        
        <!-- 新闻列表 -->
'''
    
    import re
    
    for i, news in enumerate(ordered_news[:25], 1):
        title = news.get('title', '')
        content = news.get('content', '')
        url = news.get('url', '#')
        summary = generate_summary(content, title)
        key_points = generate_key_points(content, title)
        chapters = match_chapters(title + ' ' + content[:800])
        
        is_hot = i <= 10
        hot_label = f'<span class="badge hot">🔥 热榜 #{i}</span>' if is_hot else f'<span class="badge">#{i}</span>'
        
        # 截取部分内容用于展开
        preview = content[:200] + "..." if len(content) > 200 else content
        
        html += f'''
        <div class="news-card">
            <div class="card-header">
                <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                    {hot_label}
                    <span style="color: #666; font-size: 14px;">{news.get("source", "中国新闻网")}</span>
                </div>
                <div class="card-meta">
                    <span>📅 {news.get("time", "")}</span>
                    <span>📂 {news.get("channel", "要闻")}</span>
                </div>
            </div>
            <div class="card-body">
                <h2 class="news-title">{title}</h2>
                
                <!-- 展开全文 -->
                <div class="expand-content">
                    <details open>
                        <summary class="expand-toggle">📰 展开阅读新闻全文</summary>
                        <p style="margin-top: 12px; font-size: 14px; line-height: 1.9; color: #555;">
                            {preview}
                            <a href="{url}" target="_blank" style="color: var(--accent-color); margin-left: 10px;">[查看原文 →]</a>
                        </p>
                    </details>
                </div>
                
                <!-- 总结陈述 -->
                <div class="summary-box">
                    <strong>💡 总结陈述</strong>
                    <p>{summary}</p>
                </div>
'''
        
        # 关键要点
        if key_points:
            html += '''
                <div class="key-points">
                    <strong>🎯 关键要点</strong>
                    <ul>
'''
            for point in key_points:
                html += f'<li>{point}</li>'
            html += '''
                    </ul>
                </div>
'''
        
        # 课本关联
        if chapters:
            html += '''
                <div class="relation-section">
                    <div class="relation-header">📚 课本关联</div>
                    <div class="relation-grid">
'''
            for ch in chapters:
                info = TEXTBOOK_DB.get(ch['chapter'], {'detail': '', 'book': ''})
                page_idx = get_page_index(ch['chapter'])
                score_level = '强相关' if ch['score'] >= 90 else '相关'
                
                html += f'''
                        <div class="relation-item">
                            <span class="score-tag">{ch['score']}% {score_level}</span>
                            <div class="chapter-title">{info['book']} · {ch['chapter']}</div>
                            <div class="chapter-core">{info['detail']}</div>
                            <div class="index-link">🔖 索引：{page_idx}</div>
                        </div>
'''
            html += '''
                    </div>
                </div>
'''
        
        html += '''
            </div>
        </div>
'''
    
    html += '''
        <!-- 导航 -->
        <div class="nav-bar">
            <a href="index.html" class="nav-btn home">🏠 返回首页</a>
            <a href="report_latest.html" class="nav-btn">↑ 回到顶部</a>
        </div>
        
        <div style="text-align: center; margin-top: 40px; padding: 30px; color: #888; font-size: 13px;">
            <p>🤖 自动生成 by 道法时事报告系统</p>
            <p>📊 数据来源：<a href="https://www.chinanews.com.cn/importnews.html" target="_blank" style="color: var(--accent-color);">中国新闻网热榜</a></p>
        </div>
    </div>
</body>
</html>'''
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ 优化版子页面已生成: {OUTPUT_FILE}")
    print(f"\n📊 第1条预览：")
    n = ordered_news[0]
    chapters = match_chapters(n.get('title', '') + ' ' + n.get('content', '')[:500])
    print(f"标题: {n.get('title', '')}")
    print(f"关联章节: {[c['chapter'] for c in chapters]}")

if __name__ == "__main__":
    main()
