#!/usr/bin/env python3
"""
中新热榜完整采集器
1. 从 importnews.html 获取所有新闻标题和链接
2. 批量获取每条新闻的详细内容
3. 保存到数据库
"""
import requests
import sqlite3
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置
DB_PATH = "/Users/guanliming/dailynews/turso/reports.db"
OUTPUT_DIR = "/Users/guanliming/dailynews/output"
BASE_URL = "https://www.chinanews.com.cn"
OUTPUT_FILE = f"{OUTPUT_DIR}/hotnews_detail.json"

def get_hot_list():
    """获取热榜所有新闻"""
    print("📰 获取中新热榜...")
    response = requests.get(f"{BASE_URL}/importnews.html", timeout=15)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    container = soup.find('div', class_='content_list')
    if not container:
        print("  ⚠️ 未找到列表")
        return []
    
    items = container.find_all('li')
    news_list = []
    seen_urls = set()
    
    for item in items:
        if 'nocontent' in item.get('class', []):
            continue
        
        title_elem = item.find('div', class_='dd_bt')
        if not title_elem:
            continue
        
        links = title_elem.find_all('a')
        for link in links:
            href = link.get('href', '')
            title = link.get_text(strip=True)
            
            if '/iframe/' in href or '/shipin/' in href or not title or len(title) < 5:
                continue
            
            if href.startswith('//'):
                full_url = 'https:' + href
            elif href.startswith('/'):
                full_url = BASE_URL + href
            else:
                continue
            
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            
            time_elem = item.find('div', class_='dd_time')
            time_str = time_elem.get_text(strip=True) if time_elem else ""
            
            try:
                parts = time_str.split()[0].split('-')
                month, day = int(parts[0]), int(parts[1])
                pub_date = f"{datetime.now().year}-{month:02d}-{day:02d}"
            except:
                pub_date = datetime.now().strftime('%Y-%m-%d')
            
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
            break
    
    print(f"  ✅ 获取 {len(news_list)} 条新闻")
    return news_list

def get_content(url, title):
    """获取单条新闻内容"""
    try:
        resp = requests.get(url, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 获取正文
        content = ""
        content_div = soup.find('div', class_='content')
        if content_div:
            ps = content_div.find_all('p')
            texts = [p.get_text(strip=True) for p in ps if len(p.get_text(strip=True)) > 20]
            content = ' '.join(texts)
        
        # 摘要
        summary = content[:300] + ("..." if len(content) > 300 else "")
        
        # 分类
        category = guess_category(title + " " + content[:500])
        
        return {
            'title': title,
            'url': url,
            'content': content,
            'summary': summary,
            'category': category,
            'status': 'success'
        }
    except Exception as e:
        return {
            'title': title,
            'url': url,
            'error': str(e),
            'status': 'failed'
        }

def guess_category(text):
    """根据内容分类"""
    categories = {
        '科技': ['科技', 'AI', '微信', '互联网', '数字'],
        '教育': ['教育', '学校', '学生', '考试'],
        '法律': ['法院', '检察', '司法', '违法', '犯罪'],
        '两岸': ['台湾', '两岸', '国台办', '台海', '赖清德'],
        '国际': ['美国', '日本', '韩国', '国际', '外媒'],
        '经济': ['经济', '金价', '就业', '关税', '企业'],
        '社会': ['社会', '民生', '交通', '生活'],
    }
    
    for cat, kws in categories.items():
        for kw in kws:
            if kw in text:
                return cat
    return '要闻'

def match_chapter(news):
    """匹配道法课本章节"""
    title = news.get('title', '')
    content = news.get('content', '')[:500]
    category = news.get('category', '')
    text = title + ' ' + content
    
    rules = [
        {'kws': ['台湾', '两岸', '台独', '国台办', '台海', '赖清德'], 'book': '九年级上册', 'chapter': '中华一家亲'},
        {'kws': ['反腐', '违纪', '违法', '受贿', '调查', '检察院'], 'book': '九年级上册', 'chapter': '民主与法治'},
        {'kws': ['国防', '解放军', '军队', '军事'], 'book': '九年级上册', 'chapter': '中华一家亲'},
        {'kws': ['航天', '月球', '卫星', '科技', '创新', '医疗'], 'book': '九年级上册', 'chapter': '创新驱动发展'},
        {'kws': ['美国', '日本', '韩国', '国际'], 'book': '九年级上册', 'chapter': '建设美丽中国'},
        {'kws': ['就业', '经济', '关税', '企业'], 'book': '九年级上册', 'chapter': '富强与创新'},
        {'kws': ['生活', '民生'], 'book': '九年级上册', 'chapter': '建设美丽中国'},
    ]
    
    for rule in rules:
        for kw in rule['kws']:
            if kw in text:
                return {'book': rule['book'], 'chapter': rule['chapter'], 'reason': '关键词匹配'}
    
    return {'book': '九年级上册', 'chapter': '民主与法治', 'reason': '默认分类'}

def save_to_db(all_news):
    """保存到数据库"""
    print(f"\n💾 保存到数据库...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 清空现有数据
    cursor.execute("DELETE FROM daily_reports")
    cursor.execute("DELETE FROM report_chapter_mapping")
    
    # 获取有效新闻（成功的）
    valid_news = [n for n in all_news if n.get('status') == 'success']
    print(f"  📊 有效新闻: {len(valid_news)} 条")
    
    # 按日期分组
    date_groups = {}
    for news in valid_news:
        date = news.get('publish_date', datetime.now().strftime('%Y-%m-%d'))
        date_groups.setdefault(date, []).append(news)
    
    # 保存
    total = 0
    for date in sorted(date_groups.keys(), reverse=True):
        items = date_groups[date]
        for idx, news in enumerate(items, 1):
            chapter = match_chapter(news)
            
            # 保存到 daily_reports
            cursor.execute("""
                INSERT INTO daily_reports 
                (id, report_date, news_rank, news_title, source, publish_time, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{date}_{idx}",
                date,
                idx,
                news['title'],
                news.get('source', '中国新闻网'),
                news.get('time', date),
                news.get('summary', '')[:500]
            ))
            
            total += 1
    
    conn.commit()
    conn.close()
    print(f"  ✅ 保存完成！共 {total} 条")
    return total

def main():
    print("="*60)
    print("📰 中新热榜完整采集器")
    print("="*60)
    
    # 1. 获取热榜列表
    news_list = get_hot_list()
    if not news_list:
        print("  ⚠️ 无新闻")
        return
    
    # 2. 批量获取详情（使用多线程加速）
    print(f"\n📄 获取 {len(news_list)} 条新闻详情...")
    all_results = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(get_content, n['url'], n['title']): n for n in news_list}
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            result['publish_date'] = news_list[i-1].get('publish_date', '')
            result['time'] = news_list[i-1].get('time', '')
            result['channel'] = news_list[i-1].get('channel', '')
            all_results.append(result)
            print(f"  [{i}/{len(news_list)}] {result['title'][:30]}... [{result.get('status', 'unknown')}]")
    
    # 3. 保存到数据库
    save_to_db(all_results)
    
    # 4. 保存JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ JSON已保存: {OUTPUT_FILE}")
    
    # 5. 统计
    success = sum(1 for n in all_results if n.get('status') == 'success')
    print(f"\n📊 完成！成功 {success}/{len(news_list)} 条")

if __name__ == "__main__":
    main()
