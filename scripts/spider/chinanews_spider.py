#!/usr/bin/env python3
"""
中国新闻网新闻爬虫 - 最终版
"""
import requests
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup
import time

class ChinaNewsSpider:
    def __init__(self):
        self.base_url = "https://www.chinanews.com.cn/"
        self.china_url = "https://www.chinanews.com.cn/china/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        }
    
    def fix_url(self, href):
        """修复URL格式"""
        if not href:
            return ""
        if href.startswith('http'):
            return href
        if href.startswith('//'):
            return 'https:' + href
        if href.startswith('/'):
            return 'https://www.chinanews.com.cn' + href
        return 'https://www.chinanews.com.cn/' + href
    
    def fetch_title_list(self):
        """获取新闻标题列表"""
        try:
            print("  🌐 正在获取新闻列表...")
            response = requests.get(self.china_url, headers=self.headers, timeout=20)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_list = []
            seen = set()
            
            links = soup.select('a[href*="2026/"]')
            for link in links[:30]:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                if not href or not title or len(title) < 10:
                    continue
                
                # 处理 // 前缀
                if href.startswith('//'):
                    full_url = 'https:' + href
                elif href.startswith('/'):
                    full_url = 'https://www.chinanews.com.cn' + href
                else:
                    full_url = href
                
                if full_url in seen:
                    continue
                seen.add(full_url)
                
                news_list.append({
                    'title': title,
                    'url': full_url,
                    'source': '中国新闻网',
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'category': '时政',
                })
            
            print(f"    获取 {len(news_list)} 条标题")
            return news_list[:10]
            
        except Exception as e:
            print(f"    错误: {e}")
            return []
    
    def fetch_detail(self, url):
        """获取详情页内容"""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'  # 强制utf-8编码
            if response.status_code != 200:
                return "", []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            all_p = soup.find_all('p')
            
            if not all_p:
                return "", []
            
            texts = [p.get_text(strip=True) for p in all_p]
            texts = [t for t in texts if len(t) > 15]
            content = ' '.join(texts)
            
            # 生成摘要和要点
            summary = content[:300] + ("..." if len(content) > 300 else "")
            
            key_points = []
            
            # 提取要素
            names = re.findall(r'习近平|李强|丁薛祥|李希|朱凤莲|马帅莎', content)
            if names:
                key_points.append(f"人物：{', '.join(set(names))}")
            
            orgs = re.findall(r'中共中央|国务院|中央军委|国台办|工信部|科技部|住建部|市场监管总局|知识产权局|载人航天工程办公室', content)
            if orgs:
                key_points.append(f"机构：{', '.join(set(orgs[:3]))}")
            
            events = re.findall(r'月球探测|载人航天|反腐败|两岸|科技服务|标准体系|建军|建军', content)
            if events:
                key_points.append(f"事件：{', '.join(set(events))}")
            
            dates = re.findall(r'(\d+年\d+月\d+日|\d+月\d+日|\d+日)', content)
            if dates:
                key_points.append(f"时间：{dates[0]}")
            
            return summary, key_points[:3]
            
        except Exception as e:
            return "", []
    
    def get_news(self, max_news=5):
        """获取新闻"""
        news_list = self.fetch_title_list()
        if not news_list:
            return []
        
        print(f"\n  📰 下钻到详情页...")
        for i, news in enumerate(news_list[:max_news], 1):
            print(f"    [{i}] {news['title'][:25]}...")
            summary, key_points = self.fetch_detail(news['url'])
            news['summary'] = summary if summary else news['title']
            news['key_points'] = key_points
            time.sleep(0.3)
        
        return news_list[:max_news]

if __name__ == "__main__":
    spider = ChinaNewsSpider()
    news = spider.get_news(max_news=3)
    
    print(f"\n{'='*60}")
    for i, n in enumerate(news, 1):
        print(f"\n{i}. {n['title']}")
        print(f"   摘要: {n['summary'][:100]}...")
        if n['key_points']:
            for p in n['key_points']:
                print(f"   • {p}")
