import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data, compute_kpis, get_sales_timeseries, forecast_sales, top_n

st.set_page_config(
    page_title="Lulu Retail Executive Dashboard",
    layout="wide",
    page_icon="🛒"
)

st.markdown(
    """
    <style>
        .reportview-container {background: #f9f9fa;}
        .sidebar .sidebar-content {background: #3e4756; color: #fff;}
        .css-1d391kg {background-color: #fff;}
        h1, h2, h3, .stMetricLabel {color: #264653;}
        .block-container {padding-top: 1rem;}
        .metric-label {font-size: 1.3rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -- Data Sources (Update these URLs with your actual GitHub raw URLs)
url_products = "https://raw.githubusercontent.com/<user>/<repo>/main/products_master.csv"
url_stores = "https://raw.githubusercontent.com/<user>/<repo>/main/stores_master.csv"
url_calendar = "https://raw.githubusercontent.com/<user>/<repo>/main/calendar_master.csv"
url_inventory = "https://raw.githubusercontent.com/<user>/<repo>/main/inventory_transactions.csv"
url_sales = "https://raw.githubusercontent.com/<user>/<repo>/main/sales_transactions.csv"

# -- Load Data
@st.cache_data
def get_data():
    return load_data(url_products, url_stores, url_calendar, url_inventory, url_sales)

df_products, df_stores, df_calendar, df_inventory, df_sales = get_data()

# -- Sidebar Filters
with st.sidebar:
    st.image('https://upload.wikimedia.org/wikipedia/commons/f/f4/Lulu_Logo.png', width=180)
    st.header("Filters")
    store_opt = st.selectbox("Select Store", ['All'] + df_stores['Store_Name'].tolist())
    cat_opt = st.selectbox("Select Category", ['All'] + df_products['Category'].unique().tolist())
    date_min = df_sales['Date'].min()
    date_max = df_sales['Date'].max()
    date_range = st.date_input("Select Date Range", [pd.to_datetime(date_min), pd.to_datetime(date_max)])

# -- Filter Data
df_sales['Date'] = pd.to_datetime(df_sales['Date'])
df_inventory['Date'] = pd.to_datetime(df_inventory['Date'])
if store_opt != 'All':
    store_id = df_stores[df_stores['Store_Name']==store_opt]['Store_ID'].values[0]
    df_sales = df_sales[df_sales['Store_ID'] == store_id]
    df_inventory = df_inventory[df_inventory['Store_ID'] == store_id]
if cat_opt != 'All':
    skus = df_products[df_products['Category']==cat_opt]['Product_ID']
    df_sales = df_sales[df_sales['Product_ID'].isin(skus)]
    df_inventory = df_inventory[df_inventory['Product_ID'].isin(skus)]
start_date, end_date = date_range
df_sales = df_sales[(df_sales['Date'] >= pd.to_datetime(start_date)) & (df_sales['Date'] <= pd.to_datetime(end_date))]
df_inventory = df_inventory[(df_inventory['Date'] >= pd.to_datetime(start_date)) & (df_inventory['Date'] <= pd.to_datetime(end_date))]

# -- KPIs
total_sales, total_units, oos_count, avg_stock_days, promo_pct = compute_kpis(df_inventory, df_sales)
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Net Sales (AED)", f"{total_sales:,.0f}")
col2.metric("Units Sold", f"{total_units:,}")
col3.metric("Stock Out Events", f"{oos_count:,}")
col4.metric("Avg Days of Stock Cover", f"{avg_stock_days:.2f}")
col5.metric("% Sales on Promo", f"{promo_pct:.1f}%")

# -- Sales Trend (time-series)
st.subheader("Sales Trends")
sales_trend = df_sales.groupby('Date').agg({'Net_Sales_AED':'sum', 'Units_Sold':'sum'}).reset_index()
fig1 = px.line(sales_trend, x='Date', y='Net_Sales_AED', title='Net Sales Over Time', labels={'Net_Sales_AED': 'Net Sales (AED)'})
st.plotly_chart(fig1, use_container_width=True)

# -- Category Share
cat_share = df_sales.merge(df_products[['Product_ID','Category']], on='Product_ID').groupby('Category')['Net_Sales_AED'].sum().reset_index()
fig2 = px.pie(cat_share, values='Net_Sales_AED', names='Category', title='Sales by Category')
st.plotly_chart(fig2, use_container_width=True)

# -- Top/Bottom Performers
st.subheader("Top/Bottom SKUs")
col6, col7 = st.columns(2)
with col6:
    top_skus = top_n(df_sales, field='Net_Sales_AED', n=10, ascending=False)
    top_skus = top_skus.merge(df_products[['Product_ID','Product_Name']], on='Product_ID')
    st.dataframe(top_skus[['Product_ID', 'Product_Name', 'Net_Sales_AED']].rename(columns={'Net_Sales_AED': 'Total Sales (AED)'}), height=280)
with col7:
    bottom_skus = top_n(df_sales, field='Net_Sales_AED', n=10, ascending=True)
    bottom_skus = bottom_skus.merge(df_products[['Product_ID','Product_Name']], on='Product_ID')
    st.dataframe(bottom_skus[['Product_ID', 'Product_Name', 'Net_Sales_AED']].rename(columns={'Net_Sales_AED': 'Total Sales (AED)'}), height=280)

# -- Forecasting Module
st.subheader("Sales Forecasting (Regression Model)")
sku_opt = st.selectbox("Select SKU for Forecasting", df_products['Product_ID'])
store_fcast_opt = st.selectbox("Store for SKU Forecast", ['All'] + df_stores['Store_ID'].tolist())
ts_data = get_sales_timeseries(df_sales, df_calendar, sku_opt, store=None if store_fcast_opt=='All' else store_fcast_opt)
periods = st.slider("Forecast Period (Days)", 7, 30, 14)
forecast, model = forecast_sales(ts_data, periods=periods)
future_dates = pd.date_range(ts_data['Date'].max() + pd.Timedelta(days=1), periods=periods)
fcast_df = pd.DataFrame({'Date': future_dates, 'Forecasted_Units': forecast})
all_df = pd.concat([
    pd.DataFrame({'Date': ts_data['Date'], 'Units': ts_data['Units_Sold'], 'Type': 'Actual'}),
    pd.DataFrame({'Date': fcast_df['Date'], 'Units': fcast_df['Forecasted_Units'], 'Type': 'Forecast'})
])
fig3 = px.line(all_df, x='Date', y='Units', color='Type', title=f"Sales Forecast for {sku_opt}")
st.plotly_chart(fig3, use_container_width=True)

# -- Detailed Tables
with st.expander("Show Detailed Sales Data"):
    st.dataframe(df_sales.head(1000))

with st.expander("Show Detailed Inventory Data"):
    st.dataframe(df_inventory.head(1000))

st.markdown("""
---
*This executive dashboard is designed for rapid, data-driven retail decisions at scale, with interactive business intelligence and AI-driven forecasting. For customizations or expansion (e.g., Prophet, ML-based classification, multi-SKU analysis), contact your analytics lead.*
""")
