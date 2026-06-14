"""
Forecasting module for Vyapar
Provides basic demand forecasting and restock recommendations
"""

import pandas as pd
from datetime import datetime, timedelta

from database import db, execute_with_retry


def _query(fn):
    """Run a Supabase query with retry on transient network failures."""
    return execute_with_retry(fn)


def _load_sales_history(days=365):
    """Load all sales rows since cutoff in a single query."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    response = _query(
        lambda: db()
        .table("sales")
        .select("product_id, sale_date, quantity_sold")
        .gte("sale_date", cutoff)
        .execute()
    )
    df = pd.DataFrame(response.data or [])
    if not df.empty:
        df["sale_date"] = pd.to_datetime(df["sale_date"])
    return df


def _daily_demand(sales_df, product_id):
    """Daily quantity sold for one product from a preloaded sales frame."""
    if sales_df.empty:
        return pd.Series(dtype=float)
    subset = sales_df[sales_df["product_id"] == product_id]
    if subset.empty:
        return pd.Series(dtype=float)
    return subset.groupby(subset["sale_date"].dt.date)["quantity_sold"].sum()


def get_product_demand_history(product_id, days=60, sales_df=None):
    """Get daily sales history for a product."""
    if sales_df is None:
        sales_df = _load_sales_history(days=max(days, 60))

    if sales_df.empty:
        return pd.DataFrame(columns=["date", "quantity"])

    cutoff_date = (datetime.now() - timedelta(days=days)).date()
    daily = _daily_demand(sales_df, product_id)
    if daily.empty:
        return pd.DataFrame(columns=["date", "quantity"])

    daily = daily[daily.index >= cutoff_date]
    out = daily.reset_index()
    out.columns = ["date", "quantity"]
    return out


def forecast_demand(product_id, forecast_days=7, sales_df=None):
    """
    Simple moving average forecast for product demand.
    Returns predicted units over forecast_days.
    """
    if sales_df is None:
        sales_df = _load_sales_history(days=365)

    daily = _daily_demand(sales_df, product_id)
    if daily.empty:
        return 0.0

    today = datetime.now().date()
    recent = daily[daily.index >= (today - timedelta(days=30))]

    if len(recent) >= 7:
        avg_daily = recent.tail(7).mean()
    elif len(daily) >= 7:
        avg_daily = daily.tail(7).mean()
    else:
        avg_daily = daily.mean()

    return float(avg_daily) * forecast_days


def get_restock_recommendations():
    """Get restock recommendations for all products (batched DB reads)."""
    response = _query(
        lambda: db()
        .table("products")
        .select("product_id, name, category, quantity, reorder_level, selling_price, cost_price")
        .execute()
    )
    df = pd.DataFrame(response.data or [])
    if df.empty:
        return pd.DataFrame()

    sales_df = _load_sales_history(days=365)

    recommendations = []
    for _, row in df.iterrows():
        product_id = row["product_id"]
        current_stock = row["quantity"]
        reorder_level = row["reorder_level"]

        predicted_demand = forecast_demand(product_id, forecast_days=14, sales_df=sales_df)

        days_of_stock = current_stock / (predicted_demand / 14) if predicted_demand > 0 else 999

        restock_needed = current_stock < reorder_level or days_of_stock < 7
        recommended_order = max(0, int(predicted_demand * 2 - current_stock))

        recommendations.append({
            "product_id": product_id,
            "name": row["name"],
            "category": row["category"],
            "current_stock": current_stock,
            "reorder_level": reorder_level,
            "predicted_demand_14d": round(predicted_demand, 1),
            "days_of_stock": round(days_of_stock, 1) if days_of_stock < 999 else "High",
            "restock_needed": restock_needed,
            "recommended_order": recommended_order if restock_needed else 0,
            "unit_cost": row["cost_price"],
            "order_cost": recommended_order * row["cost_price"] if restock_needed else 0,
        })

    return pd.DataFrame(recommendations)


def get_demand_forecast_chart_data():
    """Get forecast data for top products for visualization."""
    response = _query(
        lambda: db()
        .table("products")
        .select("product_id, name")
        .order("product_id")
        .execute()
    )
    products = response.data or []
    if not products:
        return pd.DataFrame()

    sales_df = _load_sales_history(days=365)

    chart_data = []
    for row in products[:10]:
        demand = forecast_demand(row["product_id"], forecast_days=7, sales_df=sales_df)
        daily_demand = demand / 7
        chart_data.append({
            "product": row["name"],
            "predicted_daily": round(daily_demand, 1),
            "predicted_weekly": round(demand, 1),
        })

    return pd.DataFrame(chart_data)


def get_sales_velocity():
    """Calculate sales velocity for each product."""
    products = _query(
        lambda: db().table("products").select("product_id, name, category, quantity").execute()
    ).data or []

    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    sales_df = pd.DataFrame(
        _query(
            lambda: db()
            .table("sales")
            .select("product_id, quantity_sold, sale_date")
            .gte("sale_date", cutoff)
            .execute()
        ).data or []
    )

    if sales_df.empty:
        sales_df = pd.DataFrame(columns=["product_id", "quantity_sold", "sale_date"])

    results = []
    for p in products:
        pid = p["product_id"]
        product_sales = sales_df[sales_df["product_id"] == pid] if not sales_df.empty else pd.DataFrame()
        total_sold = product_sales["quantity_sold"].sum() if not product_sales.empty else 0
        days_with_sales = (
            product_sales["sale_date"].apply(lambda x: str(x)[:10]).nunique()
            if not product_sales.empty else 0
        )
        velocity = total_sold / days_with_sales if days_with_sales > 0 else 0
        days_until_empty = int(p["quantity"] / velocity) if velocity > 0 else 999
        results.append({
            "product_id": pid,
            "name": p["name"],
            "category": p["category"],
            "current_stock": p["quantity"],
            "total_sold": total_sold,
            "days_with_sales": days_with_sales,
            "velocity": velocity,
            "days_until_empty": days_until_empty,
        })

    return pd.DataFrame(results).sort_values("total_sold", ascending=False)


def get_seasonal_trends():
    """Analyze seasonal trends in sales."""
    response = _query(lambda: db().table("sales").select("sale_date, total_amount").execute())
    df = pd.DataFrame(response.data or [])
    if df.empty:
        return df

    df["day_of_week"] = pd.to_datetime(df["sale_date"]).dt.dayofweek
    trend = (
        df.groupby("day_of_week")
        .agg(avg_sale_amount=("total_amount", "mean"), transaction_count=("total_amount", "count"))
        .reset_index()
        .sort_values("day_of_week")
    )

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    trend["day_name"] = trend["day_of_week"].map(lambda x: day_names[x])
    return trend


def predict_stockout_risk():
    """Predict products at risk of stockout."""
    velocity_df = get_sales_velocity()

    at_risk = velocity_df[velocity_df["days_until_empty"] < 14].copy()
    at_risk = at_risk.sort_values("days_until_empty")

    return at_risk[["product_id", "name", "category", "current_stock", "velocity", "days_until_empty"]]


def get_category_growth():
    """Analyze growth by category."""
    sales = _query(
        lambda: db().table("sales").select("product_id, sale_date, total_amount").execute()
    ).data or []
    products = _query(
        lambda: db().table("products").select("product_id, category").execute()
    ).data or []

    sales_df = pd.DataFrame(sales)
    products_df = pd.DataFrame(products)
    if sales_df.empty or products_df.empty:
        return pd.DataFrame(columns=["category", "month", "revenue"])

    merged = sales_df.merge(products_df, on="product_id")
    merged["month"] = pd.to_datetime(merged["sale_date"]).dt.strftime("%Y-%m")
    return (
        merged.groupby(["category", "month"])["total_amount"]
        .sum()
        .reset_index()
        .rename(columns={"total_amount": "revenue"})
        .sort_values(["month", "revenue"], ascending=[False, False])
    )
