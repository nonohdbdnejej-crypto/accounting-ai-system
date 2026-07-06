"""موديل المستخدمين والمصادقة (Auth)"""
from werkzeug.security import generate_password_hash, check_password_hash
from database import fetch_one, execute


def create_user(username, password, full_name=None, email=None, role="accountant"):
    password_hash = generate_password_hash(password)
    return fetch_one(
        """
        insert into users (username, password_hash, full_name, email, role)
        values (%s, %s, %s, %s, %s)
        returning id
        """,
        (username, password_hash, full_name, email, role),
    )


def verify_user(username, password):
    user = fetch_one("select * from users where username = %s and is_active = true", (username,))
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None


def get_user(user_id):
    return fetch_one("select id, username, email, full_name, role from users where id = %s", (user_id,))
