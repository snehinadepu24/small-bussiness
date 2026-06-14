"""
Vyapar - Smart Inventory & Bookkeeping for Small Businesses
Main Application Entry Point
"""

import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta

# Import custom modules
import database
import auth
import inventory
import sales
import expenses
import reports
import forecasting
import insights
import utils
import billing
import sample_data

# Page config
st.set_page_config(
    page_title="Vyapar",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'sample_data_loaded' not in st.session_state:
    st.session_state.sample_data_loaded = False
if 'bill_cart' not in st.session_state:
    st.session_state.bill_cart = []

# Apply theme
st.markdown(utils.apply_theme(st.session_state.dark_mode), unsafe_allow_html=True)
st.markdown(utils.get_form_controls_patch(st.session_state.dark_mode), unsafe_allow_html=True)
st.markdown(utils.get_sidebar_patch_css(), unsafe_allow_html=True)

# Global toast notification handler
if 'toast_msg' in st.session_state:
    st.toast(st.session_state.toast_msg, icon="✅")
    del st.session_state.toast_msg


# ---------------------------------------------------------------------------
# Chart layout helper
# ---------------------------------------------------------------------------
def _chart_layout(fig, height=320):
    """Apply consistent styling to Plotly figures"""
    is_dark = st.session_state.get('dark_mode', False)
    text_color = '#94a3b8' if is_dark else '#64748b'
    grid_color = 'rgba(148,163,184,0.15)' if is_dark else 'rgba(100,116,139,0.12)'
    fig.update_layout(
        height=height,
        margin=dict(l=16, r=16, t=32, b=16),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Plus Jakarta Sans, sans-serif', size=12, color=text_color),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02,
            xanchor='right', x=1,
            font=dict(size=11, color=text_color),
            bgcolor='rgba(0,0,0,0)',
        ),
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color=text_color)),
        yaxis=dict(gridcolor=grid_color, zeroline=False, tickfont=dict(color=text_color)),
    )
    return fig


