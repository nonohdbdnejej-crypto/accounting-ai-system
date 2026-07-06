"""
موديل تسجيل العمليات (Audit Log)
بيسجل مين عمل إيه وامتى - مهم جداً في أي نظام محاسبي حقيقي
"""
import json
from flask import request
from database import execute, fetch_all


def log_action(user_id, action, entity_type, entity_id=None, details=None):
    """
    action: 'create' | 'update' | 'delete'
    entity_type: 'invoice' | 'journal_entry' | 'payment' | 'account' | 'contact' | ...
    details: dict هيتحول لـ JSON تلقائي
    """
    try:
        ip = request.remote_addr if request else None
    except RuntimeError:
        ip = None

    execute(
        """
        insert into audit_log (user_id, action, entity_type, entity_id, details, ip_address)
        values (%s, %s, %s, %s, %s, %s)
        """,
        (user_id, action, entity_type, entity_id, json.dumps(details or {}), ip),
    )


def get_audit_log(entity_type=None, entity_id=None, limit=100):
    query = """
        select al.*, u.email as user_email
        from audit_log al
        left join users u on u.id = al.user_id
    """
    params = []
    conditions = []
    if entity_type:
        conditions.append("al.entity_type = %s")
        params.append(entity_type)
    if entity_id:
        conditions.append("al.entity_id = %s")
        params.append(entity_id)
    if conditions:
        query += " where " + " and ".join(conditions)
    query += " order by al.created_at desc limit %s"
    params.append(limit)
    return fetch_all(query, params)
