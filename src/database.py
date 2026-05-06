import sqlite3
import os

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
    
    conn.commit()
    conn.close()

def is_processed(company_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM processed_companies WHERE company_name = ?', (company_name,))
    result = cursor.fetchone()
    
    conn.close()
    return result is not None

def mark_processed(company_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO processed_companies (company_name) VALUES (?)', (company_name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    
    conn.close()

def get_all_processed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT company_name FROM processed_companies')
    results = cursor.fetchall()
    
    conn.close()
    return [row[0] for row in results]

if __name__ == "__main__":
    init_database()
    print("数据库初始化完成")
    print("已处理公司:", get_all_processed())