import pandas as pd
import sqlite3

# Load orders dataset
orders = pd.read_csv("data/olist_orders_dataset.csv")

# Connect to SQLite
conn = sqlite3.connect("olist_logistics.db")

# Save to database
orders.to_sql("orders", conn, if_exists="replace", index=False)

conn.close()

print("✅ Orders data saved to SQLite")
