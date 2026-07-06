"""موديل دليل الحسابات (Chart of Accounts)"""
from database import fetch_all, fetch_one, execute


def list_accounts(only_active=True):
    query = "select * from accounts"
    if only_active:
        query += " where is_active = true"
    query += " order by code"
    return fetch_all(query)


def get_account(account_id):
    return fetch_one("select * from accounts where id = %s", (account_id,))


def create_account(code, name, type_, parent_id=None):
    return fetch_one(
        """
        insert into accounts (code, name, type, parent_id)
        values (%s, %s, %s, %s)
        returning id
        """,
        (code, name, type_, parent_id),
    )


def update_account(account_id, code, name, type_, parent_id=None):
    return execute(
        """
        update accounts set code=%s, name=%s, type=%s, parent_id=%s
        where id=%s
        """,
        (code, name, type_, parent_id, account_id),
    )


def deactivate_account(account_id):
    return execute("update accounts set is_active=false where id=%s", (account_id,))


def get_account_balances():
    """رصيد كل الحسابات - من الـ view اللي في schema.sql"""
    return fetch_all("select * from account_balances order by code")
