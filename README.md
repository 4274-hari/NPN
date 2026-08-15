# Nextweet

A full-stack Twitter/X-style social media app.

- **Frontend:** React (Vite) + Tailwind CSS + React Router + Axios
- **Backend:** Flask + SQLAlchemy + Flask-JWT-Extended + Flask-Bcrypt
- **Database:** SQLite (file-based, zero setup)

## Features
- Register/login (JWT auth)
- Profiles: avatar, bio, followers/following, edit profile
- Tweet: create, delete, reply/comment, like/unlike, repost/retweet
- Follow/unfollow users
- Home feed (people you follow), Explore feed, hashtag trending, search (users + tweets)
- Notifications (like, comment, retweet, follow, mention) with polling
- **@mention autocomplete**: type `@n` in the composer or a reply box to see a
  live dropdown (avatar + name + username) of matching users. Navigate with
  Arrow Up/Down, select with Enter/Tab/click. Mentions are stored server-side
  and linked to real user accounts, and trigger a notification.
- Fully responsive 3-column layout (desktop/tablet) that collapses to a
  single-column + bottom nav on mobile.

## Project structure
```
nextweet/
  backend/     Flask API (SQLite database is created automatically)
  frontend/    React app (Vite)
```

## Running locally

### 1. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
python seed.py       # creates demo users: nexora, nikhil, nandha, neha, arjun
python app.py         # runs on http://localhost:5000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev            # runs on http://localhost:5173
```

The frontend reads the API base URL from `frontend/.env` (`VITE_API_URL`,
defaults to `http://localhost:5000/api`).

### Demo accounts
All demo accounts use the password `password123`:
`nexora`, `nikhil`, `nandha`, `neha`, `arjun`

## Notes on the @mention feature
- `GET /api/users/mention-suggest?q=<partial>` powers the dropdown — it matches
  on username or display name, case-insensitively, prefix-first.
- The composer (`frontend/src/components/MentionTextarea.jsx`) tracks the `@`
  fragment immediately before the cursor, debounces the lookup, and replaces
  just that fragment on selection — so mentions can appear anywhere in the text.
- On submit, the backend (`backend/utils.py`) re-parses `@username` tokens from
  the final tweet content, links them to real `User` rows in a `Mention` table,
  and fires a `mention` notification to each mentioned user.

## Production notes
This is a development-ready build. Before deploying:
- Swap SQLite for PostgreSQL (change `SQLALCHEMY_DATABASE_URI` in `backend/config.py`)
- Serve Flask with a production WSGI server (gunicorn/uwsgi) behind a reverse proxy
- Set real `SECRET_KEY`/`JWT_SECRET_KEY` via environment variables
- Run `npm run build` in `frontend/` and serve the static `dist/` output (e.g. via Nginx or a CDN)
- Add rate limiting and stricter CORS origins for the API