# ---------------------------------------------------------------------------
# Login page
# ---------------------------------------------------------------------------
def show_login_page():
    """Display login / signup page"""
    st.markdown(utils.get_login_page_css(), unsafe_allow_html=True)

    col_hero, col_spacer, col_form = st.columns([1.1, 0.08, 0.92])

    with col_hero:
        st.html(utils.get_login_hero_html())

    with col_form:
        st.markdown(utils.get_login_card_header(), unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email address", placeholder="you@company.com")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                st.markdown("<div style='height: 4px'></div>", unsafe_allow_html=True)

                if st.form_submit_button("Sign In →", use_container_width=True, type="primary"):
                    if email and password:
                        success, result = auth.login(email, password)
                        if success:
                            st.session_state.user = result
                            st.rerun()
                        else:
                            st.error(result)
                    else:
                        st.warning("Please fill in all fields")

            st.markdown(utils.get_login_demo_hint(), unsafe_allow_html=True)

        with tab2:
            with st.form("signup_form"):
                name = st.text_input("Full name", placeholder="Your full name")
                email = st.text_input("Email address", placeholder="you@company.com")
                password = st.text_input("Password", type="password", placeholder="Min. 6 characters")
                role = st.selectbox("Account type", ["staff", "owner"])
                st.markdown("<div style='height: 4px'></div>", unsafe_allow_html=True)

                if st.form_submit_button("Create Account →", use_container_width=True, type="primary"):
                    if name and email and password:
                        success, message = auth.signup(name, email, password, role)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    else:
                        st.warning("Please fill in all fields")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def show_dashboard():
    """Display main dashboard"""
    colors = utils.get_chart_colors()

    # Welcome banner
    st.markdown(utils.get_welcome_banner(st.session_state.user['name']),
                unsafe_allow_html=True)

    # Get quick stats
    stats = insights.get_quick_stats()

    # KPI Cards Row
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Total Products", stats['total_products'])

    with col2:
        st.metric("Inventory Value", utils.format_currency(stats['inventory_value']))

    with col3:
        st.metric("Today's Sales", utils.format_currency(stats['today_sales']))

    with col4:
        st.metric("Monthly Revenue", utils.format_currency(stats['monthly_revenue']))

    with col5:
        st.metric("Total Expenses", utils.format_currency(stats['total_expenses']))

    with col6:
        net_profit = stats['net_profit']
        st.metric("Net Profit", utils.format_currency(net_profit),
                 delta=f"{net_profit:.0f}" if net_profit > 0 else f"{net_profit:.0f}")

    st.markdown("---")

    # Charts Row
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(utils.get_section_header("📈", "Monthly Sales Trend"), unsafe_allow_html=True)
        monthly_sales = sales.get_monthly_sales_trend()
        if not monthly_sales.empty:
            monthly_sales = monthly_sales.sort_values('month')
            fig = px.area(monthly_sales, x='month', y='revenue',
                         labels={'revenue': 'Revenue ($)', 'month': 'Month'})
            fig.update_traces(
                line=dict(color=colors['primary'], width=2.5),
                fillcolor='rgba(13, 148, 136, 0.12)',
            )
            _chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sales data available yet")

    with col2:
        st.markdown(utils.get_section_header("💰", "Revenue vs Expenses"), unsafe_allow_html=True)
        monthly_sales_data = sales.get_monthly_sales_trend()
        monthly_expenses = expenses.get_monthly_expenses_trend()

        if not monthly_sales_data.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=monthly_sales_data['month'],
                y=monthly_sales_data['revenue'],
                name='Revenue',
                marker_color=colors['success'],
                marker_cornerradius=6,
            ))
            if not monthly_expenses.empty:
                fig.add_trace(go.Bar(
                    x=monthly_expenses['month'],
                    y=monthly_expenses['expenses'],
                    name='Expenses',
                    marker_color=colors['danger'],
                    marker_cornerradius=6,
                ))
            fig.update_layout(barmode='group')
            _chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add sales data to see trends")

    # Second row of charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(utils.get_section_header("🏆", "Top Selling Products"), unsafe_allow_html=True)
        top_products = sales.get_top_selling_products(5)
        if not top_products.empty:
            fig = px.bar(top_products, x='Product', y='Revenue',
                        color='Revenue', color_continuous_scale='Teal')
            fig.update_traces(marker_cornerradius=6)
            fig.update_layout(coloraxis_showscale=False)
            _chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sales data yet")

    with col2:
        st.markdown(utils.get_section_header("📦", "Inventory by Category"), unsafe_allow_html=True)
        inv_dist = inventory.get_inventory_distribution()
        if not inv_dist.empty:
            fig = px.pie(inv_dist, values='quantity', names='category',
                        hole=0.45,
                        color_discrete_sequence=colors['pie_colors'])
            fig.update_traces(textposition='inside', textinfo='percent+label',
                             textfont_size=11)
            _chart_layout(fig, height=340)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No inventory data yet")

    # Low stock alerts and recent transactions
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(utils.get_section_header("⚠️", "Low Stock Alerts"), unsafe_allow_html=True)
        low_stock = inventory.get_low_stock_products()
        if not low_stock.empty:
            st.dataframe(low_stock, use_container_width=True, hide_index=True)
        else:
            st.success("All products are well stocked!")

    with col2:
        st.markdown(utils.get_section_header("📋", "Recent Transactions"), unsafe_allow_html=True)
        recent = sales.get_recent_transactions(5)
        if not recent.empty:
            recent['Amount'] = recent['Amount'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(recent, use_container_width=True, hide_index=True)
        else:
            st.info("No transactions yet")


# ---------------------------------------------------------------------------
# Inventory page
# ---------------------------------------------------------------------------
def show_inventory_page():
    """Display inventory management page"""
    st.markdown(utils.get_section_header("📦", "Inventory Management",
                "Add, edit, and manage your product catalog"),
                unsafe_allow_html=True)

    col1, col2 = st.tabs(["Add Product", "Manage Inventory"])

    with col1:
        st.markdown(utils.get_section_header("➕", "Add New Product"), unsafe_allow_html=True)
        with st.form("add_product_form"):
            name = st.text_input("Product Name *")
            category = st.text_input("Category *")
            supplier = st.text_input("Supplier")
            col_a, col_b = st.columns(2)
            with col_a:
                cost_price = st.number_input("Cost Price ($)", min_value=0.0, format="%.2f")
                quantity = st.number_input("Quantity", min_value=0)
            with col_b:
                selling_price = st.number_input("Selling Price ($)", min_value=0.0, format="%.2f")
                reorder_level = st.number_input("Reorder Level", min_value=0, value=10)

            if st.form_submit_button("Add Product", type="primary"):
                if name and category:
                    success, result = inventory.add_product(
                        name, category, supplier, cost_price, selling_price,
                        quantity, reorder_level, st.session_state.user['id']
                    )
                    if success:
                        st.session_state.toast_msg = f"Product added! ID: {result}"
                        st.rerun()
                    else:
                        st.error(result)
                else:
                    st.warning("Please fill in required fields (*)")

    with col2:
        st.markdown(utils.get_section_header("📋", "Current Inventory"), unsafe_allow_html=True)

        # Search and filter
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            search = st.text_input("Search products", placeholder="Type to search...")
        with col_b:
            categories = inventory.get_categories()
            all_cats = ["All"] + categories
            cat_filter = st.selectbox("Category", all_cats)

        # Get filtered products
        if search or cat_filter != "All":
            products_df = inventory.search_products(search, cat_filter)
        else:
            products_df = inventory.get_all_products()

        if not products_df.empty:
            # Format for display
            display_df = products_df.copy()
            for col in ['Cost Price', 'Selling Price']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Edit/Delete section
            st.markdown("### Edit Product")
            product_id = st.number_input("Enter Product ID to Edit/Delete", min_value=1, step=1)

            if st.button("Load Product", key="load_product"):
                product = inventory.get_product_by_id(product_id)
                if product:
                    st.session_state.edit_product = product
                else:
                    st.error("Product not found!")

            if 'edit_product' in st.session_state and st.session_state.edit_product:
                p = st.session_state.edit_product
                with st.form("edit_product_form"):
                    new_name = st.text_input("Name", value=p[1])
                    new_cat = st.text_input("Category", value=p[2])
                    new_supplier = st.text_input("Supplier", value=p[3] or "")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        new_cost = st.number_input("Cost Price", value=float(p[4]), format="%.2f")
                        new_qty = st.number_input("Quantity", value=int(p[6]))
                    with col_b:
                        new_price = st.number_input("Selling Price", value=float(p[5]), format="%.2f")
                        new_reorder = st.number_input("Reorder Level", value=int(p[7]))

                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.form_submit_button("Update Product", type="primary"):
                            success, msg = inventory.update_product(
                                p[0], new_name, new_cat, new_supplier,
                                new_cost, new_price, new_qty, new_reorder,
                                st.session_state.user['id']
                            )
                            if success:
                                st.session_state.toast_msg = msg
                                del st.session_state.edit_product
                                st.rerun()
                            else:
                                st.error(msg)
                    with col_b:
                        if st.form_submit_button("Delete Product"):
                            inventory.delete_product(p[0], st.session_state.user['id'])
                            st.session_state.toast_msg = "Product deleted!"
                            del st.session_state.edit_product
                            st.rerun()
        else:
            st.info("No products in inventory. Add some products to get started!")


# ---------------------------------------------------------------------------
# Billing helpers
# ---------------------------------------------------------------------------
def _add_to_bill_cart(product_id, product_name, quantity, unit_price):
    """Add or merge a line in the session cart."""
    unit_price = round(float(unit_price), 2)
    quantity = int(quantity)
    for item in st.session_state.bill_cart:
        if item["product_id"] == product_id and item["unit_price"] == unit_price:
            item["quantity"] += quantity
            item["line_total"] = round(item["quantity"] * item["unit_price"], 2)
            return
    st.session_state.bill_cart.append({
        "product_id": product_id,
        "product_name": product_name,
        "quantity": quantity,
        "unit_price": unit_price,
        "line_total": round(quantity * unit_price, 2),
    })


def _bill_cart_subtotal():
    return round(sum(i["line_total"] for i in st.session_state.bill_cart), 2)


def _render_bill_summary(bill):
    """Show a formatted bill receipt."""
    items_df = billing.get_bill_items(bill["bill_id"])
    st.markdown(f"""
<div style="
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 16px;
">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 16px;">
        <div>
            <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em;">Invoice</div>
            <div style="font-size: 22px; font-weight: 800; color: #0f172a;">{bill['bill_number']}</div>
        </div>
        <div style="text-align: right; font-size: 13px; color: #64748b;">
            {utils.format_date(bill['bill_date'])}
        </div>
    </div>
    <div style="font-size: 14px; color: #334155; margin-bottom: 16px;">
        <strong>Customer:</strong> {bill.get('customer_name') or 'Walk-in Customer'}<br>
        <strong>Payment:</strong> {bill.get('payment_method', 'Cash')}
    </div>
</div>
""", unsafe_allow_html=True)

    if not items_df.empty:
        display = items_df[["Product", "Qty", "Unit Price", "Line Total"]].copy()
        display["Unit Price"] = display["Unit Price"].apply(lambda x: f"${x:,.2f}")
        display["Line Total"] = display["Line Total"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(display, use_container_width=True, hide_index=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Subtotal", utils.format_currency(bill["subtotal"]))
    with c2:
        st.metric("Discount", utils.format_currency(bill.get("discount", 0)))
    with c3:
        st.metric("Tax", utils.format_currency(bill.get("tax_amount", 0)))
    with c4:
        st.metric("Grand Total", utils.format_currency(bill["total_amount"]))


# ---------------------------------------------------------------------------
# Sales page
# ---------------------------------------------------------------------------
def show_sales_page():
    """Display billing and sales management"""
    st.markdown(utils.get_section_header("💳", "Billing & Sales",
                "Create multi-item bills and manage invoices"),
                unsafe_allow_html=True)

    tab_new, tab_history = st.tabs(["New Bill", "Bill History"])

    with tab_new:
        products_df = inventory.get_all_products()
        if products_df.empty:
            st.warning("No products in inventory. Add products first under Inventory.")
            return

        st.markdown(utils.get_section_header("🧾", "Bill Details"), unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            customer_name = st.text_input("Customer name", placeholder="Walk-in Customer")
        with col_b:
            payment_method = st.selectbox("Payment method", billing.get_payment_methods())

        col_c, col_d = st.columns(2)
        with col_c:
            tax_rate = st.number_input("Tax rate (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
        with col_d:
            discount = st.number_input("Discount ($)", min_value=0.0, value=0.0, format="%.2f")

        notes = st.text_input("Notes (optional)", placeholder="Delivery instructions, reference, etc.")

        st.markdown(utils.get_section_header("➕", "Add Items"), unsafe_allow_html=True)
        products_list = [
            f"{row['ID']} - {row['Name']} (Stock: {row['Quantity']})"
            for _, row in products_df.iterrows()
        ]

        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            selected = st.selectbox("Product", products_list, key="bill_product_select")
        with col2:
            add_qty = st.number_input("Qty", min_value=1, value=1, key="bill_add_qty")

        product_id = int(selected.split(" - ")[0])
        product = inventory.get_product_by_id(product_id)
        default_price = float(product[5]) if product else 0.0

        with col3:
            add_price = st.number_input("Unit price ($)", min_value=0.0, value=default_price, format="%.2f",
                                        key="bill_add_price")

        if st.button("Add to Bill", type="secondary"):
            if product:
                _add_to_bill_cart(product_id, product[1], add_qty, add_price)
                st.session_state.toast_msg = f"Added {add_qty}x {product[1]}"
                st.rerun()

        st.markdown(utils.get_section_header("🛒", "Current Bill"), unsafe_allow_html=True)

        if not st.session_state.bill_cart:
            st.info("No items yet. Select products above and click **Add to Bill**.")
        else:
            cart_df = pd.DataFrame(st.session_state.bill_cart)
            cart_display = cart_df[["product_name", "quantity", "unit_price", "line_total"]].copy()
            cart_display.columns = ["Product", "Qty", "Unit Price", "Line Total"]
            cart_display["Unit Price"] = cart_display["Unit Price"].apply(lambda x: f"${x:,.2f}")
            cart_display["Line Total"] = cart_display["Line Total"].apply(lambda x: f"${x:,.2f}")
            st.dataframe(cart_display, use_container_width=True, hide_index=True)

            subtotal = _bill_cart_subtotal()
            discount_applied = min(float(discount), subtotal)
            taxable = subtotal - discount_applied
            tax_amount = round(taxable * (float(tax_rate) / 100.0), 2)
            grand_total = round(taxable + tax_amount, 2)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Subtotal", utils.format_currency(subtotal))
            m2.metric("Discount", utils.format_currency(discount_applied))
            m3.metric("Tax", utils.format_currency(tax_amount))
            m4.metric("Grand Total", utils.format_currency(grand_total))

            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
            with btn_col1:
                if st.button("Clear Bill"):
                    st.session_state.bill_cart = []
                    st.rerun()
            with btn_col2:
                remove_options = {
                    f"{i + 1}. {item['product_name']} (x{item['quantity']})": i
                    for i, item in enumerate(st.session_state.bill_cart)
                }
                to_remove = st.selectbox("Remove line", ["—"] + list(remove_options.keys()), key="bill_remove_select")
                if to_remove != "—" and st.button("Remove", key="bill_remove_btn"):
                    idx = remove_options[to_remove]
                    st.session_state.bill_cart.pop(idx)
                    st.rerun()
            with btn_col3:
                if st.button("Complete Bill & Update Inventory", type="primary", use_container_width=True):
                    success, result = billing.create_bill(
                        st.session_state.bill_cart,
                        customer_name=customer_name,
                        payment_method=payment_method,
                        notes=notes,
                        tax_rate=tax_rate,
                        discount=discount,
                        user_id=st.session_state.user["id"],
                    )
                    if success:
                        st.session_state.bill_cart = []
                        st.session_state.last_bill_id = result
                        bill, _ = billing.get_bill_detail(result)
                        st.session_state.toast_msg = (
                            f"Bill {bill['bill_number']} created — {utils.format_currency(bill['total_amount'])}"
                        )
                        st.rerun()
                    else:
                        st.error(result)

        if st.session_state.get("last_bill_id"):
            bill, _ = billing.get_bill_detail(st.session_state.last_bill_id)
            if bill:
                st.markdown("---")
                st.markdown(utils.get_section_header("✅", "Last Bill Created"), unsafe_allow_html=True)
                _render_bill_summary(bill)

    with tab_history:
        st.markdown(utils.get_section_header("📜", "Bill History"), unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            start_date = st.date_input("From", value=datetime.now() - timedelta(days=30), key="bill_hist_start")
        with col_b:
            end_date = st.date_input("To", value=datetime.now(), key="bill_hist_end")

        bills_df = billing.get_bills_by_date_range(start_date, end_date)

        if bills_df.empty:
            st.info("No bills found for the selected period.")
        else:
            display_df = bills_df.copy()
            for col in ["Subtotal", "Discount", "Tax", "Total"]:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            total_billed = bills_df["Total"].sum() if "Total" in bills_df.columns else 0
            bill_count = len(bills_df)
            s1, s2 = st.columns(2)
            s1.metric("Bills Issued", bill_count)
            s2.metric("Total Billed", utils.format_currency(total_billed))

            bill_options = {
                f"{row['Bill No.']} — {row['Customer']} — ${row['Total']:,.2f}": row["Bill ID"]
                for _, row in bills_df.iterrows()
            }
            selected_bill_label = st.selectbox("View bill details", list(bill_options.keys()))
            selected_bill_id = bill_options[selected_bill_label]
            bill, _ = billing.get_bill_detail(selected_bill_id)
            if bill:
                _render_bill_summary(bill)

            if st.session_state.user["role"] == "owner":
                st.markdown(utils.get_section_header("🗑️", "Delete Bill (Owner)"), unsafe_allow_html=True)
                del_id = st.number_input("Bill ID to delete", min_value=1, step=1, key="delete_bill_id")
                if st.button("Delete Bill & Restore Stock"):
                    success, msg = billing.delete_bill(int(del_id), st.session_state.user["id"])
                    if success:
                        st.session_state.toast_msg = msg
                        if st.session_state.get("last_bill_id") == int(del_id):
                            del st.session_state.last_bill_id
                        st.rerun()
                    else:
                        st.error(msg)


# ---------------------------------------------------------------------------
# Expenses page
# ---------------------------------------------------------------------------
def show_expenses_page():
    """Display expenses tracking page"""
    st.markdown(utils.get_section_header("💸", "Expense Tracking",
                "Record and categorize your business expenses"),
                unsafe_allow_html=True)

    col1, col2 = st.tabs(["Add Expense", "View Expenses"])

    with col1:
        st.markdown(utils.get_section_header("➕", "Add New Expense"), unsafe_allow_html=True)
        with st.form("add_expense_form"):
            category = st.selectbox("Category", expenses.get_expense_categories())
            description = st.text_area("Description")
            amount = st.number_input("Amount ($)", min_value=0.0, format="%.2f")

            if st.form_submit_button("Add Expense", type="primary"):
                if amount > 0:
                    success, msg = expenses.add_expense(
                        category, description, amount,
                        st.session_state.user['id']
                    )
                    if success:
                        st.session_state.toast_msg = msg
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter an amount greater than 0")

    with col2:
        st.markdown(utils.get_section_header("📜", "Expense Records"), unsafe_allow_html=True)

        # Filters
        col_a, col_b, col_c = st.columns([2, 2, 1])
        with col_a:
            start_date = st.date_input("From", value=datetime.now() - timedelta(days=30))
        with col_b:
            cat_filter = st.selectbox("Category Filter", ["All"] + expenses.get_expense_categories())
        with col_c:
            if st.button("Filter", key="filter_expenses"):
                pass

        # Get expenses
        if cat_filter != "All":
            expenses_df = expenses.get_expenses_by_category(cat_filter)
        else:
            expenses_df = expenses.get_expenses_by_date_range(start_date, datetime.now().date())

        if not expenses_df.empty:
            # Format display
            display_df = expenses_df.copy()
            display_df['Amount'] = display_df['Amount'].apply(lambda x: f"${x:,.2f}")

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Summary by category
            st.markdown(utils.get_section_header("📊", "Expenses by Category"), unsafe_allow_html=True)
            category_summary = expenses.get_expenses_by_category_summary()
            if not category_summary.empty:
                colors = utils.get_chart_colors()
                fig = px.pie(category_summary, values='Total Amount', names='Category',
                            hole=0.45,
                            color_discrete_sequence=colors['pie_colors'])
                fig.update_traces(textposition='inside', textinfo='percent+label',
                                 textfont_size=11)
                _chart_layout(fig, height=360)
                st.plotly_chart(fig, use_container_width=True)

            # Delete expense
            expense_id = st.number_input("Enter Expense ID to Delete", min_value=0, step=1)
            if st.button("Delete Expense"):
                expenses.delete_expense(expense_id, st.session_state.user['id'])
                st.session_state.toast_msg = "Expense deleted!"
                st.rerun()
        else:
            st.info("No expense records found")


# ---------------------------------------------------------------------------
# Reports page
# ---------------------------------------------------------------------------
def show_reports_page():
    """Display reports page"""
    st.markdown(utils.get_section_header("📊", "Reports",
                "Financial summaries and downloadable reports"),
                unsafe_allow_html=True)
    colors = utils.get_chart_colors()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(utils.get_section_header("💹", "Profit & Loss Summary"), unsafe_allow_html=True)
        profit_data = reports.get_profit_report()

        # Display in metric cards
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Revenue", utils.format_currency(profit_data['total_revenue']))
        with m2:
            st.metric("COGS", utils.format_currency(profit_data['cost_of_goods']))
        with m3:
            st.metric("Expenses", utils.format_currency(profit_data['total_expenses']))

        st.metric("Net Profit", utils.format_currency(profit_data['net_profit']),
                delta=f"{profit_data['net_profit']:.0f}")

        # Monthly breakdown
        st.markdown(utils.get_section_header("📈", "Monthly Profit Trend"), unsafe_allow_html=True)
        monthly_profit = reports.get_monthly_profit_report()
        if not monthly_profit.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Revenue', x=monthly_profit['Month'],
                                y=monthly_profit['Revenue'],
                                marker_color=colors['success'],
                                marker_cornerradius=6))
            fig.add_trace(go.Bar(name='Expenses', x=monthly_profit['Month'],
                                y=monthly_profit['Expenses'],
                                marker_color=colors['danger'],
                                marker_cornerradius=6))
            fig.update_layout(barmode='group')
            _chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(utils.get_section_header("📥", "Download Reports"), unsafe_allow_html=True)

        st.markdown("""
<p style="font-size:13px; color:#9ca3af !important; margin-bottom:16px;">
    Export your data as CSV or Excel for offline analysis.</p>
""", unsafe_allow_html=True)

        # Inventory Report
        inventory_df = reports.get_inventory_report()
        inv_csv = reports.export_to_csv(inventory_df)
        inv_excel = reports.export_to_excel(inventory_df, "Inventory")

        st.download_button(
            "📦  Download Inventory (CSV)",
            inv_csv,
            "inventory_report.csv",
            "text/csv",
            use_container_width=True
        )
        st.download_button(
            "📦  Download Inventory (Excel)",
            inv_excel,
            "inventory_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        # Sales Report
        sales_df = reports.get_sales_report()
        sales_csv = reports.export_to_csv(sales_df)

        st.download_button(
            "💳  Download Sales (CSV)",
            sales_csv,
            "sales_report.csv",
            "text/csv",
            use_container_width=True
        )

        # Expense Report
        expense_df = reports.get_expense_report()
        exp_csv = reports.export_to_csv(expense_df)

        st.download_button(
            "💸  Download Expenses (CSV)",
            exp_csv,
            "expenses_report.csv",
            "text/csv",
            use_container_width=True
        )

        # Comprehensive Report
        comprehensive = reports.get_comprehensive_report()
        st.download_button(
            "📊  Download Full Report (Excel)",
            comprehensive,
            "vyapar_full_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )


# ---------------------------------------------------------------------------
# Forecasting page
# ---------------------------------------------------------------------------
def show_forecasting_page():
    """Display forecasting page"""
    st.markdown(utils.get_section_header("🔮", "Demand Forecasting",
                "AI-driven predictions and restock recommendations"),
                unsafe_allow_html=True)
    colors = utils.get_chart_colors()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(utils.get_section_header("📦", "Restock Recommendations"), unsafe_allow_html=True)
        recommendations = forecasting.get_restock_recommendations()

        if not recommendations.empty:
            urgent = recommendations[recommendations['restock_needed'] == True]

            if not urgent.empty:
                urgent = urgent[['name', 'category', 'current_stock',
                               'predicted_demand_14d', 'recommended_order', 'order_cost']]
                urgent.columns = ['Product', 'Category', 'Current Stock',
                                 'Pred. Demand (14d)', 'Order Qty', 'Est. Cost ($)']

                st.dataframe(urgent, use_container_width=True, hide_index=True)

                total_order_cost = recommendations[recommendations['restock_needed'] == True]['order_cost'].sum()
                st.metric("Total Reorder Cost", utils.format_currency(total_order_cost))
            else:
                st.success("No urgent restocking needed!")

        st.markdown(utils.get_section_header("📊", "Daily Demand Forecast"), unsafe_allow_html=True)
        forecast_data = forecasting.get_demand_forecast_chart_data()
        if not forecast_data.empty:
            fig = px.bar(forecast_data, x='product', y='predicted_weekly',
                        labels={'product': 'Product', 'predicted_weekly': 'Predicted Weekly Demand'},
                        color='predicted_weekly', color_continuous_scale='Purples')
            fig.update_traces(marker_cornerradius=6)
            _chart_layout(fig, height=400)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(utils.get_section_header("🚨", "Stockout Risk Analysis"), unsafe_allow_html=True)
        stockout_risk = forecasting.predict_stockout_risk()

        if not stockout_risk.empty:
            stockout_risk.columns = ['ID', 'Product', 'Category', 'Stock', 'Velocity', 'Days Left']
            st.dataframe(stockout_risk, use_container_width=True, hide_index=True)

            # Visualization
            fig = px.bar(stockout_risk.head(10), x='Product', y='Days Left',
                        color='Days Left', color_continuous_scale='RdYlGn')
            fig.update_traces(marker_cornerradius=6)
            _chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown(utils.get_section_header("📅", "Weekly Sales Pattern"), unsafe_allow_html=True)
        weekly_trends = forecasting.get_seasonal_trends()
        if not weekly_trends.empty:
            fig = px.bar(weekly_trends, x='day_name', y='transaction_count',
                        labels={'day_name': 'Day', 'transaction_count': 'Transactions'},
                        color='transaction_count', color_continuous_scale='Purples')
            fig.update_traces(marker_cornerradius=6)
            _chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# AI Insights page
# ---------------------------------------------------------------------------
def show_insights_page():
    """Display AI insights page"""
    st.markdown(utils.get_section_header("🤖", "AI Business Insights",
                "Smart analysis and actionable recommendations"),
                unsafe_allow_html=True)

    # Performance Score
    score_data = insights.get_performance_score()

    col1, col2 = st.columns([1, 3])
    with col1:
        score = score_data['score']
        # Determine gradient based on score
        if score >= 70:
            grad = "linear-gradient(135deg, #10b981 0%, #059669 100%)"
        elif score >= 40:
            grad = "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)"
        else:
            grad = "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)"

        st.markdown(f"""
<div style="
    background: {grad};
    border-radius: 20px;
    padding: 32px 24px;
    text-align: center;
    color: white;
    box-shadow: 0 8px 24px rgba(0,0,0,.15);
">
    <p style="font-size: 48px; font-weight: 900; margin: 0; color: white !important;
              line-height: 1;">{score:.0f}</p>
    <p style="font-size: 13px; margin: 8px 0 0 0; color: rgba(255,255,255,.85) !important;
              font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
        {score_data['rating']}</p>
</div>
""", unsafe_allow_html=True)

    with col2:
        st.markdown(utils.get_section_header("📋", "Performance Breakdown"), unsafe_allow_html=True)
        for detail in score_data['details']:
            st.markdown(f"- {detail}")

    st.markdown("---")

    # Insights Grid
    st.markdown(utils.get_section_header("💡", "Smart Insights"), unsafe_allow_html=True)
    generated_insights = insights.generate_insights()

    cols = st.columns(3)
    for i, insight in enumerate(generated_insights):
        with cols[i % 3]:
            icon_bg = {
                'success': 'rgba(16,185,129,.12)',
                'warning': 'rgba(245,158,11,.12)',
                'info':    'rgba(6,182,212,.12)',
                'danger':  'rgba(239,68,68,.12)',
            }.get(insight['type'], 'rgba(99,102,241,.12)')
            border_color = {
                'success': '#10b981',
                'warning': '#f59e0b',
                'info':    '#06b6d4',
                'danger':  '#ef4444',
            }.get(insight['type'], '#6366f1')

            st.markdown(f"""
<div style="
    background: rgba(255,255,255,.55);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(0,0,0,.06);
    border-left: 4px solid {border_color};
    border-radius: 14px;
    padding: 18px;
    margin: 8px 0;
    transition: transform .2s ease;
">
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
        <div style="
            width:32px; height:32px;
            background:{icon_bg}; border-radius:10px;
            display:flex; align-items:center; justify-content:center;
            font-size:16px;
        ">{insight['icon']}</div>
        <h4 style="margin:0; font-size:14px; font-weight:700; color:#1e1b4b !important;">
            {insight['title']}</h4>
    </div>
    <p style="margin:0; font-size:13px; line-height:1.5; color:#6b7280 !important;">
        {insight['insight']}</p>
</div>
""", unsafe_allow_html=True)

    # Restock Recommendations
    st.markdown(utils.get_section_header("📦", "Restock Recommendations"), unsafe_allow_html=True)
    restock_df = insights.get_restock_recommendations_insight()
    if not restock_df.empty:
        st.dataframe(restock_df, use_container_width=True, hide_index=True)
    else:
        st.success("All products are well stocked!")


# ---------------------------------------------------------------------------
# Settings page
# ---------------------------------------------------------------------------
def show_settings_page():
    """Display settings page"""
    st.markdown(utils.get_section_header("⚙️", "Settings",
                "Manage your account, appearance, and data"),
                unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(utils.get_section_header("👤", "Profile"), unsafe_allow_html=True)
        user = st.session_state.user

        role_color = "#10b981" if user['role'] == 'owner' else "#6366f1"
        role_bg = "rgba(16,185,129,.1)" if user['role'] == 'owner' else "rgba(99,102,241,.1)"

        st.markdown(f"""
<div style="
    background: rgba(255,255,255,.55);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(0,0,0,.06);
    border-radius: 18px;
    padding: 28px;
    margin-bottom: 20px;
">
    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
        <div style="
            width: 52px; height: 52px;
            background: linear-gradient(135deg, #6366f1, #a78bfa);
            border-radius: 16px;
            display: flex; align-items: center; justify-content: center;
            font-size: 22px; font-weight: 800; color: white;
        ">{user['name'][0].upper()}</div>
        <div>
            <p style="margin: 0; font-size: 18px; font-weight: 700; color: #1e1b4b !important;">
                {user['name']}</p>
            <p style="margin: 4px 0 0 0; font-size: 13px; color: #9ca3af !important;">
                {user['email']}</p>
        </div>
    </div>
    <span style="
        display: inline-block;
        padding: 4px 14px;
        background: {role_bg};
        border-radius: 20px;
        font-size: 12px;
        color: {role_color} !important;
        font-weight: 600;
    ">{user['role'].title()}</span>
</div>
""", unsafe_allow_html=True)

        st.markdown(utils.get_section_header("🔒", "Change Password"), unsafe_allow_html=True)
        with st.form("change_password_form"):
            old_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")

            if st.form_submit_button("Change Password"):
                if new_password == confirm_password:
                    success, msg = auth.change_password(user['id'], old_password, new_password)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.error("Passwords do not match!")

    with col2:
        st.markdown(utils.get_section_header("🎨", "Appearance"), unsafe_allow_html=True)
        dark_mode = st.checkbox("Dark Mode", value=st.session_state.dark_mode)
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()

        st.markdown(utils.get_section_header("🗃️", "Data Management"), unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Seed MVP Data", type="primary"):
                success, msg = sample_data.generate_sample_data(force=st.session_state.sample_data_loaded)
                if success:
                    st.session_state.sample_data_loaded = True
                    st.success(msg)
                    st.rerun()
                else:
                    st.info(msg)
        with col_b:
            if st.session_state.user['role'] == 'owner' and st.button("Force Reseed"):
                success, msg = sample_data.generate_sample_data(force=True)
                if success:
                    st.session_state.sample_data_loaded = True
                    st.success(msg)
                    st.rerun()

        if st.session_state.user['role'] == 'owner':
            if st.button("Clear All Data"):
                sample_data.clear_all_data()
                st.session_state.sample_data_loaded = False
                st.success("All data cleared!")
                st.rerun()

        st.markdown(utils.get_section_header("📜", "Activity Logs"), unsafe_allow_html=True)
        logs = database.get_activity_logs(10)
        if logs:
            for log in logs:
                timestamp, name, action, details = log
                st.markdown(f"- **{utils.format_date(timestamp)}** - {name}: {action} ({details or 'N/A'})")
        else:
            st.info("No activity logs yet")

def show_logout():
    """Handle logout"""
    st.session_state.user = None
    st.rerun()

def main():
    """Main application"""
    # Check authentication
    if not st.session_state.user:
        show_login_page()
        return

    # Sidebar
    with st.sidebar:
        st.markdown(utils.get_sidebar_navigation(), unsafe_allow_html=True)

        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Inventory", "Sales", "Expenses", "Reports", "Forecasting", "AI Insights", "Settings"],
            icons=["speedometer2", "box-seam", "credit-card", "cash-stack", "file-earmark-bar-graph", "graph-up-arrow", "robot", "gear"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {
                    "padding": "4px 0",
                    "background-color": "rgba(0,0,0,0)",
                    "margin": "0",
                },
                "icon": {"color": "#94a3b8", "font-size": "17px"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "2px 10px",
                    "padding": "11px 16px",
                    "border-radius": "10px",
                    "--hover-color": "rgba(255,255,255,0.08)",
                    "color": "#e2e8f0",
                    "font-weight": "500",
                    "background-color": "rgba(0,0,0,0)",
                },
                "nav-link-selected": {
                    "background-color": "rgba(0,0,0,0)",
                    "background": "linear-gradient(135deg, #0f766e 0%, #0d9488 55%, #14b8a6 100%)",
                    "color": "#ffffff",
                    "font-weight": "600",
                    "box-shadow": "0 4px 16px rgba(13, 148, 136, 0.35)",
                },
            }
        )

        st.markdown("<div style='flex:1; min-height:12px'></div>", unsafe_allow_html=True)

        # User info card
        st.markdown(
            utils.get_user_card(st.session_state.user['name'], st.session_state.user['role']),
            unsafe_allow_html=True
        )

        st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

        if st.button("Logout", use_container_width=True, icon="🚪"):
            show_logout()

    # Page routing
    if selected == "Dashboard":
        show_dashboard()
    elif selected == "Inventory":
        show_inventory_page()
    elif selected == "Sales":
        show_sales_page()
    elif selected == "Expenses":
        show_expenses_page()
    elif selected == "Reports":
        show_reports_page()
    elif selected == "Forecasting":
        show_forecasting_page()
    elif selected == "AI Insights":
        show_insights_page()
    elif selected == "Settings":
        show_settings_page()

if __name__ == "__main__":
    main()
