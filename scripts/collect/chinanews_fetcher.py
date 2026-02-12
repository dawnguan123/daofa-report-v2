#!/usr/bin/env python3
"""
中国新闻网通用新闻获取器
支持不同频道：/china/, /society/, /gn/ 等
自动保存到Turso数据库
包含AI专业总结功能
"""
import requests
import re
import json
import time
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime

# 配置
DB_PATH = "/Users/guanliming/dailynews/turso/textbook_full.db"
OUTPUT_DIR = "/Users/guanliming/dailynews/output"


class ChinaNewsFetcher:
    """中国新闻网新闻获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
    
    def get_dh_area_class(self, soup):
        """自动发现 dh 开头的区域类名"""
        for div in soup.find_all('div', class_=True):
            classes = div.get('class', [])
            for cls in classes:
                if cls.startswith('dh'):
                    return cls
        return None
    
    def extract_key_points(self, content, title):
        """从内容中提取关键要点"""
        key_points = []
        
        # 清理内容
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\d{1,2}:\d{2}', '', content)
        
        # 提取涉及机构
        org_patterns = [
            r'([^\s]{2,8}(?:部|委|局|办|政府|监委|航天局|办公室))',
            r'([^\s]{2,10}(?:公司|企业|研究所|工程办))',
        ]
        for pattern in org_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if 2 <= len(match) <= 6 and '据' not in match and '记者' not in match:
                    if match not in str(key_points):
                        key_points.append(f"机构：{match}")
        
        # 提取关键事件
        event_patterns = [
            r'([^\s]{4,12}(?:试验|发射|成功|突破|发布|实施))',
            r'([^\s]{3,10}(?:工程|计划|项目|火箭|飞船))',
        ]
        for pattern in event_patterns:
            matches = re.findall(pattern, content)
            for match in matches[:3]:
                if 3 <= len(match) <= 10 and match not in str(key_points):
                    key_points.append(f"事件：{match}")
        
        # 提取关键数字
        number_patterns = [
            r'(\d{4}年)',
            r'(\d+月\d+日)',
            r'(\d+\.\d+%)',
            r'(\d+万|\d+亿)',
        ]
        for pattern in number_patterns:
            matches = re.findall(pattern, content)
            for match in matches[:2]:
                if match not in str(key_points):
                    key_points.append(f"数据：{match}")
        
        # 去重并限制数量
        unique_points = []
        seen = set()
        for point in key_points:
            key = point[:12]
            if key not in seen:
                seen.add(key)
                unique_points.append(point)
        
        return unique_points[:4]
    
    def fetch_list(self, url, max_news=5):
        """获取新闻列表"""
        print(f"\n📰 访问: {url}")
        
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
            
            # 方法1: dh 开头的滚动区域
            dh_class = self.get_dh_area_class(soup)
            if dh_class:
                print(f"  ✅ 找到 dh 区域: {dh_class}")
                area = soup.select_one(f'.{dh_class}')
                if area:
                    links = area.find_all('a')
                    for a in links:
                        news = self._parse_link(a)
                        if news and self._is_valid(news):
                            self._add_news(news, news_list, seen_urls, seen_titles)
            
            # 方法2: news-list 区域
            if len(news_list) < max_news:
                print(f"  🔍 搜索 news-list...")
                for div in soup.select('.news-list')[:3]:
                    for a in div.find_all('a')[:max_news * 2]:
                        news = self._parse_link(a)
                        if news and self._is_valid(news):
                            self._add_news(news, news_list, seen_urls, seen_titles)
            
            print(f"  📊 获取 {len(news_list)} 条新闻")
            return news_list[:max_news]
            
        except Exception as e:
            print(f"  ⚠️ 错误: {e}")
            return []
    
    def _parse_link(self, a):
        """解析链接"""
        title = a.get_text(strip=True)
        href = a.get('href', '')
        
        if not title or not href:
            return None
        
        # 补全URL
        if href.startswith('//'):
            href = 'https:' + href
        elif href.startswith('/'):
            href = 'https://www.chinanews.com.cn' + href
        
        # 过滤有效链接
        if not href or 'chinanews' not in href:
            return None
        
        # 跳过视频、相册等链接
        skip_patterns = ['video', 'tv', 'photo', 'shipin', 'shipin', 'pic']
        if any(p in href.lower() for p in skip_patterns):
            return None
        
        # 跳过太短的标题
        if len(title) < 6:
            return None
        
        return {'title': title, 'url': href}
    
    def _is_valid(self, news):
        """验证新闻有效性"""
        title = news.get('title', '')
        url = news.get('url', '')
        
        if not title or not url:
            return False
        
        skip_titles = ['视频', '直播', '滚动', '专题', '广告', '排行榜']
        if any(t in title for t in skip_titles):
            return False
        
        return True
    
    def _add_news(self, news, news_list, seen_urls, seen_titles):
        """添加新闻到列表"""
        url = news.get('url', '')
        title = news.get('title', '')
        
        if url in seen_urls or title in seen_titles:
            return
        
        seen_urls.add(url)
        seen_titles.add(title)
        news_list.append(news)
    
    def fetch_detail(self, url):
        """获取新闻详情"""
        print(f"  📄 获取详情: {url[:60]}...")
        
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取发布时间
            pub_date = None
            time_elem = soup.select_one('.pub-time, .publish-time, .time, time')
            if time_elem:
                time_text = time_elem.get_text(strip=True)
                pub_date = self._parse_date(time_text)
            
            # 获取内容
            content = ""
            content_elem = soup.select_one('.content, .article-content, .text, .news-content, #article')
            if content_elem:
                # 获取纯文本
                content = content_elem.get_text(strip=True)
                
                # 清理内容噪声
                content = re.sub(r'来源[：:]\s*[^\s]+', '', content)
                content = re.sub(r'作者[：:]\s*[^\s]+', '', content)
                content = re.sub(r'责任编辑[：:]\s*[^\s]+', '', content)
                content = re.sub(r'\d{4}年\d{1,2}月\d{1,2}日\d{1,2}:\d{2}', '', content)
                content = re.sub(r'分享到[^\n]*', '', content)
                content = re.sub(r'大字体小字体[^\n]*', '', content)
                content = re.sub(r'\s+', ' ', content)
                content = content.strip()
            
            # 获取来源
            source = "中国新闻网"
            source_elem = soup.select_one('.source, .from, .pub-source')
            if source_elem:
                source_text = source_elem.get_text(strip=True)
                match = re.search(r'来源[：:]\s*([^\s]+)', source_text)
                if match:
                    source = match.group(1)
            
            return {
                'title': '',
                'url': url,
                'content': content,
                'publish_date': pub_date or datetime.now().strftime('%Y-%m-%d'),
                'source': source,
            }
            
        except Exception as e:
            print(f"  ⚠️ 详情获取失败: {e}")
            return None
    
    def _parse_date(self, date_str):
        """解析日期字符串"""
        try:
            # 匹配格式: 2026-02-11 10:30 或 2026年02月11日
            match = re.search(r'(\d{4})[-年](\d{1,2})[-月](\d{1,2})', date_str)
            if match:
                return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
        except:
            pass
        return None
    
    def process_news(self, news_item, category="时政"):
        """处理单条新闻"""
        url = news_item.get('url', '')
        title = news_item.get('title', '')
        
        # 获取详情
        detail = self.fetch_detail(url)
        if not detail:
            return None
        
        # 合并数据
        news = {
            'title': title or detail.get('title', ''),
            'url': url,
            'source': detail.get('source', '中国新闻网'),
            'publish_date': detail.get('publish_date', datetime.now().strftime('%Y-%m-%d')),
            'content': detail.get('content', ''),
            'category': category,
            'channel': url.split('/')[3] if len(url.split('/')) > 3 else 'news',
        }
        
        # 生成摘要
        news['summary'] = self._generate_summary(news['content'])
        
        # 提取关键要点
        news['key_points'] = self.extract_key_points(news['content'], news['title'])
        
        # 生成AI总结
        news['ai_summary'] = self.generate_ai_summary(news)
        
        # 元数据
        news['metadata'] = json.dumps({
            'rank': 0,
            'processed_at': datetime.now().isoformat()
        }, ensure_ascii=False)
        
        return news
    
    def _generate_summary(self, content):
        """生成摘要"""
        if not content:
            return ""
        
        # 清理内容噪声
        content = re.sub(r'来源[：:]\s*[^\s]+', '', content)
        content = re.sub(r'作者[：:]\s*[^\s]+', '', content)
        content = re.sub(r'责任编辑[：:]\s*[^\s]+', '', content)
        # 清理日期时间格式
        content = re.sub(r'\d{4}[-_]\d{1,2}[-_]\d{1,2}\s*\d{0,2}:\d{0,2}(?::\d{0,2})?', '', content)
        content = re.sub(r'\d{1,2}:\d{2}', '', content)
        # 清理括号内的记者名
        content = re.sub(r'\([^\)]*记者[^\)]*\)', '', content)
        # 清理分享链接等
        content = re.sub(r'分享到[^\n]*', '', content)
        content = re.sub(r'大字体小字体[^\n]*', '', content)
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        # 查找第一个段落（句号后），跳过重复的标题
        first_period = content.find('.')
        if first_period > 0 and first_period < 100:
            content = content[first_period+1:]
        
        # 取前150字
        if len(content) > 150:
            return content[:150].strip() + "..."
        return content.strip()
    
    def generate_ai_summary(self, news):
        """生成AI专业总结"""
        title = news.get('title', '')
        content = news.get('content', '')[:2000]
        category = news.get('category', '时政')
        key_points = news.get('key_points', [])
        
        summary_parts = []
        
        # 1. 新闻综述
        summary_parts.append("【新闻综述】")
        summary_parts.append(content[:300].replace('\n', ' ') + "...")
        
        # 2. 核心要点
        summary_parts.append("\n【核心要点】")
        if key_points:
            for point in key_points[:4]:
                summary_parts.append(f"• {point}")
        else:
            summary_parts.append("• 重要事件发展")
            summary_parts.append("• 相关政策措施")
        
        # 3. 道法关联
        summary_parts.append("\n【道法关联】")
        summary_parts.append(self._get_daofa_correlation(title, content, category))
        
        # 4. 思考问题
        summary_parts.append("\n【思考问题】")
        questions = self._get_thinking_questions(title, category)
        for q in questions:
            summary_parts.append(f"• {q}")
        
        return '\n'.join(summary_parts)
    
    def _get_daofa_correlation(self, title, content, category):
        """获取道法课程关联"""
        text = title + content
        
        correlations = [
            (['航天', '月球', '探测', '飞船', '火箭', '空间站'], 
             '九年级上册《创新驱动发展》', 
             '体现我国科技自立自强、航天强国建设'),
            
            (['台独', '两岸', '台湾', '祖国统一', '国台办'],
             '九年级上册《中华一家亲》',
             '体现维护国家统一、民族团结'),
             
            (['教育', '学校', '学生', '教师', '考试', '招生'],
             '九年级上册《踏上强国之路》',
             '体现教育强国、科技强国战略'),
             
            (['违法', '违纪', '腐败', '贪污', '受贿', '监察'],
             '七年级下册《走进法治天地》',
             '体现依法治国、反腐倡廉'),
             
            (['经济', '发展', '改革', '企业', '市场', '产业'],
             '九年级上册《创新驱动发展》',
             '体现高质量发展、新发展理念'),
             
            (['民生', '就业', '医疗', '养老', '社保', '住房'],
             '八年级上册《社会生活》',
             '体现以人民为中心的发展思想'),
             
            (['环保', '生态', '绿色', '碳中和', '污染防治'],
             '七年级上册《生命健康》',
             '体现生态文明建设、绿水青山就是金山银山'),
        ]
        
        for keywords, chapter, desc in correlations:
            if any(k in text for k in keywords):
                return f"{chapter}\n章节关联：{desc}\n匹配：{', '.join(keywords[:3])}"
        
        return f"{category}相关章节\n体现国家发展与社会进步的重要议题\n匹配：{category}"
    
    def _get_thinking_questions(self, title, category):
        """获取思考问题"""
        questions = {
            '时政': [
                '这一政策对普通人生活有什么影响？',
                '新闻反映了哪些社会发展趋势？',
            ],
            '科技': [
                '科技进步对国家发展有什么重要意义？',
                '作为青少年如何培养科技创新精神？',
            ],
            '社会': [
                '这一社会现象说明了什么？',
                '我们能为解决社会问题做什么？',
            ],
            '两岸': [
                '为什么说两岸同胞是一家人？',
                '青少年如何为祖国统一贡献力量？',
            ],
            '法律': [
                '这一案例说明了什么法律原则？',
                '青少年应该如何增强法治意识？',
            ],
        }
        return questions.get(category, ['这一事件有什么重要意义？', '对你有什么启发？'])
    
    def save_to_db(self, news_list, channel="china"):
        """保存到数据库"""
        if not news_list:
            return 0
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        saved_count = 0
        updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for news in news_list:
            if not news.get('title'):
                continue
            
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO news_articles 
                    (title, url, source, publish_date, content, summary, category, 
                     channel, key_points, ai_summary, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    news.get('title', ''),
                    news.get('url', ''),
                    news.get('source', '中国新闻网'),
                    news.get('publish_date', datetime.now().strftime('%Y-%m-%d')),
                    news.get('content', ''),
                    news.get('summary', ''),
                    news.get('category', '时政'),
                    news.get('channel', channel),
                    json.dumps(news.get('key_points', []), ensure_ascii=False),
                    news.get('ai_summary', ''),
                    news.get('metadata', '{}'),
                    updated_at,
                ))
                saved_count += 1
                
            except Exception as e:
                print(f"  ⚠️ 保存失败: {news.get('title', '')[:30]}... - {e}")
        
        conn.commit()
        conn.close()
        
        print(f"  💾 保存 {saved_count} 条新闻到数据库")
        return saved_count
    
    def run(self, channel_url, max_news=5):
        """主运行函数"""
        print("=" * 60)
        print("🚢 启动中国新闻网新闻获取器")
        print("=" * 60)
        
        # 解析频道
        if 'china' in channel_url:
            channel = 'china'
            category = '时政'
        elif 'society' in channel_url:
            channel = 'society'
            category = '社会'
        else:
            channel = 'news'
            category = '时政'
        
        # 获取列表
        news_list = self.fetch_list(channel_url, max_news)
        
        if not news_list:
            print("⚠️ 未获取到新闻")
            return []
        
        # 处理详情
        print("\n🔄 处理新闻详情...")
        processed_news = []
        for i, news in enumerate(news_list):
            print(f"  [{i+1}/{len(news_list)}] {news.get('title', '')[:40]}...")
            detail = self.process_news(news, category)
            if detail:
                processed_news.append(detail)
        
        # 保存
        saved = self.save_to_db(processed_news, channel)
        
        print("\n" + "=" * 60)
        print(f"✅ 完成！共处理 {len(processed_news)} 条，保存 {saved} 条")
        print("=" * 60)
        
        return processed_news


if __name__ == '__main__':
    import sys
    
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://www.chinanews.com.cn/china/'
    max_news = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    fetcher = ChinaNewsFetcher()
    fetcher.run(url, max_news)
