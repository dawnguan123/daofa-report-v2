#!/usr/bin/env python3
"""
时政新闻获取器 - 混合方案
主方案: Tavily API（已验证可用）
备选方案: newspaper3k（适用于无反爬网站）
"""
import requests
import re
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup
from tavily import TavilyClient

# 配置
TAVILY_API_KEY = "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"


class HybridNewsFetcher:
    """混合新闻获取器"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or TAVILY_API_KEY
        self.tavily_client = TavilyClient(api_key=self.api_key)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
    
    def get_news_via_tavily(self, max_news=5):
        """方案1: Tavily API 搜索"""
        print("  🔍 使用 Tavily API 搜索...")
        
        queries = [
            "2026年2月 中国时政新闻 习近平",
            "2026年2月 中国政府 国务院 政策",
        ]
        
        all_results = []
        
        for query in queries[:2]:
            print(f"    搜索: {query[:30]}...")
            try:
                response = self.tavily_client.search(
                    query=query,
                    max_results=5,
                    include_answer=True
                )
                results = response.get('results', [])
                all_results.extend(results)
                print(f"      获取 {len(results)} 条")
            except Exception as e:
                print(f"      搜索失败: {e}")
        
        # 去重
        seen_urls = set()
        unique_results = []
        for r in all_results:
            url = r.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(r)
        
        print(f"  📊 去重后: {len(unique_results)} 条")
        
        # 丰富内容
        news_list = []
        for i, r in enumerate(unique_results[:max_news], 1):
            print(f"  [{i}] 处理: {r.get('title', '')[:30]}...")
            
            news = {
                'title': r.get('title', ''),
                'url': r.get('url', ''),
                'source': self._guess_source(r.get('url', '')),
                'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'category': self._guess_category(r.get('title', '')),
                'content': r.get('content', '') or r.get('answer', ''),
                'summary': self._generate_summary(r.get('answer', '')),
                'key_points': self._extract_key_points(
                    r.get('content', '') or r.get('answer', ''),
                    r.get('title', '')
                )
            }
            news_list.append(news)
        
        return news_list
    
    def get_news_via_requests(self, url, selector, max_news=5):
        """方案2: 直接 requests（适用于无反爬网站）"""
        print(f"  🌐 直接访问: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"    状态码: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select(selector)
            
            news_list = []
            seen_urls = set()
            
            for item in items[:max_news * 2]:
                link = item.find('a')
                if not link:
                    continue
                
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                if not href or not title or len(title) < 10:
                    continue
                
                if href.startswith('//'):
                    full_url = 'https:' + href
                elif href.startswith('/'):
                    full_url = 'https://www.chinanews.com.cn' + href
                else:
                    full_url = href
                
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                # 获取详情
                content = self._fetch_content(full_url)
                
                news = {
                    'title': title,
                    'url': full_url,
                    'source': self._guess_source(full_url),
                    'time': datetime.now().strftime('%Y-%m-%d'),
                    'category': self._guess_category(title),
                    'content': content,
                    'summary': self._generate_summary(content),
                    'key_points': self._extract_key_points(content, title)
                }
                news_list.append(news)
                print(f"    [{len(news_list)}] {title[:25]}...")
                time.sleep(0.5)
                
                if len(news_list) >= max_news:
                    break
            
            return news_list
            
        except Exception as e:
            print(f"    错误: {e}")
            return []
    
    def _fetch_content(self, url):
        """获取网页内容"""
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return ""
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试找到正文
            content_div = soup.find('div', class_='content') or \
                         soup.find('div', class_='article') or \
                         soup.find('article')
            
            if content_div:
                paragraphs = content_div.find_all('p')
                texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30]
                return ' '.join(texts[:15])
            
            # 备用：所有 p 标签
            all_p = soup.find_all('p')
            texts = [p.get_text(strip=True) for p in all_p if len(p.get_text(strip=True)) > 30]
            return ' '.join(texts[:10])
            
        except:
            return ""
    
    def _generate_summary(self, content):
        """生成摘要"""
        if not content or len(content) < 50:
            return ""
        return content[:300] + ("..." if len(content) > 300 else "")
    
    def _extract_key_points(self, content, title):
        """提取关键要点"""
        key_points = []
        
        if not content:
            return key_points
        
        names = re.findall(r'习近平|李强|丁薛祥|李希|王毅|赵乐际', content)
        if names:
            key_points.append(f"涉及人物：{', '.join(set(names[:2]))}")
        
        orgs = re.findall(r'中共中央|国务院|中央军委|国台办|工信部|科技部|教育部', content)
        if orgs:
            key_points.append(f"涉及机构：{', '.join(set(orgs[:2]))}")
        
        events = re.findall(r'(月球探测|载人航天|反腐败|两岸|建军|改革|发展)', content)
        if events:
            key_points.append(f"关键事件：{', '.join(set(events[:2]))}")
        
        return key_points
    
    def _guess_category(self, title):
        """猜测分类"""
        categories = {
            '教育': ['教育', '学校', '学生', '教师', '考试'],
            '法律': ['法律', '法院', '检察', '司法', '犯罪'],
            '经济': ['经济', 'GDP', 'CPI', '统计局', '市场', '消费'],
            '政治': ['习近平', '李强', '会议', '讲话', '党建', '军队', '中共中央'],
            '社会': ['社会', '民生', '医疗', '社保', '就业'],
            '科技': ['科技', '航天', '月球', 'AI', '创新'],
            '两岸': ['台湾', '两岸', '国台办', '台海'],
            '外交': ['外交', '外长', '联合国', '国际']
        }
        
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw in title:
                    return cat
        return '时政'
    
    def _guess_source(self, url):
        """猜测来源"""
        if 'sina' in url:
            return '新浪新闻'
        elif 'qq' in url:
            return '腾讯新闻'
        elif 'people' in url:
            return '人民网'
        elif 'xinhuanet' in url:
            return '新华网'
        elif 'chinanews' in url:
            return '中国新闻网'
        elif 'moe' in url:
            return '教育部'
        else:
            return '其他媒体'
    
    def get_political_news(self, max_news=5, method='tavily'):
        """获取时政新闻主入口"""
        print(f"\n📰 开始获取时政新闻 (方案: {method})...")
        
        if method == 'tavily':
            return self.get_news_via_tavily(max_news)
        else:
            return self.get_news_via_requests(
                url='https://www.chinanews.com.cn/china/',
                selector='.content_list li',
                max_news=max_news
            )


def fetch_news():
    """便捷函数 - 使用 Tavily"""
    fetcher = HybridNewsFetcher()
    return fetcher.get_political_news(max_news=5, method='tavily')


if __name__ == "__main__":
    fetcher = HybridNewsFetcher()
    news_list = fetcher.get_political_news(max_news=5, method='tavily')
    
    print(f"\n✅ 获取到 {len(news_list)} 条新闻")
    
    for i, n in enumerate(news_list, 1):
        print(f"\n{i}. {n['title'][:50]}")
        print(f"   来源: {n['source']} | 分类: {n['category']}")
        if n['summary']:
            print(f"   摘要: {n['summary'][:60]}...")
