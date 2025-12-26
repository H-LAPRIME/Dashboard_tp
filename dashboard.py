import os
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Olist Analytics Dashboard", layout="wide")

DATA_DIR = Path("data")


@st.cache_data
def load_csv(filename: str):
	path = DATA_DIR / filename
	if not path.exists():
		return pd.DataFrame()
	try:
		return pd.read_csv(path, low_memory=False)
	except Exception:
		return pd.read_csv(path, encoding='latin-1', low_memory=False)


@st.cache_data
def load_all():
	orders = load_csv("olist_orders_dataset.csv")
	order_items = load_csv("olist_order_items_dataset.csv")
	payments = load_csv("olist_order_payments_dataset.csv")
	customers = load_csv("olist_customers_dataset.csv")
	products = load_csv("olist_products_dataset.csv")
	sellers = load_csv("olist_sellers_dataset.csv")
	geolocation = load_csv("olist_geolocation_dataset.csv")
	reviews = load_csv("olist_order_reviews_dataset.csv")

	# Normalize timestamps
	for col in [c for c in orders.columns if 'timestamp' in c or 'date' in c]:
		try:
			orders[col] = pd.to_datetime(orders[col])
		except Exception:
			pass

	return {
		"orders": orders,
		"order_items": order_items,
		"payments": payments,
		"customers": customers,
		"products": products,
		"sellers": sellers,
		"geolocation": geolocation,
		"reviews": reviews,
	}


data = load_all()
orders = data["orders"]
order_items = data["order_items"]
payments = data["payments"]
products = data["products"]
customers = data["customers"]
sellers = data["sellers"]
geolocation = data["geolocation"]
reviews = data["reviews"]


def create_master_df():
	if orders.empty or order_items.empty:
		return pd.DataFrame()

	oi = order_items.copy()
	# Ensure numeric
	for col in [c for c in oi.columns if 'price' in c or 'freight' in c or 'value' in c]:
		try:
			oi[col] = pd.to_numeric(oi[col], errors='coerce')
		except Exception:
			pass

	payments_agg = payments.groupby('order_id', as_index=False).agg({'payment_value': 'sum'}) if not payments.empty else pd.DataFrame()

	df = (
		oi.merge(orders, how='left', left_on='order_id', right_on='order_id')
		.merge(products[['product_id','product_category_name']], how='left', left_on='product_id', right_on='product_id')
		.merge(payments_agg, how='left', left_on='order_id', right_on='order_id')
	)

	# compute timestamps
	if 'order_purchase_timestamp' in df.columns:
		df['purchase_date'] = pd.to_datetime(df['order_purchase_timestamp'], errors='coerce')

	# delivery performance
	if 'order_estimated_delivery_date' in df.columns and 'order_delivered_customer_date' in df.columns:
		df['estimated_delivery'] = pd.to_datetime(df['order_estimated_delivery_date'], errors='coerce')
		df['delivered_date'] = pd.to_datetime(df['order_delivered_customer_date'], errors='coerce')
		df['delivery_delta_days'] = (df['delivered_date'] - df['estimated_delivery']).dt.days

	return df


master = create_master_df()

# Create short alias IDs for readability (e.g., P0001, S0001)
def _make_short_map(series, prefix: str):
	vals = pd.Series(series.dropna().unique())
	return {orig: f"{prefix}{i+1:04d}" for i, orig in enumerate(vals)}

if not master.empty:
	if 'product_id' in master.columns:
		_product_map = _make_short_map(master['product_id'], 'P')
		master['product_short_id'] = master['product_id'].map(_product_map)
		if not products.empty and 'product_id' in products.columns:
			products['product_short_id'] = products['product_id'].map(_product_map)
	if 'seller_id' in master.columns:
		_seller_map = _make_short_map(master['seller_id'], 'S')
		master['seller_short_id'] = master['seller_id'].map(_seller_map)
		if not sellers.empty and 'seller_id' in sellers.columns:
			sellers['seller_short_id'] = sellers['seller_id'].map(_seller_map)


def sidebar_filters(df):
	st.sidebar.header("Filters")
	min_date = df['purchase_date'].min() if 'purchase_date' in df.columns else None
	max_date = df['purchase_date'].max() if 'purchase_date' in df.columns else None
	date_range = st.sidebar.date_input("Purchase date range", [min_date, max_date]) if min_date is not None else None
	states = sorted(df['order_estimated_delivery_date'].astype(str).unique()) if 'order_estimated_delivery_date' in df.columns else []
	product_cats = sorted(df['product_category_name'].dropna().unique()) if 'product_category_name' in df.columns else []
	chosen_cats = st.sidebar.multiselect("Product categories", options=product_cats, default=product_cats[:6])
	return date_range, chosen_cats


st.title("Olist — Modern Analytics Dashboard")

if master.empty:
	st.warning("Data not found or datasets are empty. Make sure CSV files are in the `data/` folder.")
	st.stop()

date_range, chosen_cats = sidebar_filters(master)

# apply filters
df = master.copy()
if date_range and len(date_range) == 2 and 'purchase_date' in df.columns:
	start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
	df = df[(df['purchase_date'] >= start) & (df['purchase_date'] <= end)]

if chosen_cats:
	df = df[df['product_category_name'].isin(chosen_cats)]


# KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
	st.metric("Orders", f"{df['order_id'].nunique():,}")
with col2:
	revenue = df['price'].sum() if 'price' in df.columns else (df['payment_value'].sum() if 'payment_value' in df.columns else 0)
	st.metric("Revenue", f"${revenue:,.2f}")
