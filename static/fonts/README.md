# خط عربي للـ PDF

عشان الفواتير تتصدّر بالعربي صح (RTL) في ملف الـ PDF، لازم تحط خط .ttf يدعم العربي هنا.

## الخطوات
1. حمّل خط مجاني بيدعم العربي، مثلاً:
   - Amiri: https://fonts.google.com/specimen/Amiri
   - Noto Naskh Arabic: https://fonts.google.com/noto/specimen/Noto+Naskh+Arabic
   - Cairo: https://fonts.google.com/specimen/Cairo

2. حط ملف الـ `.ttf` في المجلد ده باسم:
   ```
   static/fonts/Arabic-Regular.ttf
   ```

3. النظام هيكتشفه تلقائي ويستخدمه في تصدير PDF. لو الملف مش موجود،
   الفاتورة هتتصدّر بالإنجليزي بس (fallback تلقائي - مفيش كراش).

## ليه محتاجين الخطوة دي يدوي؟
خطوط الـ TTF ملفات ثنائية كبيرة نسبياً ومحمية بحقوق نشر مختلفة حسب الخط،
فمش مناسب نحطها جاهزة جوه الكود مباشرة. تحميلها يدوي من Google Fonts بياخد دقيقتين بس.
