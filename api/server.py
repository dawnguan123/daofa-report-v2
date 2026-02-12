#!/usr/bin/env python3
"""
道法时事报告 API 服务器
"""
import sqlite3
import json
import os
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'turso', 'textbook_full.db')


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/api/dates', methods=['GET'])
def get_dates():
    """获取有报告的日期列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT publish_date, COUNT(*) as count, MAX(updated_at) as updated
        FROM news_articles 
        GROUP BY publish_date
        ORDER BY publish_date DESC
    """)
    
    dates = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'success': True,
        'dates': dates
    })


@app.route('/api/news', methods=['GET'])
def get_news():
    """获取指定日期的新闻"""
    date = request.args.get('date')
    
    if not date:
        return jsonify({'success': False, 'error': '缺少日期参数'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, url, source, publish_date, content, summary, 
               category, key_points, ai_summary, metadata
        FROM news_articles 
        WHERE publish_date = ?
        ORDER BY updated_at DESC
    """, (date,))
    
    news = []
    for row in cursor.fetchall():
        item = dict(row)
        
        # 解析JSON字段
        item['key_points'] = json.loads(row['key_points'] or '[]')
        item['metadata'] = json.loads(row['metadata'] or '{}')
        
        # 格式化内容
        if item['content']:
            item['content_preview'] = item['content'][:300].replace('\n', ' ') + '...'
        else:
            item['content_preview'] = ''
        
        news.append(item)
    
    conn.close()
    
    return jsonify({
        'success': True,
        'date': date,
        'count': len(news),
        'news': news
    })


@app.route('/api/crawl', methods=['POST'])
def crawl_news():
    """触发新闻采集"""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'collect'))
    
    try:
        from chinanews_fetcher import ChinaNewsFetcher
        
        fetcher = ChinaNewsFetcher()
        channel_url = request.json.get('url', 'https://www.chinanews.com.cn/china/')
        max_news = request.json.get('max', 5)
        
        results = fetcher.run(channel_url, max_news)
        
        return jsonify({
            'success': True,
            'count': len(results),
            'message': f'成功采集 {len(results)} 条新闻'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 新闻总数
    cursor.execute("SELECT COUNT(*) as total FROM news_articles")
    total = cursor.fetchone()['total']
    
    # 日期数
    cursor.execute("SELECT COUNT(DISTINCT publish_date) as dates FROM news_articles")
    dates = cursor.fetchone()['dates']
    
    # 最新日期
    cursor.execute("SELECT MAX(publish_date) as latest FROM news_articles")
    latest = cursor.fetchone()['latest']
    
    conn.close()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_news': total,
            'total_dates': dates,
            'latest_date': latest
        }
    })


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    print("🚀 启动道法时事报告 API 服务器...")
    print(f"📁 数据库: {DB_PATH}")
    app.run(host='0.0.0.0', port=port, debug=True)
