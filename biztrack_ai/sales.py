"""
Sales Management module for BizTrack AI
Handles sales recording and revenue tracking
"""

import pandas as pd
from datetime import datetime, timedelta
from database import db, log_activity
from utils import normalize_date_range


def _sales_df(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.rename(columns={
        "sale_id": "Sale ID",
        "product_name": "Product",
        "quantity_sold": "Quantity",
        "unit_price": "Unit Price",
        "total_amount": "Total",
        "sale_date": "Date",
    })


def record_sale(product_id, product_name, quantity_sold, unit_price, user_id=None):
    """Record a new sale and update inventory"""
    response = (
        db()
        .table("products")
        .select("quantity")
        .eq("product_id", product_id)
        .execute()
    )
    if not response.data:
        return False, "Product not found!"

    current_stock = response.data[0]["quantity"]
    if current_stock < quantity_sold:
        return False, f"Insufficient inventory! Only {current_stock} units available."

    try:
        total_amount = quantity_sold * unit_price
        sale_date = datetime.now().isoformat()

        db().table("sales").insert({
            "product_id": product_id,
            "product_name": product_name,
            "quantity_sold": quantity_sold,
            "unit_price": unit_price,
            "total_amount": total_amount,
            "sale_date": sale_date,
        }).execute()

        db().table("products").update({
            "quantity": current_stock - quantity_sold,
        }).eq("product_id", product_id).execute()

        if user_id:
            log_activity(user_id, "Record Sale", f"Sold {quantity_sold}x {product_name} (${total_amount:.2f})")
        return True, f"Sale recorded! Total: ${total_amount:.2f}"
    except Exception as e:
        return False, str(e)


def get_all_sales():
    """Get all sales as DataFrame"""
    response = db().table("sales").select("*").order("sale_date", desc=True).execute()
    return _sales_df(response.data or [])


def get_sales_by_date_range(start_date, end_date):
    """Get sales filtered by date range"""
    start_iso, end_iso = normalize_date_range(start_date, end_date)
    response = (
        db()
        .table("sales")
        .select("*")
        .gte("sale_date", start_iso)
        .lte("sale_date", end_iso)
        .order("sale_date", desc=True)
        .execute()
    )
    return _sales_df(response.data or [])


def get_sales_stats():
    """Get sales statistics"""
    response = db().table("sales").select("total_amount, sale_date").execute()
    rows = response.data or []

    today = datetime.now().date()
    month_start = today.replace(day=1)

    today_sales = sum(
        r["total_amount"] for r in rows
        if r["sale_date"] and str(r["sale_date"])[:10] == str(today)
    )
    monthly_revenue = sum(
        r["total_amount"] for r in rows
        if r["sale_date"] and str(r["sale_date"])[:10] >= str(month_start)
    )
    total_sales = len(rows)
    total_revenue = sum(r["total_amount"] for r in rows)

    return {
        'today_sales': today_sales,
        'monthly_revenue': monthly_revenue,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
    }


def get_monthly_sales_trend():
    """Get monthly sales data for charts"""
    response = db().table("sales").select("sale_date, total_amount, quantity_sold").execute()
    df = pd.DataFrame(response.data or [])
    if df.empty:
        return df

    df["month"] = pd.to_datetime(df["sale_date"]).dt.strftime("%Y-%m")
    trend = (
        df.groupby("month")
        .agg(revenue=("total_amount", "sum"), transactions=("total_amount", "count"), units_sold=("quantity_sold", "sum"))
        .reset_index()
        .sort_values("month", ascending=False)
        .head(12)
    )
    return trend


def get_top_selling_products(limit=10):
    """Get top selling products"""
    response = db().table("sales").select("product_name, quantity_sold, total_amount").execute()
    df = pd.DataFrame(response.data or [])
    if df.empty:
        return df

    return (
        df.groupby("product_name")
        .agg(**{"Units Sold": ("quantity_sold", "sum"), "Revenue": ("total_amount", "sum")})
        .reset_index()
        .rename(columns={"product_name": "Product"})
        .sort_values("Revenue", ascending=False)
        .head(limit)
    )


def get_product_sales_history(product_id, days=30):
    """Get sales history for a specific product"""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    response = (
        db()
        .table("sales")
        .select("sale_date, quantity_sold, total_amount")
        .eq("product_id", product_id)
        .gte("sale_date", cutoff)
        .order("sale_date", desc=True)
        .execute()
    )
    return pd.DataFrame(response.data or [])


def delete_sale(sale_id, user_id=None):
    """Delete a sale record (admin only)"""
    response = (
        db()
        .table("sales")
        .select("product_id, quantity_sold, product_name")
        .eq("sale_id", sale_id)
        .execute()
    )
    if response.data:
        sale = response.data[0]
        product_id = sale["product_id"]
        quantity = sale["quantity_sold"]
        product_name = sale["product_name"]

        prod = (
            db()
            .table("products")
            .select("quantity")
            .eq("product_id", product_id)
            .execute()
        )
        if prod.data:
            new_qty = prod.data[0]["quantity"] + quantity
            db().table("products").update({"quantity": new_qty}).eq("product_id", product_id).execute()

        db().table("sales").delete().eq("sale_id", sale_id).execute()

        if user_id:
            log_activity(user_id, "Delete Sale", f"Deleted sale of {product_name}")

    return True, "Sale deleted and inventory restored!"


def get_recent_transactions(limit=10):
    """Get recent transactions for dashboard feed"""
    response = (
        db()
        .table("sales")
        .select("sale_date, product_name, quantity_sold, total_amount")
        .order("sale_date", desc=True)
        .limit(limit)
        .execute()
    )
    df = pd.DataFrame(response.data or [])
    if df.empty:
        return df
    return df.rename(columns={
        "sale_date": "Time",
        "product_name": "Product",
        "quantity_sold": "Qty",
        "total_amount": "Amount",
    })
