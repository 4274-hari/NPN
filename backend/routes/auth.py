import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from models import db, User

auth_bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True) or {}
    username = (data.get("username") or "").strip().lower()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    display_name = (data.get("displayName") or username).strip()

    if not USERNAME_RE.match(username):
        return jsonify({"error": "Username must be 3-20 characters: letters, numbers, underscore."}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Please enter a valid email."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken."}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered."}), 409

    user = User(
        username=username,
        email=email,
        display_name=display_name or username,
        avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}",
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict(user.id)}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True) or {}
    identifier = (data.get("username") or data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password."}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict(user.id)})


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict(user_id))
