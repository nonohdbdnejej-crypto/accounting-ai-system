#!/usr/bin/env python3
"""
سكريبت نسخ احتياطي لقاعدة البيانات (Backup)

طريقتين للاستخدام:
1) نسخة كاملة (pg_dump) - محتاج تثبيت postgresql-client محلياً
2) نسخة منطقية (JSON export) - بتشتغل من غير أي أدوات إضافية، كويسة كـ backup سريع/يومي

الاستخدام:
    python scripts/backup.py --mode dump      # ينشئ ملف .sql بالكامل
    python scripts/backup.py --mode json       # ينشئ ملف .json بكل الجداول
"""
import os
import sys
import json
import argparse
import subprocess
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")

TABLES = [
    "users", "accounts", "journal_entries", "journal_entry_lines",
    "contacts", "products", "invoices", "invoice_items", "payments", "audit_log",
]


def backup_via_pg_dump():
    """نسخة كاملة باستخدام pg_dump (لازم يكون مثبت على جهازك)"""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("خطأ: لازم تضبط DATABASE_URL في .env")
        sys.exit(1)

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.sql")

    try:
        subprocess.run(
            ["pg_dump", database_url, "-f", output_file, "--no-owner", "--no-privileges"],
            check=True,
        )
        print(f"✅ تم إنشاء النسخة الاحتياطية: {output_file}")
    except FileNotFoundError:
        print("❌ pg_dump مش متثبت. ثبّته بـ: sudo apt install postgresql-client")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ فشل النسخ الاحتياطي: {e}")
        sys.exit(1)


def backup_via_json():
    """نسخة منطقية: بتصدّر كل جدول كـ JSON - مفيدة كـ backup سريع بدون أدوات خارجية"""
    from database import fetch_all

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.json")

    backup_data = {}
    for table in TABLES:
        try:
            rows = fetch_all(f"select * from {table}")
            # تحويل أي قيم مش قابلة للتسلسل (زي datetime) لنص
            backup_data[table] = json.loads(json.dumps(rows, default=str))
            print(f"  ✓ {table}: {len(rows)} صف")
        except Exception as e:
            print(f"  ⚠️ فشل نسخ جدول {table}: {e}")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

    print(f"✅ تم إنشاء النسخة الاحتياطية: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="نسخ احتياطي لقاعدة بيانات النظام المحاسبي")
    parser.add_argument("--mode", choices=["dump", "json"], default="json")
    args = parser.parse_args()

    if args.mode == "dump":
        backup_via_pg_dump()
    else:
        backup_via_json()
