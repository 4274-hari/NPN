import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "nextweet-dev-secret-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "nextweet-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "nextweet.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
