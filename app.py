import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np

# --- Replace these with your actual GitHub raw file URLs ---
products_url = "https://github.com/anshulguptads/lulu_retail_dashboard/blob/main/products_master.csv"
stores_url = "https://github.com/anshulguptads/lulu_retail_dashboard/blob/main/stores_master.csv"
calendar_url = "https://github.com/anshulguptads/lulu_retail_dashboard/blob/main/calendar_master.csv"
inventory_url = "https://github.com/anshulguptads/lulu_retail_dashboard/blob/main/inventory_transactions.csv"
sales_url = "https://raw.githubusercontent.com/<user>/<repo>/main/sales_transactions.csv"

# --- Load data ---
@st.cache_data
def load_data():
    df_products = pd.read_csv(products_url)
    df_stores = pd.read_csv(stores_url)
    df_calendar = pd.read_csv(calendar_url)
    df_inventory = pd.read_csv(inventory_url)
    df_sales = pd.read_csv(sales_url)
    return df_products, df_stores, df_calendar, df_inventory, df_sales

df_products, df_stores, df_calendar, df_inventory, df_sales = load_data()

st.set_page_config("Lulu Retail MVP", layout="wide", page_icon="🛒")
st.title("Lulu Hypermarket - Retail MVP Dashboard")

# --- KPIs ---
total_sales = df_sales['Net_Sales_AED'].sum()
total_units = df_sales['Units_Sold'].sum()
unique_skus = df_sales['Product_ID'].nunique()
stores_count = df_sales['Store_ID'].nunique()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Net Sales (AED)", f"{total_sales:,.0f}")
col2.metric("Total Units Sold", f"{total_units:,}")
col3.metric("Active SKUs", unique_skus)
col4.metric("Stores", stores_count)

# --- Top SKUs ---
st.subheader("Top 10 SKUs by Net Sales")
top_skus = df_sales.groupby('Product_ID')['Net_Sales_AED'].sum().reset_index().sort_values('Net_Sales_AED', ascending=False).head(10)
top_skus = top_skus.merge(df_products[['Product_ID', 'Product_Name']], on='Product_ID', how='left')

fig1, ax1 = plt.subplots(figsize=(8, 5))
ax1.bar(top_skus['Product_Name'], top_skus['Net_Sales_AED'])
ax1.set_xlabel('SKU')
ax1.set_ylabel('Net Sales (AED)')
ax1.set_title('Top 10 SKUs by Net Sales')
plt.xticks(rotation=45, ha='right')
st.pyplot(fig1)

# --- Sales Trend ---
st.subheader("Total Net Sales Trend")
df_sales['Date'] = pd.to_datetime(df_sales['Date'])
sales_trend = df_sales.groupby('Date')['Net_Sales_AED'].sum().reset_index()

fig2, ax2 = plt.subplots(figsize=(8, 5))
ax2.plot(sales_trend['Date'], sales_trend['Net_Sales_AED'], marker='o')
ax2.set_xlabel('Date')
ax2.set_ylabel('Net Sales (AED)')
ax2.set_title('Net Sales Over Time')
plt.xticks(rotation=45)
st.pyplot(fig2)

# --- Simple Sales Forecast for a SKU (Linear Regression) ---
st.subheader("Sales Forecast (Simple Linear Regression)")
sku_selected = st.selectbox("Select SKU", df_products['Product_ID'])
sku_sales = df_sales[df_sales['Product_ID'] == sku_selected].groupby('Date')['Units_Sold'].sum().reset_index()
sku_sales['Date'] = pd.to_datetime(sku_sales['Date'])
sku_sales = sku_sales.sort_values('Date')

if len(sku_sales) > 10:
    sku_sales['ds'] = np.arange(len(sku_sales))
    X = sku_sales[['ds']]
    y = sku_sales['Units_Sold']
    model = LinearRegression().fit(X, y)
    future_days = 14
    future_ds = np.arange(len(sku_sales), len(sku_sales) + future_days)
    forecast = model.predict(future_ds.reshape(-1, 1))
    future_dates = pd.date_range(sku_sales['Date'].max() + pd.Timedelta(days=1), periods=future_days)
    # Plot actual and forecast
    fig3, ax3 = plt.subplots(figsize=(8, 5))
    ax3.plot(sku_sales['Date'], sku_sales['Units_Sold'], label='Actual Units Sold', marker='o')
    ax3.plot(future_dates, forecast, label='Forecasted Units Sold', linestyle='--', marker='x')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Units Sold')
    ax3.set_title('SKU Sales Forecast')
    plt.xticks(rotation=45)
    ax3.legend()
    st.pyplot(fig3)
else:
    st.info("Not enough data to forecast this SKU. Select another SKU.")

st.write("MVP - Powered by Streamlit, Pandas & Matplotlib")
