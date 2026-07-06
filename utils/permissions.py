"""
أدوات الصلاحيات (Role-Based Access Control)
3 أدوار: admin (كل شيء) - accountant (تعديل بيانات) - viewer (عرض فقط)
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def roles_required(*allowed_roles):
    """
    ديكوريتور بيمنع أي حد صلاحيته مش ضمن allowed_roles.
    استخدام: @roles_required('admin', 'accountant')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.role not in allowed_roles:
                flash("مالكش صلاحية تعمل العملية دي - اتكلم مع الأدمن", "error")
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator


# اختصارات جاهزة للاستخدام المتكرر
def can_edit(view_func):
    """أي حد غير viewer يقدر يعدّل"""
    return roles_required("admin", "accountant")(view_func)


def admin_only(view_func):
    """الأدمن بس"""
    return roles_required("admin")(view_func)
