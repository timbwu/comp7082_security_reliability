"""SQLite persistence. Contains deliberate reliability/security problems."""

import sqlite3
from models import Product


class StoreRepository:
    def __init__(self, db_path="shop.db"):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path, timeout=2)

    def get_product(self, sku):
        conn = self.connect()
        try:
            row = conn.execute(
                "SELECT sku, name, price, stock FROM products WHERE sku = ?", (sku,)
            ).fetchone()
            return Product(*row) if row else None
        finally:
            conn.close()

    def get_saved_cart(self, user_id):
        conn = self.connect()
        try:
            rows = conn.execute(
                "SELECT sku, quantity FROM saved_cart WHERE user_id = ?", (user_id,)
            ).fetchall()
            return rows
        finally:
            conn.close()

    def save_cart(self, user_id, lines):
        conn = self.connect()
        try:
            conn.execute("DELETE FROM saved_cart WHERE user_id = ?", (user_id,))
            for line in lines:
                conn.execute(
                    "INSERT INTO saved_cart VALUES (?, ?, ?)",
                    (user_id, line.sku, line.quantity),
                )
            conn.commit()
        finally:
            conn.close()

    def update_stock(self, sku, quantity):
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            return False

        conn = self.connect()
        try:
            cursor = conn.execute(
                "UPDATE products SET stock = stock - ? WHERE sku = ? AND stock >= ?",
                (quantity, sku, quantity),
            )
            conn.commit()
            return cursor.rowcount == 1
        finally:
            conn.close()

    def save_order(self, user_id, amount, status, request_id):
        conn = self.connect()
        try:
            cur = conn.execute(
                "INSERT INTO orders(user_id, amount, status, request_id) VALUES (?, ?, ?, ?)",
                (user_id, amount, status, request_id),
            )
            conn.commit()
            order_id = cur.lastrowid

            return order_id
        finally:
            conn.close()

    def list_orders(self, user_id):
        conn = self.connect()
        try:
            rows = conn.execute(
                "SELECT id, user_id, amount, status FROM orders ORDER BY id DESC"
            ).fetchall()
            return rows
        finally:
            conn.close()

    def get_order_by_request_id(self, request_id):
        conn = self.connect()
        try:
            return conn.execute(
                "SELECT id, status, amount FROM orders WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        finally:
            conn.close()
