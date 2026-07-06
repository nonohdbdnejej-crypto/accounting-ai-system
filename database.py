"""
الاتصال بقاعدة بيانات Supabase (PostgreSQL)
بيستخدم psycopg2 مباشرة عشان نقدر نكتب SQL معقد لتقارير المحاسبة
"""
import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

DATABASE_URL = os.environ.get("DATABASE_URL")
# مثال الشكل ده لازم ياخده من Supabase > Project Settings > Database > Connection string (URI)
# postgresql://postgres:[PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("لازم تضبط متغير البيئة DATABASE_URL في ملف .env")
    return psycopg2.connect(DATABASE_URL, sslmode="require")


@contextmanager
def get_cursor(commit=False):
    """
    استخدام:
        with get_cursor() as cur:
            cur.execute("select * from accounts")
            rows = cur.fetchall()
    """
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(query, params=None):
    with get_cursor() as cur:
        cur.execute(query, params or ())
        return cur.fetchall()


def fetch_one(query, params=None):
    with get_cursor() as cur:
        cur.execute(query, params or ())
        return cur.fetchone()


def execute(query, params=None, commit=True):
    with get_cursor(commit=commit) as cur:
        cur.execute(query, params or ())
        return cur.rowcount
