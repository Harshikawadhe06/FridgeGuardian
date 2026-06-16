import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "supersecretkey"
    DATABASE = os.path.join(BASE_DIR, "database.db")