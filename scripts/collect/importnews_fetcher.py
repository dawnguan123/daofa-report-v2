#!/usr/bin/env python3
"""
中新热榜新闻采集器
从 https://www.chinanews.com.cn/importnews.html 获取热榜新闻
存储到 Turso 数据库
"""
import requests
import re
import sqlite3
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup

# 配置
DB_PATH = "/Users/guanliming/dailynews/turso/reports.db"
OUTPUT_DIR = "/Users/guanliming/dailynews/output"
BASE_URL = "https://www.chinanews.com.cn"


class ImportNewsFetcher:
    """中新热榜新闻采集器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
    
    def fetch_hot_list(self, url=f"{BASE_URL}/importnews.html"):
        """获取热榜新闻列表"""
        print(f"\n📰 获取热榜: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"  ⚠️ 状态码: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找新闻列表 - 注意结构是 .content_list > ul > li
            container = soup.find('div', class_='content_list')
            if not container:
                print(f"  ⚠️ 未找到新闻列表容器")
                return []
            
            items = container.find_all('li')
            
            news_list = []
            seen_urls = set()
            today = datetime.now().strftime('%Y-%m-%d')
            
            for item in items:
                # 跳过空分隔符 - class 可能是 nocontent 或 class_='nocontent'
                if 'nocontent' in item.get('class', []):
                    continue
                
                # 获取标题和链接 - dd_bt 内部可能有多个 a
                title_elem = item.find('div', class_='dd_bt')
                if not title_elem:
                    continue
                
                links = title_elem.find_all('a')
                if not links:
                    continue
                
                # 获取第一个有效的链接
                for link in links:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)
                    
                    # 跳过 iframe 和视频链接
                    if '/iframe/' in href or '/shipin/' in href:
                        continue
                    if not title or len(title) < 5:
                        continue
                    
                    # 清理URL
                    if href.startswith('//'):
                        full_url = 'https:' + href
                    elif href.startswith('/'):
                        full_url = BASE_URL + href
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)
                    
                    # 获取时间
                    time_elem = item.find('div', class_='dd_time')
                    time_str = time_elem.get_text(strip=True) if time_elem else ""
                    
                    # 解析日期
                    pub_date = self._parse_date(time_str, today)
                    
                    # 获取频道
                    channel_elem = item.find('div', class_='dd_lm')
                    channel = channel_elem.get_text(strip=True).strip('[]') if channel_elem else "要闻"
                    
                    news_list.append({
                        'title': title,
                        'url': full_url,
                        'source': '中国新闻网',
                        'channel': channel,
                        'time': time_str,
                        'publish_date': pub_date
                    })
                    break  # 只取第一个有效的链接
            
            print(f"  ✓ 获取 {len(news_list)} 条热榜新闻")
            return news_list
            
        except Exception as e:
            print(f"  ⚠️ 获取失败: {e}")
            return []
    
    def _parse_date(self, time_str, default_date):
        """解析日期"""
        if not time_str:
            return default_date
        
        # 格式: "2-12 13:27" -> "2026-02-12"
        try:
            month, day = time_str.split()[0].split('-')
            year = datetime.now().year
            return f"{year}-{int(month):02d}-{int(day):02d}"
        except:
            return default_date
    
    def fetch_detail(self, url, title=""):
        """获取新闻详情"""
        print(f"  🔍 下钻: {title[:30] if title else url}...")
        
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
                # 尝试其他选择器
                content_div = soup.find('div', id='content_text') or soup.find('div', class_='article')
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
            
            return {
                'title': title,
                'url': url,
                'source': source,
                'time': time_str[:16] if time_str else datetime.now().strftime('%Y-%m-%d %H:%M'),
                'category': category,
                'content': content,
                'summary': summary,
            }
            
        except Exception as e:
            print(f"  ⚠️ 错误: {e}")
            return None
    
    def _guess_category(self, title):
        """分类"""
        categories = {
            '教育': ['教育', '学校', '学生', '教师', '考试'],
            '法律': ['法院', '检察', '司法', '犯罪'],
            '政治': ['习近平', '李强', '会议', '讲话', '党建'],
            '科技': ['科技', '航天', '月球', 'AI', '创新'],
            '两岸': ['台湾', '两岸', '国台办', '台海'],
            '国际': ['美国', '日本', '韩国', '联合国', '国际'],
            '社会': ['社会', '民生', '交通', '环境'],
            '经济': ['经济', '金融', '企业', '市场'],
        }
        
        for cat, kws in categories.items():
            for kw in kws:
                if kw in title:
                    return cat
        return '要闻'
    
    def save_to_db(self, news_list):
        """保存到 Turso 数据库"""
        print(f"\n💾 保存到数据库: {DB_PATH}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 清空现有数据（保留表结构）
        print("  🗑️ 清空现有数据...")
        cursor.execute("DELETE FROM news_articles")
        cursor.execute("DELETE FROM daily_reports")
        cursor.execute("DELETE FROM report_chapter_mapping")
        
        # 按日期分组
        date_groups = {}
        for news in news_list:
            date = news.get('publish_date', datetime.now().strftime('%Y-%m-%d'))
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(news)
        
        # 保存新闻并生成报告
        report_count = 0
        for date, items in sorted(date_groups.items(), reverse=True):
            report_id = f"{date}_0"
            
            # 保存到 news_articles
            for news in items:
                cursor.execute("""
                    INSERT INTO news_articles 
                    (id, title, url, source, publish_date, content, summary, category, channel)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"{date}_{items.index(news)}",
                    news['title'],
                    news['url'],
                    news.get('source', '中国新闻网'),
                    news.get('publish_date', date),
                    news.get('content', ''),
                    news.get('summary', ''),
                    news.get('category', '要闻'),
                    news.get('channel', '要闻')
                ))
            
            # 保存报告汇总
            cursor.execute("""
                INSERT INTO daily_reports 
                (id, report_date, news_count, report_html)
                VALUES (?, ?, ?, ?)
            """, (
                report_id,
                date,
                len(items),
                f"{date}/index.html"
            ))
            
            report_count += 1
            print(f"  ✓ {date}: {len(items)} 条新闻")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ 完成！共保存 {len(news_list)} 条新闻，{report_count} 份报告")
        return True
    
    def run(self):
        """运行采集"""
        print("\n" + "="*70)
        print("📰 中新热榜新闻采集器")
        print("="*70)
        
        # 1. 获取热榜列表
        news_list = self.fetch_hot_list()
        
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
                # 合并基本信息
                detail['channel'] = news.get('channel', '要闻')
                detail['publish_date'] = news.get('publish_date', datetime.now().strftime('%Y-%m-%d'))
                collected.append(detail)
                print(f"    ✅ {detail['title'][:40]}...")
            time.sleep(0.2)
        
        # 3. 保存到数据库
        if collected:
            self.save_to_db(collected)
        
        return collected


def main():
    fetcher = ImportNewsFetcher()
    fetcher.run()


if __name__ == "__main__":
    main()
