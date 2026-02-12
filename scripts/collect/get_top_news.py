#!/usr/bin/env python3
"""
获取中国新闻网顶部焦点图片新闻
"""
import requests
import re
import json
import time
from bs4 import BeautifulSoup
from datetime import datetime

# 配置
DB_PATH = "/Users/guanliming/dailynews/turso/textbook_full.db"
OUTPUT_DIR = "/Users/guanliming/dailynews/output"


class ChinaNewsFetcher:
    """中国新闻网顶部焦点新闻获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
    
    def get_top_news(self, max_news=5):
        """获取顶部焦点新闻"""
        url = "https://www.chinanews.com.cn/china/"
        print(f"📰 访问: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"  ⚠️ 状态码: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_list = []
            seen_urls = set()
            seen_titles = set()
            
            # 方法1: dh6927ab2b3c896d07080e7d8a 区域（滚动更新，包含用户提供的正确标题）
            sfq_area = soup.select_one('.dh6927ab2b3c896d07080e7d8a')
            if sfq_area:
                print(f"  ✅ 找到 dh6927ab2b3c896d07080e7d8a 区域")
                links = sfq_area.find_all('a')
                
                for a in links:
                    title = a.get_text(strip=True)
                    href = a.get('href', '')
                    
                    # 补全URL
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        href = 'https://www.chinanews.com.cn' + href
                    
                    # 验证：标题长度15-80，URL包含2026
                    if len(title) < 15 or len(title) > 80:
                        continue
                    if '/2026/' not in href:
                        continue
                    
                    # 去重：标题和URL都可能是重复的
                    title_clean = title[:40]  # 取前40字符去重
                    if title_clean in seen_titles or href in seen_urls:
                        continue
                    seen_titles.add(title_clean)
                    seen_urls.add(href)
                    
                    news_list.append({
                        'title': title,
                        'url': href,
                        'area': 'dh6927ab2b3c896d07080e7d8a'
                    })
            
            # 方法2: news-list 区域
            if len(news_list) < max_news:
                print(f"  🔍 搜索 news-list 区域...")
                news_links = soup.select('.news-list a')[:max_news * 2]
                
                for a in news_links:
                    title = a.get_text(strip=True)
                    href = a.get('href', '')
                    
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        href = 'https://www.chinanews.com.cn' + href
                    
                    if len(title) < 15 or '/2026/' not in href:
                        continue
                    
                    title_clean = title[:40]
                    if title_clean in seen_titles or href in seen_urls:
                        continue
                    seen_titles.add(title_clean)
                    seen_urls.add(href)
                    
                    news_list.append({
                        'title': title,
                        'url': href,
                        'area': 'news-list'
                    })
            
            print(f"  📊 获取 {len(news_list)} 条顶部新闻")
            return news_list[:max_news]
            
        except Exception as e:
            print(f"  ⚠️ 错误: {e}")
            return []
    
    def fetch_detail(self, news):
        """下钻获取详情"""
        url = news['url']
        print(f"  🔍 下钻: {news['title'][:40]}...")
        
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"    ⚠️ 状态码: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 标题
            title_elem = soup.find('h1')
            if title_elem:
                news['title'] = title_elem.get_text(strip=True)
            
            # 时间
            time_elem = soup.find('div', class_='pub-time')
            if time_elem:
                news['time'] = time_elem.get_text(strip=True)
            else:
                date_match = re.search(r'/(\d{4})/(\d{2})-(\d{2})/', url)
                if date_match:
                    news['time'] = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
            
            # 来源
            source_elem = soup.find('div', class_='pub-source')
            if source_elem:
                news['source'] = source_elem.get_text(strip=True).replace('来源：', '')
            else:
                news['source'] = '中国新闻网'
            
            # 正文
            content = ""
            content_div = soup.find('div', class_='content') or soup.find('article')
            if content_div:
                paragraphs = content_div.find_all('p')
                texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20]
                content = ' '.join(texts)
            
            if not content:
                print(f"    ⚠️ 无法提取正文")
                return news
            
            # 摘要
            news['content'] = content
            news['summary'] = content[:300] + ("..." if len(content) > 300 else "")
            
            # 分类
            news['category'] = self._guess_category(news['title'])
            
            # 关键要点
            news['key_points'] = self._extract_key_points(content)
            
            print(f"    ✅ 成功")
            return news
            
        except Exception as e:
            print(f"    ⚠️ 错误: {e}")
            return news
    
    def _extract_key_points(self, content):
        """提取关键要点"""
        points = []
        
        names = re.findall(r'习近平|李强|丁薛祥|李希|王毅|赵乐际', content)
        if names:
            points.append(f"涉及人物：{', '.join(set(names[:2]))}")
        
        orgs = re.findall(r'中共中央|国务院|中央军委|国台办|工信部|科技部|教育部', content)
        if orgs:
            points.append(f"涉及机构：{', '.join(set(orgs[:2]))}")
        
        events = re.findall(r'(教育改革|月球探测|载人航天|反腐败|建军|民主|法治)', content)
        if events:
            points.append(f"关键事件：{', '.join(set(events[:2]))}")
        
        return points
    
    def _guess_category(self, title):
        """分类"""
        categories = {
            '教育': ['教育', '学校', '学生', '教师'],
            '法律': ['法律', '法院', '检察', '司法'],
            '政治': ['习近平', '李强', '会议', '讲话', '党建', '军队'],
            '科技': ['科技', '航天', '月球', 'AI'],
            '两岸': ['台湾', '两岸', '台海'],
        }
        
        for cat, kws in categories.items():
            for kw in kws:
                if kw in title:
                    return cat
        return '时政'
    
    def run(self, max_news=5):
        """运行"""
        print("\n" + "="*60)
        print("📰 中国新闻网顶部焦点新闻")
        print("="*60)
        
        # 1. 获取顶部新闻标题
        news_list = self.get_top_news(max_news)
        
        if not news_list:
            print("  ⚠️ 无新闻")
            return []
        
        # 2. 下钻获取详情
        print("\n🔍 下钻获取详情...")
        results = []
        
        for i, news in enumerate(news_list, 1):
            print(f"\n[{i}/{len(news_list)}]")
            detail = self.fetch_detail(news)
            if detail:
                results.append(detail)
            time.sleep(0.3)
        
        return results


def main():
    fetcher = ChinaNewsFetcher()
    results = fetcher.run(max_news=5)
    
    # 保存
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    report = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'count': len(results),
        'news': results
    }
    
    with open(f'{OUTPUT_DIR}/top_news.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存: {OUTPUT_DIR}/top_news.json")
    
    # 打印
    for i, n in enumerate(results, 1):
        print(f"\n{i}. {n['title'][:50]}")
        print(f"   {n.get('source', '中国新闻网')} | {n.get('time', '')}")


if __name__ == "__main__":
    main()
