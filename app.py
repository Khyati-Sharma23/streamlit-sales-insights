import streamlit as st
import pandas as pd

st.title("Shoe Company Dashboard")

# ---------------------------
# Data Cleaning Function
# ---------------------------
def clean_dataframe(df):
    # 1. Standardize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # 2. Remove duplicates
    df = df.drop_duplicates()

    # 3. Handle missing values
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("Unknown")
        else:
            df[col] = df[col].fillna(0)

    # 4. Convert all date-like columns
    for col in df.columns:
        if "date" in col:
            df[col] = pd.to_datetime(
                df[col].astype(str).str.strip(),
                errors="coerce",
                infer_datetime_format=True,
                dayfirst=True
            )

    # 5. Remove invalid negatives
    if "sales_amount" in df.columns:
        df = df[df["sales_amount"] >= 0]
    if "return_quantity" in df.columns:
        df = df[df["return_quantity"] >= 0]
    if "stock_quantity" in df.columns:
        df = df[df["stock_quantity"] >= 0]

    return df

# Upload Excel files
sales_file = st.file_uploader("Upload Sales Report", type=["xlsx"])
returns_file = st.file_uploader("Upload Return Report", type=["xlsx"])
stock_file = st.file_uploader("Upload Stock Report", type=["xlsx"])

# ---------------------------
# Apply Cleaning After Upload
# ---------------------------
if sales_file:
    sales_df = pd.read_excel(sales_file)
    sales_df = clean_dataframe(sales_df)
  
    # --- SALES: dtypes + computed fields ---
    for c in ["orderqty", "unit_price"]:
        if c in sales_df.columns:
            sales_df[c] = pd.to_numeric(sales_df[c], errors="coerce").fillna(0)

    if {"orderqty", "unit_price"}.issubset(sales_df.columns):
        sales_df["sales_amount"] = sales_df["orderqty"] * sales_df["unit_price"]

    # handle order_date / orderdate
    if "order_date" in sales_df.columns:
        sales_df["order_date"] = pd.to_datetime(sales_df["order_date"], errors="coerce")
    elif "orderdate" in sales_df.columns:
        sales_df["order_date"] = pd.to_datetime(sales_df["orderdate"], errors="coerce")


    if "order_date" in sales_df.columns:
        sales_df["order_date"] = pd.to_datetime(
            sales_df["order_date"], errors="coerce", infer_datetime_format=True, dayfirst=True
        )
        sales_df = sales_df.dropna(subset=["order_date"])

    st.subheader("📊 Sales Report (Cleaned)")
    st.dataframe(sales_df)  

if returns_file:
    returns_df = pd.read_excel(returns_file)
    returns_df = clean_dataframe(returns_df)

    # --- RETURNS: align column names + dtypes ---
    if "received_qty" in returns_df.columns and "return_quantity" not in returns_df.columns:
        returns_df["return_quantity"] = pd.to_numeric(returns_df["received_qty"], errors="coerce").fillna(0)

    # date column in your file is received_date
    if "received_date" in returns_df.columns:
        returns_df["received_date"] = pd.to_datetime(returns_df["received_date"], errors="coerce")


    if "return_date" in returns_df.columns:
        returns_df["return_date"] = pd.to_datetime(
            returns_df["return_date"], errors="coerce", infer_datetime_format=True, dayfirst=True
        )
        returns_df = returns_df.dropna(subset=["return_date"])

    st.subheader("↩️ Return Report (Cleaned)")
    st.dataframe(returns_df)   

if stock_file:
    stock_df = pd.read_excel(stock_file)
    stock_df = clean_dataframe(stock_df)

    # --- STOCK: align quantity column ---
    if "soh" in stock_df.columns and "stock_quantity" not in stock_df.columns:
        stock_df["stock_quantity"] = pd.to_numeric(stock_df["soh"], errors="coerce").fillna(0)

    st.subheader("📦 Stock Report (Cleaned)")
    st.dataframe(stock_df)  

# -----------------------------
# Dashboard Tabs
# -----------------------------
tab1, tab2, tab3, = st.tabs(["Sales", "Returns", "Stock",])

with tab1:
    if sales_file:
        st.subheader("Sales Dashboard")
        st.dataframe(sales_df)

with tab2:
    if returns_file:
        st.subheader("Returns Dashboard")
        st.dataframe(returns_df)

with tab3:
    if stock_file:
        st.subheader("Stock Dashboard")
        st.dataframe(stock_df)
