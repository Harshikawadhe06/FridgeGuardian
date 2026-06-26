from flask import Blueprint, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import re
from flask import flash

def validate_username(username):
    pattern = r"^[A-Za-z0-9_]{5,20}$"
    return re.match(pattern, username)


def validate_password(password):
    if len(password) < 8:
        return False

    if not re.search(r"[A-Z]", password):
        return False

    if not re.search(r"[a-z]", password):
        return False

    if not re.search(r"\d", password):
        return False

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False

    return True
auth_bp = Blueprint('auth', __name__)

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@auth_bp.route("/login", methods=["GET", "POST"])
def login():


    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    conn.close()

    if user is None:
        flash("User not found. Please register first.")
        return redirect(url_for("auth.register"))

    if not check_password_hash(user["password_hash"], password):
        flash("Incorrect password.")
        return render_template("login.html")

    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return redirect(url_for("fridge.dashboard"))



@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not validate_username(username):
            flash("Username must be 5-20 characters and contain only letters, numbers, or underscores.")
            return render_template("register.html")

        if not validate_password(password):
            flash("Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one number, and one special character.")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html")

        conn = get_db_connection()

        existing_user = conn.execute(
            "SELECT id FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if existing_user:
            conn.close()
            flash("Username already exists.")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)

        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hashed_password)
        )

        conn.commit()
        conn.close()

        flash("Registration successful. Please login.")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("auth.login"))