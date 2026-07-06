"""موديل المستخدمين والمصادقة (Auth)"""
from werkzeug.security import generate_password_hash, check_password_hash
from database import fetch_one, execute


def create_user(email, password, full_name=None, role="accountant"):
    password_hash = generate_password_hash(password)
    return fetch_one(
        """
        insert into users (email, password_hash, full_name, role)
        values (%s, %s, %s, %s)
        returning id
        """,
        (email, password_hash, full_name, role),
    )


def verify_user(email, password):
    user = fetch_one("select * from users where email = %s and is_active = true", (email,))
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None


def get_user(user_id):
    return fetch_one("select id, email, full_name, role from users where id = %s", (user_id,))
