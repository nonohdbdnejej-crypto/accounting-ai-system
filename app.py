"""
تطبيق Flask الرئيسي - نظام محاسبة احترافي
"""
import logging
from flask import Flask, render_template
from flask_login import LoginManager
from werkzeug.exceptions import HTTPException
from config import Config
from extensions import csrf, limiter

from routes.auth import auth_bp, User
from routes.main import main_bp
from routes.accounts_routes import accounts_bp
from routes.journal_routes import journal_bp
from routes.contacts_routes import contacts_bp
from routes.products_routes import products_bp
from routes.invoices_routes import invoices_bp
from routes.payments_routes import payments_bp
from routes.reports_routes import reports_bp
from routes.admin_routes import admin_bp
from routes.tasks_routes import tasks_bp

from models.users import get_user


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    logging.basicConfig(level=logging.INFO)

    # ---------- CSRF Protection ----------
    # csrf مُعرّف في extensions.py عشان ملفات الـ routes تقدر تستورده
    # وتعمل @csrf.exempt على مسارات الـ API الفردية بس (JSON endpoints)
    # بدل إعفاء الـ blueprint كله (اللي كان بيلغي CSRF حتى عن فورمات HTML العادية)
    csrf.init_app(app)

    # ---------- Rate Limiting (يحمي صفحة تسجيل الدخول من محاولات كسر كلمة السر) ----------
    limiter.init_app(app)

    # ---------- Flask-Login ----------
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "لازم تسجل دخول الأول"
    login_manager.login_message_category = "error"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        row = get_user(user_id)
        if not row:
            return None
        return User(row)

    # ---------- تسجيل الـ Blueprints ----------
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(journal_bp)
    app.register_blueprint(contacts_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tasks_bp)

    # ---------- Security Headers ----------
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:;"
        )
        if Config.SESSION_COOKIE_SECURE:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response

    # ---------- Rate limit على تسجيل الدخول (5 محاولات كل دقيقة) ----------
    limiter.limit("5 per minute")(auth_bp)

    # ---------- إعفاء REST API endpoints (JSON) من CSRF ----------
    # ملحوظة أمان مهمة: كان في السابق csrf.exempt(invoices_bp) و csrf.exempt(payments_bp)
    # وده كان بيلغي حماية CSRF عن الـ blueprint كله - يعني حتى فورمات HTML العادية
    # زي "إنشاء فاتورة" و"تسجيل مصروف" بقت من غير حماية! ده ثغرة حقيقية.
    # الصح: نعفي مسارات الـ API (JSON) بس، كل واحد لوحده، جوه ملفه
    # (شوف @csrf.exempt فوق api_list/api_get/api_create في routes/invoices_routes.py
    # و routes/payments_routes.py). مسار /tasks/notify-overdue بروتوكوله GET بس
    # أصلًا فمش محتاج إعفاء (CSRFProtect بيحمي POST/PUT/PATCH/DELETE بس بشكل افتراضي).

    # ---------- معالجة الأخطاء ----------
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="مالكش صلاحية تدخل الصفحة دي"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="الصفحة اللي بتدور عليها مش موجودة"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Server error")
        return render_template("error.html", code=500, message="حصل خطأ في السيرفر، جرب تاني بعد شوية"), 500

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        if isinstance(e, HTTPException):
            return e
        app.logger.exception("Unhandled exception")
        return render_template("error.html", code=500, message="حصل خطأ غير متوقع، جرب تاني بعد شوية"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
