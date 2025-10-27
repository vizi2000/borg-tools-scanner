# Borg Scanner Dashboard

**Interactive web dashboard with AI Chat Agent for project intelligence.**

## Quick Start for New Session

See **[DASHBOARD_CONTEXT.md](../DASHBOARD_CONTEXT.md)** for complete implementation guide.

## Phase 1: Backend (START HERE)

```bash
cd /Users/wojciechwiesner/ai/_Borg.tools_scan/dashboard/backend

# Create FastAPI backend
# See DASHBOARD_CONTEXT.md for detailed requirements
```

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite + WebSocket
- **Frontend:** React 18 + Vite + TypeScript + Tailwind + shadcn/ui
- **AI:** OpenRouter (llama-4-scout:free, deepseek-r1:free)
- **Deploy:** Docker Compose → dashboard.borg.tools

## OpenRouter API Key

```
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
```

## Data Sources

- VibeIntelligence: `/Users/wojciechwiesner/ai/VibeIntelligence/borg_dashboard.json`
- MCP-Vibe: `/Users/wojciechwiesner/ai/MCP-Vibe/borg_dashboard.json`
- Finco_scraper: `/Users/wojciechwiesner/ai/Finco_scraper/borg_dashboard.json`

**Total Projects:** 68

## Success Criteria

- [ ] Backend API serving 68 projects
- [ ] AI Chat responding to questions
- [ ] Frontend dashboard with cards
- [ ] Dark mode + mobile responsive
- [ ] Deployed to dashboard.borg.tools

---

**Created:** The Collective Borg.tools
