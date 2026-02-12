#!/usr/bin/env python3
"""
生成道法时事报告（专业版）
- 详细总结陈述
- 新闻内容链接
- 高相关度课本关联
"""
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime

INPUT_FILE = "/Users/guanliming/dailynews/output/hotnews_detail.json"
OUTPUT_FILE = "/Users/guanliming/dailynews/output/report_latest.html"
BASE_URL = "https://www.chinanews.com.cn"

TEXTBOOK_DB = {
    '中华一家亲': {'book': '九年级上册', 'core': '维护祖国统一、民族团结是每个公民的责任和义务'},
    '民主与法治': {'book': '九年级上册', 'core': '依法治国是党领导人民治理国家的基本方略'},
    '创新驱动发展': {'book': '九年级上册', 'core': '创新是引领发展的第一动力'},
    '建设美丽中国': {'book': '九年级上册', 'core': '坚持人与自然和谐共生，建设美丽中国'},
    '富强与创新': {'book': '九年级上册', 'core': '以人民为中心，实现共同富裕'},
    '踏上强国之路': {'book': '九年级上册', 'core': '改革开放是决定当代中国命运的关键一招'},
    '文明与家园': {'book': '九年级上册', 'core': '中华优秀传统文化是中华民族的精神命脉'},
    '中国人 中国梦': {'book': '九年级上册', 'core': '实现中华民族伟大复兴是中华民族近代以来最伟大的梦想'},
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

def extract_summary(content, title):
    """生成专业、详细的总结陈述"""
    if not content:
        return "该新闻暂无详细报道内容。"
    
    import re
    
    # 提取关键信息
    key_info = []
    
    # 核心数据
    nums = re.findall(r'(\d+\.?\d*(?:万|亿|千万|百万|千亿|%)?)', content)
    if nums:
        key_info.append(f"数据层面，本新闻涉及的关键数值包括：{', '.join(set(nums[:3]))}")
    
    # 主体机构/人物
    orgs = re.findall(r'([^\s]{2,6}(部|委|局|办|政府|法院|检察院|公司|机构))', content)
    if orgs:
        unique_orgs = list(dict.fromkeys([o[0] for o in orgs[:2]]))
        key_info.append(f"主要参与主体包括：{', '.join(unique_orgs)}")
    
    # 时间节点
    dates = re.findall(r'(\d{4}年\d{1,2}月(?:\d{1,2}日)?)', content)
    if dates:
        key_info.append(f"时间节点标注为：{dates[0]}")
    
    # 政策/措施
    measures = re.findall(r'(?:通过|实施|发布|制定|推进|加强|完善)([^。！？]+)', content)
    if measures:
        key_info.append(f"核心举措涵盖：{measures[0].strip()}")
    
    # 影响/意义
    impacts = re.findall(r'(?:促进|推动|实现|提升|加强|保障|维护|确保)([^。！？]+)', content)
    if impacts:
        key_info.append(f"预期效果或价值体现在：{impacts[0].strip()}")
    
    # 构建完整总结
    summary_parts = []
    
    # 基础背景
    if '据' in content[:100]:
        source = content[:50].split('据')[-1].split('。')[0] if '。' in content[:100] else ''
        if source:
            summary_parts.append(f"据相关报道，{source}。")
    
    # 核心要点
    if key_info:
        summary_parts.append('；'.join(key_info))
    
    # 整体评价
    if any(kw in content for kw in ['首次', '第一', '历史', '突破', '创新']):
        summary_parts.append("该事件具有里程碑意义，标志着相关领域进入新的发展阶段。")
    
    if any(kw in content for kw in ['预计', '将', '未来', '计划']):
        summary_parts.append("从发展趋势来看，相关工作正在稳步推进中。")
    
    # 拼接总结（限制字数，避免溢出）
    full_summary = ' '.join(summary_parts)
    if len(full_summary) > 400:
        return full_summary[:400] + "..."
    return full_summary if full_summary else content[:200] + "..."

def match_chapters(text):
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
    
    seen = set()
    result = []
    for chapter, score in sorted(matched, key=lambda x: -x[1]):
        if chapter not in seen:
            seen.add(chapter)
            result.append({'chapter': chapter, 'score': score})
    
    return [r for r in result if r['score'] >= 70]

def main():
    print("📄 生成专业版HTML报告...")
    
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
        .summary-header {{ display: flex; align-items: center; margin-bottom: 12px; }}
        .summary-label {{ font-size: 15px; font-weight: bold; color: #e94560; display: flex; align-items: center; gap: 8px; }}
        .content-link {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 6px 16px; border-radius: 6px; font-size: 13px; text-decoration: none; margin-left: auto; }}
        .content-link:hover {{ opacity: 0.9; }}
        .summary-text {{ font-size: 15px; color: #444; line-height: 1.9; }}
        .chapter-tags {{ margin-top: 20px; }}
        .chapter-tag {{ display: inline-block; background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); color: #155724; padding: 14px 20px; border-radius: 10px; margin-right: 15px; margin-bottom: 12px; }}
        .chapter-name {{ font-weight: bold; font-size: 15px; }}
        .chapter-core {{ font-size: 13px; margin-top: 6px; opacity: 0.85; }}
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
        summary = extract_summary(content, title)
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
                        <div class="summary-label">📝 专业总结</div>
                        <a href="{url}" target="_blank" class="content-link">📰 查看原文详情</a>
                    </div>
                    <div class="summary-text">{summary}</div>
                </div>
'''
        
        if chapters:
            html += '''
                    <div class="chapter-tags">
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
    print(f"\n📊 前3条预览：")
    for i, n in enumerate(ordered_news[:3], 1):
        chapters = match_chapters(n.get('title', '') + ' ' + n.get('content', '')[:500])
        summary = extract_summary(n.get('content', ''), n.get('title', ''))
        print(f"\n{i}. {n.get('title', '')}")
        print(f"   总结：{summary[:100]}...")

if __name__ == "__main__":
    main()
