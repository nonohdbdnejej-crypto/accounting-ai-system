"""
توليد ملف PDF للفاتورة (باستخدام reportlab)

دعم العربي:
- لو لقى خط عربي في static/fonts/Arabic-Regular.ttf، هيستخدمه ويشكّل النصوص
  العربية صح (RTL) باستخدام arabic_reshaper + python-bidi.
- لو مفيش خط، هيرجع تلقائياً لعرض إنجليزي بسيط (fallback آمن، مفيش كراش).
"""
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "fonts", "Arabic-Regular.ttf"
)

_ARABIC_FONT_AVAILABLE = False
if os.path.exists(FONT_PATH):
    try:
        pdfmetrics.registerFont(TTFont("Arabic", FONT_PATH))
        _ARABIC_FONT_AVAILABLE = True
    except Exception:
        _ARABIC_FONT_AVAILABLE = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _SHAPING_AVAILABLE = True
except ImportError:
    _SHAPING_AVAILABLE = False


def shape_arabic(text):
    """بيشكّل النص العربي عشان يتعرض صح (متصل و RTL) جوه الـ PDF"""
    if not text:
        return ""
    if _ARABIC_FONT_AVAILABLE and _SHAPING_AVAILABLE:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    return str(text)


LABELS_AR = {
    "sale_invoice": "فاتورة مبيعات",
    "purchase_invoice": "فاتورة مشتريات",
    "contact": "الجهة",
    "date": "التاريخ",
    "status": "الحالة",
    "description": "الوصف",
    "qty": "الكمية",
    "unit_price": "سعر الوحدة",
    "total": "الإجمالي",
    "subtotal": "الإجمالي الفرعي",
    "tax": "الضريبة",
    "grand_total": "الإجمالي الكلي",
    "notes": "ملاحظات",
}

LABELS_EN = {
    "sale_invoice": "Sales Invoice",
    "purchase_invoice": "Purchase Invoice",
    "contact": "Contact",
    "date": "Date",
    "status": "Status",
    "description": "Description",
    "qty": "Qty",
    "unit_price": "Unit Price",
    "total": "Total",
    "subtotal": "Subtotal",
    "tax": "Tax",
    "grand_total": "Grand Total",
    "notes": "Notes",
}


def generate_invoice_pdf(invoice):
    """
    invoice: dict فيه invoice_number, type, contact_name, invoice_date,
             subtotal, tax_total, total, items (list)
    بيرجع bytes جاهزة للتحميل
    """
    use_arabic = _ARABIC_FONT_AVAILABLE and _SHAPING_AVAILABLE
    labels = LABELS_AR if use_arabic else LABELS_EN
    font_name = "Arabic" if use_arabic else "Helvetica"
    font_bold = "Arabic" if use_arabic else "Helvetica-Bold"

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title", parent=styles["Heading1"], fontName=font_bold, fontSize=20, spaceAfter=6,
        alignment=2 if use_arabic else 0,  # 2 = right align
    )
    normal = ParagraphStyle("normal_ar", parent=styles["Normal"], fontName=font_name, alignment=2 if use_arabic else 0)

    elements = []

    invoice_type_label = shape_arabic(labels["sale_invoice"]) if invoice["type"] == "sale" else shape_arabic(labels["purchase_invoice"])
    elements.append(Paragraph(f"{invoice_type_label} #{invoice['invoice_number']}", title_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"{shape_arabic(labels['contact'])}: {shape_arabic(invoice.get('contact_name') or '-')}", normal))
    elements.append(Paragraph(f"{shape_arabic(labels['date'])}: {invoice['invoice_date']}", normal))
    elements.append(Paragraph(f"{shape_arabic(labels['status'])}: {invoice['status']}", normal))
    elements.append(Spacer(1, 16))

    header_row = [
        shape_arabic(labels["total"]), shape_arabic(labels["unit_price"]),
        shape_arabic(labels["qty"]), shape_arabic(labels["description"]),
    ] if use_arabic else [labels["description"], labels["qty"], labels["unit_price"], labels["total"]]

    table_data = [header_row]
    for item in invoice.get("items", []):
        desc = shape_arabic(item.get("description") or "-")
        qty = str(item["quantity"])
        price = f"{float(item['unit_price']):.2f}"
        total = f"{float(item['total']):.2f}"
        row = [total, price, qty, desc] if use_arabic else [desc, qty, price, total]
        table_data.append(row)

    subtotal_row = ["", "", shape_arabic(labels["subtotal"]), f"{float(invoice['subtotal']):.2f}"] if use_arabic \
        else ["", "", labels["subtotal"], f"{float(invoice['subtotal']):.2f}"]
    tax_row = ["", "", shape_arabic(labels["tax"]), f"{float(invoice['tax_total']):.2f}"] if use_arabic \
        else ["", "", labels["tax"], f"{float(invoice['tax_total']):.2f}"]
    total_row = ["", "", shape_arabic(labels["grand_total"]), f"{float(invoice['total']):.2f}"] if use_arabic \
        else ["", "", labels["grand_total"], f"{float(invoice['total']):.2f}"]

    table_data += [subtotal_row, tax_row, total_row]

    col_widths = [3 * cm, 3 * cm, 2.5 * cm, 7 * cm] if use_arabic else [7 * cm, 2.5 * cm, 3 * cm, 3 * cm]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0E4D46")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -4), 0.5, colors.HexColor("#D3DBD6")),
        ("LINEABOVE", (0, -3), (-1, -3), 1, colors.HexColor("#0E4D46")),
        ("FONTNAME", (0, -1), (-1, -1), font_bold),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
    ]))
    elements.append(table)

    if invoice.get("notes"):
        elements.append(Spacer(1, 16))
        elements.append(Paragraph(f"{shape_arabic(labels['notes'])}: {shape_arabic(invoice['notes'])}", normal))

    if not use_arabic:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            "<font size=8 color='#999999'>To show this invoice in Arabic, add a TTF font "
            "in static/fonts/ (see static/fonts/README.md)</font>",
            styles["Normal"],
        ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
