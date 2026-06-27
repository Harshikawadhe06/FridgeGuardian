import joblib
import pandas as pd

# Load model
import os
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "ML", "waste_model.pkl")

model = joblib.load(MODEL_PATH)

# Load encoders
category_encoder = joblib.load("ML/category_encoder.pkl")
storage_encoder = joblib.load("ML/storage_encoder.pkl")


def predict_waste_risk(
    quantity,
    category,
    storage_type,
    days_to_expiry
):

    try:
        category_encoded = category_encoder.transform(
            [category]
        )[0]

        storage_encoded = storage_encoder.transform(
            [storage_type]
        )[0]

    except:
        return 50

    X = pd.DataFrame([[
        quantity,
        category_encoded,
        storage_encoded,
        days_to_expiry
    ]], columns=[
        "quantity",
        "category",
        "storage_type",
        "days_to_expiry"
    ])

    probability = model.predict_proba(X)[0][1]

    return round(probability * 100, 2)