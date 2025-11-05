# Borg Scanner Dashboard - Backend

FastAPI backend for Borg Tools Scanner Dashboard with AI Chat Agent.

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/wojciechwiesner/ai/_Borg.tools_scan/dashboard/backend
pip3 install -r requirements.txt
```

### 2. Import Data

```bash
python3 -m scripts.import_data
```

This will:
- Create SQLite database (`borg.db`)
- Import 53 projects from `borg_dashboard.json`
- Extract code quality scores

### 3. Run Server

```bash
uvicorn main:app --reload --port 8000
```

Or:

```bash
python3 main.py
```

Server will start on `http://localhost:8000`

## API Endpoints

### Projects

- `GET /api/projects` - List all projects
  - Query params: `stage`, `has_tests`, `has_ci`, `min_quality`, `search`, `sort`, `order`, `limit`, `offset`
- `GET /api/projects/{id}` - Get project details + VibeSummary
- `GET /api/stats` - Portfolio statistics

### Chat

- `POST /api/chat` - Send message to AI agent
  - Body: `{message: str, session_id: str, project_id?: str}`
- `GET /api/chat/{session_id}/history` - Get chat history
- `DELETE /api/chat/{session_id}` - Clear session

### Health

- `GET /health` - Health check
- `GET /` - API info

## Testing

```bash
# Health check
curl http://localhost:8000/health

# List projects
curl http://localhost:8000/api/projects | jq

# Get project details
curl http://localhost:8000/api/projects/{id} | jq

# Get stats
curl http://localhost:8000/api/stats | jq

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Jak naprawić security w backend?",
    "session_id": "test-session-123"
  }' | jq
```

## Configuration

Environment variables (optional, defaults in `config.py`):

```bash
OPENROUTER_API_KEY=sk-or-v1-...
DATABASE_URL=sqlite:///./borg.db
```

## Tech Stack

- **FastAPI** 0.115.0 - Web framework
- **SQLAlchemy** 2.0.36 - ORM
- **SQLite** - Database
- **Pydantic** 2.10.0 - Data validation
- **httpx** 0.27.2 - HTTP client for OpenRouter API
- **Uvicorn** 0.32.0 - ASGI server

## Database Schema

### Projects Table
- 23 columns: id, name, path, stage, scores, flags, git stats, todos, raw_data
- Indexed on: name, stage, priority
- Unique constraint: path

### ChatMessages Table
- 6 columns: id, session_id, role, content, project_id, created_at
- Indexed on: session_id
- Foreign key: project_id → projects.id

## OpenRouter Models

- Primary: `meta-llama/llama-4-scout:free`
- Fallback: `deepseek/deepseek-r1:free`

---

**Created by The Collective Borg.tools**
