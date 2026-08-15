import re
from collections import Counter
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, Tweet, User, Follow, Like
from utils import extract_and_store_mentions, notify

tweets_bp = Blueprint("tweets", __name__)

HASHTAG_RE = re.compile(r"#(\w{2,50})")


def current_uid():
    try:
        return int(get_jwt_identity())
    except Exception:
        return None


@tweets_bp.route("", methods=["POST"])
@jwt_required()
def create_tweet():
    uid = current_uid()
    data = request.get_json(force=True) or {}
    content = (data.get("content") or "").strip()
    parent_id = data.get("parentId")

    if not content:
        return jsonify({"error": "Tweet cannot be empty."}), 400
    if len(content) > 500:
        return jsonify({"error": "Tweet is too long (max 500 characters)."}), 400

    tweet = Tweet(user_id=uid, content=content, parent_id=parent_id)
    db.session.add(tweet)
    db.session.commit()

    extract_and_store_mentions(tweet, uid)

    if parent_id:
        parent = Tweet.query.get(parent_id)
        if parent:
            notify(recipient_id=parent.user_id, actor_id=uid, type_="comment", tweet_id=tweet.id)

    return jsonify(tweet.to_dict(uid)), 201


@tweets_bp.route("/feed", methods=["GET"])
@jwt_required()
def home_feed():
    uid = current_uid()
    followed_ids = [f.followed_id for f in Follow.query.filter_by(follower_id=uid).all()]
    followed_ids.append(uid)

    tweets = (
        Tweet.query.filter(Tweet.user_id.in_(followed_ids), Tweet.parent_id.is_(None))
        .order_by(Tweet.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify([t.to_dict(uid) for t in tweets])


@tweets_bp.route("/explore", methods=["GET"])
@jwt_required(optional=True)
def explore():
    uid = current_uid()
    tweets = (
        Tweet.query.filter(Tweet.parent_id.is_(None))
        .order_by(Tweet.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify([t.to_dict(uid) for t in tweets])


@tweets_bp.route("/trending", methods=["GET"])
@jwt_required(optional=True)
def trending():
    tweets = Tweet.query.order_by(Tweet.created_at.desc()).limit(200).all()
    counter = Counter()
    for t in tweets:
        for tag in HASHTAG_RE.findall(t.content):
            counter[tag.lower()] += 1
    top = counter.most_common(6)
    if not top:
        # fallback sample trends so the UI never looks empty on a fresh DB
        top = [("nextweet", 0), ("technology", 0), ("webdev", 0)]
    return jsonify(
        [{"tag": tag, "count": count} for tag, count in top]
    )


@tweets_bp.route("/search", methods=["GET"])
@jwt_required(optional=True)
def search_tweets():
    q = (request.args.get("q") or "").strip()
    uid = current_uid()
    if not q:
        return jsonify([])
    tweets = (
        Tweet.query.filter(Tweet.content.ilike(f"%{q}%"))
        .order_by(Tweet.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify([t.to_dict(uid) for t in tweets])


@tweets_bp.route("/user/<username>", methods=["GET"])
@jwt_required(optional=True)
def user_tweets(username):
    user = User.query.filter_by(username=username.lower()).first_or_404()
    uid = current_uid()
    tweets = (
        Tweet.query.filter_by(user_id=user.id)
        .filter(Tweet.parent_id.is_(None))
        .order_by(Tweet.created_at.desc())
        .all()
    )
    return jsonify([t.to_dict(uid) for t in tweets])


@tweets_bp.route("/<int:tweet_id>", methods=["GET"])
@jwt_required(optional=True)
def get_tweet(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)
    uid = current_uid()
    replies = (
        Tweet.query.filter_by(parent_id=tweet_id)
        .order_by(Tweet.created_at.asc())
        .all()
    )
    result = tweet.to_dict(uid)
    result["replies"] = [r.to_dict(uid) for r in replies]
    return jsonify(result)


@tweets_bp.route("/<int:tweet_id>", methods=["DELETE"])
@jwt_required()
def delete_tweet(tweet_id):
    uid = current_uid()
    tweet = Tweet.query.get_or_404(tweet_id)
    if tweet.user_id != uid:
        return jsonify({"error": "You can only delete your own tweets."}), 403
    db.session.delete(tweet)
    db.session.commit()
    return jsonify({"success": True})


@tweets_bp.route("/<int:tweet_id>/like", methods=["POST"])
@jwt_required()
def like_tweet(tweet_id):
    uid = current_uid()
    tweet = Tweet.query.get_or_404(tweet_id)
    existing = Like.query.filter_by(user_id=uid, tweet_id=tweet_id).first()
    if not existing:
        db.session.add(Like(user_id=uid, tweet_id=tweet_id))
        db.session.commit()
        notify(recipient_id=tweet.user_id, actor_id=uid, type_="like", tweet_id=tweet_id)
    return jsonify(tweet.to_dict(uid))


@tweets_bp.route("/<int:tweet_id>/unlike", methods=["POST"])
@jwt_required()
def unlike_tweet(tweet_id):
    uid = current_uid()
    tweet = Tweet.query.get_or_404(tweet_id)
    existing = Like.query.filter_by(user_id=uid, tweet_id=tweet_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    return jsonify(tweet.to_dict(uid))


@tweets_bp.route("/<int:tweet_id>/retweet", methods=["POST"])
@jwt_required()
def retweet(tweet_id):
    uid = current_uid()
    original = Tweet.query.get_or_404(tweet_id)
    root_id = original.original_tweet_id if original.is_retweet else original.id

    existing = Tweet.query.filter_by(
        user_id=uid, original_tweet_id=root_id, is_retweet=True
    ).first()
    if existing:
        return jsonify({"error": "Already retweeted."}), 409

    rt = Tweet(user_id=uid, content="", is_retweet=True, original_tweet_id=root_id)
    db.session.add(rt)
    db.session.commit()

    root_tweet = Tweet.query.get(root_id)
    if root_tweet:
        notify(recipient_id=root_tweet.user_id, actor_id=uid, type_="retweet", tweet_id=root_id)

    return jsonify(rt.to_dict(uid)), 201


@tweets_bp.route("/<int:tweet_id>/retweet", methods=["DELETE"])
@jwt_required()
def undo_retweet(tweet_id):
    uid = current_uid()
    original = Tweet.query.get_or_404(tweet_id)
    root_id = original.original_tweet_id if original.is_retweet else original.id
    existing = Tweet.query.filter_by(
        user_id=uid, original_tweet_id=root_id, is_retweet=True
    ).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    root_tweet = Tweet.query.get(root_id)
    return jsonify(root_tweet.to_dict(uid))
