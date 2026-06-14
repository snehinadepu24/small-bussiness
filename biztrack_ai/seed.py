"""
BizTrack AI — MVP seed data
Populates Supabase with users, products, sales, expenses, and activity logs.

Run from terminal:
    python seed.py           # seed only if database is empty
    python seed.py --force   # clear everything and reseed
"""

import argparse
import random
from datetime import datetime, timedelta

import auth
import database

# ---------------------------------------------------------------------------
# Demo users (login with these after seeding)
# ---------------------------------------------------------------------------
USERS = [
    {"name": "Alex Rivera", "email": "owner@biztrack.ai", "password": "demo123", "role": "owner"},
    {"name": "Jordan Kim", "email": "staff@biztrack.ai", "password": "demo123", "role": "staff"},
    {"name": "Sam Patel", "email": "manager@biztrack.ai", "password": "demo123", "role": "staff"},
]

# ---------------------------------------------------------------------------
# Product catalog — curated for dashboard demos (low-stock items included)
# ---------------------------------------------------------------------------
PRODUCTS = [
    {"name": "Wireless Mouse Pro", "category": "Peripherals", "supplier": "TechSupply Co.", "cost_price": 14.00, "selling_price": 29.99, "quantity": 62, "reorder_level": 20},
    {"name": "Mechanical Keyboard RGB", "category": "Peripherals", "supplier": "TechWarehouse", "cost_price": 45.00, "selling_price": 89.99, "quantity": 28, "reorder_level": 15},
    {"name": "USB-C Hub 7-Port", "category": "Computer Accessories", "supplier": "Global Imports", "cost_price": 18.50, "selling_price": 39.99, "quantity": 4, "reorder_level": 12},
    {"name": "27\" Monitor Stand", "category": "Office Supplies", "supplier": "Prime Suppliers", "cost_price": 22.00, "selling_price": 49.99, "quantity": 35, "reorder_level": 10},
    {"name": "Webcam HD 1080p", "category": "Electronics", "supplier": "Direct Distribution", "cost_price": 28.00, "selling_price": 59.99, "quantity": 19, "reorder_level": 15},
    {"name": "Noise-Cancel Headphones", "category": "Audio/Video", "supplier": "Metro Wholesale", "cost_price": 55.00, "selling_price": 119.99, "quantity": 14, "reorder_level": 10},
    {"name": "Bluetooth Speaker Mini", "category": "Audio/Video", "supplier": "BestSource Inc.", "cost_price": 20.00, "selling_price": 44.99, "quantity": 41, "reorder_level": 15},
    {"name": "Laptop Sleeve 15\"", "category": "Computer Accessories", "supplier": "TechSupply Co.", "cost_price": 12.00, "selling_price": 24.99, "quantity": 55, "reorder_level": 20},
    {"name": "Desk Lamp LED", "category": "Office Supplies", "supplier": "Wholesale Plus", "cost_price": 16.00, "selling_price": 34.99, "quantity": 3, "reorder_level": 10},
    {"name": "Ergonomic Mouse Pad XL", "category": "Peripherals", "supplier": "Global Imports", "cost_price": 8.00, "selling_price": 18.99, "quantity": 78, "reorder_level": 25},
    {"name": "SSD 500GB NVMe", "category": "Storage", "supplier": "TechWarehouse", "cost_price": 38.00, "selling_price": 79.99, "quantity": 22, "reorder_level": 12},
    {"name": "Flash Drive 128GB", "category": "Storage", "supplier": "Prime Suppliers", "cost_price": 11.00, "selling_price": 22.99, "quantity": 6, "reorder_level": 15},
    {"name": "HDMI Cable 6ft", "category": "Networking", "supplier": "Direct Distribution", "cost_price": 5.50, "selling_price": 12.99, "quantity": 120, "reorder_level": 30},
    {"name": "Ethernet Cable Cat6", "category": "Networking", "supplier": "Metro Wholesale", "cost_price": 4.00, "selling_price": 9.99, "quantity": 95, "reorder_level": 25},
    {"name": "USB-C Charging Cable", "category": "Computer Accessories", "supplier": "BestSource Inc.", "cost_price": 6.00, "selling_price": 14.99, "quantity": 2, "reorder_level": 20},
    {"name": "Wireless Charger Pad", "category": "Electronics", "supplier": "TechSupply Co.", "cost_price": 15.00, "selling_price": 32.99, "quantity": 31, "reorder_level": 12},
    {"name": "Phone Stand Adjustable", "category": "Organization", "supplier": "Wholesale Plus", "cost_price": 7.00, "selling_price": 15.99, "quantity": 48, "reorder_level": 15},
    {"name": "Cable Organizer Box", "category": "Organization", "supplier": "Global Imports", "cost_price": 9.00, "selling_price": 19.99, "quantity": 37, "reorder_level": 12},
    {"name": "Gaming Mouse Pad XXL", "category": "Peripherals", "supplier": "TechWarehouse", "cost_price": 10.00, "selling_price": 21.99, "quantity": 44, "reorder_level": 15},
    {"name": "Wrist Rest Gel", "category": "Office Supplies", "supplier": "Prime Suppliers", "cost_price": 8.50, "selling_price": 17.99, "quantity": 5, "reorder_level": 12},
    {"name": "Webcam Ring Light", "category": "Electronics", "supplier": "Direct Distribution", "cost_price": 19.00, "selling_price": 42.99, "quantity": 16, "reorder_level": 10},
    {"name": "Label Maker Portable", "category": "Office Supplies", "supplier": "Metro Wholesale", "cost_price": 24.00, "selling_price": 54.99, "quantity": 11, "reorder_level": 8},
    {"name": "Sticky Notes Bulk Pack", "category": "Office Supplies", "supplier": "BestSource Inc.", "cost_price": 3.50, "selling_price": 8.99, "quantity": 200, "reorder_level": 50},
    {"name": "Whiteboard Markers Set", "category": "Office Supplies", "supplier": "TechSupply Co.", "cost_price": 4.00, "selling_price": 9.99, "quantity": 85, "reorder_level": 20},
    {"name": "Calculator Desktop", "category": "Office Supplies", "supplier": "Wholesale Plus", "cost_price": 12.00, "selling_price": 26.99, "quantity": 27, "reorder_level": 10},
    {"name": "Power Strip 6-Outlet", "category": "Electronics", "supplier": "Global Imports", "cost_price": 11.00, "selling_price": 24.99, "quantity": 1, "reorder_level": 15},
    {"name": "Extension Cord 10ft", "category": "Electronics", "supplier": "TechWarehouse", "cost_price": 9.00, "selling_price": 19.99, "quantity": 33, "reorder_level": 12},
    {"name": "Battery Pack 20000mAh", "category": "Electronics", "supplier": "Prime Suppliers", "cost_price": 22.00, "selling_price": 49.99, "quantity": 18, "reorder_level": 10},
    {"name": "Card Reader USB 3.0", "category": "Storage", "supplier": "Direct Distribution", "cost_price": 13.00, "selling_price": 27.99, "quantity": 24, "reorder_level": 10},
    {"name": "Memory Card 256GB", "category": "Storage", "supplier": "Metro Wholesale", "cost_price": 18.00, "selling_price": 39.99, "quantity": 7, "reorder_level": 15},
    {"name": "Router Stand Wall Mount", "category": "Networking", "supplier": "BestSource Inc.", "cost_price": 6.50, "selling_price": 14.99, "quantity": 29, "reorder_level": 10},
    {"name": "Headphone Stand Wood", "category": "Organization", "supplier": "TechSupply Co.", "cost_price": 14.00, "selling_price": 29.99, "quantity": 21, "reorder_level": 8},
    {"name": "Screen Cleaner Kit", "category": "Computer Accessories", "supplier": "Wholesale Plus", "cost_price": 5.00, "selling_price": 11.99, "quantity": 67, "reorder_level": 20},
    {"name": "Keyboard Cover Silicone", "category": "Computer Accessories", "supplier": "Global Imports", "cost_price": 7.50, "selling_price": 16.99, "quantity": 38, "reorder_level": 12},
    {"name": "Laptop Cooler Fan", "category": "Computer Accessories", "supplier": "TechWarehouse", "cost_price": 25.00, "selling_price": 54.99, "quantity": 13, "reorder_level": 8},
    {"name": "Controller Stand Dual", "category": "Peripherals", "supplier": "Prime Suppliers", "cost_price": 10.00, "selling_price": 22.99, "quantity": 26, "reorder_level": 10},
    {"name": "Desk Mat Leather", "category": "Office Supplies", "supplier": "Direct Distribution", "cost_price": 20.00, "selling_price": 44.99, "quantity": 15, "reorder_level": 8},
    {"name": "Monitor Light Bar", "category": "Electronics", "supplier": "Metro Wholesale", "cost_price": 30.00, "selling_price": 64.99, "quantity": 9, "reorder_level": 8},
    {"name": "Wire Clips Pack 50", "category": "Organization", "supplier": "BestSource Inc.", "cost_price": 3.00, "selling_price": 7.99, "quantity": 150, "reorder_level": 40},
    {"name": "Drawer Divider Set", "category": "Organization", "supplier": "TechSupply Co.", "cost_price": 8.00, "selling_price": 17.99, "quantity": 42, "reorder_level": 12},
]

