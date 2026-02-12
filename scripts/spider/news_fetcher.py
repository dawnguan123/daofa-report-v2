#!/usr/bin/env python3
"""
时事新闻获取器 - 道法时事报告专用
支持从中国新闻网等主流媒体获取时政新闻
"""
import requests
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup
import time

class NewsFetcher:
    """时政新闻获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # 配置要抓取的新闻源
        self.sources = [
            {
                'id': 'chinanews_gn',
                'name': '中国新闻网-国内',
                'url': 'https://www.chinanews.com.cn/gn/',
                'type': 'list',
                'selector': 'a[href*="/gn/2026/"]',
                'enabled': True
            },
        ]
    
    def fetch_list(self, source):
        """从列表页获取新闻标题和链接"""
        try:
            response = self.session.get(source['url'], timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"    状态码: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.select(source['selector'])
            
            news_list = []
            seen_urls = set()
            
            for link in links[:25]:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                if not href or not title or len(title) < 10:
                    continue
                
                # 清理URL
                if href.startswith('//'):
                    full_url = 'https:' + href
                elif href.startswith('/'):
                    full_url = 'https://www.chinanews.com.cn' + href
                else:
                    full_url = href
                
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                news_list.append({
                    'title': title,
                    'url': full_url,
                    'source': source['name'],
                    'source_id': source['id'],
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'category': self._guess_category(title),
                    'content': '',
                    'summary': '',
                    'key_points': []
                })
            
            return news_list
            
        except Exception as e:
            print(f"    获取失败: {e}")
            return []
    
    def fetch_detail(self, news):
        """下钻到详情页获取内容"""
        try:
            response = self.session.get(news['url'], timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return news
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取所有段落
            all_p = soup.find_all('p')
            if all_p:
                texts = [p.get_text(strip=True) for p in all_p]
                texts = [t for t in texts if len(t) > 20]
                content = ' '.join(texts)
                
                # 生成摘要
                news['content'] = content
                news['summary'] = self._generate_summary(content)
                news['key_points'] = self._extract_key_points(content, news['title'])
            
            return news
            
        except Exception as e:
            print(f"    详情获取失败: {e}")
            return news
    
    def _guess_category(self, title):
        """根据标题猜测分类"""
        title_lower = title.lower()
        
        categories = {
            '教育': ['教育', '学校', '学生', '教师', '考试', '升学'],
            '法律': ['法律', '法院', '检察院', '公安', '司法', '犯罪', '未成年人', '检察'],
            '经济': ['经济', 'GDP', 'CPI', '统计局', '市场', '企业', '消费', '产业'],
            '政治': ['政府', '会议', '政策', '领导人', '习近平', '李强', '讲话', '党建', '军队', '建军'],
            '社会': ['社会', '民生', '医疗', '社保', '就业', '住房', '环保'],
            '科技': ['科技', '航天', '月球', '人工智能', 'AI', '创新'],
            '两岸': ['台湾', '两岸', '国台办', '台海', '统一'],
            '外交': ['外交', '外长', '联合国', '国际', '峰会']
        }
        
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw in title:
                    return cat
        
        return '综合'
    
    def _generate_summary(self, content):
        """生成摘要"""
        if not content or len(content) < 50:
            return ""
        
        summary = content[:300]
        if len(content) > 300:
            summary += "..."
        
        return summary
    
    def _extract_key_points(self, content, title):
        """提取关键要点"""
        key_points = []
        
        # 提取人名
        names = re.findall(r'习近平|李强|丁薛祥|李希|王毅|赵乐际', content)
        if names:
            key_points.append(f"涉及人物：{', '.join(set(names[:2]))}")
        
        # 提取机构
        orgs = re.findall(r'中共中央|国务院|中央军委|国务院台办|工信部|科技部|住建部|市场监管总局|国家统计局', content)
        if orgs:
            key_points.append(f"涉及机构：{', '.join(set(orgs[:2]))}")
        
        # 提取关键事件
        events = re.findall(r'(月球探测|载人航天|反腐败|两岸|科技服务|标准体系|建军|改革|发展)', content)
        if events:
            key_points.append(f"关键事件：{', '.join(set(events[:2]))}")
        
        # 提取数据
        data = re.findall(r'(\d+年|\d+月\d+日|\d+\.?\d*%)', content)
        if data:
            key_points.append(f"关键数据：{data[0]}")
        
        return key_points
    
    def get_news(self, max_news=5):
        """获取新闻主入口"""
        all_news = []
        
        for source in self.sources:
            if not source['enabled']:
                continue
            
            print(f"  🌐 正在从 {source['name']} 获取...")
            
            # 1. 获取标题列表
            news_list = self.fetch_list(source)
            print(f"    获取 {len(news_list)} 条标题")
            
            if not news_list:
                continue
            
            # 2. 下钻获取详情
            print(f"  📰 下钻获取详情...")
            enriched_news = []
            for i, news in enumerate(news_list[:max_news], 1):
                print(f"    [{i}] {news['title'][:25]}...")
                enriched = self.fetch_detail(news)
                enriched_news.append(enriched)
                time.sleep(0.3)
            
            all_news.extend(enriched_news)
            break
        
        return all_news[:max_news]


def fetch_news():
    """便捷函数"""
    fetcher = NewsFetcher()
    return fetcher.get_news(max_news=5)


if __name__ == "__main__":
    news = fetch_news()
    
    print(f"\n获取到 {len(news)} 条新闻:\n")
    for i, n in enumerate(news, 1):
        print(f"{i}. {n['title']}")
        print(f"   来源: {n['source']} | 分类: {n['category']}")
        if n['summary']:
            print(f"   摘要: {n['summary'][:80]}...")
        if n['key_points']:
            for p in n['key_points']:
                print(f"   • {p}")
        print()
