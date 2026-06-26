import joblib
import pandas as pd

# Load model
model = joblib.load("ml/waste_model.pkl")

# Load encoders
category_encoder = joblib.load("ml/category_encoder.pkl")
storage_encoder = joblib.load("ml/storage_encoder.pkl")


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