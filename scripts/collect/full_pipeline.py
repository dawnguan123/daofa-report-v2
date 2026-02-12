#!/usr/bin/env python3
"""
新闻采集与报告生成完整工作流
1. 从中国新闻网获取标题范围
2. 下钻详情页获取内容
3. 生成道法时事报告
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
    
    def fetch_list_page(self, url="https://www.chinanews.com.cn/china/"):
        """从列表页获取新闻标题"""
        print(f"📰 获取列表: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"  ⚠️ 状态码: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找新闻列表
            items = soup.select('.hotlist li') or soup.select('.news-list li')
            
            news_list = []
            seen_urls = set()
            
            for item in items[:10]:
                link = item.find('a')
                if not link:
                    continue
                
                title = link.get_text(strip=True)
                href = link.get('href', '')
                
                if not title or len(title) < 10:
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
                    'source': '中国新闻网'
                })
            
            print(f"  ✓ 获取 {len(news_list)} 条标题")
            return news_list
            
        except Exception as e:
            print(f"  ⚠️ 获取失败: {e}")
            return []
    
    def fetch_detail(self, url, title=""):
        """下钻获取详情"""
        print(f"  🔍 下钻: {title[:40] if title else url}...")
        
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"    ⚠️ 状态码: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 标题
            if not title:
                title_elem = soup.find('h1')
                title = title_elem.get_text(strip=True) if title_elem else "无标题"
            
            # 时间
            time_str = ""
            time_elem = soup.find('div', class_='pub-time')
            if time_elem:
                time_str = time_elem.get_text(strip=True)
            else:
                date_match = re.search(r'/(\d{4})/(\d{2})-(\d{2})/', url)
                if date_match:
                    time_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
            
            # 来源
            source = "中国新闻网"
            source_elem = soup.find('div', class_='pub-source')
            if source_elem:
                source = source_elem.get_text(strip=True).replace('来源：', '')
            
            # 正文
            content = ""
            content_div = soup.find('div', class_='content') or soup.find('article')
            if content_div:
                paragraphs = content_div.find_all('p')
                texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20]
                content = ' '.join(texts)
            
            if not content:
                print(f"    ⚠️ 无法提取正文")
                return None
            
            # 摘要
            summary = content[:400] + ("..." if len(content) > 400 else "")
            
            # 分类
            category = self._guess_category(title)
            
            # 关键要点
            key_points = self._extract_key_points(content, title)
            
            return {
                'title': title,
                'url': url,
                'source': source,
                'time': time_str[:16] if time_str else datetime.now().strftime('%Y-%m-%d %H:%M'),
                'category': category,
                'content': content,
                'summary': summary,
                'key_points': key_points
            }
            
        except Exception as e:
            print(f"  ⚠️ 错误: {e}")
            return None
    
    def _extract_key_points(self, content, title):
        """提取关键要点"""
        points = []
        
        # 人物
        names = re.findall(r'习近平|李强|丁薛祥|李希|王毅|赵乐际', content)
        if names:
            points.append(f"涉及人物：{', '.join(set(names[:2]))}")
        
        # 机构
        orgs = re.findall(r'中共中央|国务院|中央军委|国台办|工信部|科技部|教育部', content)
        if orgs:
            points.append(f"涉及机构：{', '.join(set(orgs[:2]))}")
        
        # 事件
        events = re.findall(r'(教育改革|月球探测|载人航天|反腐败|建军|民主|法治)', content)
        if events:
            points.append(f"关键事件：{', '.join(set(events[:2]))}")
        
        return points
    
    def _guess_category(self, title):
        """分类"""
        categories = {
            '教育': ['教育', '学校', '学生', '教师', '考试'],
            '法律': ['法律', '法院', '检察', '司法', '犯罪'],
            '政治': ['习近平', '李强', '会议', '讲话', '党建', '军队'],
            '科技': ['科技', '航天', '月球', 'AI', '创新'],
            '两岸': ['台湾', '两岸', '国台办', '台海'],
            '外交': ['外交', '外长', '联合国', '国际'],
        }
        
        for cat, kws in categories.items():
            for kw in kws:
                if kw in title:
                    return cat
        return '时政'
    
    def match_chapters(self, news):
        """根据新闻类型智能匹配课本知识点"""
        title = news.get('title', '')
        content = news.get('content', '')[:500]
        category = news.get('category', '')
        text = title + ' ' + content
        
        # 定义匹配规则：关键词 -> 章节（优先级从高到低）
        # 注意：更具体的规则放在前面
        rules = [
            # 台海/两岸 - 高优先级
            {
                'keywords': ['台湾', '两岸', '台独', '国台办', '台海', '澎湖', '高金素梅', '赖清德'],
                'book': '九年级上册',
                'chapter': '中华一家亲',
                'reason': '两岸关系与国家统一'
            },
            # 反腐/违法 - 最高优先级，必须在最前面
            {
                'keywords': ['反腐', '违纪', '违法', '受贿', '审查', '调查', '落马', '监委', '法治', '检察院', '贪污', '公诉'],
                'book': '九年级上册',
                'chapter': '民主与法治',
                'reason': '反腐与法治'
            },
            # 国防/军事 - 仅当内容主要涉及军事时
            {
                'keywords': ['解放军', '军队', '军事', '建军', '战端', '军委', '海马斯'],
                'book': '九年级上册',
                'chapter': '中华一家亲',
                'reason': '国防与国家安全'
            },
            # 科技创新
            {
                'keywords': ['航天', '月球', '卫星', '雪豹', '探月', '载人', '黑洞', '南极', '天关'],
                'book': '九年级上册',
                'chapter': '创新驱动发展',
                'reason': '科技创新'
            },
            # 教育
            {
                'keywords': ['教育', '学校', '学生', '教师', '考试', '教育部'],
                'book': '七年级上册',
                'chapter': '成长的节拍',
                'reason': '教育与学习'
            },
            # 美丽中国/环境
            {
                'keywords': ['环境', '生态', '绿色', '碳中和'],
                'book': '九年级上册',
                'chapter': '建设美丽中国',
                'reason': '生态文明建设'
            },
            # 民主/人大
            {
                'keywords': ['民主', '人大', '政协', '全国人大'],
                'book': '九年级上册',
                'chapter': '民主与法治',
                'reason': '民主制度'
            },
            # 强国梦
            {
                'keywords': ['强国', '复兴', '梦想', '小康', '民族复兴'],
                'book': '九年级上册',
                'chapter': '中国人 中国梦',
                'reason': '中国梦'
            },
            # 科技政策
            {
                'keywords': ['科技', '创新', '服务业标准'],
                'book': '九年级上册',
                'chapter': '创新驱动发展',
                'reason': '科技创新政策'
            },
        ]
        
        # 按优先级匹配
        matched = None
        for rule in rules:
            for kw in rule['keywords']:
                if kw in text:
                    matched = rule
                    break
            if matched:
                break
        
        # 如果没匹配，根据分类兜底
        if not matched:
            category_rules = {
                '科技': {'book': '九年级上册', 'chapter': '创新驱动发展', 'reason': '科技类新闻'},
                '两岸': {'book': '九年级上册', 'chapter': '中华一家亲', 'reason': '两岸关系'},
                '法律': {'book': '九年级上册', 'chapter': '民主与法治', 'reason': '法律类'},
                '时政': {'book': '九年级上册', 'chapter': '民主与法治', 'reason': '时政要闻'},
            }
            matched = category_rules.get(category, {'book': '九年级上册', 'chapter': '民主与法治', 'reason': '时事关联'})
        
        return [{
            'book_name': matched['book'],
            'chapter_title': matched['chapter'],
            'reason': matched['reason']
        }]
    
    def generate_report(self, news_list):
        """生成报告"""
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'newsCount': len(news_list),
            'news': []
        }
        
        for i, news in enumerate(news_list, 1):
            # 匹配课本
            matched = self.match_chapters(news)
            
            report['news'].append({
                'rank': i,
                'title': news['title'],
                'source': news['source'],
                'time': news['time'],
                'category': news['category'],
                'summary': news.get('summary', ''),
                'key_points': news.get('key_points', []),
                'url': news['url'],
                'matchedChapters': matched
            })
        
        return report
    
    def run(self):
        """运行"""
        print("\n" + "="*70)
        print("📰 道法时事报告生成系统")
        print("="*70)
        
        # 1. 从列表页获取标题
        news_list = self.fetch_list_page()
        
        if not news_list:
            print("  ⚠️ 无发现新闻")
            return []
        
        # 2. 下钻获取详情
        print("\n📄 下钻获取详情...")
        collected = []
        
        for i, news in enumerate(news_list, 1):
            print(f"\n[{i}/{len(news_list)}]")
            detail = self.fetch_detail(news['url'], news['title'])
            
            if detail:
                collected.append(detail)
                print(f"    ✅ {detail['title'][:40]}...")
            time.sleep(0.3)
        
        # 3. 生成报告
        report = self.generate_report(collected)
        
        # 4. 保存
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        with open(os.path.join(OUTPUT_DIR, 'report_latest.json'), 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 报告已保存: report_latest.json")
        
        return report


def main():
    collector = NewsCollector()
    report = collector.run()
    
    # 打印报告
    print("\n" + "="*70)
    print("📰 报告预览")
    print("="*70)
    
    for news in report.get('news', []):
        print(f"\n{news['rank']}. {news['title']}")
        print(f"   {news['category']} · {news['source']} · {news['time']}")
        print(f"   摘要: {news.get('summary', '')[:100]}...")
        if news.get('key_points'):
            for p in news['key_points']:
                print(f"   📌 {p}")


if __name__ == "__main__":
    main()
