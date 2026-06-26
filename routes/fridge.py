import joblib
import numpy as np
import requests
from flask import Blueprint, render_template, request, redirect, url_for, session
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from config import Config
import pandas as pd
import joblib
from flask import request
from item_recommendation_ml.predictor import predict_waste_risk
from sklearn.metrics.pairwise import cosine_similarity
from utils.purchase_advisor import generate_purchase_advice
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
    expired_items = []

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

    for item in items:

        expiry_date = datetime.strptime(
            item["expiry_date"],
            "%Y-%m-%d"
        ).date()

        days_left = (expiry_date - today).days

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
            final_risk = "High"

        elif final_score > 0.4:
            final_risk = "Medium"

        else:
            final_risk = "Low"

        item_dict = dict(item)

        item_dict["days_left"] = days_left
        item_dict["final_risk"] = final_risk

        updated_items.append(item_dict)

        # Popup trigger
        if days_left <= 0:
            expired_items.append(item_dict)
    medium_priority_items = []

    for item in updated_items:

        if item["final_risk"] == "Medium":
            medium_priority_items.append(
                item["item_name"]
            )

    if medium_priority_items:

        recommendation_msg = (
            "💡 Consider using soon: " +
            ", ".join(medium_priority_items[:3])
        )

    else:

        recommendation_msg = ""
    expiring_count = 0
    expired_count = 0

    for item in updated_items:

        if item["days_left"] < 0:
            expired_count += 1

        elif item["days_left"] <= 2:
            expiring_count += 1


    notification_msg = None

    if expired_count > 0:
        notification_msg = (
            f"🚨 {expired_count} item(s) have already expired."
        )

    elif expiring_count > 0:
        notification_msg = (
            f"⚠ {expiring_count} item(s) will expire within 2 days."
        )
    # Dashboard Summary Cards

    total_items = len(updated_items)

    medium_risk_count = sum(
        1 for item in updated_items
        if item["final_risk"] == "Medium"
    )

    expiring_soon_count = sum(
        1 for item in updated_items
        if 0 <= item["days_left"] <= 3
    )
    return render_template(
    "dashboard.html",
    items=updated_items,
    expired_items=expired_items,
    username=session.get("username"),
    recommendation_msg=recommendation_msg,
    total_items=total_items,
    medium_risk_count=medium_risk_count,
    expiring_soon_count=expiring_soon_count
)  
    
# ---------------- ADD ITEM ----------------

@fridge_bp.route("/add", methods=["POST"])
def add_item():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    item_name = " ".join(
    word.capitalize()
    for word in request.form["item_name"].strip().split()
)
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
    """
    UPDATE items
    SET status='consumed',
        completed_date=?
    WHERE id=? AND user_id=?
    """,
    (
        datetime.now().strftime("%Y-%m-%d"),
        item_id,
        session["user_id"]
    )
)

    conn.commit()
    conn.close()

    return redirect(url_for("fridge.dashboard"))

@fridge_bp.route("/confirm_consumed/<int:item_id>")
def confirm_consumed(item_id):

    conn = get_db_connection()

    conn.execute(
    """
    UPDATE items
    SET status='consumed',
        completed_date=?
    WHERE id=?
    """,
    (
        datetime.now().strftime("%Y-%m-%d"),
        item_id
    )
)

    conn.commit()
    conn.close()

    return redirect(url_for("fridge.dashboard"))

