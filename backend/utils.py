import re
from models import db, User, Mention, Notification

MENTION_RE = re.compile(r"@(\w{1,50})")


def extract_and_store_mentions(tweet, actor_id):
    """Find @username occurrences in tweet.content, link them, and notify."""
    usernames = set(MENTION_RE.findall(tweet.content))
    if not usernames:
        return
    users = User.query.filter(User.username.in_(usernames)).all()
    for user in users:
        if user.id == actor_id:
            continue
        db.session.add(Mention(tweet_id=tweet.id, mentioned_user_id=user.id))
        notify(recipient_id=user.id, actor_id=actor_id, type_="mention", tweet_id=tweet.id)
    db.session.commit()


def notify(recipient_id, actor_id, type_, tweet_id=None):
    if recipient_id == actor_id:
        return
    n = Notification(
        recipient_id=recipient_id,
        actor_id=actor_id,
        type=type_,
        tweet_id=tweet_id,
    )
    db.session.add(n)
    db.session.commit()
