from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
from datetime import datetime
from pathlib import Path

DB_FILE = "pos.db"

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if Path(DB_FILE).exists():
        return
    conn = get_db()
    cur = conn.cursor()

    # ตารางเมนู
    cur.execute(
        """
        CREATE TABLE menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        );
        """
    )

    # ตารางออเดอร์
    cur.execute(
        """
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_number TEXT NOT NULL,
            created_at TEXT NOT NULL,
            payment_status TEXT NOT NULL DEFAULT 'unpaid'
        );
        """
    )

    # รายการในออเดอร์
    cur.execute(
        """
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        );
        """
    )

    # เมนูก๋วยเตี๋ยวเรือ ป.ประทีป (ตัวอย่าง)
    menu_items = [
        ("ก๋วยเตี๋ยวเรือน้ำตกหมู เส้นเล็ก", 45),
        ("ก๋วยเตี๋ยวเรือน้ำตกหมู เส้นหมี่", 45),
        ("ก๋วยเตี๋ยวเรือน้ำตกหมู เส้นใหญ่", 45),
        ("ก๋วยเตี๋ยวเรือน้ำตกเนื้อ เส้นเล็ก", 50),
        ("ก๋วยเตี๋ยวเรือน้ำตกเนื้อ เส้นหมี่", 50),
        ("ก๋วยเตี๋ยวเรือน้ำตกเนื้อ เส้นใหญ่", 50),
        ("ก๋วยเตี๋ยวเรือหมู แห้ง", 45),
        ("ก๋วยเตี๋ยวเรือเนื้อ แห้ง", 50),
        ("เกาเหลาหมู", 55),
        ("เกาเหลาหมู พิเศษ", 65),
        ("เกาเหลาหมูต้มยำ", 60),
        ("เพิ่มเส้น", 10),
        ("เพิ่มหมู/เนื้อ", 15),
        ("กากหมูเจียว", 10),
    ]
    cur.executemany(
        "INSERT INTO menu_items(name, price) VALUES (?, ?);", menu_items
    )

    conn.commit()
    conn.close()
    print("Initialized DB with sample data.")


def print_kitchen_ticket(order_id):
    """
    ฟังก์ชันตัวอย่างสำหรับพิมพ์บิลในครัว
    ตอนนี้ยังพิมพ์แค่ใน console
    ถ้าจะต่อเครื่องปริ้นจริง ให้แทนที่ส่วนนี้ด้วยโค้ด ESC/POS
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id = ?;", (order_id,))
    order = cur.fetchone()
    cur.execute("SELECT * FROM order_items WHERE order_id = ?;", (order_id,))
    items = cur.fetchall()
    conn.close()

    print("====== KITCHEN ORDER ======")
    print(f"โต๊ะ: {order['table_number']}")
    print(f"เวลา: {order['created_at']}")
    print("---------------------------")
    total = 0
    for it in items:
        line_total = it["price"] * it["quantity"]
        total += line_total
        print(f"{it['item_name']} x {it['quantity']} = {line_total:.2f}")
    print("---------------------------")
    print(f"รวม: {total:.2f} บาท")
    print("====== END ======\n")


@app.route("/")
def home():
    return "Boat Noodle POS (ป.ประทีป) is running."


@app.route("/order")
def order_page():
    table = request.args.get("table", "ไม่ระบุ")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, price FROM menu_items;")
    menu_items = cur.fetchall()
    conn.close()
    return render_template(
        "order.html",
        table_number=table,
        menu_items=menu_items,
    )


@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.json
    table_number = data.get("table_number")
    items = data.get("items", [])

    if not table_number or not items:
        return jsonify({"error": "ข้อมูลไม่ครบ"}), 400

    conn = get_db()
    cur = conn.cursor()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        "INSERT INTO orders(table_number, created_at) VALUES (?, ?);",
        (table_number, created_at),
    )
    order_id = cur.lastrowid

    # บันทึกรายการ
    for item in items:
        item_name = item.get("name")
        quantity = int(item.get("quantity", 0))
        price = float(item.get("price", 0))
        if quantity <= 0:
            continue
        cur.execute(
            """
            INSERT INTO order_items(order_id, item_name, quantity, price)
            VALUES (?, ?, ?, ?);
            """,
            (order_id, item_name, quantity, price),
        )

    conn.commit()
    conn.close()

    # พิมพ์บิลครัว (ตอนนี้พิมพ์ใน console)
    print_kitchen_ticket(order_id)

    # ส่งลูกค้าไปหน้า "ชำระเงิน"
    return jsonify({"message": "รับออเดอร์แล้ว", "order_id": order_id})


@app.route("/pay/<int:order_id>")
def pay_page(order_id):
    """หน้าเลือกวิธีชำระเงิน (จำลอง)"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id = ?;", (order_id,))
    order = cur.fetchone()
    cur.execute("SELECT * FROM order_items WHERE order_id = ?;", (order_id,))
    items = cur.fetchall()
    conn.close()

    if not order:
        return "ไม่พบออเดอร์", 404

    total = sum(it["price"] * it["quantity"] for it in items)
    return render_template(
        "pay.html",
        order=order,
        items=items,
        total=total,
    )


@app.route("/pay/<int:order_id>/confirm", methods=["POST"])
def pay_confirm(order_id):
    """ทำเครื่องหมายว่าออเดอร์นี้จ่ายเงินแล้ว (ไม่ผูกเกตเวย์จริง)"""
    method = request.form.get("method", "cash")
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE orders SET payment_status = ? WHERE id = ?;",
        (f"paid_{method}", order_id),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("pay_success", order_id=order_id))


@app.route("/pay/<int:order_id>/success")
def pay_success(order_id):
    return render_template("pay_success.html", order_id=order_id)


@app.route("/admin/orders")
def admin_orders():
    """หน้าดูออเดอร์ทั้งหมดแบบง่าย ๆ"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT o.id, o.table_number, o.created_at, o.payment_status,
               SUM(oi.quantity * oi.price) AS total
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        GROUP BY o.id
        ORDER BY o.id DESC;
        """
    )
    orders = cur.fetchall()
    conn.close()
    return render_template("admin_orders.html", orders=orders)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
