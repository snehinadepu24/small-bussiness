"""
Expense Tracking module for BizTrack AI
Handles expense management and tracking
"""

import pandas as pd
from datetime import datetime, timedelta
from database import db, log_activity
from utils import normalize_date_range

EXPENSE_CATEGORIES = [
    'Rent',
    'Utilities',
    'Marketing',
    'Salaries',
    'Transportation',
    'Supplies',
    'Equipment',
    'Insurance',
    'Taxes',
    'Miscellaneous'
]


def _expenses_df(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.rename(columns={
        "expense_id": "ID",
        "category": "Category",
        "description": "Description",
        "amount": "Amount",
        "expense_date": "Date",
    })


def add_expense(category, description, amount, user_id=None):
    """Add a new expense"""
    try:
        db().table("expenses").insert({
            "category": category,
            "description": description,
            "amount": amount,
            "expense_date": datetime.now().isoformat(),
        }).execute()

        if user_id:
            log_activity(user_id, "Add Expense", f"Added ${amount:.2f} for {category}")
        return True, "Expense added successfully!"
    except Exception as e:
        return False, str(e)


def get_all_expenses():
    """Get all expenses as DataFrame"""
    response = db().table("expenses").select("*").order("expense_date", desc=True).execute()
    return _expenses_df(response.data or [])


def get_expenses_by_date_range(start_date, end_date):
    """Get expenses filtered by date range"""
    start_iso, end_iso = normalize_date_range(start_date, end_date)
    response = (
        db()
        .table("expenses")
        .select("*")
        .gte("expense_date", start_iso)
        .lte("expense_date", end_iso)
        .order("expense_date", desc=True)
        .execute()
    )
    return _expenses_df(response.data or [])


def get_expenses_by_category(category):
    """Get expenses filtered by category"""
    response = (
        db()
        .table("expenses")
        .select("*")
        .eq("category", category)
        .order("expense_date", desc=True)
        .execute()
    )
    return _expenses_df(response.data or [])


def delete_expense(expense_id, user_id=None):
    """Delete an expense"""
    if user_id:
        log_activity(user_id, "Delete Expense", "Deleted expense")

    db().table("expenses").delete().eq("expense_id", expense_id).execute()
    return True, "Expense deleted successfully!"


def get_expense_stats():
    """Get expense statistics"""
    response = db().table("expenses").select("amount, expense_date").execute()
    rows = response.data or []

    today = datetime.now().date()
    month_start = today.replace(day=1)

    total_expenses = sum(r["amount"] for r in rows)
    monthly_expenses = sum(
        r["amount"] for r in rows
        if r["expense_date"] and str(r["expense_date"])[:10] >= str(month_start)
    )
    today_expenses = sum(
        r["amount"] for r in rows
        if r["expense_date"] and str(r["expense_date"])[:10] == str(today)
    )

    return {
        'total_expenses': total_expenses,
        'monthly_expenses': monthly_expenses,
        'today_expenses': today_expenses,
    }


def get_expenses_by_category_summary():
    """Get expenses grouped by category"""
    response = db().table("expenses").select("category, amount").execute()
    df = pd.DataFrame(response.data or [])
    if df.empty:
        return df

    return (
        df.groupby("category")
        .agg(**{
            "Transactions": ("amount", "count"),
            "Total Amount": ("amount", "sum"),
            "Average": ("amount", "mean"),
        })
        .reset_index()
        .rename(columns={"category": "Category"})
        .sort_values("Total Amount", ascending=False)
    )


def get_monthly_expenses_trend():
    """Get monthly expenses data for charts"""
    response = db().table("expenses").select("expense_date, amount").execute()
    df = pd.DataFrame(response.data or [])
    if df.empty:
        return df

    df["month"] = pd.to_datetime(df["expense_date"]).dt.strftime("%Y-%m")
    return (
        df.groupby("month")
        .agg(expenses=("amount", "sum"), transactions=("amount", "count"))
        .reset_index()
        .sort_values("month", ascending=False)
        .head(12)
    )


def get_expense_categories():
    """Get all expense categories"""
    return EXPENSE_CATEGORIES
