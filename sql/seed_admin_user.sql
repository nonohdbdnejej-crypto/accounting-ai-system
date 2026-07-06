-- ============================================
-- إنشاء مستخدم Admin افتراضي
-- يوزرنيم: admin | باسورد: admin123
-- نفّذه في Supabase SQL Editor بعد schema.sql
-- ============================================

insert into users (email, password_hash, full_name, role, is_active)
values (
    'admin',
    'scrypt:32768:8:1$W6mB5hAC8oK6QBi4$41eff9f2ae3b9bb34822004d2bfac41716b33009b55eabbf142f7829140dd8553824ec5ba446e116db8e900618686b405ed13d11fec579721332d853e8d7affb',
    'Admin',
    'admin',
    true
)
on conflict (email) do nothing;

-- ملحوظة أمان مهمة:
-- admin123 كلمة سر تجريبية للتشغيل الأول بس. لازم تغيّرها فورًا بعد أول دخول
-- (النظام دلوقتي مفيهوش صفحة "تغيير كلمة السر" من الواجهة - لو محتاجها قولّي أضيفها).
-- لحد ما تتضاف، تقدر تغيّرها بنفس الطريقة: تولّد hash جديد وتعمل update يدوي:
--
-- update users set password_hash = '<hash جديد>' where email = 'admin';
