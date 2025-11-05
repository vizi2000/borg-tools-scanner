# Notes API - Usage Examples

## Overview
The Notes System provides full CRUD operations for project annotations with markdown support, type classification, tagging, and quick note templates.

## Endpoints

### 1. GET /api/projects/{project_id}/notes
Get all notes for a project, optionally filtered by type.

**Query Parameters:**
- `note_type` (optional): Filter by type (general, decision, idea, blocker, todo)

**Examples:**
```bash
# Get all notes for a project
curl http://localhost:8000/api/projects/abc-123/notes

# Get only blocker notes
curl http://localhost:8000/api/projects/abc-123/notes?note_type=blocker
```

**Response:**
```json
[
  {
    "id": "note-uuid-1",
    "project_id": "abc-123",
    "content": "## Implementation Note\n\nNeed to refactor auth module",
    "note_type": "todo",
    "tags": ["refactoring", "auth"],
    "created_at": "2025-11-05T10:30:00Z",
    "updated_at": null
  }
]
```

---

### 2. POST /api/projects/{project_id}/notes
Create a new note for a project.

**Request Body:**
```json
{
  "content": "## Architecture Decision\n\nDecided to use PostgreSQL for analytics",
  "note_type": "decision",
  "tags": ["architecture", "database"]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/projects/abc-123/notes \
  -H "Content-Type: application/json" \
  -d '{
    "content": "## Blocker\n\nAPI rate limit reached",
    "note_type": "blocker",
    "tags": ["urgent", "api"]
  }'
```

**Response:** (201 Created)
```json
{
  "id": "note-uuid-new",
  "project_id": "abc-123",
  "content": "## Blocker\n\nAPI rate limit reached",
  "note_type": "blocker",
  "tags": ["urgent", "api"],
  "created_at": "2025-11-05T11:00:00Z",
  "updated_at": null
}
```

---

### 3. PUT /api/notes/{note_id}
Update an existing note (partial updates supported).

**Request Body:** (all fields optional)
```json
{
  "content": "## Updated Content\n\nRevised approach",
  "note_type": "idea",
  "tags": ["revised", "approved"]
}
```

**Example:**
```bash
# Update only content
curl -X PUT http://localhost:8000/api/notes/note-uuid-1 \
  -H "Content-Type: application/json" \
  -d '{"content": "## Updated\n\nNew information added"}'
```

**Response:**
```json
{
  "id": "note-uuid-1",
  "project_id": "abc-123",
  "content": "## Updated\n\nNew information added",
  "note_type": "todo",
  "tags": ["refactoring", "auth"],
  "created_at": "2025-11-05T10:30:00Z",
  "updated_at": "2025-11-05T11:15:00Z"
}
```

---

### 4. DELETE /api/notes/{note_id}
Delete a note (hard delete).

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/notes/note-uuid-1
```

**Response:** (204 No Content)

---

### 5. POST /api/projects/{project_id}/notes/quick (Bonus)
Quick note creation with pre-formatted templates.

**Request Body:**
```json
{
  "type": "blocker",
  "content": "Authentication service is down"
}
```

**Supported Types:**
- `blocker`: Creates note with 🚫 **BLOCKER** template
- `idea`: Creates note with 💡 **IDEA** template
- `decision`: Creates note with ✅ **DECISION** template

**Example:**
```bash
curl -X POST http://localhost:8000/api/projects/abc-123/notes/quick \
  -H "Content-Type: application/json" \
  -d '{
    "type": "blocker",
    "content": "Database migration failing on production"
  }'
```

**Response:** (201 Created)
```json
{
  "id": "note-uuid-quick",
  "project_id": "abc-123",
  "content": "🚫 **BLOCKER**\n\nDatabase migration failing on production\n\n---\n*Quick blocker note*",
  "note_type": "blocker",
  "tags": ["blocker"],
  "created_at": "2025-11-05T11:30:00Z",
  "updated_at": null
}
```

---

## Note Types

| Type | Description | Use Case |
|------|-------------|----------|
| `general` | Default type | General observations, comments |
| `decision` | Architecture/design decisions | ADRs, tech choices |
| `idea` | Feature ideas, improvements | Brainstorming, future work |
| `blocker` | Critical issues | Production issues, dependencies |
| `todo` | Action items | Tasks, reminders |

---

## Tag Best Practices

**Common Tags:**
- `urgent` - Needs immediate attention
- `frontend` - UI/UX related
- `backend` - API/server related
- `refactoring` - Code quality improvements
- `security` - Security concerns
- `performance` - Performance issues
- `documentation` - Docs needed

**Examples:**
```json
{
  "tags": ["urgent", "security", "blocker"]
}
```

---

## Error Responses

**404 - Project Not Found:**
```json
{
  "detail": "Project abc-123 not found"
}
```

**400 - Invalid Note Type:**
```json
{
  "detail": "note_type must be one of ['general', 'decision', 'idea', 'blocker', 'todo']"
}
```

**422 - Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "content"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Database Schema

```sql
CREATE TABLE project_notes (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    note_type TEXT NOT NULL DEFAULT 'general',
    tags JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_project_notes_project_id ON project_notes(project_id);
CREATE INDEX idx_project_notes_type ON project_notes(note_type);
```

---

**Created by The Collective Borg.tools**
