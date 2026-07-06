"""موديل المنتجات والمخزون (Products / Inventory)"""
from database import fetch_all, fetch_one, execute


def list_products(only_active=True):
    query = "select * from products"
    if only_active:
        query += " where is_active = true"
    query += " order by name"
    return fetch_all(query)


def get_product(product_id):
    return fetch_one("select * from products where id = %s", (product_id,))


def create_product(name, sku=None, unit="قطعة", cost_price=0, sale_price=0,
                    quantity=0, reorder_level=0):
    return fetch_one(
        """
        insert into products (name, sku, unit, cost_price, sale_price, quantity, reorder_level)
        values (%s, %s, %s, %s, %s, %s, %s)
        returning id
        """,
        (name, sku, unit, cost_price, sale_price, quantity, reorder_level),
    )


def update_product(product_id, **fields):
    if not fields:
        return 0
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [product_id]
    return execute(f"update products set {set_clause} where id = %s", values)


def adjust_stock(product_id, delta_quantity):
    """زيادة أو نقصان الكمية (delta موجب = زيادة، سالب = نقصان)"""
    return execute(
        "update products set quantity = quantity + %s where id = %s",
        (delta_quantity, product_id),
    )


def get_low_stock_products():
    return fetch_all(
        "select * from products where quantity <= reorder_level and is_active = true"
    )
