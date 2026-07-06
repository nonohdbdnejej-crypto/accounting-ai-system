"""
سكريبت لإنشاء حساب الإدمن الافتراضي
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.users import create_user
from database import fetch_one

def init_admin():
    """إنشاء حساب إدمن افتراضي"""
    username = "admin"
    password = "admin123"
    
    # التحقق من عدم وجود المستخدم بالفعل
    existing_user = fetch_one(
        "select id from users where username = %s",
        (username,)
    )
    
    if existing_user:
        print(f"المستخدم {username} موجود بالفعل")
        return
    
    try:
        # إنشاء المستخدم الإدمن
        result = create_user(
            username=username,
            password=password,
            full_name="المسؤول",
            email="admin@accounting.local",
            role="admin"
        )
        if result:
            print(f"✓ تم إنشاء حساب الإدمن بنجاح")
            print(f"  اسم المستخدم: {username}")
            print(f"  كلمة المرور: {password}")
            print(f"  الدور: admin")
        else:
            print("✗ فشل إنشاء حساب الإدمن")
    except Exception as e:
        print(f"✗ حدث خطأ: {str(e)}")

if __name__ == "__main__":
    init_admin()
