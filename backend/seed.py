"""Run with: python seed.py
Creates demo users (including nexora, nikhil, nandha, neha used in the
@mention example) plus a handful of tweets so the app isn't empty on first run.
"""
from app import create_app
from models import db, User, Tweet, Follow, Like

app = create_app()

DEMO_USERS = [
    ("nexora", "Nexora", "AI & product builder. Making things people love."),
    ("nikhil", "Nikhil Rao", "Full-stack dev. Coffee-powered."),
    ("nandha", "Nandha Kumar", "Designer. Pixels & typography nerd."),
    ("neha", "Neha Sharma", "Photographer | traveler | storyteller."),
    ("arjun", "Arjun Mehta", "Building Nextweet. Open source enthusiast."),
]

SAMPLE_TWEETS = [
    ("nexora", "Just shipped a new feature on Nextweet! #nextweet #buildinpublic"),
    ("nikhil", "Debugging is like being a detective in a crime movie where you are also the murderer. 😅"),
    ("nandha", "Good design is invisible. #design"),
    ("neha", "Sunset over the mountains today was unreal. #photography #travel"),
    ("arjun", "Hey @nexora, loving what you're building! #technology"),
]


def run():
    with app.app_context():
        if User.query.first():
            print("Database already has data. Skipping seed.")
            return

        users = {}
        for username, display_name, bio in DEMO_USERS:
            u = User(
                username=username,
                email=f"{username}@nextweet.demo",
                display_name=display_name,
                bio=bio,
                avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}",
            )
            u.set_password("password123")
            db.session.add(u)
            users[username] = u
        db.session.commit()

        # everyone follows nexora, nexora follows everyone back
        for username, u in users.items():
            if username != "nexora":
                db.session.add(Follow(follower_id=u.id, followed_id=users["nexora"].id))
                db.session.add(Follow(follower_id=users["nexora"].id, followed_id=u.id))
        db.session.commit()

        for username, content in SAMPLE_TWEETS:
            t = Tweet(user_id=users[username].id, content=content)
            db.session.add(t)
        db.session.commit()

        print("Seeded demo users: nexora, nikhil, nandha, neha, arjun (password: password123)")


if __name__ == "__main__":
    run()
