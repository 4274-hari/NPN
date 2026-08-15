from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, User, Follow, Tweet
from utils import notify

users_bp = Blueprint("users", __name__)


def current_uid():
    try:
        return int(get_jwt_identity())
    except Exception:
        return None


@users_bp.route("/search", methods=["GET"])
@jwt_required(optional=True)
def search_users():
    q = (request.args.get("q") or "").strip().lower()
    if not q:
        return jsonify([])
    users = (
        User.query.filter(
            (User.username.ilike(f"%{q}%")) | (User.display_name.ilike(f"%{q}%"))
        )
        .limit(20)
        .all()
    )
    uid = current_uid()
    return jsonify([u.to_dict(uid) for u in users])


@users_bp.route("/mention-suggest", methods=["GET"])
@jwt_required(optional=True)
def mention_suggest():
    q = (request.args.get("q") or "").strip().lower()
    query = User.query
    if q:
        query = query.filter(
            (User.username.ilike(f"{q}%")) | (User.display_name.ilike(f"{q}%"))
        )
    users = query.order_by(User.username.asc()).limit(6).all()
    return jsonify([u.to_public_dict() for u in users])


@users_bp.route("/suggested", methods=["GET"])
@jwt_required(optional=True)
def suggested_users():
    uid = current_uid()
    query = User.query
    if uid:
        query = query.filter(User.id != uid)
    users = query.order_by(User.created_at.desc()).limit(5).all()
    return jsonify([u.to_dict(uid) for u in users])


@users_bp.route("/<username>", methods=["GET"])
@jwt_required(optional=True)
def get_user(username):
    user = User.query.filter_by(username=username.lower()).first_or_404()
    return jsonify(user.to_dict(current_uid()))


@users_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_me():
    uid = current_uid()
    user = User.query.get_or_404(uid)
    data = request.get_json(force=True) or {}
    for field, attr in [
        ("displayName", "display_name"),
        ("bio", "bio"),
        ("avatarUrl", "avatar_url"),
        ("bannerUrl", "banner_url"),
        ("location", "location"),
    ]:
        if field in data:
            setattr(user, attr, data[field])
    db.session.commit()
    return jsonify(user.to_dict(uid))


@users_bp.route("/<username>/followers", methods=["GET"])
@jwt_required(optional=True)
def followers(username):
    user = User.query.filter_by(username=username.lower()).first_or_404()
    follows = Follow.query.filter_by(followed_id=user.id).all()
    uid = current_uid()
    people = [User.query.get(f.follower_id).to_dict(uid) for f in follows]
    return jsonify(people)


@users_bp.route("/<username>/following", methods=["GET"])
@jwt_required(optional=True)
def following(username):
    user = User.query.filter_by(username=username.lower()).first_or_404()
    follows = Follow.query.filter_by(follower_id=user.id).all()
    uid = current_uid()
    people = [User.query.get(f.followed_id).to_dict(uid) for f in follows]
    return jsonify(people)


@users_bp.route("/<username>/follow", methods=["POST"])
@jwt_required()
def follow_user(username):
    uid = current_uid()
    target = User.query.filter_by(username=username.lower()).first_or_404()
    if target.id == uid:
        return jsonify({"error": "You can't follow yourself."}), 400
    existing = Follow.query.filter_by(follower_id=uid, followed_id=target.id).first()
    if existing:
        return jsonify({"error": "Already following."}), 409
    db.session.add(Follow(follower_id=uid, followed_id=target.id))
    db.session.commit()
    notify(recipient_id=target.id, actor_id=uid, type_="follow")
    return jsonify(target.to_dict(uid))


@users_bp.route("/<username>/unfollow", methods=["POST"])
@jwt_required()
def unfollow_user(username):
    uid = current_uid()
    target = User.query.filter_by(username=username.lower()).first_or_404()
    existing = Follow.query.filter_by(follower_id=uid, followed_id=target.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    return jsonify(target.to_dict(uid))