EXPENSES = [
    ("Rent", "Monthly storefront lease", 2800.00, 75),
    ("Rent", "Warehouse storage unit", 950.00, 74),
    ("Utilities", "Electric bill — March", 342.18, 68),
    ("Utilities", "Internet & phone bundle", 189.00, 45),
    ("Utilities", "Water & sewer", 78.50, 60),
    ("Marketing", "Google Ads campaign", 450.00, 55),
    ("Marketing", "Instagram sponsored posts", 275.00, 40),
    ("Marketing", "Print flyers & signage", 180.00, 82),
    ("Marketing", "Email marketing platform", 49.99, 30),
    ("Salaries", "Part-time sales associate", 1200.00, 70),
    ("Salaries", "Weekend cashier wages", 680.00, 63),
    ("Salaries", "Inventory manager stipend", 900.00, 35),
    ("Transportation", "Delivery van fuel", 156.40, 50),
    ("Transportation", "Courier service — bulk order", 89.00, 25),
    ("Transportation", "Vehicle maintenance", 320.00, 88),
    ("Supplies", "Packaging materials restock", 245.00, 42),
    ("Supplies", "Cleaning supplies", 67.80, 20),
    ("Supplies", "Receipt paper rolls", 34.50, 15),
    ("Supplies", "Office stationery order", 112.00, 58),
    ("Equipment", "New POS terminal", 899.00, 90),
    ("Equipment", "Security camera upgrade", 425.00, 77),
    ("Equipment", "Label printer replacement", 189.00, 48),
    ("Insurance", "General liability premium", 520.00, 65),
    ("Insurance", "Property insurance quarterly", 380.00, 33),
    ("Taxes", "State sales tax remittance", 1847.00, 72),
    ("Taxes", "Quarterly estimated tax", 950.00, 31),
    ("Miscellaneous", "Emergency shelf repair", 145.00, 10),
    ("Miscellaneous", "Customer refund processing fee", 22.50, 5),
    ("Miscellaneous", "Breakroom supplies", 78.00, 18),
    ("Miscellaneous", "Software subscription — accounting", 29.99, 1),
    ("Rent", "April storefront lease", 2800.00, 32),
    ("Utilities", "Electric bill — April", 298.44, 28),
    ("Marketing", "Facebook local ads", 320.00, 22),
    ("Salaries", "April payroll — associates", 2400.00, 15),
    ("Transportation", "Supplier pickup mileage", 45.00, 12),
    ("Supplies", "Bubble wrap & boxes", 178.00, 8),
    ("Equipment", "Barcode scanner", 149.00, 38),
    ("Insurance", "Workers comp monthly", 210.00, 2),
    ("Taxes", "City business license renewal", 175.00, 45),
    ("Miscellaneous", "Team lunch — inventory count day", 95.00, 3),
    ("Utilities", "Electric bill — May", 315.20, 0),
    ("Marketing", "May promo mailers", 195.00, 1),
    ("Salaries", "May payroll — associates", 2400.00, 0),
    ("Supplies", "Shipping tape & labels", 56.00, 0),
    ("Transportation", "Same-day delivery fee", 42.00, 0),
]

