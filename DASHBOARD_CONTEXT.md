# Context for New Session: Borg Scanner Dashboard Implementation

## 🎯 Mission
Implement **interactive web dashboard with AI Chat Agent** for Borg Tools Scanner.

## 📦 Current State

### ✅ Completed Work
1. **Borg Scanner V2.0** - Fully functional CLI scanner
   - GitHub: https://github.com/vizi2000/borg-tools-scanner
   - 39 E2E tests (100% pass)
   - Deep code analysis (AST, security, complexity)
   - Multi-model LLM pipeline (OpenRouter)
   - VibeSummary.md generation
   - 800+ lines VibeIntelligence integration docs

2. **Projects Scanned** (68 total)
   - VibeIntelligence: 8 sub-projects
   - MCP-Vibe: 7 sub-projects
   - Finco_scraper: 53 projects
   - All with VibeSummary.md generated

3. **Output Files Available**
   - `/Users/wojciechwiesner/ai/VibeIntelligence/BORG_INDEX.md`
   - `/Users/wojciechwiesner/ai/VibeIntelligence/borg_dashboard.json`
   - `/Users/wojciechwiesner/ai/MCP-Vibe/BORG_INDEX.md`
   - `/Users/wojciechwiesner/ai/Finco_scraper/BORG_INDEX.md`
   - Individual `VibeSummary.md` for each project

## 🎨 What We're Building

**Interactive Dashboard with:**
- 📊 Project cards grid (scores, status, filters)
- 🎯 Sorting/filtering (priority, quality, stage)
- 📈 Visualizations (radar charts for 6-category scores)
- 💬 **AI Chat Agent** (OpenRouter integration)
- 📝 Live TODO lists from MVP checklists
- 🔴 Security alerts panel
- 📦 Deployment status tracker
- 🌙 Dark mode
- 📱 Mobile-responsive

## 🏗️ Approved Tech Stack

**Frontend:**
- React 18 + Vite + TypeScript
- Tailwind CSS + shadcn/ui
- Recharts (visualizations)
- React Query (data fetching)
- Zustand (state management)

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy + SQLite
- WebSocket (streaming chat)
- OpenRouter API (models: llama-4-scout, deepseek-r1)

**Deployment:**
- Docker Compose
- Target: dashboard.borg.tools
- SSH: vizi@borg.tools

## 📋 Implementation Plan (20h total)

### Phase 1: Backend API (6h) ← **START HERE**
**Goal:** Working FastAPI with Projects API + Chat Agent

#### 1.1 Setup (1h)
```bash
cd /Users/wojciechwiesner/ai/_Borg.tools_scan/dashboard/backend
```

**Files to create:**
- `main.py` - FastAPI app
- `models/database.py` - SQLAlchemy models
- `models/schemas.py` - Pydantic schemas
- `api/projects.py` - CRUD endpoints
- `api/chat.py` - Chat endpoint
- `services/chat_agent.py` - OpenRouter integration
- `requirements.txt`

**Database Schema:**
```python
class Project(Base):
    id: UUID (PK)
    name: str
    path: str
    code_quality_score: float
    deployment_readiness_score: float
    documentation_score: float
    vibecodibility_score: float
    stage: str  # idea/prototype/mvp/beta/production
    priority: int
    last_scanned: datetime
    vibesummary_path: str
    raw_data: JSON  # Full borg_dashboard.json entry

class ChatMessage(Base):
    id: UUID (PK)
    session_id: UUID
    role: str  # user/assistant
    content: str
    project_context: UUID (FK → Project, nullable)
    created_at: datetime
```

#### 1.2 Projects API (2h)
**Endpoints:**
```python
GET /api/projects
  ?filter=stage,priority,quality
  &sort=priority,quality,date
  &search=name
  → Returns: List[ProjectSchema]

GET /api/projects/{id}
  → Returns: ProjectDetailSchema (includes VibeSummary content)

POST /api/projects/import
  body: { borg_dashboard_json_path: str }
  → Imports existing scan results

POST /api/projects/{id}/rescan
  → Triggers borg_tools_scan.py on project
```

#### 1.3 Chat Agent (3h)
**Service: `services/chat_agent.py`**

**Key Features:**
- OpenRouter integration
- Context building from project data
- Streaming responses (WebSocket)
- Memory/session management

**Chat Capabilities:**
1. Answer questions about specific project
2. Compare multiple projects
3. Generate action plans
4. Explain technical metrics
5. Suggest priorities

**Prompt Template:**
```python
SYSTEM_PROMPT = """You are a senior software architect analyzing projects.

AVAILABLE DATA:
{project_data}

CONTEXT: User asked: {user_question}

Provide actionable, concise advice with time estimates."""
```

**Models to use:**
- Primary: `meta-llama/llama-4-scout:free` (works, tested)
- Fallback: `deepseek/deepseek-r1:free`
- **Avoid:** `mistralai/mistral-small-3.1:free` (broken), `llama-4-maverick:free` (moderation issues)

**Endpoint:**
```python
POST /api/chat
  body: {
    message: str,
    session_id: UUID,
    project_id: UUID (optional)
  }
  → Returns: { response: str, session_id: UUID }

WebSocket /ws/chat/{session_id}
  → Streaming responses
```

### Phase 2: Frontend Dashboard (8h)

#### 2.1 Setup React + Vite (1h)
```bash
cd /Users/wojciechwiesner/ai/_Borg.tools_scan/dashboard/frontend
npm create vite@latest . -- --template react-ts
npm install tailwindcss @radix-ui/react-* recharts zustand @tanstack/react-query
```

