import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def load_data(url_products, url_stores, url_calendar, url_inventory, url_sales):
    df_products = pd.read_csv(url_products)
    df_stores = pd.read_csv(url_stores)
    df_calendar = pd.read_csv(url_calendar)
    df_inventory = pd.read_csv(url_inventory)
    df_sales = pd.read_csv(url_sales)
    return df_products, df_stores, df_calendar, df_inventory, df_sales

def compute_kpis(df_inventory, df_sales):
    total_sales = df_sales['Net_Sales_AED'].sum()
    total_units = df_sales['Units_Sold'].sum()
    oos_count = df_inventory[df_inventory['Closing_Stock'] == 0].shape[0]
    avg_stock_days = (df_inventory['Closing_Stock'] / df_sales['Units_Sold'].replace(0, np.nan)).mean()
    promo_sales = df_sales[df_sales['Promotion_Flag']=='Y']['Net_Sales_AED'].sum()
    promo_pct = promo_sales / total_sales * 100
    return total_sales, total_units, oos_count, avg_stock_days, promo_pct

def get_sales_timeseries(df_sales, df_calendar, sku, store=None):
    mask = (df_sales['Product_ID'] == sku)
    if store:
        mask = mask & (df_sales['Store_ID'] == store)
    df = df_sales[mask].copy()
    df = df.groupby('Date').agg({'Units_Sold':'sum', 'Net_Sales_AED':'sum'}).reset_index()
    df = df.merge(df_calendar[['Date','Is_Holiday','Day_Of_Week']], on='Date', how='left')
    df['Date'] = pd.to_datetime(df['Date'])
    return df.sort_values('Date')

def forecast_sales(df_ts, periods=14):
    df = df_ts.copy()
    df['ds'] = np.arange(len(df))
    X = df[['ds']]
    y = df['Units_Sold']
    model = LinearRegression().fit(X, y)
    future = pd.DataFrame({'ds': np.arange(len(df), len(df)+periods)})
    forecast = model.predict(future)
    return forecast, model

def top_n(df_sales, field='Net_Sales_AED', n=10, ascending=False):
    grp = df_sales.groupby('Product_ID').agg({field:'sum'}).reset_index()
    return grp.sort_values(field, ascending=ascending).head(n)
