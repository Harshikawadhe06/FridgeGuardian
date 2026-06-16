import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# ==========================
# LOAD DATASET
# ==========================

df = pd.read_excel(r"C:\Users\Mahesh\Desktop\FridgeGuardian\fridge_guardian_research\recipe_training_dataset.xlsx")

print("Dataset Loaded")
print(df.head())

# ==========================
# ENCODE INGREDIENTS
# ==========================

ingredient_cols = [
    "ingredient_1",
    "ingredient_2",
    "ingredient_3",
    "ingredient_4"
]

encoders = {}

for col in ingredient_cols:

    le = LabelEncoder()

    df[col] = le.fit_transform(df[col])

    encoders[col] = le

# ==========================
# ENCODE TARGET
# ==========================

recipe_encoder = LabelEncoder()

df["recipe_name"] = recipe_encoder.fit_transform(
    df["recipe_name"]
)

# ==========================
# FEATURES & TARGET
# ==========================

X = df[ingredient_cols]

y = df["recipe_name"]

# ==========================
# TRAIN TEST SPLIT
# ==========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# ==========================
# MODEL
# ==========================

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=15,
    random_state=42
)

# ==========================
# TRAIN
# ==========================

model.fit(X_train, y_train)

# ==========================
# PREDICT
# ==========================

pred = model.predict(X_test)

accuracy = accuracy_score(y_test, pred)

print("\nAccuracy:", accuracy)

print("\nClassification Report")
print(classification_report(y_test, pred))

# ==========================
# SAVE MODEL
# ==========================

joblib.dump(model, "recipe_model.pkl")

joblib.dump(recipe_encoder, "recipe_encoder.pkl")

for col in ingredient_cols:

    joblib.dump(
        encoders[col],
        f"{col}_encoder.pkl"
    )

print("\nRecipe Model Saved Successfully")