#### 2.2 Layout (1h)
- Header (Borg logo, search, dark mode toggle)
- Sidebar (filters)
- Main content (projects grid)

#### 2.3 Projects Dashboard (3h)
**Components:**
- `ProjectCard.tsx` - Card with scores, status badges
- `ProjectGrid.tsx` - Grid layout with filtering
- `FilterSidebar.tsx` - Stage, priority, quality filters
- `SearchBar.tsx`

**Features:**
- Click card → open detail view
- Re-scan button
- Sort by: priority, quality, name, date

#### 2.4 Project Detail View (2h)
**Components:**
- `ScoreRadar.tsx` - 6-category radar chart
- `MVPChecklist.tsx` - Interactive checklist
- `SecurityAlerts.tsx` - Red/yellow/green alerts
- `DeploymentStatus.tsx` - Status tracker

#### 2.5 Visualizations (1h)
- Portfolio overview chart
- Score distribution
- Priority heatmap

### Phase 3: AI Chat Agent UI (4h)

#### 3.1 Chat Component (2h)
**`ChatAgent.tsx`:**
- Message list (scrollable)
- Input box
- Send button
- Typing indicator
- Markdown rendering (code syntax highlighting)

#### 3.2 WebSocket Integration (1h)
- Real-time streaming responses
- Auto-scroll to latest message

#### 3.3 Context Awareness (1h)
- "Ask about this project" button in detail view
- Auto-include project data in context
- Suggested questions:
  - "How do I fix security issues?"
  - "What should I prioritize?"
  - "Compare this with [other project]"

### Phase 4: Integration (2h)

#### 4.1 Data Loading (1h)
- Import existing `borg_dashboard.json`
- Sync VibeSummary.md files
- Real-time updates on rescan

#### 4.2 Polish (1h)
- Loading states
- Error handling
- Animations (framer-motion)
- Mobile responsive
- Keyboard shortcuts

### Phase 5: Deployment (1h)

#### 5.1 Docker Compose (30min)
```yaml
version: '3.8'
services:
  frontend:
    build: ./dashboard/frontend
    ports:
      - "3000:80"

  backend:
    build: ./dashboard/backend
    ports:
      - "8000:8000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    volumes:
      - ./data:/app/data
```

#### 5.2 Deploy to borg.tools (30min)
```bash
ssh vizi@borg.tools
cd /home/vizi/borg-scanner-dashboard
git pull
docker-compose up -d
```

**Nginx config:**
```nginx
server {
    listen 80;
    server_name dashboard.borg.tools;

    location / {
        proxy_pass http://localhost:3000;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🔑 Key Resources

**Existing Files:**
- Scanner: `/Users/wojciechwiesner/ai/_Borg.tools_scan/borg_tools_scan.py`
- Modules: `/Users/wojciechwiesner/ai/_Borg.tools_scan/modules/`
- Data: `/Users/wojciechwiesner/ai/*/borg_dashboard.json`

**OpenRouter API Key:**
```
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
```

**Working Models:**
- ✅ `meta-llama/llama-4-scout:free`
- ✅ `deepseek/deepseek-r1:free`
- ❌ `mistralai/mistral-small-3.1:free` (404 error)
- ❌ `meta-llama/llama-4-maverick:free` (moderation issues)

## 📊 Sample Data

**VibeIntelligence Backend:**
- Code Quality: 6.7/10
- Deployment: 7/10
- Documentation: 2/10
- 57 API endpoints (0 documented)
- 2 HIGH security issues
- MVP time: 3.5h

**Top Priority Projects:**
1. VibeIntelligence/backend (Priority 2/20)
2. VibeIntelligence/frontend (Priority 2/20)
3. agricultural-machinery-valuation-bot (Priority 4/20)

## 🎯 Success Criteria

**Backend:**
- [ ] FastAPI running on :8000
- [ ] GET /api/projects returns all 68 projects
- [ ] GET /api/projects/{id} returns VibeSummary content
- [ ] POST /api/chat returns AI response
- [ ] WebSocket streaming works
- [ ] SQLite database created

**Frontend:**
- [ ] Dashboard shows all projects in cards
- [ ] Filters/sort work
- [ ] Click project → detail view
- [ ] Radar chart displays 6 scores
- [ ] Chat agent responds to questions
- [ ] Dark mode toggle works
- [ ] Mobile responsive

**Integration:**
- [ ] Chat agent can answer: "How to fix backend security?"
- [ ] Re-scan button triggers borg_tools_scan.py
- [ ] Real-time updates when scan completes

## 🚀 Getting Started

**Command for new session:**
```
I need you to implement Phase 1 of the Borg Scanner Dashboard.

Context: Full project details in DASHBOARD_CONTEXT.md

Task:
1. Create FastAPI backend in dashboard/backend/
2. Implement database models (Project, ChatMessage)
3. Create Projects API (GET /api/projects, GET /api/projects/{id})
4. Implement Chat Agent service with OpenRouter
5. Add POST /api/chat endpoint
6. Import existing borg_dashboard.json data

Working directory: /Users/wojciechwiesner/ai/_Borg.tools_scan

OpenRouter API Key: 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

Use models: meta-llama/llama-4-scout:free, deepseek/deepseek-r1:free

Acceptance criteria:
- FastAPI running on localhost:8000
- GET /api/projects returns 68 projects from scans
- POST /api/chat responds with AI advice
- All endpoints tested with curl/httpie

Act as senior backend developer. Be precise. Think hard.
```

---

**Created:** 2025-10-28
**Author:** The Collective Borg.tools
**Status:** Ready for implementation
