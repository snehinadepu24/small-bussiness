"""
AI Business Insights module for BizTrack AI
Generates smart business insights from data analysis
"""

import pandas as pd
from datetime import datetime, timedelta
import inventory
import sales
import expenses
from utils import format_currency

def generate_insights():
    """Generate comprehensive business insights"""
    insights = []

    # Get all stats
    inventory_stats = inventory.get_inventory_stats()
    sales_stats = sales.get_sales_stats()
    expense_stats = expenses.get_expense_stats()

    # Top selling product insight
    top_products = sales.get_top_selling_products(limit=5)
    if not top_products.empty:
        best_seller = top_products.iloc[0]
        insights.append({
            'type': 'success',
            'icon': '🏆',
            'title': 'Best Selling Product',
            'insight': f'"{best_seller["Product"]}" is your top seller with {int(best_seller["Units Sold"])} units sold, generating {format_currency(best_seller["Revenue"])} in revenue.'
        })

    # Low stock warning
    low_stock = inventory.get_low_stock_products()
    if len(low_stock) > 0:
        insights.append({
            'type': 'warning',
            'icon': '⚠️',
            'title': 'Low Stock Alert',
            'insight': f'{len(low_stock)} products are below reorder level. Top priority: {low_stock.iloc[0]["Product"]} (Stock: {low_stock.iloc[0]["Stock"]}).'
        })

    # Revenue growth analysis
    monthly_sales = sales.get_monthly_sales_trend()
    if len(monthly_sales) >= 2:
        current = monthly_sales.iloc[0]['revenue']
        previous = monthly_sales.iloc[1]['revenue'] if len(monthly_sales) > 1 else current
        if previous > 0:
            growth = ((current - previous) / previous) * 100
            trend = 'increased' if growth > 0 else 'decreased'
            symbol = '📈' if growth > 0 else '📉'
            insights.append({
                'type': 'info',
                'icon': symbol,
                'title': 'Revenue Trend',
                'insight': f'Revenue {trend} by {abs(growth):.1f}% compared to last month. Current: {format_currency(current)}'
            })

    # Profit margin insight
    total_revenue = sales_stats['total_revenue']
    total_expenses = expense_stats['total_expenses']
    if total_revenue > 0:
        profit_margin = ((total_revenue - total_expenses) / total_revenue) * 100
        insights.append({
            'type': 'info' if profit_margin > 20 else 'warning',
            'icon': '💰',
            'title': 'Profit Margin',
            'insight': f'Your current profit margin is {profit_margin:.1f}%. {"This is healthy!" if profit_margin > 20 else "Consider reviewing expenses."}'
        })

    # Stockout risk
    import forecasting
    stockout_risk = forecasting.predict_stockout_risk()
    if len(stockout_risk) > 0:
        at_risk_product = stockout_risk.iloc[0]
        days_left = at_risk_product['days_until_empty']
        if days_left < 7:
            insights.append({
                'type': 'danger',
                'icon': '🚨',
                'title': 'Stockout Risk',
                'insight': f'"{at_risk_product["name"]}" may run out in {int(days_left)} days based on current sales velocity.'
            })

    # Expenses analysis
    monthly_expenses = expenses.get_monthly_expenses_trend()
    if len(monthly_expenses) >= 2:
        current_exp = monthly_expenses.iloc[0]['expenses']
        prev_exp = monthly_expenses.iloc[1]['expenses'] if len(monthly_expenses) > 1 else current_exp
        if prev_exp > 0 and current_exp > prev_exp * 1.2:
            diff = current_exp - prev_exp
            insights.append({
                'type': 'warning',
                'icon': '💡',
                'title': 'Expense Alert',
                'insight': f'Expenses increased by {format_currency(diff)} this month. Review your spending in top categories.'
            })

    # Top category performance
    inv_dist = inventory.get_inventory_distribution()
    if not inv_dist.empty:
        top_cat = inv_dist.iloc[0]
        insights.append({
            'type': 'info',
            'icon': '📊',
            'title': 'Category Leader',
            'insight': f'Your largest category is "{top_cat["category"]}" with {int(top_cat["quantity"])} units across {int(top_cat["products"])} products.'
        })

    return insights

