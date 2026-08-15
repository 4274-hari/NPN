from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.String(280), default="")
    avatar_url = db.Column(db.String(300), default="")
    banner_url = db.Column(db.String(300), default="")
    location = db.Column(db.String(100), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tweets = db.relationship("Tweet", backref="author", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def followers_count(self):
        return Follow.query.filter_by(followed_id=self.id).count()

    def following_count(self):
        return Follow.query.filter_by(follower_id=self.id).count()

    def is_followed_by(self, user_id):
        if not user_id:
            return False
        return Follow.query.filter_by(follower_id=user_id, followed_id=self.id).first() is not None

    def to_dict(self, current_user_id=None):
        return {
            "id": self.id,
            "username": self.username,
            "displayName": self.display_name,
            "email": self.email,
            "bio": self.bio,
            "avatarUrl": self.avatar_url,
            "bannerUrl": self.banner_url,
            "location": self.location,
            "createdAt": self.created_at.isoformat(),
            "followersCount": self.followers_count(),
            "followingCount": self.following_count(),
            "tweetsCount": self.tweets.count(),
            "isFollowedByMe": self.is_followed_by(current_user_id),
            "isMe": current_user_id == self.id,
        }

    def to_public_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "displayName": self.display_name,
            "avatarUrl": self.avatar_url,
        }


class Follow(db.Model):
    __tablename__ = "follows"

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("follower_id", "followed_id", name="uq_follow"),)


class Tweet(db.Model):
    __tablename__ = "tweets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("tweets.id"), nullable=True)
    original_tweet_id = db.Column(db.Integer, db.ForeignKey("tweets.id"), nullable=True)
    is_retweet = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    replies = db.relationship(
        "Tweet",
        backref=db.backref("parent", remote_side=[id]),
        foreign_keys=[parent_id],
        lazy="dynamic",
    )

    def likes_count(self):
        return Like.query.filter_by(tweet_id=self.id).count()

    def retweets_count(self):
        return Tweet.query.filter_by(original_tweet_id=self.id, is_retweet=True).count()

    def replies_count(self):
        return Tweet.query.filter_by(parent_id=self.id).count()

    def is_liked_by(self, user_id):
        if not user_id:
            return False
        return Like.query.filter_by(user_id=user_id, tweet_id=self.id).first() is not None

    def is_retweeted_by(self, user_id):
        if not user_id:
            return False
        return Tweet.query.filter_by(
            user_id=user_id, original_tweet_id=self.id, is_retweet=True
        ).first() is not None

    def to_dict(self, current_user_id=None):
        author = User.query.get(self.user_id)
        original = None
        content = self.content
        display_author = author
        base_tweet = self

        if self.is_retweet and self.original_tweet_id:
            original_tweet = Tweet.query.get(self.original_tweet_id)
            if original_tweet:
                base_tweet = original_tweet
                content = original_tweet.content
                original = User.query.get(original_tweet.user_id).to_public_dict()

        return {
            "id": self.id,
            "author": display_author.to_public_dict() if display_author else None,
            "content": content,
            "parentId": base_tweet.parent_id,
            "isRetweet": self.is_retweet,
            "retweetedBy": author.to_public_dict() if self.is_retweet else None,
            "originalTweetId": base_tweet.id if self.is_retweet else None,
            "createdAt": base_tweet.created_at.isoformat(),
            "likesCount": base_tweet.likes_count(),
            "retweetsCount": base_tweet.retweets_count(),
            "repliesCount": base_tweet.replies_count(),
            "isLiked": base_tweet.is_liked_by(current_user_id),
            "isRetweeted": base_tweet.is_retweeted_by(current_user_id),
            "mentions": [
                m.mentioned_user_id for m in Mention.query.filter_by(tweet_id=base_tweet.id).all()
            ],
        }


class Like(db.Model):
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey("tweets.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "tweet_id", name="uq_like"),)


class Mention(db.Model):
    __tablename__ = "mentions"

    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.Integer, db.ForeignKey("tweets.id"), nullable=False)
    mentioned_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # like, comment, follow, retweet, mention
    tweet_id = db.Column(db.Integer, db.ForeignKey("tweets.id"), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        actor = User.query.get(self.actor_id)
        return {
            "id": self.id,
            "type": self.type,
            "actor": actor.to_public_dict() if actor else None,
            "tweetId": self.tweet_id,
            "isRead": self.is_read,
            "createdAt": self.created_at.isoformat(),
        }