ACTIVITY_LOGS = [
    ("Login", "User Alex Rivera logged in"),
    ("Login", "User Jordan Kim logged in"),
    ("Add Product", "Added Wireless Mouse Pro ($29.99)"),
    ("Add Product", "Added Mechanical Keyboard RGB ($89.99)"),
    ("Add Product", "Added USB-C Hub 7-Port ($39.99)"),
    ("Record Sale", "Sold 2x Wireless Mouse Pro ($59.98)"),
    ("Record Sale", "Sold 1x Webcam HD 1080p ($59.99)"),
    ("Record Sale", "Sold 3x HDMI Cable 6ft ($38.97)"),
    ("Add Expense", "Added $2800.00 for Rent"),
    ("Add Expense", "Added $450.00 for Marketing"),
    ("Update Product", "Updated Flash Drive 128GB stock levels"),
    ("Record Sale", "Sold 1x Noise-Cancel Headphones ($119.99)"),
    ("Record Sale", "Sold 2x Sticky Notes Bulk Pack ($17.98)"),
    ("Add Expense", "Added $342.18 for Utilities"),
    ("Delete Expense", "Deleted duplicate expense entry"),
    ("Record Sale", "Sold 1x SSD 500GB NVMe ($79.99)"),
    ("Add Product", "Added Monitor Light Bar ($64.99)"),
    ("Login", "User Sam Patel logged in"),
    ("Record Sale", "Sold 4x USB-C Charging Cable ($59.96)"),
    ("Add Expense", "Added $1200.00 for Salaries"),
    ("Update Product", "Updated Power Strip 6-Outlet reorder level"),
    ("Record Sale", "Sold 1x Gaming Mouse Pad XXL ($21.99)"),
    ("Record Sale", "Sold 2x Bluetooth Speaker Mini ($89.98)"),
    ("Add Expense", "Added $245.00 for Supplies"),
    ("Login", "User Alex Rivera logged in"),
]


