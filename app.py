from flask import Flask
import sqlite3
import os
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from routes.auth import auth_bp
    from routes.fridge import fridge_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(fridge_bp)

    return app


def init_db():
    db_path = Config.DATABASE
    schema_path = os.path.join(os.path.dirname(__file__), "database", "schema.sql")

    conn = sqlite3.connect(db_path)
    with open(schema_path, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


app = create_app()

from flask import redirect, url_for

@app.route("/")
def home():
    return redirect(url_for("auth.login"))

if __name__ == "__main__":
    if not os.path.exists(Config.DATABASE):
        init_db()
        print("Database initialized.")

    app.run(debug=True)