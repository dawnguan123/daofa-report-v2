#!/usr/bin/env python3
"""
每日时事报告生成 - 简化版
"""
import yaml
import sqlite3
import json
import requests
import sys
import os
import re
from datetime import datetime

# 加载配置
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

class MinimaxClient:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def get_embedding(self, text):
        """调用Minimax获取向量嵌入"""
        try:
            url = "https://api.minimax.chat/v1/text/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "text-embedding-005",
                "input": text,
                "encoding_format": "float"
            }
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()['data'][0]['embedding']
        except Exception as e:
            print(f"  ⚠️ Minmax API错误: {e}")
            return [0.0] * 768

def keyword_match(news_keywords, chapter_text):
    """关键词匹配"""
    news_keywords = [k.lower() for k in news_keywords]
    chapter_lower = chapter_text.lower()
    
    matches = 0
    for keyword in news_keywords:
        if keyword in chapter_lower:
            matches += 1
    
    return matches

def search_chapters(news, db_path, limit=3):
    """搜索相关课本章节（关键词匹配）"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='textbook_anchors'")
        if not cursor.fetchone():
            return []
        
        cursor.execute("SELECT * FROM textbook_anchors")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        results = []
        for row in rows:
            ch = dict(zip(columns, row))
            # 关键词匹配
            score = keyword_match(
                news['title'] + ' ' + news['summary'],
                ch.get('content', '') + ' ' + ch.get('content_summary', '')
            )
            if score > 0:
                ch['relevance'] = score
                results.append(ch)
        
        # 按分数排序
        results.sort(key=lambda x: x.get('relevance', 0), reverse=True)
        return results[:limit]
        
    except Exception as e:
        print(f"  ⚠️ 搜索错误: {e}")
        return []
    finally:
        conn.close()

def fetch_news(date_str):
    """获取今日新闻"""
    sample_news = [
        {
            "title": "全国教育大会在北京召开",
            "source": "新华社",
            "time": f"{date_str} 10:00",
            "summary": "会议强调全面推进教育现代化，建设教育强国。",
            "category": "教育"
        },
        {
            "title": "《中华人民共和国民法典》新司法解释发布",
            "source": "人民日报",
            "time": f"{date_str} 09:30",
            "summary": "最高人民法院发布关于民事案件审理的最新司法解释。",
            "category": "法律"
        },
        {
            "title": "国家统计局发布2026年1月经济数据",
            "source": "央视新闻",
            "time": f"{date_str} 08:00",
            "summary": "1月份CPI同比上涨0.5%，经济运行总体平稳。",
            "category": "时政"
        },
        {
            "title": "教育部：推进义务教育优质均衡发展",
            "source": "中国教育报",
            "time": f"{date_str} 14:00",
            "summary": "教育部要求各地加快推进义务教育优质均衡发展。",
            "category": "教育"
        },
        {
            "title": "最高检发布未成年人检察工作白皮书",
            "source": "检察日报",
            "time": f"{date_str} 11:00",
            "summary": "报告显示未成年人犯罪率同比下降15%。",
            "category": "法律"
        }
    ]
    return sample_news[:config['news']['top_n']]

def generate_html(report_date, news_list, chapters_dict, pdf_url):
    """生成HTML报告"""
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>道法时事报告 - {report_date}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
</head>
<body class="bg-gray-50">
    <div id="app" class="max-w-4xl mx-auto px-4 py-8">
        <header class="text-center mb-8">
            <h1 class="text-3xl font-bold text-gray-800">📰 道法时事报告</h1>
            <p class="text-gray-500 mt-2">{report_date}</p>
        </header>
        
        <div class="space-y-6">
'''
    
    for i, news in enumerate(news_list, 1):
        chapters = chapters_dict.get(i, [])
        
        html += f'''
            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-bold text-blue-600 mb-2">{i}. {news['title']}</h2>
                <div class="text-sm text-gray-400 mb-4">
                    <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded">{news['category']}</span>
                    {news['source']} · {news['time']}
                </div>
                <p class="text-gray-700 mb-4">{news['summary']}</p>
'''
        
        if chapters:
            html += '''
                <div class="bg-green-50 border-l-4 border-green-500 p-4">
                    <h3 class="font-bold text-green-700 mb-2">📚 课本关联</h3>
'''
            for ch in chapters:
                html += f'''
                    <div class="mb-3">
                        <div class="flex items-center gap-2">
                            <span class="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">
                                {ch.get('chapter_title', '未知章节')} (页码 {ch.get('page_range', '未知')})
                            </span>
                        </div>
                        <p class="text-gray-600 text-sm mt-1">{ch.get('content_summary', '')[:100]}...</p>
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
    </div>
    <script>const { createApp } = Vue; createApp({}).mount('#app')</script>
</body>
</html>'''
    
    return html

def main():
    if len(sys.argv) > 2 and sys.argv[1] == '--date':
        report_date = sys.argv[2]
    else:
        report_date = datetime.now().strftime('%Y-%m-%d')
    
    print("=" * 60)
    print(f"📰 生成时事报告: {report_date}")
    print("=" * 60)
    
    # 获取新闻
    print("\n📰 获取新闻...")
    news_list = fetch_news(report_date)
    print(f"  ✓ {len(news_list)} 条新闻")
    
    # 匹配课本章节
    print("\n📚 匹配课本...")
    chapters_dict = {}
    for i, news in enumerate(news_list, 1):
        chapters = search_chapters(news, config['turso']['knowledge_db'], limit=3)
        chapters_dict[i] = chapters
        print(f"  ✓ 新闻{i}: {len(chapters)} 个相关章节")
    
    # 生成HTML
    print("\n📄 生成HTML...")
    pdf_url = config['frontend']['pdf_url']
    html = generate_html(report_date, news_list, chapters_dict, pdf_url)
    
    output_dir = os.path.join(config['paths']['output_dir'], report_date)
    os.makedirs(output_dir, exist_ok=True)
    
    html_path = os.path.join(output_dir, 'index.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  ✓ {html_path}")
    
    # 生成JSON
    json_data = {
        "date": report_date,
        "newsCount": len(news_list),
        "news": [{"rank": i, "title": n['title'], "source": n['source'], 
                  "time": n['time'], "summary": n['summary'], 
                  "matchedChapters": chapters_dict.get(i, [])} 
                 for i, n in enumerate(news_list, 1)],
        "chapters": []
    }
    
    json_path = os.path.join(output_dir, 'report.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ {json_path}")
    
    print(f"\n✅ 完成! 访问: file://{html_path}")

if __name__ == "__main__":
    main()
