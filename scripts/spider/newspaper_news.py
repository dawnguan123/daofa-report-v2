#!/usr/bin/env python3
"""
时政新闻获取器 - Newspaper3k 版
使用 newspaper3k 智能提取新闻正文
"""
import requests
import re
import json
import time
import sys
from datetime import datetime
from bs4 import BeautifulSoup
from newspaper import Article

# 尝试下载 nltk 数据（首次运行需要）
try:
    import nltk
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except:
    pass


class NewspaperNewsFetcher:
    """基于 newspaper3k 的新闻获取器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def fetch_list(self, url, selector='.content_list li'):
        """获取新闻列表"""
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
            
            for item in items[:15]:
                link = item.find('a')
                if not link:
                    continue
                
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                if not href or not title or len(title) < 8:
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
                
                # 提取时间
                time_elem = item.find('span', class_='dd')
                time_str = time_elem.get_text(strip=True) if time_elem else datetime.now().strftime('%Y-%m-%d')
                
                news_list.append({
                    'title': title,
                    'url': full_url,
                    'time': time_str,
                    'category': self._guess_category(title),
                })
            
            return news_list
            
        except Exception as e:
            print(f"    获取列表失败: {e}")
            return []
    
    def fetch_detail(self, news):
        """使用 newspaper3k 提取新闻详情"""
        try:
            article = Article(news['url'], language='zh')
            article.download()
            article.parse()
            
            # 获取标题
            if article.title:
                news['title'] = article.title
            
            # 获取正文（已自动去除广告和导航栏）
            news['content'] = article.text
            
            # 获取发布时间
            if article.publish_date:
                news['time'] = article.publish_date.strftime('%Y-%m-%d %H:%M')
            
            # 生成摘要
            news['summary'] = self._generate_summary(article.text)
            
            # 提取关键要点
            news['key_points'] = self._extract_key_points(article.text, news['title'])
            
            # 来源
            news['source'] = self._guess_source(news['url'])
            
            return news
            
        except Exception as e:
            print(f"    详情获取失败: {e}")
            # 备用：使用简化的 requests 获取
            return self._fetch_detail_backup(news)
    
    def _fetch_detail_backup(self, news):
        """备用详情获取方法"""
        try:
            response = self.session.get(news['url'], timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return news
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取正文
            content_div = soup.find('div', class_='content')
            if content_div:
                paragraphs = content_div.find_all('p')
                texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30]
                news['content'] = ' '.join(texts)
            else:
                all_p = soup.find_all('p')
                texts = [p.get_text(strip=True) for p in all_p if len(p.get_text(strip=True)) > 30]
                news['content'] = ' '.join(texts[:10])
            
            news['summary'] = self._generate_summary(news.get('content', ''))
            news['key_points'] = self._extract_key_points(news.get('content', ''), news['title'])
            news['source'] = self._guess_source(news['url'])
            
            return news
            
        except Exception as e:
            print(f"    备用获取也失败: {e}")
            return news
    
    def _generate_summary(self, content):
        """生成摘要"""
        if not content or len(content) < 50:
            return ""
        
        # 取前300字
        summary = content[:300]
        if len(content) > 300:
            summary += "..."
        
        return summary
    
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
    
    def _guess_category(self, title):
        """猜测分类"""
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
    
    def get_chinanews(self, max_news=5):
        """获取中国新闻网新闻"""
        print("  🌐 正在从中国新闻网获取...")
        
        # 获取列表
        news_list = self.fetch_list(
            url='https://www.chinanews.com.cn/china/',
            selector='.content_list li'
        )
        
        if not news_list:
            # 尝试备用选择器
            news_list = self.fetch_list(
                url='https://www.chinanews.com.cn/gn/',
                selector='.dd_box li'
            )
        
        print(f"    获取 {len(news_list)} 条标题")
        
        if not news_list:
            return []
        
        # 丰富内容
        enriched = []
        for i, news in enumerate(news_list[:max_news], 1):
            print(f"    [{i}] 提取: {news['title'][:25]}...")
            enriched_news = self.fetch_detail(news)
            enriched.append(enriched_news)
            time.sleep(1)  # 避免请求过快
        
        return enriched


def fetch_news():
    """便捷函数"""
    fetcher = NewspaperNewsFetcher()
    return fetcher.get_chinanews(max_news=5)


if __name__ == "__main__":
    print("=" * 60)
    print(" Newspaper3k 新闻获取器")
    print("=" * 60)
    
    fetcher = NewspaperNewsFetcher()
    news_list = fetcher.get_chinanews(max_news=5)
    
    print(f"\n{'=' * 60}")
    print(f"获取到 {len(news_list)} 条新闻:")
    print('=' * 60)
    
    for i, n in enumerate(news_list, 1):
        print(f"\n{i}. {n.get('title', '无标题')[:50]}")
        print(f"   来源: {n.get('source', '未知')} | 分类: {n.get('category', '未知')}")
        if n.get('summary'):
            print(f"   摘要: {n['summary'][:80]}...")
        if n.get('key_points'):
            for p in n['key_points']:
                print(f"   • {p}")
    
    # 保存为 JSON
    output = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'count': len(news_list),
        'news': news_list
    }
    
    with open('output/chinanews_latest.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存到 output/chinanews_latest.json")
