# Phase 2: Frontend Dashboard - Szczegółowa Specyfikacja

**Status:** Ready for implementation
**Estimated Time:** 6h (3h realtime with parallel agents)
**Dependencies:** Phase 1 Backend ✅ COMPLETE

---

## 🎯 Cel Phase 2

Zbudować React dashboard który:
1. Wyświetla 53 projekty w kartach
2. Filtruje/sortuje interaktywnie
3. Pokazuje detail view z radar chart
4. Ma działającego AI Chat Agenta
5. Jest responsive + dark mode

---

## 📐 CZĘŚĆ 1: ARCHITEKTURA FRONTEND

### Tech Stack (zgodnie z DASHBOARD_CONTEXT.md)

```
Frontend:
├─ React 18.3
├─ Vite 6.x
├─ TypeScript 5.x
├─ Tailwind CSS 3.x
├─ shadcn/ui (Radix UI components)
├─ Recharts (radar charts)
├─ Zustand (state management)
└─ React Query (data fetching)
```

### Struktura Folderów

```
dashboard/frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx              # Logo, search, dark mode
│   │   │   ├── Sidebar.tsx             # Filters panel
│   │   │   └── Layout.tsx              # Main layout wrapper
│   │   ├── projects/
│   │   │   ├── ProjectCard.tsx         # Card component
│   │   │   ├── ProjectGrid.tsx         # Grid + pagination
│   │   │   ├── ProjectDetail.tsx       # Detail modal/page
│   │   │   └── ScoreRadar.tsx          # Recharts radar
│   │   ├── chat/
│   │   │   ├── ChatAgent.tsx           # Chat interface
│   │   │   ├── ChatMessage.tsx         # Message bubble
│   │   │   └── ChatInput.tsx           # Input box
│   │   └── ui/                         # shadcn/ui components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── badge.tsx
│   │       ├── input.tsx
│   │       ├── select.tsx
│   │       └── dialog.tsx
│   ├── hooks/
│   │   ├── useProjects.ts              # React Query hook
│   │   ├── useChat.ts                  # Chat hook
│   │   └── useDarkMode.ts              # Dark mode hook
│   ├── store/
│   │   └── filterStore.ts              # Zustand store
│   ├── services/
│   │   └── api.ts                      # API client (axios/fetch)
│   ├── types/
│   │   └── index.ts                    # TypeScript types
│   ├── lib/
│   │   └── utils.ts                    # Utilities (cn, etc.)
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

---

## 📋 CZĘŚĆ 2: SZCZEGÓŁOWE SPECYFIKACJE KOMPONENTÓW

### SPEC 1: TypeScript Types (types/index.ts)

```typescript
// Direct mapping z backend schemas

export interface Project {
  id: string;
  name: string;
  stage: 'idea' | 'prototype' | 'mvp' | 'beta' | 'production' | 'abandoned';
  priority: number; // 0-20
  code_quality_score: number; // 0-10
  languages: string[];
  has_tests: boolean;
  has_ci: boolean;
  fundamental_errors: string[];
  todo_now: string[];
}

export interface ProjectDetail extends Project {
  path: string;
  value_score: number;
  risk_score: number;
  deps: Record<string, string[]>;
  has_readme: boolean;
  has_license: boolean;
  commits_count: number | null;
  branches_count: number | null;
  last_commit_dt: string | null;
  todos: string[];
  todo_next: string[];
  vibesummary_content: string | null;
  created_at: string;
}

export interface Stats {
  total_projects: number;
  by_stage: Record<string, number>;
  avg_code_quality: number;
  projects_with_tests: number;
  projects_with_ci: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  project_id: string | null;
  created_at: string;
}

export interface ChatRequest {
  message: string;
  session_id: string;
  project_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  message_id: string;
}

export interface Filters {
  stage: string | null;
  has_tests: boolean | null;
  has_ci: boolean | null;
  min_quality: number | null;
  search: string;
  sort: 'priority' | 'code_quality_score' | 'name';
  order: 'asc' | 'desc';
}
```

### SPEC 2: API Client (services/api.ts)

```typescript
const API_BASE = 'http://localhost:8000/api';

