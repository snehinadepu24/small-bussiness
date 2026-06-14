# Vyapar

Smart Inventory & Bookkeeping for Indian Kirana & Grocery Stores

All amounts are in **Indian Rupees (₹)**.

## Installation

```bash
pip install -r requirements.txt
```

## Run the Application

```bash
streamlit run app.py
```

## Seed MVP Demo Data

After starting the app (or from terminal):

```bash
python seed.py           # seed if database is empty
python seed.py --force   # wipe and reseed everything
```

Or use **Settings → Seed MVP Data** inside the app.

## Demo Accounts

After seeding:

| Role  | Email               | Password |
|-------|---------------------|----------|
| Owner | owner@biztrack.ai   | demo123  |
| Staff | staff@biztrack.ai   | demo123  |
| Staff | manager@biztrack.ai | demo123  |

**Seed includes:** 40 Indian grocery products (7+ low-stock), ~168 sales, 45 expenses, 25 activity logs — all in ₹.

## Features

- Dashboard with KPIs and charts
- Inventory management with CRUD operations
- Sales tracking with automatic inventory updates
- Expense tracking with categories
- Report generation (CSV/Excel)
- Demand forecasting and restock recommendations
- AI-powered business insights
- Dark mode support
- User authentication with roles (Owner/Staff)

## Project Structure

```
biztrack_ai/
  app.py              # Main Streamlit application
  database.py         # Supabase connection
  seed.py             # MVP demo data seeder (run: python seed.py)
  auth.py             # Authentication module
  inventory.py        # Inventory management
  sales.py            # Sales management
  expenses.py         # Expense tracking
  reports.py          # Report generation
  forecasting.py      # Demand forecasting
  insights.py         # AI business insights
  sample_data.py      # App wrapper for seed.py
  utils.py            # Utilities and theming
```
