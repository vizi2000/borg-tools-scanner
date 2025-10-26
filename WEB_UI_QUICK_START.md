# Web UI v2.0 - Quick Start Guide

## Installation & Launch

```bash
# 1. Install Flask
pip install flask

# 2. Ensure you have project data
# Use sample data for testing:
cp borg_dashboard_sample.json borg_dashboard.json

# 3. Start the server
python3 web_ui.py

# 4. Open your browser
# Navigate to: http://localhost:5001
```

---

## Features at a Glance

### 📊 Main Dashboard
- **Statistics Cards**: Total projects, deployment-ready count, Borg fit projects, avg code quality
- **Project Cards**: Click any project to view details
- **Multi-Filter System**: Search, stage, deployment status, Borg fit score
- **Real-time Search**: Type to instantly filter projects

### 🎯 Project Details Modal (4 Tabs)

#### 1️⃣ Overview Tab
- Project information (path, languages, commits, branches)
- Feature badges (README, License, Tests, CI/CD)
- Description and monetization analysis
- Dependencies breakdown
- TODO list

#### 2️⃣ Scores Dashboard Tab
- **Radar Chart** showing 6 categories:
  - Code Quality
  - Deployment Readiness
  - Documentation
  - Borg.tools Fit
  - MVP Proximity
  - Monetization Viability
- **Score Breakdown** with detailed metrics

#### 3️⃣ Deployment Tab
- **Traffic Light Status**:
  - 🟢 Ready to Deploy (score ≥ 7)
  - 🟡 Warning (score 4-6)
  - 🔴 Blocked (score < 4)
- **MVP Checklist** with progress bar
- **Critical Blockers** list
- **Next Steps** recommendations

#### 4️⃣ VibeSummary Tab
- Full markdown-rendered VibeSummary
- Auto-loads from project directory
- Fallback message if not found

### 💬 AI Assistant
- Chat interface at bottom of page
- Ask questions about your projects
- Powered by LLM (requires OPENROUTER_API_KEY)

---

## Using the Filters

### Search Projects
Type in the search box to filter by project name in real-time.

### Filter by Stage
- All Stages
- Prototype
- MVP
- Beta
- Production

### Filter by Deployment Status
- All Status
- Ready (🟢)
- Warning (🟡)
- Blocked (🔴)

### Filter by Borg.tools Fit
- All Scores
- ≥ 7 (High Fit) - Shows only projects well-suited for Borg.tools
- ≥ 5 (Medium Fit)

**Tip:** Combine multiple filters for advanced queries!

---

## Understanding the Scores

### Code Quality (0-10)
Based on value_score, linting results, and code metrics.
- **High (7+)**: Production-ready code
- **Medium (4-6)**: Needs improvement
- **Low (<4)**: Requires significant work

### Deployment Readiness (0-10)
Inverse of risk_score - lower risk = higher readiness.
- **7+**: Ready to deploy ✅
- **4-6**: Review required ⚠️
- **<4**: Deployment blocked ❌

### Documentation (0-10)
Based on README presence and quality.
- **7+**: Well documented
- **<7**: Needs documentation

### Borg.tools Fit (0-10)
Suitability for Borg.tools ecosystem.
- **7+**: Excellent fit for ecosystem
- **<7**: May need adjustments

### MVP Proximity (0-10)
How close to Minimum Viable Product.
- **Prototype**: 3
- **MVP**: 7
- **Beta**: 9
- **Production**: 10

### Monetization Viability (0-10)
Potential for revenue generation.
- **High (7+)**: Clear monetization path
- **Low (<4)**: Needs business model

---

## API Endpoints

### `/api/projects`
Get all projects with processed scores.

```bash
curl http://localhost:5001/api/projects
```

### `/api/project/<name>`
Get detailed information for a specific project.

```bash
curl http://localhost:5001/api/project/sample_project_1
```

### `/api/vibesummary/<name>`
Get VibeSummary markdown content.

```bash
curl http://localhost:5001/api/vibesummary/sample_project_1
```

### `/api/chat` (POST)
Chat with AI assistant about projects.

```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Which projects are ready to deploy?"}'
```

---

## Testing

Run the test suite to verify everything works:

```bash
python3 test_web_ui_standalone.py
```

Expected output:
```
✅ ALL TESTS PASSED

📊 New Features Implemented:
  ✓ 6-Category Scores Dashboard with Radar Chart
  ✓ VibeSummary Viewer with Markdown Rendering
  ✓ Deployment Status Widget (Traffic Light)
  ✓ Filter by Borg.tools Fit Score
  ✓ Bootstrap 5 Upgrade
  ✓ Modern Card-Based Layout
  ✓ Statistics Dashboard
```

---

## Sample Data

The included `borg_dashboard_sample.json` contains 5 diverse projects:

1. **sample_project_1** - Beta stage, high value (9/10)
2. **legacy_project** - Prototype, needs work (4/10)
3. **borg_tools_integration** - MVP, excellent fit (8/10)
4. **ml_experiment** - Prototype, experimental (6/10)
5. **microservice_starter** - Production, ready to ship (9/10)

Use this to explore all features without running a full scan.

---

## Keyboard Shortcuts

- **Search**: Start typing to activate search
- **Enter**: Apply filters
- **Esc**: Close project modal
- **Tab**: Navigate between tabs in modal

---

## Tips & Tricks

### Finding Deployment-Ready Projects
1. Set "Deployment" filter to "Ready"
2. Sort by "Borg Fit" to find best candidates
3. Check Deployment tab for any last-minute blockers

### Identifying High-Value Projects
1. Set "Borg Fit" filter to "≥ 7"
2. Look for high Code Quality scores
3. Check Monetization Viability in Scores tab

### Cleaning Up Technical Debt
1. Set "Deployment" filter to "Blocked"
2. Review Critical Blockers in Deployment tab
3. Follow Next Steps recommendations

---

## Troubleshooting

**Problem:** Page is blank
**Solution:** Check that `borg_dashboard.json` exists and contains valid JSON

**Problem:** Charts not showing
**Solution:** Check browser console - ensure CDN resources loaded

**Problem:** Filters don't work
**Solution:** Enable JavaScript, try refreshing the page

**Problem:** VibeSummary shows "Loading..."
**Solution:** VibeSummary.md doesn't exist - run scanner with `--deep-scan`

---

## Next Steps

1. **Run a Full Scan**: Use `borg_tools_scan.py` on your projects
2. **Generate VibeSummaries**: Enable deep-scan mode
3. **Configure AI Assistant**: Set OPENROUTER_API_KEY environment variable
4. **Deploy**: Move to production server for team access

---

**Happy Analyzing! 🚀**

Created by The Collective Borg.tools
