# 🌐 BORG TOOLS SCANNER - WEB TOOL ARCHITECTURE

**Date:** November 5, 2025
**Status:** Design Phase
**Goal:** Transform Borg Scanner into full-featured web application with local folder scanning

---

## 🎯 EXECUTIVE SUMMARY

**Question:** Is it possible to make Borg Scanner work as a web tool with local folder access?

**Answer:** **YES! 100% możliwe!**

We'll use **Hybrid Architecture**:
- Backend FastAPI runs locally (localhost:8000) with filesystem access
- Frontend React SPA runs in browser (localhost:3000)
- User can configure folders to scan via web UI
- Real-time updates through WebSocket
- Beautiful modern interface

---

## 🏗️ ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                     USER'S BROWSER                          │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  REACT FRONTEND (localhost:3000 or served by FastAPI) │ │
│  │                                                        │ │
│  │  • Project Dashboard (grid/list view)                 │ │
│  │  • Deep Analysis Button (with WebSocket progress)     │ │
│  │  • Chat V3 Interface (8 functions, Minimax M2)        │ │
│  │  • Notes Panel (Markdown editor)                      │ │
│  │  • Screenshot Gallery (4 strategies)                  │ │
│  │  • Folder Configuration (select paths to scan)        │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↕ HTTP/WebSocket                  │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND (localhost:8000)               │
│                                                             │
│  20 API Endpoints:                                          │
│  • GET  /api/projects (list, filter, sort)                 │
│  • GET  /api/projects/{id} (detail)                        │
│  • POST /api/projects/scan (trigger new scan)              │
│  • POST /api/projects/{id}/deep-analysis                   │
│  • GET  /api/analysis/{task_id}/status                     │
│  • WS   /ws/analysis/{task_id} (progress)                  │
│  • POST /api/chat (Minimax M2 with 8 functions)            │
│  • GET  /api/chat/{session_id}/history                     │
│  • GET  /api/projects/{id}/notes                           │
│  • POST /api/projects/{id}/notes                           │
│  • PUT  /api/notes/{id}                                    │
│  • DELETE /api/notes/{id}                                  │
│  • POST /api/projects/{id}/notes/quick                     │
│  • GET  /api/config (get scan paths)                       │
│  • PUT  /api/config (update scan paths)                    │
│  • GET  /api/stats                                         │
│  • GET  /health                                            │
│                                                             │
│  Full filesystem access to local machine!                  │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│              LOCAL FILESYSTEM                               │
│                                                             │
│  /Users/yourname/Projects/                                  │
│  ├── project-1/                                             │
│  ├── project-2/                                             │
│  └── project-3/                                             │
│                                                             │
│  SQLite Database: borg.db                                   │
│  Scanner modules: code_analyzer, doc_analyzer, etc.         │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ WHY THIS WORKS

### 1. **Backend ma pełny dostęp do filesystem**
- FastAPI działa jako lokalny proces na maszynie użytkownika
- Może czytać/pisać dowolne pliki
- Może uruchamiać `borg_tools_scan.py` w tle
- Nie ma limitów bezpieczeństwa przeglądarki

### 2. **Frontend to piękny interface w przeglądarce**
- React + Tailwind CSS + shadcn/ui components
- WebSocket dla real-time progress
- Może być hostowany lokalnie lub zdalnie
- Komunikuje się z backend przez API

### 3. **Zero upload - wszystko lokalne**
- Kod nigdy nie opuszcza maszyny użytkownika
- Szybkie skanowanie (brak przesyłania plików)
- Prywatność zachowana
- Może skanować setki projektów

---

## 🚀 IMPLEMENTATION PLAN

### PHASE 1: Configuration API (2 godziny)

**Endpoint:** `GET/PUT /api/config`

**File:** `dashboard/backend/api/config.py`

