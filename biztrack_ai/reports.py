"""
Reports module for BizTrack AI
Handles generation and export of various reports
"""

import pandas as pd
import io
from database import db
import inventory
import sales
import expenses


def get_inventory_report():
    """Generate inventory report"""
    return inventory.get_all_products()


def get_sales_report(start_date=None, end_date=None):
    """Generate sales report"""
    if start_date and end_date:
        return sales.get_sales_by_date_range(start_date, end_date)
    return sales.get_all_sales()


def get_expense_report(start_date=None, end_date=None, category=None):
    """Generate expense report"""
    if start_date and end_date:
        return expenses.get_expenses_by_date_range(start_date, end_date)
    if category and category != "All":
        return expenses.get_expenses_by_category(category)
    return expenses.get_all_expenses()


def get_profit_report():
    """Generate profit & loss report"""
    sales_rows = db().table("sales").select("total_amount, product_id, quantity_sold").execute().data or []
    expense_rows = db().table("expenses").select("amount").execute().data or []
    product_rows = db().table("products").select("product_id, cost_price").execute().data or []

    total_revenue = sum(r["total_amount"] for r in sales_rows)
    total_expenses = sum(r["amount"] for r in expense_rows)

    cost_map = {r["product_id"]: r["cost_price"] for r in product_rows}
    cost_of_goods = sum(
        r["quantity_sold"] * cost_map.get(r["product_id"], 0) for r in sales_rows
    )

    gross_profit = total_revenue - cost_of_goods
    net_profit = gross_profit - total_expenses

    return {
        'total_revenue': total_revenue,
        'cost_of_goods': cost_of_goods,
        'gross_profit': gross_profit,
        'total_expenses': total_expenses,
        'net_profit': net_profit
    }


def get_monthly_profit_report():
    """Get monthly profit breakdown"""
    sales_rows = db().table("sales").select("sale_date, total_amount").execute().data or []
    expense_rows = db().table("expenses").select("expense_date, amount").execute().data or []

    sales_df = pd.DataFrame(sales_rows)
    expense_df = pd.DataFrame(expense_rows)

    if not sales_df.empty:
        sales_df["month"] = pd.to_datetime(sales_df["sale_date"]).dt.strftime("%Y-%m")
        monthly_sales = sales_df.groupby("month")["total_amount"].sum().reset_index().rename(columns={"total_amount": "Revenue"})
    else:
        monthly_sales = pd.DataFrame(columns=["month", "Revenue"])

    if not expense_df.empty:
        expense_df["month"] = pd.to_datetime(expense_df["expense_date"]).dt.strftime("%Y-%m")
        monthly_expenses = expense_df.groupby("month")["amount"].sum().reset_index().rename(columns={"amount": "Expenses"})
    else:
        monthly_expenses = pd.DataFrame(columns=["month", "Expenses"])

    merged = pd.merge(monthly_sales, monthly_expenses, on="month", how="outer").fillna(0)
    merged = merged.rename(columns={"month": "Month"})
    merged["Profit"] = merged["Revenue"] - merged["Expenses"]
    return merged.sort_values("Month", ascending=False).head(12)


def export_to_csv(df):
    """Convert DataFrame to CSV for download"""
    return df.to_csv(index=False).encode('utf-8')


def export_to_excel(df, sheet_name='Report'):
    """Convert DataFrame to Excel for download"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()


def get_comprehensive_report():
    """Generate comprehensive business report"""
    inventory_df = inventory.get_all_products()
    sales_df = sales.get_all_sales()
    expenses_df = expenses.get_all_expenses()
    profit_data = get_profit_report()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        summary_data = {
            'Metric': ['Total Revenue', 'Total Expenses', 'Net Profit',
                       'Total Products', 'Inventory Value', 'Low Stock Count'],
            'Value': [f"${profit_data['total_revenue']:,.2f}",
                      f"${profit_data['total_expenses']:,.2f}",
                      f"${profit_data['net_profit']:,.2f}",
                      len(inventory_df),
                      f"${inventory.get_inventory_stats()['inventory_value']:,.2f}",
                      len(inventory.get_low_stock_products())]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

        inventory_df.to_excel(writer, sheet_name='Inventory', index=False)
        sales_df.to_excel(writer, sheet_name='Sales', index=False)
        expenses_df.to_excel(writer, sheet_name='Expenses', index=False)

    return output.getvalue()
