import joblib
import numpy as np
import requests
from flask import Blueprint, render_template, request, redirect, url_for, session
import sqlite3
import pandas as pd
from datetime import datetime
from config import Config
import pandas as pd
import joblib

from sklearn.metrics.pairwise import cosine_similarity

model = joblib.load("food_waste_model.pkl")
recipe_vectorizer = joblib.load("recipe_vectorizer.pkl")
recipe_vectors = joblib.load("recipe_vectors.pkl")
recipe_df = pd.read_excel("recipe_dataset.xlsx")
recipe_df = pd.read_excel("recipe_dataset.xlsx")


model = joblib.load("food_waste_model.pkl")
recipe_model = joblib.load("recipe_model.pkl")
recipe_encoder = joblib.load("recipe_encoder.pkl")
recipe_df = pd.read_excel("recipe_dataset.xlsx")
fridge_bp = Blueprint('fridge', __name__)


def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- DASHBOARD ----------------
@fridge_bp.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    items = conn.execute(
        "SELECT * FROM items WHERE user_id=? AND status='active'",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    today = datetime.today().date()
    updated_items = []

    category_map = {
        "Dairy": 0,
        "Vegetable": 1,
        "Fruit": 2,
        "Meat": 3,
        "Bakery": 4
    }

    storage_map = {
        "Fridge": 0,
        "Room": 1,
        "Freezer": 2
    }

    # ---------------- PROCESS ITEMS ----------------
    for item in items:

        expiry_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
        days_left = (expiry_date - today).days

        category_encoded = category_map.get(item["category"], 0)
        storage_encoded = storage_map.get(item["storage_type"], 0)

        prob = model.predict_proba([[category_encoded, storage_encoded, days_left]])[0][1]

        if days_left <= 1:
            expiry_score = 1
        elif days_left <= 3:
            expiry_score = 0.7
        elif days_left <= 5:
            expiry_score = 0.4
        else:
            expiry_score = 0.1

        final_score = (0.6 * prob) + (0.4 * expiry_score)

        if final_score > 0.7:
            final_risk = "High"
        elif final_score > 0.4:
            final_risk = "Medium"
        else:
            final_risk = "Low"

        item_dict = dict(item)
        item_dict["days_left"] = days_left
        item_dict["final_risk"] = final_risk

        updated_items.append(item_dict)

    # ---------------- FIXED BLOCK ----------------
    high_priority_items = []

    for item in updated_items:
        if item["days_left"] >= 0 and item["final_risk"] == "High":
            high_priority_items.append(item["item_name"])

    if high_priority_items:
        recommendation_msg = "🚨 Eat today: " + ", ".join(high_priority_items)
    else:
        recommendation_msg = "✅ No urgent items. You're doing great!"

    return render_template(
        "dashboard.html",
        items=updated_items,
        username=session.get("username"),
        recommendation_msg=recommendation_msg
    )

# ---------------- ADD ITEM ----------------

@fridge_bp.route("/add", methods=["POST"])
def add_item():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    item_name = request.form["item_name"]
    quantity = request.form["quantity"]
    category = request.form["category"]
    storage_type = request.form["storage_type"]
    expiry_date = request.form["expiry_date"]

    conn = get_db_connection()

    conn.execute("""
    INSERT INTO items 
    (user_id,item_name,quantity,category,storage_type,expiry_date,status)
    VALUES (?,?,?,?,?,?,?)
    """,(
        user_id,
        item_name,
        quantity,
        category,
        storage_type,
        expiry_date,
        "active"
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("fridge.dashboard"))


# ---------------- DELETE ITEM ----------------

@fridge_bp.route("/delete/<int:item_id>")
def delete_item(item_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM items WHERE id=? AND user_id=?",
        (item_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("fridge.dashboard"))


# ---------------- EDIT ITEM ----------------

@fridge_bp.route("/edit/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):

    conn = get_db_connection()

    item = conn.execute(
        "SELECT * FROM items WHERE id=? AND user_id=?",
        (item_id, session["user_id"])
    ).fetchone()

    if request.method == "POST":

        item_name = request.form["item_name"]
        quantity = request.form["quantity"]
        category = request.form["category"]
        storage_type = request.form["storage_type"]
        expiry_date = request.form["expiry_date"]

        conn.execute("""
        UPDATE items
        SET item_name=?, quantity=?, category=?, storage_type=?, expiry_date=?
        WHERE id=? AND user_id=?
        """,(
            item_name,
            quantity,
            category,
            storage_type,
            expiry_date,
            item_id,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("fridge.dashboard"))

    conn.close()

    return render_template("edit_item.html", item=item)


# ---------------- MARK CONSUMED ----------------

@fridge_bp.route("/mark_consumed/<int:item_id>")
def mark_consumed(item_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    conn.execute(
        "UPDATE items SET status='consumed' WHERE id=? AND user_id=?",
        (item_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("fridge.dashboard"))


# ---------------- MARK WASTED ----------------

@fridge_bp.route("/mark_wasted/<int:item_id>")
def mark_wasted(item_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    conn.execute(
        "UPDATE items SET status='wasted' WHERE id=? AND user_id=?",
        (item_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("fridge.dashboard"))


# ---------------- HISTORY ----------------

@fridge_bp.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    items = conn.execute(
        """
        SELECT * FROM items 
        WHERE user_id=? AND (status='consumed' OR status='wasted')
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template("history.html", items=items)


# ---------------- ANALYTICS ----------------

@fridge_bp.route("/analytics")
def analytics():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    total = conn.execute(
        "SELECT COUNT(*) FROM items WHERE user_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    consumed = conn.execute(
        "SELECT COUNT(*) FROM items WHERE user_id=? AND status='consumed'",
        (session["user_id"],)
    ).fetchone()[0]

    wasted = conn.execute(
        "SELECT COUNT(*) FROM items WHERE user_id=? AND status='wasted'",
        (session["user_id"],)
    ).fetchone()[0]

    conn.close()

    waste_percent = 0
    if total > 0:
        waste_percent = round((wasted / total) * 100, 2)

    return render_template(
        "analytics.html",
        total=total,
        consumed=consumed,
        wasted=wasted,
        waste_percent=waste_percent
    )


# ---------------- RECIPES ----------------

@fridge_bp.route("/recipes")
def recipes():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    items = conn.execute(
        """
        SELECT * FROM items
        WHERE user_id=? AND status='active'
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    today = datetime.today().date()

    category_map = {
        "Dairy": 0,
        "Vegetable": 1,
        "Fruit": 2,
        "Meat": 3,
        "Bakery": 4
    }

    storage_map = {
        "Fridge": 0,
        "Room": 1,
        "Freezer": 2
    }

    priority_items = []

    # ---------------- FIND HIGH/MEDIUM RISK INGREDIENTS ----------------

    for item in items:

        expiry = datetime.strptime(
            item["expiry_date"],
            "%Y-%m-%d"
        ).date()

        days_left = (expiry - today).days

        if days_left < 0:
            continue

        category_encoded = category_map.get(
            item["category"],
            0
        )

        storage_encoded = storage_map.get(
            item["storage_type"],
            0
        )

        prob = model.predict_proba(
            [[
                category_encoded,
                storage_encoded,
                days_left
            ]]
        )[0][1]

        if days_left <= 1:
            expiry_score = 1

        elif days_left <= 3:
            expiry_score = 0.7

        elif days_left <= 5:
            expiry_score = 0.4

        else:
            expiry_score = 0.1

        final_score = (
            0.6 * prob +
            0.4 * expiry_score
        )

        if final_score > 0.7:
            risk = "High"

        elif final_score > 0.4:
            risk = "Medium"

        else:
            risk = "Low"

        print("ITEM:", item["item_name"])
        print("DAYS LEFT:", days_left)
        print("FINAL SCORE:", final_score)
        print("RISK:", risk)

        if risk in ["High", "Medium"]:
            priority_items.append(item["item_name"].lower())

    # ---------------- NO ITEMS FOUND ----------------

    if len(priority_items) == 0:

        return render_template(
            "recipes.html",
            recipes=[],
            reason="No High or Medium Risk Items"
        )

    # ---------------- CREATE USER VECTOR ----------------
    print("\nPriority Items Selected:")
    print(priority_items)

    ingredient_text = " ".join(priority_items)

    user_vector = recipe_vectorizer.transform(
        [ingredient_text]
    )

    # ---------------- COSINE SIMILARITY ----------------

    similarity_scores = cosine_similarity(
        user_vector,
        recipe_vectors
    )

    scores = similarity_scores[0]

    recipe_df["score"] = scores

    print("\nTop 10 Recipes")
    print(
     recipe_df[
        ["recipe_name","score"]
    ].sort_values(
        by="score",
        ascending=False
    ).head(10)
)

    recipe_df_copy = recipe_df.copy()

    recipe_df_copy["score"] = scores

    # ---------------- TOP 3 RECIPES ----------------

    top_recipes = recipe_df_copy.sort_values(
        by="score",
        ascending=False
    ).head(3)

    recipes = top_recipes.to_dict(
        orient="records"
    )

    print("Priority Ingredients:", priority_items)

    print("Recommended Recipes:")
    print(top_recipes[[
        "recipe_name",
        "score"
    ]])

    # ---------------- SEND TO HTML ----------------

    return render_template(
        "recipes.html",
        recipes=recipes,
        reason=", ".join(priority_items)
    )