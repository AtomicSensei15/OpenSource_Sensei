# OpenSource Sensei - Agentic AI for Contributors

An intelligent agentic AI system that guides code contributors through various functionalities including setup, code review, documentation, testing, and real-time assistance.

## Key Features

- 🤖 **Multi-Agent System**: Specialized agents for different aspects of contribution guidance
- 🔧 **Automatic Setup & Onboarding**: Guides new contributors through repo structure and guidelines
- 🔍 **Code Review Agent**: Analyzes code changes and suggests improvements
- 📦 **Dependency Analysis**: Manages dependencies and build processes
- 🌐 **Multi-Language Support**: Handles various programming languages
- 🔍 **Research Agent**: Provides relevant resources and examples
- 💬 **Real-Time Q&A**: Contextual assistance and coaching

## Architecture

```text
├── backend/              # FastAPI backend with AI agents
├── frontend/             # React frontend application  
├── agents/              # Core agent implementations
├── database/            # Database models and migrations
├── storage/             # File storage for repositories
├── config/              # Configuration files
## Fallback In-Memory Storage Mode

If MongoDB is unreachable at startup, the API now switches to an in-memory storage layer:

└── deploy/              # Deployment scripts and Docker files
```

## Getting Started

### Installation

1. Clone the repository
2. Set up backend: `cd backend && pip install -r requirements.txt`
3. Set up frontend: `cd frontend && npm install`
4. Configure database and environment variables
5. Run the application: `docker-compose up`

## Usage

1. Upload a GitHub repository link or ZIP/RAR file
2. The system analyzes the codebase structure
3. Interact with specialized agents for guidance
4. Receive personalized feedback and recommendations

## Environment Configuration

Create a local `.env` file (never commit real secrets) based on the provided template.

1. Copy the example file:
   ```bash
   copy .env.example .env   # Windows
   # or
   cp .env.example .env      # macOS/Linux
   ```
2. Fill in the required values:

| Variable | Description | Required | Notes |
|----------|-------------|----------|-------|
| `GITHUB_API_KEY` | GitHub Personal Access Token | Optional (recommended) | Needed for higher rate limits / private repos |
| `STACKOVERFLOW_API_KEY` | Stack Exchange API key | Optional | Improves quota for research queries |
| `GOOGLE_CSE_API_KEY` | Google Programmable Search API key | Optional | Needed if enabling Google search |
| `GOOGLE_CSE_ID` | Custom Search Engine ID (cx) | Optional | Pair with API key |

If you don't provide keys, related features will gracefully degrade or use unauthenticated quotas.

Security tips:
- Never commit `.env` (it's already in `.gitignore`).
- Use least-privilege scopes for tokens.
- Rotate keys regularly.
- For deployment, set these variables via your platform's secret manager (Docker secrets, GitHub Actions secrets, etc.).

## Frontend ↔ Backend Connection

The frontend (Vite React app under `frontend/user_fe`) expects the backend FastAPI server to expose its routes under the prefix defined in `backend/app/core/config.py` (default: `/api/v1`).

### Quick Start (Development)
1. Start backend (with auto-reload):

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend listens on: <http://localhost:8000>

2. Start frontend:

```bash
cd frontend/user_fe
npm install
npm run dev
```

Frontend dev server (Vite) listens on: <http://localhost:5173>

### Configure API Base URL
The frontend uses an environment variable `VITE_API_BASE_URL` (falls back to `http://localhost:8000/api/v1`). Create `frontend/user_fe/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```
Restart the Vite dev server after adding the file.

### Health Check Endpoints
- Root (no prefix): `GET http://localhost:8000/health`
- Prefixed (frontend base path): `GET http://localhost:8000/api/v1/health`

The prefixed version was added so the frontend call `axios.get('/health')` with baseURL ending in `/api/v1` succeeds.

### CORS
Default allowed origins (can override with `CORS_ORIGINS` env, comma-separated):

```text
http://localhost:3000, http://localhost:8080, http://localhost:5173
```
If you use a different port, export `CORS_ORIGINS` before starting backend:
```bash
set CORS_ORIGINS=http://localhost:5174
```
(Use `export` instead of `set` on macOS/Linux.)

### Docker Compose Notes
`docker-compose.yml` exposes backend on host port 8000. If you run the frontend outside Docker, point it to `http://localhost:8000/api/v1`.

### Troubleshooting
| Symptom | Cause | Fix |
|--------|-------|-----|
| 404 on `/health` in browser console | Prefixed route missing (older code) | Update code / ensure backend restarted |
| CORS error (blocked by CORS policy) | Origin not in `cors_origins` | Add origin via env `CORS_ORIGINS` or edit settings |
| Network error / ECONNREFUSED | Backend not running | Start backend / check port 8000 availability |
| Mixed Content (HTTPS frontend) | Backend over HTTP with secure context | Use HTTPS proxy or dev both on HTTP |
| Wrong base URL in production build | Missing env var at build time | Set `VITE_API_BASE_URL` before `npm run build` |

### Verifying Connectivity
From frontend dev console:
```js
fetch(import.meta.env.VITE_API_BASE_URL + '/health')
   .then(r => r.json())
   .then(console.log)
```
You should see JSON with `prefixed: true`.

## MongoDB Configuration

The backend attempts to connect to MongoDB on startup but will continue in a degraded (no-DB) mode if unavailable.

Environment variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `MONGODB_URI` | Connection string (can omit db name) | `mongodb://localhost:27017` |
| `MONGODB_DATABASE` | Desired database name | `opensourcesensei` |

Rules & behavior:

- If `MONGODB_DATABASE` contains invalid characters (e.g. `.`) it is sanitized (non-alphanumeric replaced with `_`).
- If no db name provided in URI and no explicit env, defaults to `opensourcesensei`.
- On connection failure the app logs an error and still serves API endpoints that don't require persistence.

Local test (PowerShell):

```powershell
$env:MONGODB_URI="mongodb://localhost:27017"
$env:MONGODB_DATABASE="opensourcesensei_dev"
python -m uvicorn backend.main:app --reload
```

Docker Compose already supplies a Mongo service; ensure the container is healthy before expecting successful DB operations.

### Fallback In-Memory Storage Mode

If MongoDB is unreachable at startup, the API now switches to an in-memory storage layer:

- CRUD endpoints still work for the lifetime of the process.
- Data is NOT persisted; restart clears everything.
- Mode visible at: `/api/v1/mode` (returns `{ "mode": "memory" | "mongo" }`).
- Once started in memory mode it will not auto-promote to Mongo without a restart.

Limitations in memory mode:

- No cross-process sharing.
- No advanced querying beyond simple filters / regex.
- Not suitable for production; for development convenience only.

To force Mongo usage, ensure the database is reachable before starting the server.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and submission process.

## License

This project is licensed under the MIT License - see LICENSE file for details.
