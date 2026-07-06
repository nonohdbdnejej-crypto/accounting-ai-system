"""
مسارات الأدمن (Admin) - عرض سجل العمليات + تحميل نسخة احتياطية
كل المسارات دي admin بس
"""
import json
from datetime import datetime
from flask import Blueprint, render_template, request, Response, jsonify
from flask_login import login_required
from utils.permissions import admin_only
import models.audit as audit_model
from database import fetch_all

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

BACKUP_TABLES = [
    "users", "accounts", "journal_entries", "journal_entry_lines",
    "contacts", "products", "invoices", "invoice_items", "payments", "audit_log",
]


@admin_bp.route("/audit-log")
@login_required
@admin_only
def audit_log():
    entity_type = request.args.get("entity_type") or None
    logs = audit_model.get_audit_log(entity_type=entity_type, limit=200)
    return render_template("admin_audit_log.html", logs=logs, current_type=entity_type)


@admin_bp.route("/backup/download")
@login_required
@admin_only
def download_backup():
    """
    نسخة احتياطية منطقية (JSON) لكل الجداول - بتتحمل مباشرة من المتصفح.
    ملحوظة: دي نسخة "منطقية" سريعة. للنسخ الكامل الاحترافي استخدم pg_dump
    (شوف scripts/backup.py) أو فعّل الـ Point-in-Time Recovery في Supabase.
    """
    backup_data = {}
    for table in BACKUP_TABLES:
        try:
            rows = fetch_all(f"select * from {table}")
            backup_data[table] = json.loads(json.dumps(rows, default=str))
        except Exception as e:
            backup_data[table] = {"error": str(e)}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    payload = json.dumps(backup_data, ensure_ascii=False, indent=2)

    return Response(
        payload,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=backup_{timestamp}.json"},
    )