export const api = {
  // Projects
  async getProjects(filters: Partial<Filters>): Promise<Project[]> {
    const params = new URLSearchParams();
    if (filters.stage) params.set('stage', filters.stage);
    if (filters.has_tests !== null) params.set('has_tests', String(filters.has_tests));
    if (filters.has_ci !== null) params.set('has_ci', String(filters.has_ci));
    if (filters.min_quality) params.set('min_quality', String(filters.min_quality));
    if (filters.search) params.set('search', filters.search);
    if (filters.sort) params.set('sort', filters.sort);
    if (filters.order) params.set('order', filters.order);

    const res = await fetch(`${API_BASE}/projects?${params}`);
    if (!res.ok) throw new Error('Failed to fetch projects');
    return res.json();
  },

  async getProjectDetail(id: string): Promise<ProjectDetail> {
    const res = await fetch(`${API_BASE}/projects/${id}`);
    if (!res.ok) throw new Error('Failed to fetch project');
    return res.json();
  },

  async getStats(): Promise<Stats> {
    const res = await fetch(`${API_BASE}/stats`);
    if (!res.ok) throw new Error('Failed to fetch stats');
    return res.json();
  },

  // Chat
  async sendMessage(req: ChatRequest): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error('Failed to send message');
    return res.json();
  },

  async getChatHistory(sessionId: string): Promise<ChatMessage[]> {
    const res = await fetch(`${API_BASE}/chat/${sessionId}/history`);
    if (!res.ok) throw new Error('Failed to fetch history');
    return res.json();
  },
};
```

### SPEC 3: Zustand Store (store/filterStore.ts)

```typescript
import { create } from 'zustand';

interface FilterState {
  filters: Filters;
  setFilter: <K extends keyof Filters>(key: K, value: Filters[K]) => void;
  resetFilters: () => void;
}

const defaultFilters: Filters = {
  stage: null,
  has_tests: null,
  has_ci: null,
  min_quality: null,
  search: '',
  sort: 'priority',
  order: 'desc',
};

export const useFilterStore = create<FilterState>((set) => ({
  filters: defaultFilters,
  setFilter: (key, value) =>
    set((state) => ({
      filters: { ...state.filters, [key]: value },
    })),
  resetFilters: () => set({ filters: defaultFilters }),
}));
```

### SPEC 4: React Query Hooks (hooks/useProjects.ts)

```typescript
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { useFilterStore } from '@/store/filterStore';

export function useProjects() {
  const { filters } = useFilterStore();

  return useQuery({
    queryKey: ['projects', filters],
    queryFn: () => api.getProjects(filters),
    staleTime: 60000, // 1min cache
  });
}

export function useProjectDetail(id: string) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => api.getProjectDetail(id),
    enabled: !!id,
  });
}

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getStats(),
    staleTime: 300000, // 5min cache
  });
}
```

### SPEC 5: Project Card (components/projects/ProjectCard.tsx)

```typescript
interface Props {
  project: Project;
  onClick: () => void;
}

export function ProjectCard({ project, onClick }: Props) {
  // Stage badge color mapping
  const stageColors = {
    idea: 'bg-gray-500',
    prototype: 'bg-blue-500',
    mvp: 'bg-yellow-500',
    beta: 'bg-orange-500',
    production: 'bg-green-500',
    abandoned: 'bg-red-500',
  };

  return (
    <Card onClick={onClick} className="cursor-pointer hover:shadow-lg transition">
      <CardHeader>
        <div className="flex justify-between items-start">
          <CardTitle className="text-lg">{project.name}</CardTitle>
          <Badge className={stageColors[project.stage]}>{project.stage}</Badge>
        </div>
      </CardHeader>

      <CardContent>
        {/* Code Quality Bar */}
        <div className="mb-2">
          <div className="flex justify-between text-sm mb-1">
            <span>Quality</span>
            <span>{project.code_quality_score.toFixed(1)}/10</span>
          </div>
          <div className="w-full bg-gray-200 rounded h-2">
            <div
              className="bg-blue-500 h-2 rounded"
              style={{ width: `${(project.code_quality_score / 10) * 100}%` }}
            />
          </div>
        </div>

        {/* Languages */}
        <div className="flex gap-1 flex-wrap mb-2">
          {project.languages.map(lang => (
            <Badge key={lang} variant="secondary" className="text-xs">
              {lang}
            </Badge>
          ))}
        </div>

        {/* Flags */}
        <div className="flex gap-2 text-xs">
          {project.has_tests && <span className="text-green-600">✓ Tests</span>}
          {project.has_ci && <span className="text-green-600">✓ CI</span>}
          {!project.has_tests && <span className="text-red-600">✗ Tests</span>}
          {!project.has_ci && <span className="text-red-600">✗ CI</span>}
        </div>

        {/* Fundamental Errors */}
        {project.fundamental_errors.length > 0 && (
          <div className="mt-2 text-xs text-red-600">
            ⚠️ {project.fundamental_errors.length} issues
          </div>
        )}

        {/* Priority */}
        <div className="mt-2 text-xs text-gray-500">
          Priority: {project.priority}/20
        </div>
      </CardContent>
    </Card>
  );
}
```

### SPEC 6: Radar Chart (components/projects/ScoreRadar.tsx)

```typescript
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts';

