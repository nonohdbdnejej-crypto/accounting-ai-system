"""
مسارات المهام الدورية (Scheduled Tasks)
مصممة عشان تتنادى من Vercel Cron (أو أي scheduler) - مش من المستخدم مباشرة
محمية بـ secret token في الـ URL بدل تسجيل الدخول العادي
"""
import os
from flask import Blueprint, request, jsonify
from utils.notifications import send_overdue_notification

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")

CRON_SECRET = os.environ.get("CRON_SECRET")


@tasks_bp.route("/notify-overdue")
def notify_overdue():
    """
    مثال استدعاء: GET /tasks/notify-overdue?secret=xxxxx
    اضبط CRON_SECRET في متغيرات البيئة، وحطه في vercel.json كـ cron job يومي.
    """
    if not CRON_SECRET or request.args.get("secret") != CRON_SECRET:
        return jsonify({"error": "unauthorized"}), 403

    result = send_overdue_notification()
    return jsonify(result)
