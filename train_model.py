import pandas as pd
import os

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report
)

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier

import joblib
import matplotlib.pyplot as plt
import seaborn as sns


# ---------------- DEBUG PATH ----------------
print("Working Directory:", os.getcwd())


# ---------------- LOAD DATA ----------------
df = pd.read_csv("food_waste_dataset.csv")

print("\nDataset Preview:")
print(df.head())


# ---------------- ENCODING ----------------
le_category = LabelEncoder()
le_storage = LabelEncoder()
le_status = LabelEncoder()

df["category"] = le_category.fit_transform(df["category"])
df["storage_type"] = le_storage.fit_transform(df["storage_type"])
df["status"] = le_status.fit_transform(df["status"])


# ---------------- CHECK BALANCE ----------------
print("\nTarget Distribution:")
print(df["status"].value_counts())


# ---------------- FEATURES ----------------
X = df[["category", "storage_type", "days_to_expiry"]]
y = df["status"]


# ---------------- SPLIT (IMPROVED) ----------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)


# ---------------- MODELS (IMPROVED) ----------------
models = {
    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        class_weight='balanced',
        random_state=42
    ),
    "Logistic Regression": LogisticRegression(max_iter=300),
    "Decision Tree": DecisionTreeClassifier(),
    "KNN": KNeighborsClassifier()
}

results = {}


# ---------------- TRAIN & EVALUATE ----------------
for name, model in models.items():
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    acc = accuracy_score(y_test, pred)
    prec = precision_score(y_test, pred, average='weighted', zero_division=0)
    rec = recall_score(y_test, pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, pred, average='weighted', zero_division=0)

    results[name] = {
        "Accuracy": acc,
        "Precision": prec,
        "Recall": rec,
        "F1 Score": f1
    }

    print(f"\n{name}")
    print("Accuracy:", acc)
    print("Precision:", prec)
    print("Recall:", rec)
    print("F1 Score:", f1)

    # 🔥 Classification report (VERY IMPORTANT FOR VIVA)
    print("\nClassification Report:")
    print(classification_report(y_test, pred))


# ---------------- BEST MODEL ----------------
best_model_name = max(results, key=lambda x: results[x]["Accuracy"])
best_model = models[best_model_name]

print("\nBest Model:", best_model_name)


# ---------------- SAVE MODEL ----------------
joblib.dump(best_model, "food_waste_model.pkl")
print("Best model saved successfully!")


# ---------------- SAVE RESULTS CSV ----------------
df_results = pd.DataFrame(results).T
df_results.to_csv("model_results.csv")
print("Model results saved as CSV!")


# ---------------- CREATE STATIC FOLDER ----------------
if not os.path.exists("static"):
    os.makedirs("static")


# ---------------- PLOT MODEL COMPARISON ----------------
plt.figure()
df_results.plot(kind="bar")

plt.title("Model Comparison")
plt.ylabel("Score")
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig("static/model_comparison.png")   # ✅ FIXED PATH
print("Model comparison graph saved!")

plt.close()


# ---------------- CONFUSION MATRIX ----------------
best_pred = best_model.predict(X_test)
cm = confusion_matrix(y_test, best_pred)

plt.figure()
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")

plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")

plt.savefig("static/confusion_matrix.png")   # ✅ FIXED PATH
print("Confusion matrix saved!")

plt.close()