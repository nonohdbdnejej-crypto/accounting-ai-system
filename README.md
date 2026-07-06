# نظام محاسبة احترافي - دفتر الأستاذ

نظام محاسبة بقيد مزدوج (Double-Entry Bookkeeping) مبني بـ Flask + Supabase (PostgreSQL)، جاهز للنشر على Vercel.

## المميزات
- دليل حسابات كامل (أصول / التزامات / حقوق ملكية / إيرادات / مصروفات)
- قيود يومية يدوية بقيد مزدوج مع تحقق تلقائي من التوازن (مدين = دائن)
- فواتير بيع وشراء بتولّد قيدها المحاسبي تلقائياً
- مصروفات عامة (إيجار، رواتب...) بقيد تلقائي
- مقبوضات ومدفوعات (تحصيل من عملاء / سداد لموردين)
- عملاء وموردين + كشف حساب
- منتجات ومخزون مع تنبيه نفاد الكمية
- تقارير: ميزان المراجعة، قائمة الدخل، الميزانية العمومية + رسوم بيانية
- تصدير فاتورة PDF (بدعم عربي لو حطيت خط - شوف تحت)
- صلاحيات (admin / accountant / viewer) + CSRF protection + rate limiting
- Audit Log كامل (مين عمل إيه وامتى) + صفحة لعرضه
- نسخ احتياطي (JSON فوري من لوحة التحكم، أو pg_dump من `scripts/backup.py`)
- تنبيه إيميل تلقائي بالفواتير المتأخرة (عبر Vercel Cron)
- اختبارات (pytest) لأهم منطق محاسبي: توازن القيد، حساب الفواتير، الصلاحيات
- REST API (JSON) للفواتير والمصروفات

## 1) إعداد قاعدة البيانات (Supabase)

