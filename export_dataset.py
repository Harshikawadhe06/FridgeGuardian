import sqlite3
import pandas as pd

# connect database
conn = sqlite3.connect("database.db")

# read items table
query = """
SELECT
    item_name,
    quantity,
    category,
    storage_type,
    expiry_date,
    completed_date,
    status
FROM items
WHERE status IN ('consumed','wasted')
"""

df = pd.read_sql_query(query, conn)

conn.close()

# convert expiry date to days_to_expiry
df["expiry_date"] = pd.to_datetime(df["expiry_date"])
today = pd.Timestamp.today()

df["days_to_expiry"] = (df["expiry_date"] - today).dt.days

# keep required columns
df = df[
    [
        "quantity",
        "category",
        "storage_type",
        "days_to_expiry",
        "status"
    ]
]

# convert target variable
df["status"] = df["status"].map({
    "consumed":0,
    "wasted":1
})

# save dataset
df.to_csv("food_waste_dataset.csv", index=False)

print("Dataset created successfully!")