interface Props {
  project: ProjectDetail;
}

export function ScoreRadar({ project }: Props) {
  // Calculate 6 scores
  const data = [
    { metric: 'Code Quality', score: project.code_quality_score },
    { metric: 'Value', score: project.value_score },
    { metric: 'Deployment', score: 10 - project.risk_score }, // Invert risk
    { metric: 'Documentation', score: project.has_readme ? 8 : 2 },
    { metric: 'Testing', score: project.has_tests ? 8 : 2 },
    { metric: 'CI/CD', score: project.has_ci ? 8 : 2 },
  ];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="metric" />
        <Radar
          dataKey="score"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.6}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
```

### SPEC 7: Chat Component (components/chat/ChatAgent.tsx)

```typescript
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { v4 as uuid } from 'uuid';

const SESSION_ID = uuid(); // Generate on mount

interface Props {
  projectId?: string;
}

export function ChatAgent({ projectId }: Props) {
  const [input, setInput] = useState('');

  // Load history
  const { data: history = [] } = useQuery({
    queryKey: ['chat', SESSION_ID],
    queryFn: () => api.getChatHistory(SESSION_ID),
  });

  // Send message mutation
  const sendMutation = useMutation({
    mutationFn: (message: string) =>
      api.sendMessage({ message, session_id: SESSION_ID, project_id: projectId }),
    onSuccess: () => {
      setInput('');
      // Refetch history
      queryClient.invalidateQueries(['chat', SESSION_ID]);
    },
  });

  const handleSend = () => {
    if (!input.trim()) return;
    sendMutation.mutate(input);
  };

  return (
    <div className="flex flex-col h-[600px]">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {history.map(msg => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        {sendMutation.isPending && (
          <div className="text-gray-500 italic">AI is thinking...</div>
        )}
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Ask about this project..."
            disabled={sendMutation.isPending}
          />
          <Button onClick={handleSend} disabled={sendMutation.isPending}>
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}
```

---

## 🚀 CZĘŚĆ 3: PLAN RÓWNOLEGŁYCH GRUP IMPLEMENTACJI

### Strategia Paralelizacji

**Kluczowe zasady:**
1. **Dependencies first** - setup musi być przed componentami
2. **Niezależne moduły równolegle** - UI components vs hooks vs store
3. **Integration ostatni** - gdy wszystkie części gotowe

### Dependency Graph

```
GROUP 0: Setup (MUST be first, sequential)
  ↓
GROUP 1: Foundation (parallel - no dependencies)
  ├─ Types
  ├─ API Client
  └─ Utils
  ↓
GROUP 2: State & Data (parallel - depends on GROUP 1)
  ├─ Zustand Store
  └─ React Query Hooks
  ↓
GROUP 3: UI Components (parallel - depends on GROUP 2)
  ├─ Layout Components
  ├─ Project Components
  └─ Chat Components
  ↓
GROUP 4: Integration (sequential - depends on GROUP 3)
  └─ App.tsx + main.tsx
```

---

## 📦 GROUP 0: Project Setup (SEQUENTIAL)

**Agent:** single-agent-setup
**Time:** 30min
**Dependencies:** None

### Tasks:

**1. Initialize Vite + React + TypeScript**
```bash
cd /Users/wojciechwiesner/ai/_Borg.tools_scan/dashboard/frontend
npm create vite@latest . -- --template react-ts
```

**2. Install Dependencies**
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "zustand": "^5.0.2",
    "@tanstack/react-query": "^5.62.0",
    "recharts": "^2.15.0",
    "react-router-dom": "^7.1.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.18",
    "@types/react-dom": "^18.3.5",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "^5.6.3",
    "vite": "^6.0.0",
    "tailwindcss": "^3.4.17",
    "postcss": "^8.4.49",
    "autoprefixer": "^10.4.20"
  }
}
```

**3. Configure Tailwind**
```bash
npx tailwindcss init -p
```

```js
// tailwind.config.js
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: { extend: {} },
  plugins: [],
}
```

**4. Install shadcn/ui**
```bash
npx shadcn@latest init
npx shadcn@latest add card badge button input select dialog
```

**5. Setup Path Aliases**
```json
// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

```ts
// vite.config.ts
import path from 'path'
export default defineConfig({
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') }
  }
})
```

**Deliverables:**
- ✅ Vite project initialized
- ✅ All dependencies installed
- ✅ Tailwind configured
- ✅ shadcn/ui components added
- ✅ Path aliases working
- ✅ `npm run dev` starts on :5173

---

## 📦 GROUP 1: Foundation Layer (PARALLEL - 3 agents)

**Time:** 30min
**Dependencies:** GROUP 0 complete

### AGENT 1.1: Types & Utilities

**Files to create:**
1. `src/types/index.ts` - All TypeScript interfaces
2. `src/lib/utils.ts` - Utility functions (cn, formatters)

**SPEC types/index.ts:** (Copy from SPEC 1 above - all interfaces)

**SPEC lib/utils.ts:**
```typescript
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | null): string {
  if (!date) return 'Never';
  return new Date(date).toLocaleDateString();
}

export function getStageColor(stage: string): string {
  const colors = {
    idea: 'bg-gray-500',
    prototype: 'bg-blue-500',
    mvp: 'bg-yellow-500',
    beta: 'bg-orange-500',
    production: 'bg-green-500',
    abandoned: 'bg-red-500',
  };
  return colors[stage as keyof typeof colors] || 'bg-gray-500';
}
```

### AGENT 1.2: API Client

**Files to create:**
1. `src/services/api.ts` - API client (copy from SPEC 2 above)

**Additional:** Add error handling, retry logic

### AGENT 1.3: shadcn/ui Components Setup

**Files to verify/create:**
1. `src/components/ui/card.tsx`
2. `src/components/ui/badge.tsx`
3. `src/components/ui/button.tsx`
4. `src/components/ui/input.tsx`
5. `src/components/ui/select.tsx`
6. `src/components/ui/dialog.tsx`

**Task:** Run shadcn add commands, verify all components exist

---

## 📦 GROUP 2: State & Data Layer (PARALLEL - 2 agents)

**Time:** 30min
**Dependencies:** GROUP 1 complete

### AGENT 2.1: Zustand Store

**Files to create:**
1. `src/store/filterStore.ts` - Filters state (copy from SPEC 3)
2. `src/store/themeStore.ts` - Dark mode state

**SPEC themeStore.ts:**
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ThemeState {
  isDark: boolean;
  toggle: () => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      isDark: false,
      toggle: () => set((state) => ({ isDark: !state.isDark })),
    }),
    { name: 'theme-storage' }
  )
);
```

### AGENT 2.2: React Query Hooks

**Files to create:**
1. `src/hooks/useProjects.ts` - Projects hooks (copy from SPEC 4)
2. `src/hooks/useChat.ts` - Chat hooks

**SPEC useChat.ts:**
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { useState } from 'react';
import { v4 as uuid } from 'uuid';

export function useChat(projectId?: string) {
  const [sessionId] = useState(() => uuid());
  const queryClient = useQueryClient();

  const history = useQuery({
    queryKey: ['chat', sessionId],
    queryFn: () => api.getChatHistory(sessionId),
    initialData: [],
  });

  const sendMessage = useMutation({
    mutationFn: (message: string) =>
      api.sendMessage({ message, session_id: sessionId, project_id: projectId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', sessionId] });
    },
  });

  return { history: history.data, sendMessage, sessionId };
}
```

---

## 📦 GROUP 3: UI Components (PARALLEL - 3 agents)

**Time:** 2h
**Dependencies:** GROUP 2 complete

### AGENT 3.1: Layout Components

**Files to create:**
1. `src/components/layout/Header.tsx`
2. `src/components/layout/Sidebar.tsx`
3. `src/components/layout/Layout.tsx`

**SPEC Header.tsx:**
```typescript
import { useThemeStore } from '@/store/themeStore';
import { useFilterStore } from '@/store/filterStore';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export function Header() {
  const { isDark, toggle } = useThemeStore();
  const { filters, setFilter } = useFilterStore();

  return (
    <header className="border-b p-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">🤖 Borg Scanner</h1>
        <Input
          placeholder="Search projects..."
          value={filters.search}
          onChange={e => setFilter('search', e.target.value)}
          className="w-64"
        />
      </div>

      <Button onClick={toggle} variant="outline">
        {isDark ? '☀️' : '🌙'}
      </Button>
    </header>
  );
}
```

**SPEC Sidebar.tsx:**
```typescript
import { useFilterStore } from '@/store/filterStore';
import { useStats } from '@/hooks/useProjects';
import { Select } from '@/components/ui/select';
import { Button } from '@/components/ui/button';

export function Sidebar() {
  const { filters, setFilter, resetFilters } = useFilterStore();
  const { data: stats } = useStats();

  return (
    <aside className="w-64 border-r p-4 space-y-4">
      <div>
        <h3 className="font-semibold mb-2">Filters</h3>

        {/* Stage filter */}
        <Select
          value={filters.stage || ''}
          onValueChange={val => setFilter('stage', val || null)}
        >
          <option value="">All Stages</option>
          {stats?.by_stage && Object.keys(stats.by_stage).map(stage => (
            <option key={stage} value={stage}>
              {stage} ({stats.by_stage[stage]})
            </option>
          ))}
        </Select>

        {/* Boolean filters */}
        <label className="flex items-center gap-2 mt-2">
          <input
            type="checkbox"
            checked={filters.has_tests || false}
            onChange={e => setFilter('has_tests', e.target.checked ? true : null)}
          />
          Has Tests
        </label>

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={filters.has_ci || false}
            onChange={e => setFilter('has_ci', e.target.checked ? true : null)}
          />
          Has CI
        </label>

        {/* Min quality slider */}
        <div className="mt-2">
          <label className="text-sm">Min Quality: {filters.min_quality || 0}</label>
          <input
            type="range"
            min="0"
            max="10"
            step="0.5"
            value={filters.min_quality || 0}
            onChange={e => setFilter('min_quality', Number(e.target.value) || null)}
            className="w-full"
          />
        </div>

        <Button onClick={resetFilters} variant="outline" className="w-full mt-4">
          Reset Filters
        </Button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="text-sm space-y-1">
          <div>Total: {stats.total_projects}</div>
          <div>Avg Quality: {stats.avg_code_quality.toFixed(1)}</div>
          <div>With Tests: {stats.projects_with_tests}</div>
          <div>With CI: {stats.projects_with_ci}</div>
        </div>
      )}
    </aside>
  );
}
```

**SPEC Layout.tsx:**
```typescript
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { useThemeStore } from '@/store/themeStore';
import { useEffect } from 'react';

