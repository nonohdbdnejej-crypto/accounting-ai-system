"""
نقطة الدخول لـ Vercel (Serverless Function)
Vercel بينادي على الملف ده، وهو بيستورد التطبيق من app.py في الروت
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel's Python runtime يتعرف على المتغير ده تلقائي
