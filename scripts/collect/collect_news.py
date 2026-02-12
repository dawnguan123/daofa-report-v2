#!/usr/bin/env python3
"""
新闻采集完整工作流（混合方案）
1. Tavily 发现新闻链接 → 2. 下钻详情页获取内容 → 3. 存储到 Turso → 4. 向量化
"""
import requests
import re
import sqlite3
import json
import time
import os
from datetime import datetime
from bs4 import BeautifulSoup
from tavily import TavilyClient

# 配置
DB_PATH = "/Users/guanliming/dailynews/turso/textbook_full.db"
OUTPUT_DIR = "/Users/guanliming/dailynews/output"
TAVILY_API_KEY = "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"


class NewsCollector:
    """新闻采集器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        self.tavily = TavilyClient(api_key=TAVILY_API_KEY)
    
    def discover_via_tavily(self, query="2026年2月 中国新闻网 时政新闻", max_results=10):
        """通过 Tavily 发现新闻链接"""
        print(f"\n🔍 Tavily 搜索: {query}")
        
        try:
            response = self.tavily.search(
                query=query,
                max_results=max_results,
                include_answer=False
            )
            
            results = response.get('results', [])
            print(f"  ✓ 获取 {len(results)} 条结果")
            
            news_list = []
            for r in results:
                url = r.get('url', '')
                title = r.get('title', '')
                
                # 只保留中国新闻网链接
                if 'chinanews.com.cn' in url and '/2026/' in url:
                    news_list.append({
                        'title': title,
                        'url': url,
                        'source': '中国新闻网'
                    })
            
            print(f"  ✓ 筛选出 {len(news_list)} 条新闻网链接")
            return news_list
            
        except Exception as e:
            print(f"  ⚠️ Tavily 搜索失败: {e}")
            return []
    
    def fetch_detail_page(self, url, search_title=""):
        """下钻到详情页获取内容"""
        title = search_title
        print(f"  🔍 下钻: {url[-50:]}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"    ⚠️ 状态码: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # 提取时间
            time_str = ""
            time_elem = soup.find('div', class_='pub-time')
            if time_elem:
                time_str = time_elem.get_text(strip=True)
            else:
                date_match = re.search(r'/(\d{4})/(\d{2})-(\d{2})/', url)
                if date_match:
                    time_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
            
            # 提取来源
            source = "中国新闻网"
            source_elem = soup.find('div', class_='pub-source')
            if source_elem:
                source = source_elem.get_text(strip=True).replace('来源：', '')
            
            # 提取正文
            content = ""
            content_div = soup.find('div', class_='content') or \
                         soup.find('article') or \
                         soup.find('div', class_='article')
            
            if content_div:
                paragraphs = content_div.find_all('p')
                texts = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 20:
                        texts.append(text)
                content = ' '.join(texts)
            
            if not content:
                print(f"    ⚠️ 无法提取正文")
                return None
            
            # 生成摘要
            summary = content[:300] + ("..." if len(content) > 300 else "")
            
            # 提取关键要点
            key_points = self._extract_key_points(content)
            
            return {
                'title': title,
                'url': url,
                'source': source,
                'publish_date': time_str[:10] if len(time_str) >= 10 else datetime.now().strftime('%Y-%m-%d'),
                'content': content,
                'summary': summary,
                'key_points': key_points,
                'category': self._guess_category(title),
            }
            
        except Exception as e:
            print(f"  ⚠️ 详情获取失败: {e}")
            return None
    
    def _extract_key_points(self, content):
        """提取关键要点"""
        key_points = []
        
        names = re.findall(r'习近平|李强|丁薛祥|李希|王毅|赵乐际', content)
        if names:
            key_points.append(f"人物：{', '.join(set(names))}")
        
        orgs = re.findall(r'中共中央|国务院|中央军委|国台办|工信部|科技部|教育部|国家航天局', content)
        if orgs:
            key_points.append(f"机构：{', '.join(set(orgs))}")
        
        events = re.findall(r'(月球探测|载人航天|反腐败|建军|改革|研制|突破|民主|法治)', content)
        if events:
            key_points.append(f"关键词：{', '.join(set(events))}")
        
        return key_points
    
    def _guess_category(self, title):
        """猜测分类"""
        categories = {
            '教育': ['教育', '学校', '学生', '教师', '考试'],
            '法律': ['法律', '法院', '检察', '司法', '犯罪'],
            '经济': ['经济', 'GDP', 'CPI', '统计局', '市场'],
            '政治': ['习近平', '李强', '会议', '讲话', '党建', '军队', '中共中央'],
            '科技': ['科技', '航天', '月球', 'AI', '创新'],
            '两岸': ['台湾', '两岸', '国台办', '台海'],
        }
        
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw in title:
                    return cat
        return '时政'
    
    def save_to_db(self, news):
        """保存到 SQLite"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO news_articles 
                (title, url, source, publish_date, content, summary, category, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                news['title'],
                news['url'],
                news['source'],
                news['publish_date'],
                news['content'],
                news['summary'],
                news['category'],
                json.dumps({'key_points': news.get('key_points', [])}, ensure_ascii=False),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            conn.commit()
            print(f"    💾 已保存到数据库")
            return True
        except Exception as e:
            print(f"    ⚠️ 数据库错误: {e}")
            return False
        finally:
            conn.close()
    
    def save_to_json(self, news, index=1):
        """保存到 JSON"""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        vector = self.generate_vector(news.get('content', ''))
        
        output = {
            **news,
            'vector': vector,
            'word_count': len(news.get('content', '')),
        }
        
        with open(os.path.join(OUTPUT_DIR, f'news_{index}.json'), 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"    📁 已保存")
    
    def generate_vector(self, text):
        """生成关键词向量"""
        words = re.findall(r'[\u4e00-\u9fff]{2,}', text)
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)[:20])
    
    def run(self, target_title=None, max_news=5):
        """运行采集流程"""
        print("\n" + "="*60)
        print("📰 新闻采集工作流")
        print("="*60)
        
        # 1. 发现新闻
        if target_title:
            news_list = self.discover_via_tavily(f"{target_title} site:chinanews.com.cn 2026", max_results=max_news)
        else:
            news_list = self.discover_via_tavily("2026年2月 中国时政新闻", max_results=max_news)
        
        if not news_list:
            print("  ⚠️ 无发现新闻")
            return []
        
        # 2. 去重
        seen = set()
        unique_list = []
        for n in news_list:
            if n['url'] not in seen:
                seen.add(n['url'])
                unique_list.append(n)
        
        # 3. 采集详情
        collected = []
        for i, news in enumerate(unique_list[:max_news], 1):
            print(f"\n[{i}/{len(unique_list[:max_news])}]")
            detail = self.fetch_detail_page(news['url'], news['title'])
            
            if detail:
                self.save_to_db(detail)
                self.save_to_json(detail, index=i)
                collected.append(detail)
                print(f"    ✅ {detail['title'][:30]}...")
            time.sleep(0.3)
        
        print(f"\n" + "="*60)
        print(f"✅ 采集完成! 共 {len(collected)} 条")
        print("="*60)
        
        return collected


def main():
    """主入口"""
    import sys
    
    target = sys.argv[1] if len(sys.argv) > 1 else None
    max_news = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    collector = NewsCollector()
    results = collector.run(target_title=target, max_news=max_news)
    
    # 打印摘要
    for i, n in enumerate(results, 1):
        print(f"\n{i}. {n['title'][:50]}")
        print(f"   日期: {n['publish_date']} | 分类: {n['category']}")
        if n.get('key_points'):
            print(f"   要点: {'; '.join(n['key_points'])}")


if __name__ == "__main__":
    main()