def get_restock_recommendations_insight():
    """Get specific restock recommendations"""
    import forecasting
    recommendations = forecasting.get_restock_recommendations()

    urgent = recommendations[recommendations['restock_needed'] == True].copy()
    urgent['days_of_stock'] = pd.to_numeric(urgent['days_of_stock'], errors='coerce')
    urgent = urgent.sort_values('days_of_stock', na_position='last')

    output = []
    for _, row in urgent.head(5).iterrows():
        output.append({
            'product': row['name'],
            'current_stock': row['current_stock'],
            'recommended_order': row['recommended_order'],
            'est_cost': row['order_cost'],
            'urgency': 'High' if pd.notna(row['days_of_stock']) and row['days_of_stock'] < 3 else 'Medium'
        })

    return pd.DataFrame(output)

def get_performance_score():
    """Calculate overall business performance score"""
    score = 0
    details = []

    # Inventory health (0-25 points)
    inventory_stats = inventory.get_inventory_stats()
    low_stock_count = inventory_stats['low_stock_count']
    total_products = inventory_stats['total_products']

    if total_products > 0:
        stock_health_ratio = 1 - (low_stock_count / total_products)
        inventory_score = stock_health_ratio * 25
        score += inventory_score
        details.append(f'Inventory Health: {inventory_score:.0f}/25')

    # Sales performance (0-25 points)
    sales_stats = sales.get_sales_stats()
    monthly_revenue = sales_stats['monthly_revenue']

    if monthly_revenue > 500000:
        score += 25
    elif monthly_revenue > 200000:
        score += 20
    elif monthly_revenue > 50000:
        score += 15
    elif monthly_revenue > 0:
        score += 10
    details.append(f'Sales Performance: Based on {format_currency(monthly_revenue)} monthly revenue')

    # Profitability (0-30 points)
    expense_stats = expenses.get_expense_stats()
    profit = sales_stats['total_revenue'] - expense_stats['total_expenses']
    if sales_stats['total_revenue'] > 0:
        profit_margin = (profit / sales_stats['total_revenue']) * 100
        if profit_margin > 30:
            score += 30
        elif profit_margin > 20:
            score += 25
        elif profit_margin > 10:
            score += 20
        elif profit_margin > 0:
            score += 15
    details.append(f'Profitability: Profit margin drives this score')

    # Growth trend (0-20 points)
    monthly_sales = sales.get_monthly_sales_trend()
    if len(monthly_sales) >= 2:
        current = monthly_sales.iloc[0]['revenue']
        previous = monthly_sales.iloc[1]['revenue']
        if previous > 0:
            growth = ((current - previous) / previous) * 100
            if growth > 20:
                score += 20
            elif growth > 10:
                score += 15
            elif growth > 0:
                score += 10
            elif growth > -10:
                score += 5
    details.append(f'Growth Trend: Based on month-over-month comparison')

    return {
        'score': min(100, score),
        'details': details,
        'rating': 'Excellent' if score >= 80 else 'Good' if score >= 60 else 'Fair' if score >= 40 else 'Needs Improvement'
    }

def get_quick_stats():
    """Get quick statistics for dashboard cards"""
    inventory_stats = inventory.get_inventory_stats()
    sales_stats = sales.get_sales_stats()
    expense_stats = expenses.get_expense_stats()

    return {
        'total_products': inventory_stats['total_products'],
        'inventory_value': inventory_stats['inventory_value'],
        'today_sales': sales_stats['today_sales'],
        'monthly_revenue': sales_stats['monthly_revenue'],
        'total_expenses': expense_stats['total_expenses'],
        'net_profit': sales_stats['total_revenue'] - expense_stats['total_expenses']
    }
