from datetime import datetime

# Category perishability weights
CATEGORY_WEIGHTS = {
    "dairy": 5,
    "meat": 6,
    "vegetable": 4,
    "fruit": 3,
    "grains": 1,
    "beverages": 1,
    "others": 2
}

# Storage weights
STORAGE_WEIGHTS = {
    "room": 3,
    "refrigerator": 1,
    "freezer": 0.5
}

def calculate_risk(category, quantity, expiry_date, storage_type):
    
    today = datetime.today().date()
    expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    days_left = (expiry - today).days

    if days_left <= 0:
        return 100, "High"

    category_weight = CATEGORY_WEIGHTS.get(category.lower(), 2)
    storage_weight = STORAGE_WEIGHTS.get(storage_type.lower(), 2)

    urgency_score = 10 / (days_left + 1)

    risk_score = (
        category_weight * 2 +
        quantity * 1.5 +
        urgency_score * 3 +
        storage_weight
    )

    if risk_score > 25:
        risk_level = "High"
    elif risk_score > 15:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return round(risk_score, 2), risk_level