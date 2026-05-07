"""
database.py  —  SQLite 去重与记录管理
"""

import sqlite3
import hashlib
from datetime import datetime, timedelta

DB_PATH = "funding.db"


def init_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS processed_news (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            company_key TEXT    NOT NULL UNIQUE,
            company_name TEXT,
            source      TEXT,
            funding_date TEXT,
            processed_at TEXT   NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _make_key(company_name: str, source: str = "", funding_date: str = "") -> str:
    """
    用 company_name + source 生成去重 key（忽略日期，避免同公司不同日期重复推送）。
    """
    raw = f"{company_name.strip()}::{source.strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


def is_processed(company_name: str, source: str = "") -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    key = _make_key(company_name, source)
    c.execute("SELECT 1 FROM processed_news WHERE company_key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result is not None


def get_unprocessed_news(funding_data: list) -> list:
    """过滤掉已处理过的公司，返回新增条目"""
    unprocessed = []
    for item in funding_data:
        name = item.get("company_name", "")
        source = item.get("source", "")
        if name and not is_processed(name, source):
            unprocessed.append(item)
    return unprocessed


def mark_news_processed(company_name: str, source: str = "", funding_date: str = ""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    key = _make_key(company_name, source)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT OR IGNORE INTO processed_news (company_key, company_name, source, funding_date, processed_at) VALUES (?,?,?,?,?)",
        (key, company_name, source, funding_date, now),
    )
    conn.commit()
    conn.close()


def cleanup_old_records(days: int = 30):
    """删除超过 N 天的记录，让老数据可以重新出现"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("DELETE FROM processed_news WHERE processed_at < ?", (cutoff,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    if deleted:
        print(f"  [DB] 清理 {deleted} 条过期记录")