def has_data():
    """Return True if any seedable data already exists."""
    response = database.db().table("products").select("*", count="exact").limit(1).execute()
    return bool(response.count and response.count > 0)


def clear_all_data():
    """Remove all rows from every table."""
    db = database.db()
    db.table("activity_logs").delete().gte("log_id", 0).execute()
    db.table("sales").delete().gte("sale_id", 0).execute()
    try:
        db.table("bill_items").delete().gte("item_id", 0).execute()
        db.table("bills").delete().gte("bill_id", 0).execute()
    except Exception:
        pass
    db.table("expenses").delete().gte("expense_id", 0).execute()
    db.table("products").delete().gte("product_id", 0).execute()
    db.table("users").delete().gte("id", 0).execute()
    return True, "All data cleared successfully!"


def _days_ago(days, hour=None, minute=0):
    dt = datetime.now().replace(second=0, microsecond=0) - timedelta(days=days)
    if hour is not None:
        dt = dt.replace(hour=hour % 24, minute=minute % 60)
    else:
        dt = dt.replace(hour=random.randint(9, 18), minute=random.randint(0, 59))
    return dt.isoformat()


def _seed_users():
    """Insert demo users; returns {email: id} map."""
    user_ids = {}
    for user in USERS:
        success, result = auth.signup(
            user["name"], user["email"], user["password"], user["role"]
        )
        if success:
            row = (
                database.db()
                .table("users")
                .select("id")
                .eq("email", user["email"])
                .execute()
            )
            user_ids[user["email"]] = row.data[0]["id"]
        else:
            row = (
                database.db()
                .table("users")
                .select("id")
                .eq("email", user["email"])
                .execute()
            )
            if row.data:
                user_ids[user["email"]] = row.data[0]["id"]
    return user_ids


def _seed_products():
    """Insert products; returns list of product dicts with product_id."""
    now = datetime.now().isoformat()
    rows = [{**p, "date_added": now} for p in PRODUCTS]
    response = database.db().table("products").insert(rows).execute()
    return response.data or []


