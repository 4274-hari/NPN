# NPN Social Copilot - Base

React frontend, FastAPI backend, and MongoDB connection base. Your `models`, `rag`, and `llm` files stay separate from this server foundation.

## Prerequisites

- Node.js 18+
- Python 3.11+
- A running MongoDB instance (local or Atlas)

## Start the backend

```powershell
cd backend
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Confirm it at `http://localhost:8000/health` and open interactive API docs at `http://localhost:8000/docs`.

## Start the frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Layout

- `frontend/` - React + Vite application.
- `backend/main.py` - FastAPI application, CORS, and API endpoints.
- `backend/config.py` - environment settings.
- `backend/database.py` - MongoDB connection helpers.
- `models/`, `rag/`, `llm/` - keep your ML/RAG/LLM files separate; add routes that call them when ready.
