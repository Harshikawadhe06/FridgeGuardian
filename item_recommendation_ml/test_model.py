from predictor import predict_waste_risk

risk = predict_waste_risk(
    quantity=5,
    category="Fruit",
    storage_type="Pieces",
    days_to_expiry=3
)

print(risk)