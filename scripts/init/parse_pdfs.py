#!/usr/bin/env python3
"""
PDF课本解析入库脚本
提取所有7个PDF的章节内容和知识点，存入SQLite
"""
import os
import re
import sqlite3
import json
import pdfplumber
from datetime import datetime

# PDF文件列表
PDF_FILES = [
    ("七年级上册", "道法课本/义务教育教科书 道德与法治 七年级上册.pdf"),
    ("七年级下册", "道法课本/义务教育教科书 道德与法治 七年级下册.pdf"),
    ("八年级上册", "道法课本/义务教育教科书 道德与法治 八年级上册.pdf"),
    ("八年级下册", "道法课本/义务教育教科书 道德与法治 八年级下册.pdf"),
    ("九年级上册", "道法课本/义务教育教科书 道德与法治 九年级上册.pdf"),
    ("九年级下册", "道法课本/义务教育教科书 道德与法治 九年级下册.pdf"),
    ("学生读本", "道法课本/学生读本·初中.pdf"),
]

def clean_text(text):
    """清理文本"""
    if not text:
        return ""
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_chapters_from_pdf(pdf_path, book_name):
    """从PDF提取章节"""
    chapters = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"\n📖 处理 {book_name} ({len(pdf.pages)} 页)")
            
            current_chapter = None
            current_section = None
            content_buffer = []
            page_num = 1
            
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    page_num += 1
                    continue
                
                text = clean_text(text)
                
                # 查找章节标题（常见格式）
                chapter_patterns = [
                    r'第[一二三四五六七八九十]+单元\s+([^\n]+)',
                    r'第[一二三四五六七八九十]+课\s+([^\n]+)',
                    r'^第一单元\s*$',
                    r'^第二单元\s*$',
                    r'^第三单元\s*$',
                    r'^第四单元\s*$',
                ]
                
                lines = text.split('。')
                for line in lines[:10]:  # 只检查前几行
                    for pattern in chapter_patterns:
                        match = re.match(pattern, line)
                        if match:
                            # 保存之前的章节
                            if current_chapter:
                                chapters.append({
                                    "book": book_name,
                                    "chapter": current_chapter,
                                    "section": current_section or "",
                                    "content": clean_text(' '.join(content_buffer)),
                                    "page": page_num
                                })
                            
                            current_chapter = match.group(1) if match.group(1) else line.strip()
                            current_section = ""
                            content_buffer = [line]
                            break
                    else:
                        # 不是章节标题，添加到内容
                        if current_chapter and len(line) > 10:
                            content_buffer.append(line)
                
                page_num += 1
            
            # 保存最后一个章节
            if current_chapter and content_buffer:
                chapters.append({
                    "book": book_name,
                    "chapter": current_chapter,
                    "section": current_section,
                    "content": clean_text(' '.join(content_buffer)),
                    "page": page_num
                })
    
    except Exception as e:
        print(f"  ✗ 错误: {e}")
    
    return chapters

def init_database():
    """初始化数据库"""
    conn = sqlite3.connect('turso/textbook_full.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS textbook_chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_name TEXT NOT NULL,
            chapter_title TEXT NOT NULL,
            section_title TEXT,
            page_range TEXT,
            content TEXT,
            content_summary TEXT,
            keywords TEXT,
            embedding BLOB,
            metadata TEXT,
            created_at DATETIME,
            updated_at DATETIME
        )
    ''')
    
    cursor.execute('DELETE FROM textbook_chapters')
    conn.commit()
    return conn

def generate_summary(content, max_length=150):
    """生成内容摘要"""
    if not content:
        return ""
    
    # 取前200字作为摘要
    summary = content[:200]
    if len(content) > 200:
        summary += "..."
    return summary

def extract_keywords(content):
    """提取关键词"""
    if not content:
        return []
    
    # 常见主题词
    theme_words = [
        '教育', '法律', '权利', '义务', '责任', '道德', '诚信', '友谊', '亲情',
        '生命', '成长', '青春', '梦想', '自信', '自强', '感恩', '奉献', '创新',
        '法治', '民主', '平等', '公正', '和谐', '文明', '友善', '敬业', '爱国',
        '市场经济', '消费', '劳动', '文化', '传统', '美德', '责任', '担当',
        '未成年', '保护', '安全', '健康', '心理', '网络', '媒体', '舆论'
    ]
    
    found = []
    for word in theme_words:
        if word in content:
            found.append(word)
    
    return found[:10]

def save_to_db(conn, chapters):
    """保存到数据库"""
    cursor = conn.cursor()
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    total = 0
    
    for ch in chapters:
        if len(ch['content']) < 50:  # 跳过太短的
            continue
        
        content_summary = generate_summary(ch['content'])
        keywords = json.dumps(extract_keywords(ch['content']), ensure_ascii=False)
        
        cursor.execute('''
            INSERT INTO textbook_chapters 
            (book_name, chapter_title, section_title, page_range, content, 
             content_summary, keywords, embedding, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            ch['book'],
            ch['chapter'],
            ch['section'],
            f"{ch['page']}-{ch['page']+5}",
            ch['content'],
            content_summary,
            keywords,
            json.dumps([0.0] * 768),  # 空的embedding
            json.dumps(ch),
            now,
            now
        ])
        total += 1
    
    conn.commit()
    return total

def main():
    print("=" * 60)
    print("📚 PDF课本解析入库")
    print("=" * 60)
    
    # 初始化数据库
    conn = init_database()
    
    all_chapters = []
    
    for book_name, pdf_path in PDF_FILES:
        if not os.path.exists(pdf_path):
            print(f"\n⚠️  跳过: {pdf_path} 不存在")
            continue
        
        print(f"\n📄 处理: {book_name}")
        chapters = extract_chapters_from_pdf(pdf_path, book_name)
        print(f"  → 提取 {len(chapters)} 个章节")
        
        for ch in chapters[:3]:  # 显示前3个
            print(f"     - {ch['chapter'][:30]}...")
        
        all_chapters.extend(chapters)
    
    # 保存到数据库
    print(f"\n💾 保存到数据库...")
    saved = save_to_db(conn, all_chapters)
    print(f"  → 成功保存 {saved} 个章节")
    
    conn.close()
    print("\n✅ 完成!")
    print(f"📁 数据库: turso/textbook_full.db")

if __name__ == "__main__":
    main()
