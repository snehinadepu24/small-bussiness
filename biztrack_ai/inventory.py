"""
Inventory Management module for BizTrack AI
Handles CRUD operations for products
"""

import pandas as pd
from database import db, log_activity


def _product_tuple(row):
    """Convert product dict to tuple matching SELECT * column order."""
    return (
        row["product_id"],
        row["name"],
        row["category"],
        row.get("supplier"),
        row["cost_price"],
        row["selling_price"],
        row["quantity"],
        row["reorder_level"],
        row.get("date_added"),
    )


def add_product(name, category, supplier, cost_price, selling_price, quantity, reorder_level, user_id=None):
    """Add a new product to inventory"""
    try:
        response = db().table("products").insert({
            "name": name,
            "category": category,
            "supplier": supplier,
            "cost_price": cost_price,
            "selling_price": selling_price,
            "quantity": quantity,
            "reorder_level": reorder_level,
        }).execute()
        product_id = response.data[0]["product_id"]
        if user_id:
            log_activity(user_id, "Add Product", f"Added {name} (${selling_price})")
        return True, product_id
    except Exception as e:
        return False, str(e)


def update_product(product_id, name, category, supplier, cost_price, selling_price, quantity, reorder_level, user_id=None):
    """Update an existing product"""
    try:
        db().table("products").update({
            "name": name,
            "category": category,
            "supplier": supplier,
            "cost_price": cost_price,
            "selling_price": selling_price,
            "quantity": quantity,
            "reorder_level": reorder_level,
        }).eq("product_id", product_id).execute()
        if user_id:
            log_activity(user_id, "Update Product", f"Updated {name}")
        return True, "Product updated successfully!"
    except Exception as e:
        return False, str(e)


def delete_product(product_id, user_id=None):
    """Delete a product"""
    response = (
        db()
        .table("products")
        .select("name")
        .eq("product_id", product_id)
        .execute()
    )
    product_name = response.data[0]["name"] if response.data else "Unknown"

    db().table("products").delete().eq("product_id", product_id).execute()

    if user_id:
        log_activity(user_id, "Delete Product", f"Deleted {product_name}")
    return True, "Product deleted successfully!"


def get_all_products():
    """Get all products as a DataFrame"""
    response = (
        db()
        .table("products")
        .select("*")
        .order("product_id", desc=True)
        .execute()
    )
    df = pd.DataFrame(response.data or [])
    if df.empty:
        return df
    return df.rename(columns={
        "product_id": "ID",
        "name": "Name",
        "category": "Category",
        "supplier": "Supplier",
        "cost_price": "Cost Price",
        "selling_price": "Selling Price",
        "quantity": "Quantity",
        "reorder_level": "Reorder Level",
        "date_added": "Date Added",
    })


def get_product_by_id(product_id):
    """Get a single product by ID"""
    response = (
        db()
        .table("products")
        .select("*")
        .eq("product_id", product_id)
        .execute()
    )
    if not response.data:
        return None
    return _product_tuple(response.data[0])


def get_low_stock_products():
    """Get products below reorder level"""
    response = db().table("products").select("*").execute()
    rows = [r for r in (response.data or []) if r["quantity"] < r["reorder_level"]]
    rows.sort(key=lambda r: r["quantity"])
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.rename(columns={
        "product_id": "ID",
        "name": "Product",
        "category": "Category",
        "quantity": "Stock",
        "reorder_level": "Reorder Level",
    })[["ID", "Product", "Category", "Stock", "Reorder Level"]]


def search_products(search_term="", category="All"):
    """Search products by name and filter by category"""
    query = db().table("products").select("*")

    if search_term:
        query = query.ilike("name", f"%{search_term}%")
    if category != "All":
        query = query.eq("category", category)

    response = query.order("product_id", desc=True).execute()
    df = pd.DataFrame(response.data or [])
    if df.empty:
        return df
    return df.rename(columns={
        "product_id": "ID",
        "name": "Name",
        "category": "Category",
        "supplier": "Supplier",
        "cost_price": "Cost Price",
        "selling_price": "Selling Price",
        "quantity": "Quantity",
        "reorder_level": "Reorder Level",
        "date_added": "Date Added",
    })


def get_categories():
    """Get all unique categories"""
    response = db().table("products").select("category").execute()
    categories = sorted({r["category"] for r in (response.data or [])})
    return categories


def get_inventory_stats():
    """Get inventory statistics"""
    response = db().table("products").select("cost_price, selling_price, quantity, reorder_level").execute()
    rows = response.data or []

    total_products = len(rows)
    inventory_value = sum(r["cost_price"] * r["quantity"] for r in rows)
    retail_value = sum(r["selling_price"] * r["quantity"] for r in rows)
    low_stock_count = sum(1 for r in rows if r["quantity"] < r["reorder_level"])
    total_quantity = sum(r["quantity"] for r in rows)

    return {
        'total_products': total_products,
        'inventory_value': inventory_value,
        'retail_value': retail_value,
        'low_stock_count': low_stock_count,
        'total_quantity': total_quantity,
    }


def get_inventory_distribution():
    """Get inventory distribution by category"""
    response = db().table("products").select("category, quantity").execute()
    df = pd.DataFrame(response.data or [])
    if df.empty:
        return df
    return (
        df.groupby("category")
        .agg(quantity=("quantity", "sum"), products=("quantity", "count"))
        .reset_index()
        .sort_values("quantity", ascending=False)
    )
