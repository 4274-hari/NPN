# NPN Social Copilot

React frontend, FastAPI backend, and MongoDB connection base.

## Start

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

## Demo users database

Registration is intentionally disabled. Import these supplied files into MongoDB before logging in. They contain plain-text demo passwords, so only use them for local demonstrations.

```powershell
mongoimport --uri "mongodb://localhost:27017" --db npn_social_clone --collection social_users --jsonArray --file data/social_users.json
mongoimport --uri "mongodb://localhost:27017" --db npn_social_copilot --collection company_users --jsonArray --file data/company_users.json
```

Social login: `@nikhil`, `@nandha`, `@neha`, or `@arjun` (password: `password123`).

Company login: `admin@npn.demo` or `support@npn.demo` (password: `password123`).
