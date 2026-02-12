#!/usr/bin/env python3
"""快速获取中新热榜新闻列表"""
import requests
import sqlite3
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup

DB_PATH = "/Users/guanliming/dailynews/turso/reports.db"
OUTPUT_DIR = "/Users/guanliming/dailynews/output"
BASE_URL = "https://www.chinanews.com.cn"

def get_news_list():
    print("📰 获取热榜...")
    response = requests.get(f"{BASE_URL}/importnews.html", timeout=15)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    container = soup.find('div', class_='content_list')
    items = container.find_all('li') if container else []
    
    news_list = []
    seen_urls = set()
    today = datetime.now().strftime('%Y-%m-%d')
    
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
            
            if '/iframe/' in href or '/shipin/' in href or not title:
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
            
            # 时间
            time_elem = item.find('div', class_='dd_time')
            time_str = time_elem.get_text(strip=True) if time_elem else ""
            
            # 解析日期
            try:
                parts = time_str.split()[0].split('-')
                month, day = int(parts[0]), int(parts[1])
                pub_date = f"{datetime.now().year}-{month:02d}-{day:02d}"
                pub_time = f"{datetime.now().year}-{parts[0]}-{parts[1]} {time_str.split()[1]}" if ' ' in time_str else f"{pub_date} 00:00"
            except:
                pub_date = today
                pub_time = today
            
            # 频道
            channel_elem = item.find('div', class_='dd_lm')
            channel = channel_elem.get_text(strip=True).strip('[]') if channel_elem else "要闻"
            
            news_list.append({
                'title': title,
                'url': full_url,
                'source': '中国新闻网',
                'channel': channel,
                'time': time_str,
                'publish_date': pub_date,
                'publish_time': pub_time
            })
            break
    
    print(f"  ✓ 获取 {len(news_list)} 条新闻")
    return news_list

def save_to_db(news_list):
    print(f"\n💾 保存到数据库...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 清空现有数据
    cursor.execute("DELETE FROM daily_reports")
    cursor.execute("DELETE FROM report_chapter_mapping")
    print("  🗑️ 已清空现有数据")
    
    # 按日期分组
    date_groups = {}
    for news in news_list:
        date = news.get('publish_date', datetime.now().strftime('%Y-%m-%d'))
        date_groups.setdefault(date, []).append(news)
    
    # 保存 - 按日期和排名
    total = 0
    for date in sorted(date_groups.keys(), reverse=True):
        items = date_groups[date]
        for idx, news in enumerate(items, 1):
            cursor.execute("""
                INSERT INTO daily_reports 
                (id, report_date, news_rank, news_title, source, publish_time, summary, html_path)
                VALUES (?, ?, ?, ?, ?, ?, '', ?)
            """, (
                f"{date}_{idx}",
                date,
                idx,
                news['title'],
                news.get('source', '中国新闻网'),
                news.get('publish_time', date),
                f"{date}/index.html"
            ))
            total += 1
    
    conn.commit()
    conn.close()
    print(f"  ✅ 保存完成！共 {total} 条新闻")
    return total

def generate_report(news_list):
    """生成HTML报告"""
    print(f"\n📄 生成报告...")
    
    # 按日期分组
    date_groups = {}
    for news in news_list:
        date = news.get('publish_date', datetime.now().strftime('%Y-%m-%d'))
        date_groups.setdefault(date, []).append(news)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 生成最新报告
    if news_list:
        date = news_list[0].get('publish_date', datetime.now().strftime('%Y-%m-%d'))
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>道法时事报告 - {date}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh; padding: 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 20px; box-shadow: 0 25px 80px rgba(0,0,0,0.4); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%); color: white; padding: 35px; text-align: center; }}
        .header h1 {{ font-size: 32px; margin-bottom: 8px; }}
        .content {{ padding: 30px; }}
        .news-item {{ background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 16px; padding: 24px; margin-bottom: 20px; border-left: 5px solid #e94560; }}
        .news-rank {{ display: inline-block; background: #e94560; color: white; width: 28px; height: 28px; border-radius: 50%; text-align: center; line-height: 28px; font-size: 14px; font-weight: bold; margin-right: 10px; }}
        .news-title {{ font-size: 18px; font-weight: bold; color: #1a1a2e; margin-bottom: 10px; }}
        .news-meta {{ font-size: 12px; color: #666; margin-bottom: 12px; }}
        .news-meta span {{ background: #e9ecef; padding: 3px 10px; border-radius: 15px; margin-right: 8px; }}
        .footer {{ text-align: center; padding: 20px; background: #f8f9fa; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 道法时事报告</h1>
            <p>{date} · 共{len(news_list)}条新闻 · 数据来源：中国新闻网热榜</p>
        </div>
        <div class="content">
'''
        
        for i, news in enumerate(news_list[:20], 1):
            html += f'''
            <div class="news-item">
                <span class="news-rank">{i}</span>
                <span class="news-title">{news['title']}</span>
                <div class="news-meta">
                    <span>📎 {news.get('source', '中国新闻网')}</span>
                    <span>📅 {news.get('time', news.get('publish_date', ''))}</span>
                    <span>📂 {news.get('channel', '要闻')}</span>
                </div>
            </div>
'''
        
        html += '''
        </div>
        <div class="footer">
            <p>🤖 自动生成 by News Collector</p>
        </div>
    </div>
</body>
</html>'''
        
        with open(f"{OUTPUT_DIR}/report_latest.html", 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"  ✅ 报告已生成: {OUTPUT_DIR}/report_latest.html")

import os

def main():
    print("="*50)
    print("📰 中新热榜新闻采集器")
    print("="*50)
    
    news = get_news_list()
    if news:
        save_to_db(news)
        generate_report(news)
        
        print("\n📊 新闻列表 (前10条):")
        for i, n in enumerate(news[:10], 1):
            print(f"  {i}. {n['title'][:45]}... [{n['channel']}]")
        
        print(f"\n✅ 完成！共采集 {len(news)} 条新闻")

if __name__ == "__main__":
    main()