```python
from pydantic import BaseModel

class ScanConfig(BaseModel):
    scan_paths: list[str]  # ["/Users/name/Projects", "/Users/name/Work"]
    exclude_patterns: list[str]  # ["node_modules", ".venv", "dist"]
    auto_scan_on_startup: bool = False
    scan_interval_hours: int = 0  # 0 = manual only

@router.get("/config")
def get_config(db: Session = Depends(get_db)):
    """Get current scan configuration."""
    # Load from database or config file
    return {"scan_paths": [...], "exclude_patterns": [...]}

@router.put("/config")
def update_config(config: ScanConfig, db: Session = Depends(get_db)):
    """Update scan configuration."""
    # Save to database or config file
    # Validate paths exist
    return {"message": "Configuration updated"}
```

**Frontend Component:** `<ConfigurationPanel />`
- Input fields for paths
- "Browse" button (uses `<input type="file" webkitdirectory>` for folder picker)
- Exclude patterns (chips input)
- Auto-scan toggle

---

### PHASE 2: Scan Trigger API (3 godziny)

**Endpoint:** `POST /api/projects/scan`

**File:** `dashboard/backend/api/projects.py` (add new endpoint)

```python
@router.post("/projects/scan")
async def trigger_scan(
    background_tasks: BackgroundTasks,
    force_full: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Trigger new portfolio scan.

    - force_full: Re-scan all projects (ignore cache)
    - Returns task_id for progress tracking
    """
    task_id = str(uuid.uuid4())

    # Create ScanTask (new model)
    task = ScanTask(id=task_id, status="queued", progress=0.0)
    db.add(task)
    db.commit()

    # Queue background task
    background_tasks.add_task(run_portfolio_scan, task_id, force_full, db_path)

    return {"task_id": task_id, "status": "queued"}

async def run_portfolio_scan(task_id: str, force_full: bool, db_path: str):
    """Background task: Run borg_tools_scan.py."""
    import subprocess

    # Update task status
    # ...

    # Run scanner as subprocess
    result = subprocess.run([
        "python3",
        "borg_tools_scan.py",
        "--root", scan_paths[0],
        "--use-llm", "openrouter"
    ], capture_output=True, text=True)

    # Parse output and update database
    # Send WebSocket updates
    # ...
```

**WebSocket:** `/ws/scan/{task_id}`
- Progress: "Scanning project 15/185..."
- Status: "Running code analysis..."
- ETA: "~2 minutes remaining"

**Frontend Component:** `<ScanButton />`
- "Scan Portfolio" button with loading state
- Progress bar during scan
- Real-time log output (WebSocket)

---

### PHASE 3: Frontend Dashboard (8 godzin)

**Technology Stack:**
```json
{
  "framework": "React 18 + TypeScript",
  "bundler": "Vite",
  "ui": "shadcn/ui + Tailwind CSS",
  "state": "Zustand or React Query",
  "routing": "React Router v6",
  "websocket": "native WebSocket API",
  "http": "fetch or axios"
}
```

**File Structure:**
```
dashboard/frontend/
├── src/
│   ├── components/
│   │   ├── ProjectGrid.tsx          # Main dashboard grid
│   │   ├── ProjectCard.tsx          # Single project card
│   │   ├── ProjectDetailModal.tsx   # Full project details
│   │   ├── DeepAnalysisButton.tsx   # Trigger deep analysis
│   │   ├── WebSocketProgress.tsx    # Real-time progress bar
│   │   ├── ChatInterface.tsx        # Chat V3 with Minimax M2
│   │   ├── NotesPanel.tsx           # Markdown notes editor
│   │   ├── ScreenshotGallery.tsx    # Image carousel
│   │   ├── FilterBar.tsx            # Stage/language filters
│   │   ├── SortDropdown.tsx         # Sort by priority/value/risk
│   │   └── ConfigurationPanel.tsx   # Folder path config
│   │
│   ├── hooks/
│   │   ├── useProjects.ts           # Fetch projects
│   │   ├── useDeepAnalysis.ts       # Trigger analysis + WebSocket
│   │   ├── useChat.ts               # Chat V3 integration
│   │   ├── useNotes.ts              # CRUD for notes
│   │   └── useWebSocket.ts          # Generic WebSocket hook
│   │
│   ├── api/
│   │   └── client.ts                # Axios/fetch wrapper
│   │
│   ├── types/
│   │   └── index.ts                 # TypeScript types
│   │
│   ├── App.tsx                      # Main app component
│   └── main.tsx                     # Entry point
│
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

**Key Components:**

#### 1. `<ProjectGrid />` - Main Dashboard
```tsx
interface Project {
  id: string;
  name: string;
  stage: "idea" | "prototype" | "mvp" | "beta" | "production" | "abandoned";
  priority: number;
  value_score: number;
  risk_score: number;
  code_quality_score: number;
  languages: string[];
  has_tests: boolean;
  has_ci: boolean;
  fundamental_errors: string[];
  todo_now: string[];
}

