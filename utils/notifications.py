"""
إرسال إشعار إيميل بالفواتير المتأخرة (Overdue Invoices)
مصمم عشان ينفَّذ دورياً (يومي) عن طريق Vercel Cron أو أي scheduler تاني
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import fetch_all

SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
NOTIFY_EMAIL_TO = os.environ.get("NOTIFY_EMAIL_TO")


def get_overdue_invoices():
    return fetch_all(
        """
        select i.*, c.name as contact_name
        from invoices i
        left join contacts c on c.id = i.contact_id
        where i.due_date is not null
          and i.due_date < current_date
          and i.status not in ('paid', 'cancelled')
        order by i.due_date
        """
    )


def build_email_body(invoices):
    if not invoices:
        return None
    lines = ["الفواتير المتأخرة عن السداد:", ""]
    for inv in invoices:
        lines.append(
            f"- فاتورة #{inv['invoice_number']} | {inv['contact_name'] or '-'} | "
            f"المبلغ: {float(inv['total']):.2f} | تاريخ الاستحقاق: {inv['due_date']}"
        )
    return "\n".join(lines)


def send_overdue_notification():
    """
    بيرجع dict فيه النتيجة: {"sent": bool, "count": int, "reason": str}
    """
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS, NOTIFY_EMAIL_TO]):
        return {"sent": False, "count": 0, "reason": "SMTP غير مضبوط (شوف .env.example)"}

    invoices = get_overdue_invoices()
    if not invoices:
        return {"sent": False, "count": 0, "reason": "لا توجد فواتير متأخرة"}

    body = build_email_body(invoices)

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = NOTIFY_EMAIL_TO
    msg["Subject"] = f"⚠️ {len(invoices)} فاتورة متأخرة عن السداد"
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return {"sent": True, "count": len(invoices), "reason": "تم الإرسال بنجاح"}
    except Exception as e:
        return {"sent": False, "count": len(invoices), "reason": str(e)}
