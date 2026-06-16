import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer

# Load recipe dataset
df = pd.read_excel(r"C:\Users\Mahesh\Desktop\FridgeGuardian\fridge_guardian_research\recipe_dataset.xlsx")

print(df.head())

# Convert ingredients to lowercase
df["ingredients"] = df["ingredients"].str.lower()

# TF-IDF Vectorization
vectorizer = TfidfVectorizer()

recipe_vectors = vectorizer.fit_transform(df["ingredients"])

# Save everything
joblib.dump(vectorizer, "recipe_vectorizer.pkl")
joblib.dump(recipe_vectors, "recipe_vectors.pkl")

print("Recipe Recommender Model Saved Successfully")