@fridge_bp.route("/confirm_wasted/<int:item_id>")
def confirm_wasted(item_id):

    conn = get_db_connection()

    conn.execute(
    """
    UPDATE items
    SET status='wasted',
        completed_date=?
    WHERE id=?
    """,
    (
        datetime.now().strftime("%Y-%m-%d"),
        item_id
    )
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
    """
    UPDATE items
    SET status='wasted',
        completed_date=?
    WHERE id=? AND user_id=?
    """,
    (
        datetime.now().strftime("%Y-%m-%d"),
        item_id,
        session["user_id"]
    )
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

    from datetime import datetime

    items = conn.execute(
        """
        SELECT *
        FROM items
        WHERE user_id=?
        AND status='active'
        """,
        (session["user_id"],)
    ).fetchall()

    today = datetime.today().date()

    predictions = []

    for item in items:

        expiry_date = datetime.strptime(
            item["expiry_date"],
            "%Y-%m-%d"
        ).date()

        days_left = (
            expiry_date - today
        ).days

        risk = predict_waste_risk(
            quantity=item["quantity"],
            category=item["category"],
            storage_type=item["storage_type"],
            days_to_expiry=days_left
        )

        reason_list = []

        if days_left <= 2:
            reason_list.append(
                f"Expires in {days_left} day(s)"
            )

        if item["quantity"] >= 5:
            reason_list.append(
                "High quantity stored"
            )

        if risk >= 70:
            reason_list.append(
                "Frequently wasted in past"
            )

        predictions.append({
            "name": item["item_name"],
            "risk": risk,
            "reasons": reason_list
        })

    predictions.sort(
        key=lambda x: x["risk"],
        reverse=True
    )

    high_risk_items = predictions[:5]

    # --------------------------------
    # Statistics
    # --------------------------------

    total = conn.execute(
        """
        SELECT COUNT(*)
        FROM items
        WHERE user_id=?
        """,
        (session["user_id"],)
    ).fetchone()[0]

    consumed = conn.execute(
        """
        SELECT COUNT(*)
        FROM items
        WHERE user_id=?
        AND status='consumed'
        """,
        (session["user_id"],)
    ).fetchone()[0]

    wasted = conn.execute(
        """
        SELECT COUNT(*)
        FROM items
        WHERE user_id=?
        AND status='wasted'
        """,
        (session["user_id"],)
    ).fetchone()[0]

    # --------------------------------
    # Most Wasted Category
    # --------------------------------

    most_wasted_category = conn.execute(
        """
        SELECT category,
               COUNT(*) as total
        FROM items
        WHERE user_id=?
        AND status='wasted'
        GROUP BY category
        ORDER BY total DESC
        LIMIT 1
        """,
        (session["user_id"],)
    ).fetchone()

    # --------------------------------
    # Most Consumed Category
    # --------------------------------

    most_consumed_category = conn.execute(
        """
        SELECT category,
               COUNT(*) as total
        FROM items
        WHERE user_id=?
        AND status='consumed'
        GROUP BY category
        ORDER BY total DESC
        LIMIT 1
        """,
        (session["user_id"],)
    ).fetchone()

    # --------------------------------
    # Most Wasted Item
    # --------------------------------

    most_wasted_item = conn.execute(
        """
        SELECT item_name,
               COUNT(*) as total
        FROM items
        WHERE user_id=?
        AND status='wasted'
        GROUP BY item_name
        ORDER BY total DESC
        LIMIT 1
        """,
        (session["user_id"],)
    ).fetchone()

    # --------------------------------
    # Most Consumed Item
    # --------------------------------

    most_consumed_item = conn.execute(
        """
        SELECT item_name,
               COUNT(*) as total
        FROM items
        WHERE user_id=?
        AND status='consumed'
        GROUP BY item_name
        ORDER BY total DESC
        LIMIT 1
        """,
        (session["user_id"],)
    ).fetchone()
    

    # =========================
    # CURRENT WEEK WASTE TREND
    # =========================

    today = datetime.today().date()

    week_start = today - timedelta(days=today.weekday())

    week_labels = []
    week_data = []

    for i in range(7):

        day = week_start + timedelta(days=i)

        label = day.strftime("%a")   # Mon Tue Wed

        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM items
            WHERE user_id=?
            AND status='wasted'
            AND DATE(completed_date)=?
            """,
            (
                session["user_id"],
                day.strftime("%Y-%m-%d")
            )
        ).fetchone()[0]

        week_labels.append(label)
        week_data.append(count)
    

    # --------------------------------
    # Waste %
    # --------------------------------

    waste_percent = 0

    if total > 0:
        waste_percent = round(
            (wasted / total) * 100,
            2
        )

    # --------------------------------
    # Food Score
    # --------------------------------

    food_score = max(
        0,
        round(100 - waste_percent)
    )

    # --------------------------------
    # Smart Purchase Advisor
    # --------------------------------

    

    buy_more, buy_less = generate_purchase_advice(
        conn,
        session["user_id"]
    )
    monthly_labels = [
    "Week 1",
    "Week 2",
    "Week 3",
    "Week 4",
    "Week 5"
]

    monthly_data = [0, 0, 0, 0, 0]

    yearly_labels = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    yearly_data = [0] * 12

    # =====================================
    # Fetch all wasted records once
    # =====================================

    monthly_rows = conn.execute(
        """
        SELECT completed_date
        FROM items
        WHERE user_id=?
        AND status='wasted'
        """,
        (session["user_id"],)
    ).fetchall()

    # =====================================
    # Monthly Trend
    # Current Month -> Week1, Week2...
    # =====================================

    for row in monthly_rows:

        if row["completed_date"]:

            date_obj = datetime.strptime(
                row["completed_date"][:10],
                "%Y-%m-%d"
            )

            if (
                date_obj.month == today.month and
                date_obj.year == today.year
            ):

                week_index = min(
                    (date_obj.day - 1) // 7,
                    4
                )

                monthly_data[week_index] += 1

    # =====================================
    # Yearly Trend
    # Current Year -> Jan-Dec
    # =====================================

    for row in monthly_rows:

        if row["completed_date"]:

            date_obj = datetime.strptime(
                row["completed_date"][:10],
                "%Y-%m-%d"
            )

            if date_obj.year == today.year:

                yearly_data[
                    date_obj.month - 1
                ] += 1
    

    # --------------------------------
    # Safe Handling
    # --------------------------------

    most_wasted_category_name = (
        most_wasted_category["category"]
        if most_wasted_category
        else "N/A"
    )

    most_consumed_category_name = (
        most_consumed_category["category"]
        if most_consumed_category
        else "N/A"
    )

    most_wasted_item_name = (
        most_wasted_item["item_name"]
        if most_wasted_item
        else "N/A"
    )

    most_consumed_item_name = (
        most_consumed_item["item_name"]
        if most_consumed_item
        else "N/A"
    )
    conn.close()
    # --------------------------------
    # Render Page
    # --------------------------------

    return render_template(
        "analytics.html",

        total=total,
        consumed=consumed,
        wasted=wasted,
        waste_percent=waste_percent,
        food_score=food_score,

        most_wasted_category=most_wasted_category_name,
        most_consumed_category=most_consumed_category_name,
        monthly_labels=monthly_labels,
        monthly_data=monthly_data,

        yearly_labels=yearly_labels,
        yearly_data=yearly_data,
        most_wasted_item=most_wasted_item_name,
        most_consumed_item=most_consumed_item_name,
        week_labels=week_labels,
        week_data=week_data,
        buy_more=buy_more,
        buy_less=buy_less,

        high_risk_items=high_risk_items
    )
# ---------------- RECIPES ----------------

@fridge_bp.route("/recipes")
def recipes():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    meal_filter = request.args.get(
    "meal_type",
    "All"
)

    food_filter = request.args.get(
        "food_type",
        "All"
)
    conn = get_db_connection()

    items = conn.execute(
        """
        SELECT * FROM items
        WHERE user_id=? AND status='active'
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    

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


    recipe_df_copy = recipe_df.copy()

    recipe_df_copy["score"] = scores
    recipe_df_copy["match_percent"] = (
    recipe_df_copy["score"] * 100
).round().astype(int)
    top_recipes = recipe_df_copy.sort_values(
        by="score",
        ascending=False
    ).head(3)

    # ---------------- TOP 3 RECIPES ----------------

    # ---------------- TOP RECIPES ----------------

    top_recipes = recipe_df_copy.sort_values(
        by="score",
        ascending=False
    )

    if meal_filter != "All":
        top_recipes = top_recipes[
            top_recipes["meal_type"] == meal_filter
        ]

    if food_filter != "All":
        top_recipes = top_recipes[
            top_recipes["food_type"] == food_filter
        ]

    top_recipes = top_recipes.head(6)

    recipes = top_recipes.to_dict(
        orient="records"
    )

    print("Priority Ingredients:", priority_items)

    print("Recommended Recipes:")

    print(
        top_recipes[
            ["recipe_name", "score"]
        ]
    )

    # ---------------- SEND TO HTML ----------------

    return render_template(
        "recipes.html",
        recipes=recipes,
        reason=", ".join(priority_items),
        meal_filter=meal_filter,
        food_filter=food_filter
    )