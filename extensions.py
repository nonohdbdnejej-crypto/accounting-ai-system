"""
Extensions مشتركة بين app.py وملفات الـ routes.
بنعملها هنا (مش جوه app.py) عشان أي route file يقدر يعمل import لـ csrf
من غير ما يحصل circular import مع app.py.
"""
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

csrf = CSRFProtect()
limiter = Limiter(get_remote_address, default_limits=[])
