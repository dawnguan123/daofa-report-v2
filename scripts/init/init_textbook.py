#!/usr/bin/env python3
"""
初始化道法课本 - 手动插入示例数据
"""
import sqlite3
import json
import os
from datetime import datetime

def init_database(db_path):
    """初始化数据库"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS textbook_anchors (
            anchor_id TEXT PRIMARY KEY,
            chapter_title TEXT NOT NULL,
            section_title TEXT,
            page_range TEXT NOT NULL,
            page_start INT,
            page_end INT,
            content TEXT,
            content_summary TEXT,
            embedding BLOB,
            raw_metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

def insert_sample_data(conn):
    """插入示例课本数据"""
    cursor = conn.cursor()
    
    sample_chapters = [
        {
            "anchor_id": "ch1_p1",
            "chapter_title": "第一单元 成长的节拍",
            "section_title": "中学时代",
            "page_range": "1-10",
            "page_start": 1,
            "page_end": 10,
            "content": "中学时代是人生发展的重要时期，伴随着身体的成长和心理的变化，我们要适应新的学习环境。",
            "content_summary": "中学时代是人生发展的关键期，需要适应新环境，建立新的人际关系。"
        },
        {
            "anchor_id": "ch2_p11",
            "chapter_title": "第一单元 成长的节拍",
            "section_title": "学习新天地",
            "page_range": "11-20",
            "page_start": 11,
            "page_end": 20,
            "content": "学习是中学生活的重要组成部分，我们要学会学习，掌握学习方法，培养良好的学习习惯。",
            "content_summary": "学习需要掌握科学的方法，包括自主学习、合作学习等。"
        },
        {
            "anchor_id": "ch3_p21",
            "chapter_title": "第一单元 成长的节拍",
            "section_title": "发现自己",
            "page_range": "21-30",
            "page_start": 21,
            "page_end": 30,
            "content": "认识自己是一种重要的能力，我们要通过多种途径了解自己，正确评价自己。",
            "content_summary": "认识自己的途径包括自我评价、他人评价等。"
        },
        {
            "anchor_id": "ch4_p31",
            "chapter_title": "第二单元 友谊的天空",
            "section_title": "和朋友在一起",
            "page_range": "31-40",
            "page_start": 31,
            "page_end": 40,
            "content": "友谊是人生中宝贵的财富，友谊的力量能够支持我们度过困难，获得成长。",
            "content_summary": "友谊是心灵的相遇，需要真诚、信任和包容。"
        },
        {
            "anchor_id": "ch5_p41",
            "chapter_title": "第二单元 友谊的天空",
            "section_title": "网络生活新空间",
            "page_range": "41-50",
            "page_start": 41,
            "page_end": 50,
            "content": "网络改变了我们的生活方式，我们要学会合理使用网络，遵守网络道德。",
            "content_summary": "网络交往需要谨慎，注意保护个人隐私。"
        },
        {
            "anchor_id": "ch6_p58",
            "chapter_title": "第三单元 师长情谊",
            "section_title": "师生之间",
            "page_range": "58-70",
            "page_start": 58,
            "page_end": 70,
            "content": "教师是我们成长的引路人，我们要尊重老师，建立良好的师生关系。",
            "content_summary": "良好的师生关系有助于学生的健康成长。"
        },
        {
            "anchor_id": "ch7_p71",
            "chapter_title": "第三单元 师长情谊",
            "section_title": "亲子之间",
            "page_range": "71-80",
            "page_start": 71,
            "page_end": 80,
            "content": "家庭是我们成长的港湾，亲情是世界上最珍贵的情感，我们要孝敬父母。",
            "content_summary": "理解父母、孝敬父母是中华民族的传统美德。"
        },
        {
            "anchor_id": "ch8_p81",
            "chapter_title": "第四单元 生命的思考",
            "section_title": "探问生命",
            "page_range": "81-90",
            "page_start": 81,
            "page_end": 90,
            "content": "生命是宝贵的，我们要珍爱生命，探索生命的意义，追求生命的价值。",
            "content_summary": "生命的意义在于创造和奉献，要活出生命的精彩。"
        },
        {
            "anchor_id": "ch9_p91",
            "chapter_title": "第四单元 生命的思考",
            "section_title": "珍视生命",
            "page_range": "91-100",
            "page_start": 91,
            "page_end": 100,
            "content": "我们要增强安全意识，掌握必要的安全技能，珍爱自己和他人的生命。",
            "content_summary": "增强安全意识，掌握基本的自救互救技能。"
        },
        {
            "anchor_id": "ch10_p101",
            "chapter_title": "第四单元 生命的思考",
            "section_title": "绽放生命",
            "page_range": "101-110",
            "page_start": 101,
            "page_end": 110,
            "content": "生命需要滋养，我们要用奋斗让生命绽放光彩，实现人生的价值。",
            "content_summary": "通过努力学习和实践，让生命更有意义。"
        }
    ]
    
    for ch in sample_chapters:
        cursor.execute('''
            INSERT OR REPLACE INTO textbook_anchors
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', [
            ch["anchor_id"],
            ch["chapter_title"],
            ch.get("section_title", ""),
            ch["page_range"],
            ch["page_start"],
            ch["page_end"],
            ch["content"],
            ch["content_summary"],
            json.dumps([0.0] * 768),
            json.dumps(ch)
        ])
    
    conn.commit()
    print(f"已插入 {len(sample_chapters)} 个章节")

def main():
    print("=" * 60)
    print("初始化课本数据库")
    print("=" * 60)
    
    db_path = "turso/textbook.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = init_database(db_path)
    insert_sample_data(conn)
    conn.close()
    
    print(f"\n完成! 数据库: {db_path}")

if __name__ == "__main__":
    main()
