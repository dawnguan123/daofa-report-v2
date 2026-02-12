#!/usr/bin/env python3
"""
时政新闻获取器 - Tavily API 版
使用 Tavily AI 搜索引擎获取时政新闻
"""
import os
import re
from datetime import datetime
from tavily import TavilyClient

# API Key (用户提供的)
TAVILY_API_KEY = "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"


class TavilyNewsFetcher:
    """基于 Tavily 的时政新闻获取器"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or TAVILY_API_KEY
        self.client = TavilyClient(api_key=self.api_key)
    
    def search_news(self, query, max_results=10):
        """搜索新闻"""
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                include_answer=True,
                include_raw_content=False
            )
            return response.get('results', [])
        except Exception as e:
            print(f"  搜索错误: {e}")
            return []
    
    def fetch_content(self, url):
        """获取网页内容"""
        try:
            response = self.client.fetch_content(url=url)
            return response.get('content', '')
        except Exception as e:
            print(f"  获取内容错误: {e}")
            return ''
    
    def enrich_news(self, search_result):
        """丰富新闻内容"""
        url = search_result.get('url', '')
        title = search_result.get('title', '')
        answer = search_result.get('answer', '')
        
        # 使用 search 已返回的内容
        content = search_result.get('content', '') or answer
        
        # 提取关键要点
        key_points = self._extract_key_points(content, title)
        
        # 生成摘要
        summary = self._generate_summary(content, answer)
        
        return {
            'title': title,
            'url': url,
            'source': self._guess_source(url),
            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'category': self._guess_category(title),
            'content': content,
            'summary': summary,
            'key_points': key_points
        }
    
    def _extract_key_points(self, content, title):
        """提取关键要点"""
        key_points = []
        
        if not content:
            return []
        
        # 提取人名
        names = re.findall(r'习近平|李强|丁薛祥|李希|王毅|赵乐际', content)
        if names:
            key_points.append(f"涉及人物：{', '.join(set(names[:2]))}")
        
        # 提取机构
        orgs = re.findall(r'中共中央|国务院|中央军委|国台办|工信部|科技部|教育部|市场监管总局', content)
        if orgs:
            key_points.append(f"涉及机构：{', '.join(set(orgs[:2]))}")
        
        # 提取关键事件
        events = re.findall(r'(月球探测|载人航天|反腐败|两岸|建军|改革|发展|科技自立自强)', content)
        if events:
            key_points.append(f"关键事件：{', '.join(set(events[:2]))}")
        
        # 提取时间
        dates = re.findall(r'(\d+年\d+月\d+日|\d+月\d+日)', content)
        if dates:
            key_points.append(f"时间：{dates[0]}")
        
        return key_points
    
    def _generate_summary(self, content, answer):
        """生成摘要"""
        # 如果有 Tavily 的 answer，直接使用
        if answer and len(answer) > 50:
            return answer[:300] + ("..." if len(answer) > 300 else "")
        
        # 否则从内容截取
        if content:
            return content[:300] + ("..." if len(content) > 300 else "")
        
        return ""
    
    def _guess_category(self, title):
        """猜测分类"""
        title_lower = title.lower()
        
        categories = {
            '教育': ['教育', '学校', '学生', '教师', '考试'],
            '法律': ['法律', '法院', '检察', '司法', '犯罪', '未成年'],
            '经济': ['经济', 'GDP', 'CPI', '统计局', '市场', '消费', '产业'],
            '政治': ['习近平', '李强', '会议', '讲话', '党建', '军队', '建军', '中共中央'],
            '社会': ['社会', '民生', '医疗', '社保', '就业', '住房'],
            '科技': ['科技', '航天', '月球', 'AI', '创新', '自立自强'],
            '两岸': ['台湾', '两岸', '国台办', '台海', '统一'],
            '外交': ['外交', '外长', '联合国', '国际', '峰会']
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
        elif 'ifeng' in url:
            return '凤凰新闻'
        elif 'people' in url:
            return '人民网'
        elif 'xinhuanet' in url:
            return '新华网'
        elif 'chinanews' in url:
            return '中国新闻网'
        elif 'inewsweek' in url:
            return '中国新闻周刊'
        elif 'moe' in url:
            return '教育部'
        else:
            return '其他媒体'
    
    def get_political_news(self, max_news=5):
        """获取时政新闻主入口"""
        print("🔍 使用 Tavily 搜索时政新闻...")
        
        # 搜索策略
        queries = [
            "2026年2月 中国时政新闻 习近平",
            "2026年2月 中国政府 国务院", 
            "2026年2月 中国两会 政策"
        ]
        
        all_results = []
        
        for query in queries[:2]:  # 只搜索前2个
            print(f"  📰 搜索: {query[:30]}...")
            results = self.search_news(query, max_results=5)
            all_results.extend(results)
            print(f"     获取 {len(results)} 条结果")
        
        # 去重
        seen_urls = set()
        unique_results = []
        for r in all_results:
            url = r.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(r)
        
        print(f"\n  📊 去重后: {len(unique_results)} 条")
        
        # 丰富内容
        news_list = []
        for i, result in enumerate(unique_results[:max_news], 1):
            print(f"  [{i}] 丰富内容: {result.get('title', '')[:30]}...")
            enriched = self.enrich_news(result)
            news_list.append(enriched)
        
        return news_list


def fetch_news():
    """便捷函数"""
    fetcher = TavilyNewsFetcher()
    return fetcher.get_political_news(max_news=5)


if __name__ == "__main__":
    news = fetch_news()
    
    print(f"\n{'='*60}")
    print(f"获取到 {len(news)} 条时政新闻:")
    print('='*60)
    
    for i, n in enumerate(news, 1):
        print(f"\n{i}. {n['title']}")
        print(f"   来源: {n['source']} | 分类: {n['category']}")
        if n['summary']:
            print(f"   摘要: {n['summary'][:80]}...")
        if n['key_points']:
            for p in n['key_points']:
                print(f"   • {p}")
