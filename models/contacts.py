"""موديل العملاء والموردين (Contacts)"""
from database import fetch_all, fetch_one, execute


def list_contacts(type_=None):
    if type_:
        return fetch_all(
            "select * from contacts where type = %s or type = 'both' order by name",
            (type_,),
        )
    return fetch_all("select * from contacts order by name")


def get_contact(contact_id):
    return fetch_one("select * from contacts where id = %s", (contact_id,))


def create_contact(name, type_, phone=None, email=None, address=None,
                    tax_number=None, account_id=None, opening_balance=0):
    return fetch_one(
        """
        insert into contacts (name, type, phone, email, address, tax_number, account_id, opening_balance)
        values (%s, %s, %s, %s, %s, %s, %s, %s)
        returning id
        """,
        (name, type_, phone, email, address, tax_number, account_id, opening_balance),
    )


def update_contact(contact_id, **fields):
    if not fields:
        return 0
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [contact_id]
    return execute(f"update contacts set {set_clause} where id = %s", values)


def delete_contact(contact_id):
    return execute("delete from contacts where id = %s", (contact_id,))


def get_contact_statement(contact_id):
    """كشف حساب: كل الفواتير والمدفوعات الخاصة بالعميل/المورد"""
    invoices = fetch_all(
        "select * from invoices where contact_id = %s order by invoice_date",
        (contact_id,),
    )
    payments = fetch_all(
        "select * from payments where contact_id = %s order by payment_date",
        (contact_id,),
    )
    return {"invoices": invoices, "payments": payments}