export function Layout({ children }: { children: React.ReactNode }) {
  const { isDark } = useThemeStore();

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
  }, [isDark]);

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-black dark:text-white">
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
```

### AGENT 3.2: Project Components

**Files to create:**
1. `src/components/projects/ProjectCard.tsx` - (copy from SPEC 5)
2. `src/components/projects/ProjectGrid.tsx`
3. `src/components/projects/ProjectDetail.tsx`
4. `src/components/projects/ScoreRadar.tsx` - (copy from SPEC 6)

**SPEC ProjectGrid.tsx:**
```typescript
import { useProjects } from '@/hooks/useProjects';
import { ProjectCard } from './ProjectCard';
import { useState } from 'react';
import { Dialog } from '@/components/ui/dialog';
import { ProjectDetail } from './ProjectDetail';

export function ProjectGrid() {
  const { data: projects = [], isLoading } = useProjects();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  if (isLoading) return <div>Loading...</div>;

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.map(project => (
          <ProjectCard
            key={project.id}
            project={project}
            onClick={() => setSelectedId(project.id)}
          />
        ))}
      </div>

      <Dialog open={!!selectedId} onOpenChange={() => setSelectedId(null)}>
        {selectedId && <ProjectDetail projectId={selectedId} />}
      </Dialog>
    </>
  );
}
```

**SPEC ProjectDetail.tsx:**
```typescript
import { useProjectDetail } from '@/hooks/useProjects';
import { ScoreRadar } from './ScoreRadar';
import { Badge } from '@/components/ui/badge';
import { ChatAgent } from '@/components/chat/ChatAgent';

