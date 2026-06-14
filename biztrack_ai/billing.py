"""
Billing module for Vyapar
Multi-item invoices with inventory sync and sales line tracking
"""

import pandas as pd
from datetime import datetime

from database import db, log_activity
from utils import normalize_date_range

PAYMENT_METHODS = ["Cash", "Card", "UPI", "Bank Transfer", "Other"]


def _bills_df(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    rename = {
        "bill_id": "Bill ID",
        "bill_number": "Bill No.",
        "customer_name": "Customer",
        "subtotal": "Subtotal",
        "discount": "Discount",
        "tax_rate": "Tax %",
        "tax_amount": "Tax",
        "total_amount": "Total",
        "payment_method": "Payment",
        "notes": "Notes",
        "bill_date": "Date",
    }
    if "item_count" in df.columns:
        rename["item_count"] = "Items"
    return df.rename(columns={k: v for k, v in rename.items() if k in df.columns})


def _bill_items_df(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.rename(columns={
        "product_name": "Product",
        "quantity": "Qty",
        "unit_price": "Unit Price",
        "line_total": "Line Total",
    })


def _generate_bill_number():
    """Generate unique bill number: INV-YYYYMMDD-NNN"""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"INV-{today}-"
    response = (
        db()
        .table("bills")
        .select("bill_number")
        .like("bill_number", f"{prefix}%")
        .order("bill_id", desc=True)
        .limit(1)
        .execute()
    )
    seq = 1
    if response.data:
        last = response.data[0]["bill_number"]
        try:
            seq = int(last.split("-")[-1]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:03d}"


def _get_product_stock(product_id):
    response = (
        db()
        .table("products")
        .select("quantity, name, selling_price")
        .eq("product_id", product_id)
        .execute()
    )
    if not response.data:
        return None
    row = response.data[0]
    return row["quantity"], row["name"], row["selling_price"]


def _validate_cart(items):
    """Validate cart lines and stock. Returns (ok, message)."""
    if not items:
        return False, "Add at least one item to the bill."

    merged = {}
    for item in items:
        pid = int(item["product_id"])
        qty = int(item["quantity"])
        if qty <= 0:
            return False, "Quantity must be at least 1 for each item."
        merged[pid] = merged.get(pid, 0) + qty

    for product_id, total_qty in merged.items():
        stock_info = _get_product_stock(product_id)
        if stock_info is None:
            return False, f"Product ID {product_id} not found."
        stock, name, _ = stock_info
        if stock < total_qty:
            return False, f"Insufficient stock for {name}. Available: {stock}, requested: {total_qty}."

    return True, ""


def create_bill(items, customer_name="", payment_method="Cash", notes="",
                tax_rate=0.0, discount=0.0, user_id=None):
    """
    Create a multi-item bill.
    items: list of dicts with product_id, product_name, quantity, unit_price
    Returns (success, bill_id_or_message)
    """
    ok, msg = _validate_cart(items)
    if not ok:
        return False, msg

    if payment_method not in PAYMENT_METHODS:
        payment_method = "Cash"

    tax_rate = max(0.0, float(tax_rate or 0))
    discount = max(0.0, float(discount or 0))

    normalized_items = []
    for item in items:
        qty = int(item["quantity"])
        unit_price = round(float(item["unit_price"]), 2)
        normalized_items.append({
            "product_id": int(item["product_id"]),
            "product_name": item["product_name"],
            "quantity": qty,
            "unit_price": unit_price,
            "line_total": round(qty * unit_price, 2),
        })

    subtotal = round(sum(i["line_total"] for i in normalized_items), 2)
    discount = min(discount, subtotal)
    taxable = subtotal - discount
    tax_amount = round(taxable * (tax_rate / 100.0), 2)
    total_amount = round(taxable + tax_amount, 2)

    bill_number = _generate_bill_number()
    bill_date = datetime.now().isoformat()

    try:
        bill_resp = db().table("bills").insert({
            "bill_number": bill_number,
            "customer_name": customer_name.strip() or "Walk-in Customer",
            "subtotal": subtotal,
            "discount": discount,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "payment_method": payment_method,
            "notes": notes.strip(),
            "user_id": user_id,
            "bill_date": bill_date,
        }).execute()

        bill_id = bill_resp.data[0]["bill_id"]

        for item in normalized_items:
            db().table("bill_items").insert({
                "bill_id": bill_id,
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "line_total": item["line_total"],
            }).execute()

            db().table("sales").insert({
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "quantity_sold": item["quantity"],
                "unit_price": item["unit_price"],
                "total_amount": item["line_total"],
                "sale_date": bill_date,
                "bill_id": bill_id,
            }).execute()

            stock_info = _get_product_stock(item["product_id"])
            new_qty = stock_info[0] - item["quantity"]
            db().table("products").update({
                "quantity": new_qty,
            }).eq("product_id", item["product_id"]).execute()

        if user_id:
            log_activity(
                user_id,
                "Create Bill",
                f"{bill_number} — ${total_amount:.2f} ({len(normalized_items)} items)",
            )

        return True, bill_id
    except Exception as e:
        err = str(e).lower()
        if "bills" in err and ("does not exist" in err or "relation" in err):
            return False, (
                "Billing tables not found. Run the billing SQL in supabase_schema.sql "
                "inside your Supabase SQL Editor, then try again."
            )
        return False, str(e)


def get_all_bills():
    """Get all bills with item counts."""
    bills_resp = db().table("bills").select("*").order("bill_date", desc=True).execute()
    bills = bills_resp.data or []
    if not bills:
        return _bills_df([])

    items_resp = db().table("bill_items").select("bill_id").execute()
    counts = {}
    for row in items_resp.data or []:
        bid = row["bill_id"]
        counts[bid] = counts.get(bid, 0) + 1

    for bill in bills:
        bill["item_count"] = counts.get(bill["bill_id"], 0)

    return _bills_df(bills)


def get_bills_by_date_range(start_date, end_date):
    """Get bills filtered by date range."""
    start_iso, end_iso = normalize_date_range(start_date, end_date)
    response = (
        db()
        .table("bills")
        .select("*")
        .gte("bill_date", start_iso)
        .lte("bill_date", end_iso)
        .order("bill_date", desc=True)
        .execute()
    )
    bills = response.data or []
    if not bills:
        return _bills_df([])

    items_resp = db().table("bill_items").select("bill_id").execute()
    counts = {}
    for row in items_resp.data or []:
        bid = row["bill_id"]
        counts[bid] = counts.get(bid, 0) + 1

    for bill in bills:
        bill["item_count"] = counts.get(bill["bill_id"], 0)

    return _bills_df(bills)


def get_bill_items(bill_id):
    """Get line items for a bill."""
    response = (
        db()
        .table("bill_items")
        .select("*")
        .eq("bill_id", bill_id)
        .execute()
    )
    return _bill_items_df(response.data or [])


def get_bill_detail(bill_id):
    """Get bill header dict and items DataFrame."""
    response = (
        db()
        .table("bills")
        .select("*")
        .eq("bill_id", bill_id)
        .execute()
    )
    if not response.data:
        return None, pd.DataFrame()
    return response.data[0], get_bill_items(bill_id)


def delete_bill(bill_id, user_id=None):
    """Delete bill, restore inventory, remove linked sales rows."""
    bill, items_df = get_bill_detail(bill_id)
    if not bill:
        return False, "Bill not found."

    items_resp = (
        db()
        .table("bill_items")
        .select("product_id, quantity")
        .eq("bill_id", bill_id)
        .execute()
    )

    for row in items_resp.data or []:
        prod = (
            db()
            .table("products")
            .select("quantity")
            .eq("product_id", row["product_id"])
            .execute()
        )
        if prod.data:
            restored = prod.data[0]["quantity"] + row["quantity"]
            db().table("products").update({"quantity": restored}).eq(
                "product_id", row["product_id"]
            ).execute()

    db().table("sales").delete().eq("bill_id", bill_id).execute()
    db().table("bill_items").delete().eq("bill_id", bill_id).execute()
    db().table("bills").delete().eq("bill_id", bill_id).execute()

    if user_id:
        log_activity(user_id, "Delete Bill", f"Deleted {bill['bill_number']}")

    return True, f"Bill {bill['bill_number']} deleted and stock restored."


def get_payment_methods():
    return PAYMENT_METHODS