with col3:
	st.metric("Unique Customers", f"{df['customer_id'].nunique():,}")
with col4:
	avg_delivery = df['delivery_delta_days'].mean() if 'delivery_delta_days' in df.columns else np.nan
	st.metric("Avg Delivery Delta (days)", f"{avg_delivery:.1f}" if not np.isnan(avg_delivery) else "N/A")


# Time series orders and revenue
st.markdown("**Orders and Revenue Over Time**")
if 'purchase_date' in df.columns:
	ts = df.groupby(pd.Grouper(key='purchase_date', freq='W')).agg({'order_id':'nunique', 'price':'sum'}).reset_index()
	ts = ts.sort_values('purchase_date')
	fig = px.line(ts, x='purchase_date', y='order_id', title='Orders (weekly)', labels={'order_id':'Orders','purchase_date':'Date'})
	fig2 = px.area(ts, x='purchase_date', y='price', title='Revenue (weekly)', labels={'price':'Revenue','purchase_date':'Date'})
	st.plotly_chart(fig, use_container_width=True)
	st.plotly_chart(fig2, use_container_width=True)


# Top products and sellers
st.markdown("**Top Products & Sellers**")
left, right = st.columns([2,1])
with left:
	top_products = df.groupby('product_id').agg({'price':'sum','order_id':'nunique'}).reset_index().nlargest(15,'price')
	if not top_products.empty:
		merge_prod = top_products.merge(products[[
			'product_id',
			'product_short_id' if 'product_short_id' in products.columns else 'product_id',
			'product_name_lenght',
			'product_category_name'
		]], how='left', on='product_id')
		# Choose short id when available
		x_col = 'product_short_id' if 'product_short_id' in merge_prod.columns else 'product_id'
		figp = px.bar(merge_prod, x=x_col, y='price', hover_data=['product_category_name','product_id'], title='Top products by revenue')
		st.plotly_chart(figp, use_container_width=True)
with right:
		top_sellers = df.groupby('seller_id').agg({'price':'sum'}).reset_index().nlargest(10,'price')
		if not top_sellers.empty:
			if not sellers.empty and 'seller_id' in sellers.columns and 'seller_short_id' in sellers.columns:
				top_sellers = top_sellers.merge(sellers[['seller_id','seller_short_id']], how='left', on='seller_id')
			x_seller = 'seller_short_id' if 'seller_short_id' in top_sellers.columns else 'seller_id'
			figs = px.bar(top_sellers, x=x_seller, y='price', hover_data=['seller_id'], title='Top sellers by revenue')
			st.plotly_chart(figs, use_container_width=True)


# Reviews distribution
st.markdown("**Customer Reviews**")
if not reviews.empty and 'review_score' in reviews.columns:
	rs = reviews['review_score'].value_counts().sort_index()
	figr = px.bar(x=rs.index, y=rs.values, labels={'x':'Review score','y':'Count'}, title='Review score distribution')
	st.plotly_chart(figr, use_container_width=True)


# Delivery performance scatter
st.markdown("**Delivery Performance**")
if 'delivery_delta_days' in df.columns:
	perf = df.groupby('order_id').agg({'delivery_delta_days':'mean','price':'sum'}).reset_index()
	# Plot with trendline if statsmodels is available, otherwise omit trendline
	try:
		import statsmodels.api  # noqa: F401
		use_trend = True
	except Exception:
		use_trend = False

	if use_trend:
		figd = px.scatter(perf, x='delivery_delta_days', y='price', size='price', trendline='ols', title='Delivery delta vs order value')
		st.plotly_chart(figd, use_container_width=True)
	else:
		figd = px.scatter(perf, x='delivery_delta_days', y='price', size='price', title='Delivery delta vs order value (no trendline)')
		st.plotly_chart(figd, use_container_width=True)
		st.info("Optional package `statsmodels` not installed — trendline omitted. Install with `pip install statsmodels` to enable trendline.")


# Map visualization (if geolocation present)
st.markdown("**Geolocation (Seller / Customer) Sample**")
if not geolocation.empty:
	# try to find lat/lon columns
	lat_cols = [c for c in geolocation.columns if 'lat' in c.lower()]
	lon_cols = [c for c in geolocation.columns if 'lon' in c.lower() or 'lng' in c.lower()]
	if lat_cols and lon_cols:
		lat = lat_cols[0]
		lon = lon_cols[0]
		g = geolocation.dropna(subset=[lat, lon]).drop_duplicates(subset=[lat, lon]).sample(min(1000, len(geolocation)))
		try:
			# Prefer the newer `scatter_map` API; fall back to `scatter_mapbox` if not available
			try:
				figm = px.scatter_map(g, lat=lat, lon=lon, hover_name=g.columns[0], zoom=3, height=450)
			except Exception:
				figm = px.scatter_mapbox(g, lat=lat, lon=lon, hover_name=g.columns[0], zoom=3, height=450)
			# Use OpenStreetMap style (Mapbox / MapLibre compatible)
			try:
				figm.update_layout(mapbox_style='open-street-map')
			except Exception:
				pass
			figm.update_layout(margin={'r':0,'t':0,'l':0,'b':0})
			st.plotly_chart(figm, use_container_width=True)
		except Exception:
			st.info("Unable to render map with available geolocation columns.")
	else:
		st.info("No latitude/longitude columns found in geolocation dataset.")
else:
	st.info("No geolocation dataset found.")


st.markdown("---")
st.markdown("Built with Streamlit • Interactive analytics for Olist dataset.\n.")

