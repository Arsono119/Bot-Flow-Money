import sqlite3
from datetime import datetime
from config import DB_NAME


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            amount INTEGER NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    conn.close()


def save_transaction(user_id, ttype, amount, category, note=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO transactions (user_id, type, amount, category, note) VALUES (?, ?, ?, ?, ?)",
        (user_id, ttype, amount, category, note)
    )
    conn.commit()
    conn.close()


def get_summary(user_id, period="all"):
    conn = get_connection()
    filter_sql = ""
    if period == "day":
        filter_sql = "AND created_at >= datetime('now', 'start of day')"
    elif period == "week":
        filter_sql = "AND created_at >= datetime('now', '-7 days')"
    elif period == "month":
        filter_sql = "AND created_at >= datetime('now', 'start of month')"

    query = f"""
        SELECT
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as total_income,
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as total_expense
        FROM transactions
        WHERE user_id = ? {filter_sql}
    """
    row = conn.execute(query, (user_id,)).fetchone()
    conn.close()

    return {
        "total_income": row["total_income"],
        "total_expense": row["total_expense"],
        "balance": row["total_income"] - row["total_expense"],
    }


def get_recent_transactions(user_id, limit=5):
    conn = get_connection()
    rows = conn.execute(
        "SELECT type, amount, category, note, created_at FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_category_summary(user_id, period="month"):
    conn = get_connection()
    filter_sql = "AND created_at >= datetime('now', 'start of month')"
    rows = conn.execute(
        f"""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE user_id = ? AND type = 'expense' {filter_sql}
        GROUP BY category
        ORDER BY total DESC
        """,
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