def _seed_sales(products, user_ids):
    """Insert historical + recent sales; sync inventory quantities."""
    random.seed(42)
    owner_id = user_ids.get("owner@biztrack.ai")
    staff_id = user_ids.get("staff@biztrack.ai")

    popular = {p["name"] for p in products[:8]}
    stock = {p["product_id"]: p["quantity"] for p in products}
    sales_rows = []

    # ~160 random sales over 90 days
    for _ in range(160):
        product = random.choice(products)
        if product["name"] in popular:
            product = random.choice([p for p in products if p["name"] in popular] or products)

        qty = random.randint(1, 4)
        days = random.randint(0, 89)
        sale_date = _days_ago(days)
        total = round(qty * product["selling_price"], 2)

        sales_rows.append({
            "product_id": product["product_id"],
            "product_name": product["name"],
            "quantity_sold": qty,
            "unit_price": product["selling_price"],
            "total_amount": total,
            "sale_date": sale_date,
        })
        stock[product["product_id"]] = max(0, stock[product["product_id"]] - qty)

    # Guaranteed today's sales (dashboard KPIs)
    today_targets = products[:6]
    for i, product in enumerate(today_targets):
        qty = random.randint(1, 3)
        total = round(qty * product["selling_price"], 2)
        sales_rows.append({
            "product_id": product["product_id"],
            "product_name": product["name"],
            "quantity_sold": qty,
            "unit_price": product["selling_price"],
            "total_amount": total,
            "sale_date": _days_ago(0, hour=10 + i, minute=15 * i),
        })
        stock[product["product_id"]] = max(0, stock[product["product_id"]] - qty)

    # Batch insert in chunks (Supabase limit)
    db = database.db()
    chunk_size = 50
    for i in range(0, len(sales_rows), chunk_size):
        db.table("sales").insert(sales_rows[i:i + chunk_size]).execute()

    # Sync product stock after all sales
    for product_id, quantity in stock.items():
        db.table("products").update({"quantity": quantity}).eq("product_id", product_id).execute()

    return len(sales_rows), owner_id, staff_id


def _seed_expenses():
    """Insert expense records."""
    rows = [
        {
            "category": cat,
            "description": desc,
            "amount": amount,
            "expense_date": _days_ago(days),
        }
        for cat, desc, amount, days in EXPENSES
    ]
    db = database.db()
    chunk_size = 50
    for i in range(0, len(rows), chunk_size):
        db.table("expenses").insert(rows[i:i + chunk_size]).execute()
    return len(rows)


def _seed_activity_logs(user_ids):
    """Insert activity log entries."""
    owner_id = user_ids.get("owner@biztrack.ai", 1)
    staff_id = user_ids.get("staff@biztrack.ai", 2)
    assignees = [owner_id, staff_id, user_ids.get("manager@biztrack.ai", staff_id)]

    rows = []
    for i, (action, details) in enumerate(ACTIVITY_LOGS):
        rows.append({
            "user_id": assignees[i % len(assignees)],
            "action": action,
            "details": details,
            "timestamp": _days_ago(min(i * 2, 60), hour=9 + (i % 8)),
        })

    database.db().table("activity_logs").insert(rows).execute()
    return len(rows)


def seed_all(force=False):
    """
    Seed the full MVP dataset.
    Returns (success: bool, message: str).
    """
    if has_data():
        if not force:
            return False, "Database already has data. Run: python seed.py --force"
        clear_all_data()

    user_ids = _seed_users()
    products = _seed_products()
    sale_count, _, _ = _seed_sales(products, user_ids)
    expense_count = _seed_expenses()
    log_count = _seed_activity_logs(user_ids)

    low_stock = sum(1 for p in products if p["quantity"] < p["reorder_level"])

    return True, (
        f"MVP seed complete! "
        f"{len(USERS)} users, {len(products)} products ({low_stock} low-stock), "
        f"{sale_count} sales, {expense_count} expenses, {log_count} activity logs."
    )


def main():
    parser = argparse.ArgumentParser(description="Seed BizTrack AI MVP demo data")
    parser.add_argument(
        "--force", action="store_true",
        help="Clear existing data and reseed from scratch",
    )
    args = parser.parse_args()

    print("BizTrack AI — seeding MVP data...")
    success, message = seed_all(force=args.force)
    print(message)

    if success:
        print("\nDemo logins:")
        for u in USERS:
            print(f"  {u['role'].title():6}  {u['email']}  /  {u['password']}")
    else:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