1. ادخل على مشروعك في [supabase.com](https://supabase.com)
2. من القائمة الجانبية: **SQL Editor** → New query
3. نفّذ الملفات بالترتيب ده (RUN لكل واحد لوحده):
   - `sql/schema.sql`
   - `sql/seed_accounts.sql`
   - `sql/audit_log.sql`
4. من **Project Settings > Database > Connection string** انسخ الـ URI (Session pooler أفضل للـ serverless)

## 2) التشغيل محلياً

```bash
cd accounting-system
python -m venv venv
source venv/bin/activate   # على ويندوز: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# افتح .env واملأ DATABASE_URL و SECRET_KEY (والباقي اختياري)

python app.py
```
هيفتح على `http://localhost:5000`

## 3) إنشاء أول مستخدم (Admin)

```bash
python -c "
from app import app
from models.users import create_user
with app.app_context():
    create_user('you@example.com', 'YourPassword123', full_name='Admin', role='admin')
    print('تم إنشاء المستخدم')
"
```

الأدوار المتاحة: `admin` (كل شيء) / `accountant` (إضافة وتعديل) / `viewer` (عرض فقط).

## 4) تشغيل الاختبارات

```bash
pip install pytest
pytest
```

الاختبارات بتغطي أهم منطق محاسبي (توازن القيد المزدوج، حساب إجماليات الفاتورة،
التحقق من صحة البيانات، الصلاحيات) - مفيهاش اتصال فعلي بقاعدة البيانات عشان تشتغل بسرعة.

## 5) النسخ الاحتياطي (Backups)

**الطريقة السريعة:** ادخل كـ admin على `/admin/audit-log` واضغط "تحميل نسخة احتياطية (JSON)".

**من الطرفية:**
```bash
python scripts/backup.py --mode json    # نسخة JSON (مفيش أدوات إضافية مطلوبة)
python scripts/backup.py --mode dump    # نسخة SQL كاملة (لازم postgresql-client)
```

**للحماية الكاملة:** فعّل Point-in-Time Recovery من Supabase Dashboard
(Project Settings > Database > Backups) - ده أهم من أي backup يدوي.

## 6) خط عربي لتصدير PDF (اختياري)

الفواتير بتتصدّر إنجليزي افتراضياً. عشان تطلع بالعربي:
1. حمّل خط زي [Amiri](https://fonts.google.com/specimen/Amiri) أو [Cairo](https://fonts.google.com/specimen/Cairo)
2. حطه في `static/fonts/Arabic-Regular.ttf`
3. النظام هيكتشفه تلقائي في المرة الجاية

## 7) تنبيهات الفواتير المتأخرة (اختياري)

1. اضبط `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`, `NOTIFY_EMAIL_TO`, `CRON_SECRET` في `.env`
2. في `vercel.json`، غيّر `REPLACE_WITH_YOUR_CRON_SECRET` لنفس قيمة `CRON_SECRET`
3. Vercel هينده على `/tasks/notify-overdue` يومياً الساعة 8 صباحاً تلقائي
4. لو عايز تجربه يدوي: `https://your-app.vercel.app/tasks/notify-overdue?secret=xxxxx`

> ملحوظة: Vercel Cron محتاج خطة Pro للتشغيل اليومي الدقيق - على الخطة المجانية
> ممكن يشتغل أقل تكراراً. البديل: استخدم GitHub Actions scheduled workflow ينده على نفس الرابط.

## 8) النشر على Vercel

```bash
npm install -g vercel   # لو مش متثبت
vercel login
vercel
```

بعد أول نشر، اضبط متغيرات البيئة من Vercel Dashboard:
**Project Settings > Environment Variables** — كل المتغيرات اللي في `.env.example`

بعدها:
```bash
vercel --prod
```

## هيكل المشروع

```
accounting-system/
├── api/index.py          # نقطة دخول Vercel
├── app.py                 # تطبيق Flask (factory)
├── config.py
├── database.py             # الاتصال بـ Supabase
├── vercel.json
├── requirements.txt
├── models/                 # منطق العمل (business logic)
│   ├── accounts.py
│   ├── journal.py          # ← قلب نظام القيد المزدوج
│   ├── contacts.py
│   ├── products.py
│   ├── invoices.py          # ← بيربط الفاتورة بقيد تلقائي
│   ├── payments.py
│   └── users.py
├── routes/                  # الـ Blueprints (Views + API)
│   ├── auth.py
│   ├── main.py
│   ├── accounts_routes.py
│   ├── journal_routes.py
│   ├── contacts_routes.py
│   ├── products_routes.py
│   ├── invoices_routes.py   # فيه REST API جاهز
│   ├── payments_routes.py   # فيه REST API + المصروفات
│   └── reports_routes.py
├── templates/                # HTML (Jinja2)
├── static/css/style.css       # الهوية البصرية
├── static/js/app.js            # المنطق الديناميكي (فواتير + قيود)
└── sql/
    ├── schema.sql
    └── seed_accounts.sql
```

## ملاحظة مهمة عن القيد المزدوج

كل عملية مالية بتتسجل مرتين: مرة مدين ومرة دائن، وبنفس القيمة بالظبط. ده بيضمن إن دفتر الأستاذ متوازن دايماً. النظام بيرفض حفظ أي قيد مش متوازن (شوف `models/journal.py` - `UnbalancedEntryError`).

## أكواد الحسابات الافتراضية المستخدمة في القيود التلقائية

| الكود | الحساب |
|------|--------|
| 1100 | النقدية بالخزينة |
| 1200 | البنك |
| 1300 | العملاء |
| 1400 | المخزون |
| 2100 | الموردون |
| 2200 | ضرائب مستحقة |
| 4100 | إيرادات المبيعات |
| 5100 | تكلفة البضاعة المباعة |

لو غيّرت الأكواد دي في `seed_accounts.sql`، لازم تحدّث `DEFAULT_ACCOUNT_CODES` في `models/invoices.py` و `models/payments.py`.