# ---------------------------------------------------------
# Advanced Data Analysis
# ---------------------------------------------------------

  
if ('sales_df' in locals()) and ('returns_df' in locals()) and ('stock_df' in locals()):
    st.markdown("---")
    st.header("📊 Advanced Analytics & Insights")

    tab_a, tab_b, tab_c, tab_d, tab_e, tab_f, tab_g = st.tabs([
        "Overview",
        "Demand Forecasting",
        "Top Sellers",
        "Profitability",
        "Returns Analysis",
        "Inventory Management",
        "Additional Insights"
    ])

    # 1. Overview
    with tab_a:
        st.subheader("Business Overview")
        if "orderqty" in sales_df.columns and "unit_price" in sales_df.columns:
            sales_df["sales_amount"] = sales_df["orderqty"] * sales_df["unit_price"]
            total_sales = sales_df["sales_amount"].sum()
            total_orders = sales_df["orderqty"].sum()
        else:
            total_sales, total_orders = 0, 0

        if "received_qty" in returns_df.columns:
            total_returns = returns_df["received_qty"].sum()
        else:
            total_returns = 0

        return_rate = (total_returns / total_orders * 100) if total_orders > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Sales", f"₹{total_sales:,.0f}")
        col2.metric("Total Orders", f"{total_orders:,}")
        col3.metric("Total Returns", f"{total_returns:,}")
        col4.metric("Return Rate", f"{return_rate:.2f}%")

    # 2. Demand Forecasting
    with tab_b:
        if "order_date" in sales_df.columns and "orderqty" in sales_df.columns:
            st.subheader("Demand Forecast (Next 3 Months)")
            monthly_sales = sales_df.groupby(sales_df["order_date"].dt.to_period("M"))["orderqty"].sum()
            monthly_sales.index = monthly_sales.index.to_timestamp()
            forecast = monthly_sales.rolling(window=3).mean().shift(1).tail(3)
            chart_data = pd.concat([monthly_sales, forecast.rename("Forecast")])
            st.line_chart(chart_data)
        else:
            st.warning("Sales data missing 'order_date' or 'orderqty' column.")
  
  
   # 3. Top Sellers
    with tab_c:
        if "sku" in sales_df.columns and "orderqty" in sales_df.columns:
            st.subheader("Top 10 Selling Products")
            top_products = sales_df.groupby("sku")["orderqty"].sum().nlargest(10)
            st.bar_chart(top_products)
        else:
            st.warning("Sales data missing 'sku' or 'orderqty' column.")

    # 4. Profitability
    with tab_d:
        if "invoice_amount" in sales_df.columns:
            st.subheader("Profitability Analysis")
            sales_df["profit"] = sales_df["invoice_amount"] - sales_df.get("cost", 0) - sales_df.get("returns", 0)
            profit_summary = sales_df.groupby("sku")["profit"].sum().sort_values(ascending=False).head(10)
            st.bar_chart(profit_summary)
        else:
            st.warning("Sales data missing 'invoice_amount' column.")

    # 5. Returns Analysis
    with tab_e:
        if "reason" in returns_df.columns:
            st.subheader("Returns Analysis")
            return_reasons = returns_df["reason"].value_counts()
            st.bar_chart(return_reasons)
        else:
            st.warning("Returns data missing 'reason' column.")

    # 6. Inventory Management
    with tab_f:
        if "sku" in stock_df.columns and "soh" in stock_df.columns:
            st.subheader("Inventory Management")
            deadstock = stock_df[stock_df["soh"] > 0].sort_values("soh", ascending=False).head(10)
            st.dataframe(deadstock)
        else:
            st.warning("Stock data missing 'sku' or 'soh' column.")

     # 7. Additional Insights
    with tab_g:
        st.subheader("Additional Insights")

        # Insight 1: Daily Sales Trend for the Month
        st.markdown("### Insight 1: Daily Sales Trend for the Month")
        if "order_date" in sales_df.columns and "orderqty" in sales_df.columns:
            sales_df["day"] = sales_df["order_date"].dt.day
            sales_by_day = sales_df.groupby("day")["orderqty"].sum()
            st.line_chart(sales_by_day)
            st.markdown("#### Daily Sales Table")
            st.dataframe(sales_by_day)
            top_day = sales_by_day.idxmax()
            peak_qty = sales_by_day.max()
            lowest_day = sales_by_day.idxmin()
            low_qty = sales_by_day.min()
            st.markdown(f"**Peak Sales Day:** Day {top_day} with {peak_qty} units sold.")
            st.markdown(f"**Lowest Sales Day:** Day {lowest_day} with {low_qty} units sold.")
            st.info("This chart shows daily sales trends within the month, useful for spotting high activity days and adjusting daily operations.")
        else:
            st.warning("Data missing for daily sales trend (need order_date & orderqty).")

        # Insight 2: Daily Average Order Value (AOV) Trends
        st.markdown("### Insight 2: Daily Average Order Value (AOV) Trends")
        if all(col in sales_df.columns for col in ["order_date", "invoice_amount", "order_no"]):
            sales_df["day"] = sales_df["order_date"].dt.day
            aov_by_day = sales_df.groupby("day").apply(lambda x: x["invoice_amount"].sum() / x["order_no"].nunique())
            st.line_chart(aov_by_day)
            st.markdown("#### Daily AOV Table")
            st.dataframe(aov_by_day)
            peak_day = aov_by_day.idxmax()
            peak_aov = aov_by_day.max()
            low_day = aov_by_day.idxmin()
            low_aov = aov_by_day.min()
            st.markdown(f"**Highest AOV Day:** Day {peak_day} (AOV: £{peak_aov:.2f})")
            st.markdown(f"**Lowest AOV Day:** Day {low_day} (AOV: £{low_aov:.2f})")
            st.info("This chart shows how Average Order Value (AOV) changed daily in the month. High AOV may suggest large orders or effective promotions on certain days!")
        else:
            st.warning("Data missing for daily AOV trends (need order_date, invoice_amount, order_no).")

        # Insight 3: Geographic Sales Hotspots
        st.markdown("### Insight 3: Geographic Sales Hotspots")
        if "state" in sales_df.columns and "invoice_amount" in sales_df.columns:
            geo_sales = sales_df.groupby("state")["invoice_amount"].sum().sort_values(ascending=False).head(10)
            st.bar_chart(geo_sales)
            st.markdown("#### Detailed Sales by State")
            st.dataframe(geo_sales)
            top_state = geo_sales.idxmax()
            top_value = geo_sales.max()
            lowest_state = geo_sales.idxmin()
            lowest_value = geo_sales.min()
            st.markdown(f"**Top Sales State:** {top_state} (£{top_value:,.2f})")
            st.markdown(f"**Lowest Sales State in Top 10:** {lowest_state} (£{lowest_value:,.2f})")
            st.info("Geographic sales distribution helps focus on key markets.")
        else:
            st.warning("Data missing for geographic sales (need state & invoice_amount).")

        # Insight 4: Impact of Discounts/Promotions on Sales
        st.markdown("### Insight 4: Impact of Discounts/Promotions on Sales")
        if "discount" in sales_df.columns and "invoice_amount" in sales_df.columns:
            discount_impact = sales_df.groupby("discount")["invoice_amount"].sum().sort_values(ascending=False)
            st.bar_chart(discount_impact)
            st.markdown("#### Sales Revenue by Discount Level")
            st.dataframe(discount_impact)
            max_discount = discount_impact.idxmax()
            max_sales = discount_impact.max()
            min_discount = discount_impact.idxmin()
            min_sales = discount_impact.min()
            st.markdown(f"**Highest Sales with Discount Level:** {max_discount} (£{max_sales:,.2f})")
            st.markdown(f"**Lowest Sales with Discount Level:** {min_discount} (£{min_sales:,.2f})")
            st.info("Analysis of sales by discount level shows which promotions drive revenue best.")
        else:
            st.warning("Data missing for discount analysis (need discount & invoice_amount).")

        # Insight 5: Repeat vs New Customers
        st.markdown("### Insight 5: Repeat vs New Customers")
        if all(col in sales_df.columns for col in ["customer_name", "order_date", "invoice_amount"]):
            first_purchase = sales_df.groupby("customer_name")["order_date"].min().reset_index()
            first_purchase.rename(columns={"order_date": "order_date_first"}, inplace=True)
            sales_df = sales_df.merge(first_purchase, on="customer_name", how="left")
            sales_df["order_date"] = pd.to_datetime(sales_df["order_date"])
            sales_df["order_date_first"] = pd.to_datetime(sales_df["order_date_first"])
            sales_df["customer_type"] = (sales_df["order_date"].dt.date == sales_df["order_date_first"].dt.date)
            sales_df["customer_type"] = sales_df["customer_type"].map({True: "New", False: "Repeat"})
            repeat_vs_new = sales_df.groupby("customer_type")["invoice_amount"].sum()
            total_sales = repeat_vs_new.sum()
            repeat_vs_new_pct = (repeat_vs_new / total_sales * 100).round(2)
            summary_df = pd.DataFrame({
                "Sales Amount (£)": repeat_vs_new,
                "Percent of Total Sales (%)": repeat_vs_new_pct
            })
            st.bar_chart(repeat_vs_new)
            st.markdown("#### Sales Amount & % Contribution")
            st.dataframe(summary_df)
            st.markdown("This analysis shows revenue from new vs repeat customers.")
        else:
            st.warning("Data missing for repeat vs new customers (need customer_name, order_date, invoice_amount).")
