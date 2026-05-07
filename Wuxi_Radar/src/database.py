import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "funding.db")

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT UNIQUE NOT NULL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            source TEXT,
            funding_date TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company_name, source, funding_date)
        )
    ''')
    
    conn.commit()
    conn.close()

def is_company_processed(company_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM processed_companies WHERE company_name = ?', (company_name,))
    result = cursor.fetchone()
    
    conn.close()
    return result is not None

def mark_company_processed(company_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO processed_companies (company_name) VALUES (?)', (company_name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    
    conn.close()

def is_news_processed(company_name, source, funding_date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM processed_news 
        WHERE company_name = ? AND source = ? AND funding_date = ?
    ''', (company_name, source, funding_date))
    result = cursor.fetchone()
    
    conn.close()
    return result is not None

def mark_news_processed(company_name, source, funding_date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO processed_news (company_name, source, funding_date) 
            VALUES (?, ?, ?)
        ''', (company_name, source, funding_date))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    
    conn.close()

def get_all_processed_companies():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT company_name FROM processed_companies')
    results = cursor.fetchall()
    
    conn.close()
    return [row[0] for row in results]

def cleanup_old_records(days=30):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('DELETE FROM processed_news WHERE processed_at < ?', (cutoff_str,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted > 0:
        print(f"清理了 {deleted} 条过期记录")

def get_unprocessed_news(news_list):
    unprocessed = []
    for news in news_list:
        company_name = news.get('company_name', '')
        source = news.get('source', 'unknown')
        funding_date = news.get('funding_date', '')
        
        if company_name and not is_news_processed(company_name, source, funding_date):
            unprocessed.append(news)
    
    print(f"原始 {len(news_list)} 条，未处理 {len(unprocessed)} 条")
    return unprocessed

if __name__ == "__main__":
    init_database()
    print("数据库初始化完成")
    cleanup_old_records()