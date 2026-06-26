import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

# Load dataset
df = pd.read_csv("food_waste_dataset.csv")

# Encode category
category_encoder = LabelEncoder()
df["category"] = category_encoder.fit_transform(
    df["category"]
)

# Encode storage
storage_encoder = LabelEncoder()
df["storage_type"] = storage_encoder.fit_transform(
    df["storage_type"]
)

# Features
X = df[
    [
        "quantity",
        "category",
        "storage_type",
        "days_to_expiry"
    ]
]

# Target
y = df["status"]

# Train model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X, y)

# Save model and encoders
joblib.dump(model, "ml/waste_model.pkl")
joblib.dump(category_encoder, "ml/category_encoder.pkl")
joblib.dump(storage_encoder, "ml/storage_encoder.pkl")

print("Model trained successfully")