export function ProjectGrid() {
  const { projects, isLoading } = useProjects();
  const [filters, setFilters] = useState({});

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {projects.map(project => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
}
```

#### 2. `<DeepAnalysisButton />` - Trigger Analysis
```tsx
export function DeepAnalysisButton({ projectId }: { projectId: string }) {
  const { trigger, progress, phase, isRunning } = useDeepAnalysis(projectId);

  return (
    <button onClick={trigger} disabled={isRunning}>
      {isRunning ? (
        <div>
          <ProgressBar value={progress * 100} />
          <span>{phase}</span>
        </div>
      ) : (
        "Deep Analysis"
      )}
    </button>
  );
}
```

#### 3. `<ChatInterface />` - Chat V3
```tsx
export function ChatInterface({ projectId }: { projectId: string }) {
  const { messages, sendMessage, isLoading, suggestedQuestions } = useChat(projectId);
  const [input, setInput] = useState("");

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        {messages.map(msg => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
      </div>

      <div className="flex gap-2">
        {suggestedQuestions.map(q => (
          <button key={q} onClick={() => sendMessage(q)}>
            {q}
          </button>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === "Enter" && sendMessage(input)}
          placeholder="Zapytaj o projekt..."
        />
        <button onClick={() => sendMessage(input)} disabled={isLoading}>
          Send
        </button>
      </div>
    </div>
  );
}
```

#### 4. `<NotesPanel />` - Markdown Notes
```tsx
import MarkdownEditor from "react-markdown-editor-lite";
import ReactMarkdown from "react-markdown";

export function NotesPanel({ projectId }: { projectId: string }) {
  const { notes, createNote, updateNote, deleteNote } = useNotes(projectId);
  const [content, setContent] = useState("");
  const [noteType, setNoteType] = useState<NoteType>("general");

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        {notes.map(note => (
          <NoteCard key={note.id} note={note} onDelete={deleteNote} />
        ))}
      </div>

      <div className="border-t pt-4">
        <select value={noteType} onChange={e => setNoteType(e.target.value)}>
          <option value="general">General</option>
          <option value="decision">Decision</option>
          <option value="idea">Idea</option>
          <option value="blocker">Blocker</option>
          <option value="todo">TODO</option>
        </select>

        <MarkdownEditor
          value={content}
          onChange={({ text }) => setContent(text)}
          renderHTML={text => <ReactMarkdown>{text}</ReactMarkdown>}
        />

        <button onClick={() => createNote({ content, note_type: noteType })}>
          Save Note
        </button>
      </div>
    </div>
  );
}
```

---

### PHASE 4: WebSocket Integration (2 godziny)

**Custom Hook:** `useWebSocket.ts`

```typescript
export function useWebSocket(url: string) {
  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => setData(JSON.parse(event.data));
    ws.onclose = () => setIsConnected(false);
    ws.onerror = (error) => console.error("WebSocket error:", error);

    return () => ws.close();
  }, [url]);

  return { data, isConnected };
}
```

**Usage:**
```typescript
function DeepAnalysisProgress({ taskId }: { taskId: string }) {
  const { data } = useWebSocket(`ws://localhost:8000/api/ws/analysis/${taskId}`);

  if (!data) return null;

  return (
    <div>
      <ProgressBar value={data.progress * 100} />
      <p>{data.phase}</p>
      {data.type === "complete" && <p>✅ Analysis complete!</p>}
      {data.type === "error" && <p>❌ Error: {data.error}</p>}
    </div>
  );
}
```

---

## 📦 DEPLOYMENT OPTIONS

### Option A: Electron App (Desktop Application)
**Pros:**
- Native app experience
- Auto-start backend on launch
- System tray integration
- Auto-updates

**Cons:**
- Larger download size
- Platform-specific builds

**Setup:**
```bash
npm install electron electron-builder
```

---

### Option B: Docker Compose (Easiest for non-technical users)
**File:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - /Users/yourname/Projects:/projects:ro  # Read-only access
      - ./borg.db:/app/borg.db
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}

  frontend:
    build: ./dashboard/frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

**Run:**
```bash
docker-compose up -d
# Open http://localhost:3000
```

---

### Option C: Standalone Python Script (Current Approach - Enhanced)
**File:** `start_borg_web.sh`

```bash
#!/bin/bash
# Start backend
cd dashboard/backend
../../venv/bin/uvicorn main:app --port 8000 &
BACKEND_PID=$!

# Start frontend (if using dev server)
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ Borg Tools Scanner is running!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop..."

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
```

**Run:**
```bash
chmod +x start_borg_web.sh
./start_borg_web.sh
```

---

## 🎨 UI/UX MOCKUP

### Main Dashboard View
```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 BORG TOOLS SCANNER              [Scan Portfolio] [⚙ Config] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Filters: [All Stages ▼] [All Languages ▼] [Has Tests? ▼]     │
│  Sort by: [Priority ▼] [↓ Desc]               Search: [____]  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Project A    │  │ Project B    │  │ Project C    │         │
│  │ Stage: MVP   │  │ Stage: Beta  │  │ Stage: Idea  │         │
│  │ Priority: 18 │  │ Priority: 15 │  │ Priority: 12 │         │
│  │ Quality: 8.5 │  │ Quality: 7.2 │  │ Quality: 5.0 │         │
│  │              │  │              │  │              │         │
│  │ 🐍 Python    │  │ ⚛️  React    │  │ 🦀 Rust      │         │
│  │ 🟢 Tests     │  │ 🔴 No Tests  │  │ 🟢 Tests     │         │
│  │ 🟢 CI        │  │ 🟢 CI        │  │ 🔴 No CI     │         │
│  │              │  │              │  │              │         │
│  │ [Deep Scan]  │  │ [Deep Scan]  │  │ [Deep Scan]  │         │
│  │ [View Notes] │  │ [View Notes] │  │ [View Notes] │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  Showing 3 of 185 projects                       [< 1 2 3 >]  │
└─────────────────────────────────────────────────────────────────┘
```

### Project Detail Modal
```
┌─────────────────────────────────────────────────────────────────┐
│ PROJECT: Borg Tools Scanner                              [✕]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 📊 Overview  |  💬 Chat  |  📝 Notes  |  🖼️  Screenshots       │
│ ─────────────────────────────────────────────────────────────  │
│                                                                 │
│ Stage: MVP           Priority: 18         Quality: 8.5/10      │
│ Value: 9.2/10        Risk: 3.1/10                              │
│                                                                 │
│ Languages: Python, JavaScript, TypeScript                       │
│ Dependencies: fastapi, react, vite, sqlalchemy                 │
│                                                                 │
│ ✅ Has README    ✅ Has Tests    ✅ Has CI    ✅ Has License    │
│                                                                 │
│ Fundamental Errors: None                                        │
│                                                                 │
│ TODO Now (Top 5):                                              │
│ • [45min] Add tests for deep analysis module                   │
│ • [60min] Implement WebSocket reconnection logic               │
│ • [90min] Create Docker Compose setup                          │
│ • [45min] Add error boundaries in React components             │
│ • [60min] Write API documentation                              │
│                                                                 │
│ [🔍 Deep Analysis]  [💬 Chat with AI]  [📝 Add Note]          │
│                                                                 │
│ Git Stats: 142 commits, 5 branches, last commit: 2h ago        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚧 TECHNICAL CHALLENGES & SOLUTIONS

### Challenge 1: Folder Picker in Browser
**Problem:** Browser security doesn't allow direct filesystem access

**Solution A:** Use `<input type="file" webkitdirectory>` attribute
- User selects folder through native dialog
- Upload entire folder structure (for remote hosting scenario)

**Solution B:** Backend-driven configuration
- User enters path as text: "/Users/name/Projects"
- Backend validates path exists
- No upload needed (for local hosting scenario)

**✅ Recommended:** Solution B for local hosting (our primary use case)

---

### Challenge 2: Large Portfolio Scans (185 projects)
**Problem:** Scanning takes 44-154 minutes with LLM

**Solution:**
- On-demand deep analysis per project (14-49 seconds)
- Quick scan on startup (just file structure, no LLM)
- Background scanning with WebSocket progress
- Cache results (1-hour TTL)

---

### Challenge 3: Screenshot Generation Requires Running Apps
**Problem:** Strategy 2 (real screenshots) needs to start dev servers

**Solution:**
- Make it optional (checkbox: "Capture real screenshots")
- Default to Strategy 1 (extract from README) + Strategy 3 (AI mockup)
- Run server in Docker container for safety
- Timeout after 60 seconds if server doesn't start

---

### Challenge 4: Multiple Users Scanning Same Machine
**Problem:** Concurrent scans could conflict

**Solution:**
- Single scan queue (one at a time)
- Lock file: `/tmp/borg_scanner.lock`
- Return 409 Conflict if scan already running
- Show queue position in UI

---

## 📊 ESTIMATED TIMELINE

| Phase | Task | Time | Complexity |
|-------|------|------|------------|
| 1 | Configuration API | 2h | Low |
| 2 | Scan Trigger API | 3h | Medium |
| 3 | React Dashboard | 8h | High |
| 4 | WebSocket Integration | 2h | Medium |
| 5 | Notes Panel | 3h | Medium |
| 6 | Chat Interface | 4h | Medium |
| 7 | Screenshot Gallery | 2h | Low |
| 8 | Deployment Setup | 2h | Low |
| 9 | Testing & Bug Fixes | 4h | Medium |
| **TOTAL** | **Full Web Tool** | **30h** | **3-4 days** |

---

## ✅ SUCCESS CRITERIA

1. **User can configure scan paths via web UI** ✅
2. **User can trigger portfolio scan with progress tracking** ✅
3. **Dashboard displays all projects with filtering/sorting** ✅
4. **Deep Analysis works with WebSocket real-time updates** ✅
5. **Chat V3 integrated with 8 functions** ✅
6. **Notes system with Markdown editor** ✅
7. **Screenshot gallery shows 1-4 images per project** ✅
8. **Works on localhost without internet connection** ✅
9. **No code leaves the machine (privacy guaranteed)** ✅
10. **Beautiful, modern, ADHD-friendly UI** ✅

---

## 🎁 BONUS FEATURES (Future)

- **Auto-sync with GitHub:** Detect new repos, auto-add to portfolio
- **Team collaboration:** Multi-user notes, shared analysis
- **Export reports:** PDF/Markdown portfolio reports
- **Project comparison:** Side-by-side comparison view
- **Trends dashboard:** Track portfolio health over time
- **Browser extension:** Quick-add projects from GitHub/GitLab
- **Mobile app:** View portfolio on phone (read-only)

---

## 🔧 QUICK START (After Implementation)

```bash
# 1. Install dependencies
cd dashboard/backend && ../../venv/bin/pip install -r requirements.txt
cd dashboard/frontend && npm install

# 2. Configure scan paths
# Edit dashboard/backend/config.json:
{
  "scan_paths": ["/Users/yourname/Projects"],
  "exclude_patterns": ["node_modules", ".venv", "dist"]
}

# 3. Start backend
cd dashboard/backend
../../venv/bin/uvicorn main:app --reload --port 8000

# 4. Start frontend
cd dashboard/frontend
npm run dev  # Opens http://localhost:3000

# 5. Open browser and enjoy! 🎉
```

---

## 📞 SUMMARY

**Answer:** TAK, jest w 100% możliwe zrobienie Borg Scanner jako web tool z lokalnym dostępem do folderów!

**Architecture:** Hybrid (local backend + browser frontend)
**Timeline:** 30 godzin (3-4 dni)
**Complexity:** Medium (większość kodu już gotowa w V3.0)
**Privacy:** Perfekcyjna (kod nie opuszcza maszyny)
**User Experience:** Profesjonalna (React + Tailwind + shadcn/ui)

**Created by The Collective Borg.tools**