export function ProjectDetail({ projectId }: { projectId: string }) {
  const { data: project, isLoading } = useProjectDetail(projectId);

  if (isLoading || !project) return <div>Loading...</div>;

  return (
    <div className="grid grid-cols-2 gap-6 p-6">
      {/* Left: Project Info */}
      <div className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold">{project.name}</h2>
          <p className="text-sm text-gray-500">{project.path}</p>
        </div>

        <ScoreRadar project={project} />

        <div>
          <h3 className="font-semibold mb-2">TODO Now</h3>
          <ul className="space-y-1">
            {project.todo_now.map((todo, i) => (
              <li key={i} className="text-sm">• {todo}</li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="font-semibold mb-2">Fundamental Errors</h3>
          <div className="flex gap-2">
            {project.fundamental_errors.map((err, i) => (
              <Badge key={i} variant="destructive">{err}</Badge>
            ))}
          </div>
        </div>

        {project.vibesummary_content && (
          <details>
            <summary className="cursor-pointer font-semibold">VibeSummary</summary>
            <pre className="text-xs mt-2 bg-gray-100 p-2 rounded overflow-auto max-h-64">
              {project.vibesummary_content}
            </pre>
          </details>
        )}
      </div>

      {/* Right: Chat */}
      <div>
        <h3 className="font-semibold mb-2">Ask AI About This Project</h3>
        <ChatAgent projectId={project.id} />
      </div>
    </div>
  );
}
```

### AGENT 3.3: Chat Components

**Files to create:**
1. `src/components/chat/ChatAgent.tsx` - (copy from SPEC 7)
2. `src/components/chat/ChatMessage.tsx`
3. `src/components/chat/ChatInput.tsx`

**SPEC ChatMessage.tsx:**
```typescript
import { ChatMessage as ChatMessageType } from '@/types';

export function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] p-3 rounded-lg ${
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-gray-200 dark:bg-gray-700 text-black dark:text-white'
        }`}
      >
        <div className="text-sm whitespace-pre-wrap">{message.content}</div>
        <div className="text-xs opacity-70 mt-1">
          {new Date(message.created_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
```

---

## 📦 GROUP 4: Integration (SEQUENTIAL)

**Time:** 30min
**Dependencies:** GROUP 3 complete

### AGENT 4.1: App Integration

**Files to create/update:**
1. `src/App.tsx`
2. `src/main.tsx`
3. `src/index.css`

**SPEC App.tsx:**
```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { ProjectGrid } from '@/components/projects/ProjectGrid';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Layout>
        <ProjectGrid />
      </Layout>
    </QueryClientProvider>
  );
}
```

**SPEC main.tsx:**
```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

**SPEC index.css:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
  }
}
```

---

## 🎯 EXECUTION PLAN - PARALLEL AGENTS

### Timeline (3h realtime)

```
Hour 0:00-0:30  GROUP 0 (Setup)           [1 agent sequential]
       ↓
Hour 0:30-1:00  GROUP 1 (Foundation)      [3 agents parallel]
       ↓
Hour 1:00-1:30  GROUP 2 (State & Data)    [2 agents parallel]
       ↓
Hour 1:30-3:30  GROUP 3 (UI Components)   [3 agents parallel]
       ↓
Hour 3:30-4:00  GROUP 4 (Integration)     [1 agent sequential]
```

### Agent Commands

**GROUP 0: Setup**
```
Create Vite React TypeScript project in dashboard/frontend.
Install: react, react-dom, zustand, @tanstack/react-query, recharts, react-router-dom.
Setup Tailwind CSS.
Install shadcn/ui: card, badge, button, input, select, dialog.
Configure path aliases (@/*).
Verify: npm run dev works on :5173.
```

**GROUP 1.1: Types**
```
Create src/types/index.ts with TypeScript interfaces matching backend schemas.
Create src/lib/utils.ts with cn(), formatDate(), getStageColor().
Deliverable: 2 files, TypeScript compiles.
```

**GROUP 1.2: API Client**
```
Create src/services/api.ts with fetch-based API client.
Endpoints: getProjects(), getProjectDetail(), getStats(), sendMessage(), getChatHistory().
Base URL: http://localhost:8000/api.
Add error handling.
```

**GROUP 1.3: shadcn Components**
```
Verify shadcn/ui components exist in src/components/ui/.
Run: npx shadcn@latest add card badge button input select dialog.
Ensure all 6 components present.
```

**GROUP 2.1: Zustand**
```
Create src/store/filterStore.ts for filters state.
Create src/store/themeStore.ts for dark mode (persisted).
Test: stores can be imported without errors.
```

**GROUP 2.2: React Query**
```
Create src/hooks/useProjects.ts with useProjects(), useProjectDetail(), useStats().
Create src/hooks/useChat.ts with useChat() hook.
Use @tanstack/react-query.
Depends on: api client, types.
```

**GROUP 3.1: Layout**
```
Create src/components/layout/Header.tsx (search + dark mode).
Create src/components/layout/Sidebar.tsx (filters + stats).
Create src/components/layout/Layout.tsx (wrapper).
Use: Zustand stores, shadcn components.
```

**GROUP 3.2: Projects**
```
Create src/components/projects/ProjectCard.tsx.
Create src/components/projects/ProjectGrid.tsx.
Create src/components/projects/ProjectDetail.tsx.
Create src/components/projects/ScoreRadar.tsx with Recharts.
Use: hooks, types, shadcn.
```

**GROUP 3.3: Chat**
```
Create src/components/chat/ChatAgent.tsx.
Create src/components/chat/ChatMessage.tsx.
Create src/components/chat/ChatInput.tsx.
Use: useChat hook, types.
```

**GROUP 4: Integration**
```
Create src/App.tsx with QueryClientProvider + Layout + ProjectGrid.
Update src/main.tsx with React 18 root render.
Update src/index.css with Tailwind directives.
Verify: npm run dev shows dashboard with all 53 projects.
Test: filters work, detail modal opens, chat sends messages.
```

---

## ✅ Acceptance Criteria Phase 2

- [ ] Dashboard shows all 53 projects in cards
- [ ] Filters work (stage, has_tests, has_ci, min_quality, search)
- [ ] Sort works (priority, code_quality_score, name)
- [ ] Click card opens detail modal
- [ ] Detail modal shows radar chart with 6 scores
- [ ] Detail modal shows TODO list
- [ ] Detail modal shows fundamental errors
- [ ] Chat agent accepts messages
- [ ] Chat agent displays history
- [ ] Chat with project context includes project data
- [ ] Dark mode toggle works
- [ ] Layout is responsive (mobile + desktop)
- [ ] No TypeScript errors
- [ ] No console errors
- [ ] Frontend connects to backend on :8000

---

## 📊 Summary

**Total Files:** ~25 TypeScript/TSX files
**Total Lines:** ~2000
**Groups:** 5 (1 sequential setup + 3 parallel + 1 sequential integration)
**Agents:** 11 total (1 + 3 + 2 + 3 + 1 + 1 final test)
**Estimated Time:** 6h solo, 3h with parallel agents

**Next:** Run implementation groups in order.

---

**Created by The Collective Borg.tools** 🤖
