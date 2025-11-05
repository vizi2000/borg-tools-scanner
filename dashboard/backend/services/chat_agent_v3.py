"""Chat Agent V3 with Minimax M2 integration and function calling capabilities."""

import json
import uuid
import os
import re
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from sqlalchemy.orm import Session
import httpx

from models.project import Project
from models.chat import ChatMessage


SYSTEM_PROMPT = """Jesteś doświadczonym architektem oprogramowania i starszym deweloperem.

Twoje odpowiedzi powinny być:
1. Zwięzłe (max 3-4 zdania analizy)
2. Konkretne z czasem (format: "- [30min] Zrób X")
3. Techniczne i precyzyjne
4. ADHD-friendly (zadania 45-90min)
5. Priorytetyzowane

Masz dostęp do 8 funkcji pomocniczych:
- get_project_detail: Pobierz pełne dane projektu
- get_file_content: Odczytaj plik z projektu
- analyze_function_complexity: Analiza złożoności funkcji (cyclomatic/cognitive)
- suggest_refactoring: Wygeneruj sugestie refaktoringu
- generate_readme_section: Wygeneruj sekcję README (Installation, Usage, etc.)
- generate_tests: Wygeneruj testy jednostkowe
- create_dockerfile: Wygeneruj Dockerfile
- fix_security_issue: Wygeneruj patch bezpieczeństwa

Używaj tych funkcji gdy potrzebujesz konkretnych danych lub generowania kodu."""


FUNCTION_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_project_detail",
            "description": "Pobiera szczegółowe informacje o projekcie z bazy danych",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "ID projektu w formacie UUID"
                    }
                },
                "required": ["project_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_content",
            "description": "Odczytuje zawartość pliku z projektu",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "ID projektu w formacie UUID"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Ścieżka względna do pliku w projekcie (np. 'src/main.py')"
                    }
                },
                "required": ["project_id", "file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_function_complexity",
            "description": "Analizuje złożoność cyklomatyczną i kognitywną funkcji",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "ID projektu w formacie UUID"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Ścieżka do pliku"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "Nazwa funkcji do analizy"
                    }
                },
                "required": ["project_id", "file_path", "function_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_refactoring",
            "description": "Generuje sugestie refaktoringu dla podanego kodu",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Fragment kodu do refaktoringu"
                    },
                    "language": {
                        "type": "string",
                        "description": "Język programowania (python, javascript, typescript, rust, go, java)"
                    }
                },
                "required": ["code", "language"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_readme_section",
            "description": "Generuje sekcję README.md dla projektu",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "ID projektu w formacie UUID"
                    },
                    "section": {
                        "type": "string",
                        "description": "Nazwa sekcji: Installation, Usage, API, Configuration, Contributing"
                    }
                },
                "required": ["project_id", "section"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_tests",
            "description": "Generuje testy jednostkowe dla kodu",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "ID projektu w formacie UUID"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Ścieżka do pliku źródłowego"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "Opcjonalna nazwa funkcji (jeśli pusta, generuje testy dla całego pliku)"
                    }
                },
                "required": ["project_id", "file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_dockerfile",
            "description": "Generuje Dockerfile dla projektu",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "ID projektu w formacie UUID"
                    },
                    "base_image": {
                        "type": "string",
                        "description": "Opcjonalny obraz bazowy (np. 'python:3.11-slim', 'node:18-alpine')"
                    }
                },
                "required": ["project_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fix_security_issue",
            "description": "Generuje patch bezpieczeństwa dla zidentyfikowanego problemu",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "ID projektu w formacie UUID"
                    },
                    "issue_description": {
                        "type": "string",
                        "description": "Opis problemu bezpieczeństwa"
                    }
                },
                "required": ["project_id", "issue_description"]
            }
        }
    }
]


class ChatAgentV3:
    """
    Chat Agent V3 with Minimax M2 integration and function calling.

    Features:
    - Primary model: minimax/minimax-m2:free
    - Fallback models: gemini-2.0-flash-exp, deepseek-r1t-chimera
    - 8 callable functions for project analysis and code generation
    - Multi-turn conversations with context preservation
    - Dynamic suggested questions based on project state
    """

    def __init__(self, db: Session, api_key: str):
        """
        Initialize Chat Agent V3.

        Args:
            db: SQLAlchemy database session
            api_key: OpenRouter API key
        """
        self.db = db
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        # Model configuration with fallbacks
        self.models = [
            "minimax/minimax-m2:free",
            "google/gemini-2.0-flash-exp:free",
            "tngtech/deepseek-r1t-chimera:free"
        ]

        # Function registry
        self.functions: Dict[str, Callable] = {
            "get_project_detail": self._func_get_project_detail,
            "get_file_content": self._func_get_file_content,
            "analyze_function_complexity": self._func_analyze_function_complexity,
            "suggest_refactoring": self._func_suggest_refactoring,
            "generate_readme_section": self._func_generate_readme_section,
            "generate_tests": self._func_generate_tests,
            "create_dockerfile": self._func_create_dockerfile,
            "fix_security_issue": self._func_fix_security_issue,
        }

    async def chat(
        self,
        message: str,
        session_id: str,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process chat message with function calling support.

        Args:
            message: User message
            session_id: Chat session ID
            project_id: Optional focused project ID

        Returns:
            Dict with: response, function_calls, suggested_questions
        """
        # Build conversation history
        messages = self._build_messages(session_id, message, project_id)

        # Call LLM with function schemas
        response_text = ""
        function_calls_made = []

        for attempt in range(5):  # Max 5 function calling iterations
            llm_response = await self._call_openrouter(messages)

            if not llm_response:
                response_text = "Przepraszam, wystąpił błąd przy komunikacji z AI."
                break

            # Check for function calls
            if "tool_calls" in llm_response and llm_response["tool_calls"]:
                # Execute functions
                for tool_call in llm_response["tool_calls"]:
                    func_name = tool_call["function"]["name"]
                    func_args = json.loads(tool_call["function"]["arguments"])

                    # Execute function
                    func_result = await self._execute_function(func_name, func_args)
                    function_calls_made.append({
                        "name": func_name,
                        "arguments": func_args,
                        "result": func_result
                    })

                    # Add function result to messages
                    messages.append({
                        "role": "assistant",
                        "content": llm_response.get("content", ""),
                        "tool_calls": [tool_call]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": func_name,
                        "content": json.dumps(func_result, ensure_ascii=False)
                    })
            else:
                # No more function calls, extract final response
                response_text = llm_response.get("content", "")
                break

        # Save conversation to database
        self._save_messages(session_id, message, response_text, project_id, function_calls_made)

        # Generate suggested questions
        suggested_questions = self._generate_suggested_questions(session_id, project_id)

        return {
            "response": response_text,
            "function_calls": function_calls_made,
            "suggested_questions": suggested_questions
        }

    def _build_messages(
        self,
        session_id: str,
        current_message: str,
        project_id: Optional[str]
    ) -> List[Dict[str, str]]:
        """Build conversation messages for LLM."""
        messages = []

        # System prompt with context
        context = self._build_context(session_id, project_id)
        system_content = SYSTEM_PROMPT
        if context:
            system_content += f"\n\n{context}"

        messages.append({"role": "system", "content": system_content})

        # Fetch last 5 messages from session
        history = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(10)  # Last 5 pairs (user + assistant)
            .all()
        )

        # Reverse to chronological order
        history = list(reversed(history))

        for msg in history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Add current message
        messages.append({"role": "user", "content": current_message})

        return messages

    def _build_context(self, session_id: str, project_id: Optional[str]) -> str:
        """Build context string from focused project."""
        if not project_id:
            return ""

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return ""

        context_data = {
            "name": project.name,
            "path": project.path,
            "stage": project.stage,
            "code_quality": f"{project.code_quality_score}/10",
            "value_score": f"{project.value_score}/10",
            "risk_score": f"{project.risk_score}/10",
            "priority": f"{project.priority}/20",
            "languages": project.languages,
            "has_tests": project.has_tests,
            "has_ci": project.has_ci,
            "has_readme": project.has_readme,
            "has_license": project.has_license,
            "fundamental_errors": project.fundamental_errors,
            "todo_now": project.todo_now[:3] if project.todo_now else [],
            "todo_next": project.todo_next[:3] if project.todo_next else [],
        }

        return f"\nFOKUS PROJEKTU:\n```json\n{json.dumps(context_data, indent=2, ensure_ascii=False)}\n```"

    async def _call_openrouter(self, messages: List[Dict]) -> Optional[Dict]:
        """Call OpenRouter API with function schemas and model fallback."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Borg Scanner Dashboard V3",
        }

        payload = {
            "messages": messages,
            "tools": FUNCTION_SCHEMAS,
            "max_tokens": 1500,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            for model in self.models:
                payload["model"] = model

                try:
                    response = await client.post(
                        self.base_url,
                        json=payload,
                        headers=headers
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["choices"][0]["message"]

                except httpx.HTTPError as e:
                    print(f"Model {model} failed: {e}")
                    continue
                except Exception as e:
                    print(f"Unexpected error with {model}: {e}")
                    continue

        return None

    async def _execute_function(self, func_name: str, arguments: Dict) -> Any:
        """Execute a registered function."""
        if func_name not in self.functions:
            return {"error": f"Function {func_name} not found"}

        try:
            func = self.functions[func_name]
            result = await func(**arguments)
            return result
        except Exception as e:
            return {"error": str(e)}

    def _save_messages(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        project_id: Optional[str],
        function_calls: List[Dict]
    ):
        """Save conversation to database."""
        # User message
        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=user_message,
            project_id=project_id,
        )
        self.db.add(user_msg)

        # Assistant message with function calls metadata
        assistant_content = assistant_message
        if function_calls:
            assistant_content += f"\n\n[Wywołano {len(function_calls)} funkcji]"

        assistant_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=assistant_content,
            project_id=project_id,
        )
        self.db.add(assistant_msg)

        self.db.commit()

    def _generate_suggested_questions(
        self,
        session_id: str,
        project_id: Optional[str]
    ) -> List[str]:
        """Generate 3-5 dynamic suggested questions based on project state."""
        questions = []

        if project_id:
            project = self.db.query(Project).filter(Project.id == project_id).first()

            if not project:
                return [
                    "Pokaż listę wszystkich projektów",
                    "Które projekty mają najwyższy priorytet?",
                    "Jakie są najczęstsze błędy w portfolio?"
                ]

            # Dynamic questions based on project state
            if not project.has_tests:
                questions.append(f"Wygeneruj testy dla głównego pliku w {project.name}")

            if not project.has_ci:
                questions.append(f"Stwórz konfigurację CI/CD dla {project.name}")

            if not project.has_readme:
                questions.append(f"Wygeneruj README.md dla {project.name}")

            if project.fundamental_errors:
                error = project.fundamental_errors[0]
                questions.append(f"Jak naprawić: {error}?")

            if project.todo_now:
                todo = project.todo_now[0]
                questions.append(f"Jak zrealizować: {todo}?")

            if project.code_quality_score < 5:
                questions.append(f"Jakie są największe problemy jakości w {project.name}?")

            questions.append(f"Stwórz Dockerfile dla {project.name}")

            if project.languages:
                lang = project.languages[0]
                questions.append(f"Przeanalizuj złożoność kodu {lang} w projekcie")

            # Limit to 5 questions
            questions = questions[:5]
        else:
            # Generic portfolio questions
            questions = [
                "Które projekty mają najwyższy potencjał komercyjny?",
                "Pokaż projekty wymagające natychmiastowej uwagi",
                "Jakie technologie są najbardziej popularne w portfolio?",
                "Które projekty są gotowe do produkcji?",
                "Zidentyfikuj projekty z problemami bezpieczeństwa"
            ]

        return questions

    # ========================
    # FUNCTION IMPLEMENTATIONS
    # ========================

    async def _func_get_project_detail(self, project_id: str) -> Dict:
        """Get full project data from database."""
        project = self.db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {"error": f"Project {project_id} not found"}

        return {
            "id": project.id,
            "name": project.name,
            "path": project.path,
            "stage": project.stage,
            "priority": project.priority,
            "value_score": project.value_score,
            "risk_score": project.risk_score,
            "code_quality_score": project.code_quality_score,
            "languages": project.languages,
            "deps": project.deps,
            "has_readme": project.has_readme,
            "has_license": project.has_license,
            "has_tests": project.has_tests,
            "has_ci": project.has_ci,
            "commits_count": project.commits_count,
            "branches_count": project.branches_count,
            "last_commit_dt": project.last_commit_dt.isoformat() if project.last_commit_dt else None,
            "todos": project.todos[:5],
            "todo_now": project.todo_now,
            "todo_next": project.todo_next,
            "fundamental_errors": project.fundamental_errors,
        }

    async def _func_get_file_content(self, project_id: str, file_path: str) -> Dict:
        """Read file content from project."""
        project = self.db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {"error": f"Project {project_id} not found"}

        full_path = Path(project.path) / file_path

        if not full_path.exists():
            return {"error": f"File {file_path} not found in project"}

        if full_path.stat().st_size > 1_000_000:  # 1MB limit
            return {"error": "File too large (max 1MB)"}

        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            return {
                "file_path": file_path,
                "content": content,
                "lines": len(content.split("\n")),
                "size_bytes": len(content)
            }
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

    async def _func_analyze_function_complexity(
        self,
        project_id: str,
        file_path: str,
        function_name: str
    ) -> Dict:
        """Analyze function cyclomatic and cognitive complexity."""
        # Read file content
        file_result = await self._func_get_file_content(project_id, file_path)

        if "error" in file_result:
            return file_result

        content = file_result["content"]

        # Simple heuristic complexity analysis
        # Find function definition
        patterns = [
            rf"def {function_name}\s*\(",  # Python
            rf"function {function_name}\s*\(",  # JavaScript
            rf"func {function_name}\s*\(",  # Go
            rf"fn {function_name}\s*\(",  # Rust
        ]

        func_start = -1
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                func_start = match.start()
                break

        if func_start == -1:
            return {"error": f"Function {function_name} not found"}

        # Extract function body (approximate)
        lines = content[func_start:].split("\n")
        func_lines = []
        indent_level = None

        for line in lines[:100]:  # Max 100 lines
            if indent_level is None and line.strip():
                indent_level = len(line) - len(line.lstrip())
            if indent_level and line.strip() and len(line) - len(line.lstrip()) <= indent_level and len(func_lines) > 0:
                break
            func_lines.append(line)

        func_body = "\n".join(func_lines)

        # Calculate complexity heuristics
        cyclomatic = 1  # Base complexity
        cyclomatic += func_body.count("if ")
        cyclomatic += func_body.count("elif ")
        cyclomatic += func_body.count("else:")
        cyclomatic += func_body.count("for ")
        cyclomatic += func_body.count("while ")
        cyclomatic += func_body.count("except ")
        cyclomatic += func_body.count("&&")
        cyclomatic += func_body.count("||")
        cyclomatic += func_body.count("case ")

        # Cognitive complexity (nested control structures weighted)
        cognitive = cyclomatic + func_body.count("    if ") * 2  # Nested if
        cognitive += func_body.count("        if ") * 3  # Deeply nested

        return {
            "function_name": function_name,
            "lines_of_code": len(func_lines),
            "cyclomatic_complexity": cyclomatic,
            "cognitive_complexity": cognitive,
            "complexity_rating": "low" if cyclomatic <= 5 else "medium" if cyclomatic <= 10 else "high",
            "recommendation": (
                "OK" if cyclomatic <= 5 else
                "Rozważ rozbicie funkcji" if cyclomatic <= 10 else
                "Wymagany refaktoring - zbyt złożona funkcja"
            )
        }

    async def _func_suggest_refactoring(self, code: str, language: str) -> Dict:
        """Generate refactoring suggestions for code."""
        suggestions = []

        # Analyze code patterns
        lines = code.split("\n")

        # Check for long functions
        if len(lines) > 50:
            suggestions.append({
                "type": "long_function",
                "severity": "high",
                "message": "Funkcja ma ponad 50 linii - rozważ podział na mniejsze funkcje",
                "effort_minutes": 45
            })

        # Check for deep nesting
        max_indent = max([len(line) - len(line.lstrip()) for line in lines if line.strip()])
        if max_indent > 16:  # 4 levels of indentation
            suggestions.append({
                "type": "deep_nesting",
                "severity": "high",
                "message": "Głębokie zagnieżdżenia - zastosuj early returns lub wydziel logikę",
                "effort_minutes": 30
            })

        # Check for repetition
        if code.count("if ") > 5:
            suggestions.append({
                "type": "multiple_conditionals",
                "severity": "medium",
                "message": "Wiele warunków - rozważ pattern matching lub strategię",
                "effort_minutes": 60
            })

        # Language-specific suggestions
        if language == "python":
            if "print(" in code:
                suggestions.append({
                    "type": "debug_statements",
                    "severity": "low",
                    "message": "Użyj logger zamiast print()",
                    "effort_minutes": 10
                })

        if language in ["javascript", "typescript"]:
            if "var " in code:
                suggestions.append({
                    "type": "outdated_syntax",
                    "severity": "medium",
                    "message": "Użyj const/let zamiast var",
                    "effort_minutes": 15
                })

        return {
            "language": language,
            "suggestions": suggestions,
            "total_effort_minutes": sum(s["effort_minutes"] for s in suggestions)
        }

    async def _func_generate_readme_section(self, project_id: str, section: str) -> Dict:
        """Generate README.md section for project."""
        project = self.db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {"error": f"Project {project_id} not found"}

        sections_map = {
            "Installation": self._generate_installation_section,
            "Usage": self._generate_usage_section,
            "API": self._generate_api_section,
            "Configuration": self._generate_configuration_section,
            "Contributing": self._generate_contributing_section,
        }

        if section not in sections_map:
            return {"error": f"Unknown section: {section}"}

        content = sections_map[section](project)

        return {
            "section": section,
            "content": content,
            "project_name": project.name
        }

    def _generate_installation_section(self, project: Project) -> str:
        """Generate Installation section."""
        lines = ["## Installation\n"]

        if "python" in project.languages:
            lines.append("```bash")
            lines.append("# Clone repository")
            lines.append(f"git clone {project.path}")
            lines.append("")
            lines.append("# Create virtual environment")
            lines.append("python -m venv venv")
            lines.append("source venv/bin/activate  # Linux/Mac")
            lines.append("# venv\\Scripts\\activate  # Windows")
            lines.append("")
            lines.append("# Install dependencies")
            if project.deps.get("python"):
                lines.append("pip install -r requirements.txt")
            lines.append("```")

        if "node" in project.languages:
            lines.append("```bash")
            lines.append("# Clone repository")
            lines.append(f"git clone {project.path}")
            lines.append("")
            lines.append("# Install dependencies")
            lines.append("npm install")
            lines.append("# or")
            lines.append("pnpm install")
            lines.append("```")

        return "\n".join(lines)

    def _generate_usage_section(self, project: Project) -> str:
        """Generate Usage section."""
        return f"""## Usage

### Quick Start

```bash
# Run the application
{"python main.py" if "python" in project.languages else "npm start"}
```

### Configuration

Edit the configuration file to customize settings:
- Set environment variables in `.env`
- Modify `config.json` or `config.yaml`

### Examples

See the `examples/` directory for usage examples.
"""

    def _generate_api_section(self, project: Project) -> str:
        """Generate API section."""
        return """## API Reference

### Main Functions

#### `function_name(param1, param2)`

Description of the function.

**Parameters:**
- `param1` (type): Description
- `param2` (type): Description

**Returns:**
- (type): Description

**Example:**
```
# Example usage
result = function_name("value1", "value2")
```
"""

    def _generate_configuration_section(self, project: Project) -> str:
        """Generate Configuration section."""
        return """## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (dev/prod) | `dev` |
| `PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Configuration File

Create a `config.yaml` file:

```yaml
app:
  name: application
  debug: true

database:
  host: localhost
  port: 5432
```
"""

    def _generate_contributing_section(self, project: Project) -> str:
        """Generate Contributing section."""
        return """## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"  # Python
# or
npm install --save-dev  # Node.js

# Run tests
pytest  # Python
# or
npm test  # Node.js
```

### Code Style

- Follow PEP 8 for Python
- Use ESLint for JavaScript/TypeScript
- Run linters before committing
"""

    async def _func_generate_tests(
        self,
        project_id: str,
        file_path: str,
        function_name: Optional[str] = None
    ) -> Dict:
        """Generate unit tests for code."""
        project = self.db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {"error": f"Project {project_id} not found"}

        # Read source file
        file_result = await self._func_get_file_content(project_id, file_path)
        if "error" in file_result:
            return file_result

        language = project.languages[0] if project.languages else "python"

        # Generate test template based on language
        if language == "python":
            test_content = self._generate_python_tests(file_path, function_name)
        elif language in ["javascript", "typescript"]:
            test_content = self._generate_js_tests(file_path, function_name)
        else:
            test_content = f"# TODO: Generate tests for {language}"

        return {
            "file_path": file_path,
            "function_name": function_name,
            "test_framework": "pytest" if language == "python" else "jest",
            "test_content": test_content,
            "estimated_coverage": "75%"
        }

    def _generate_python_tests(self, file_path: str, function_name: Optional[str]) -> str:
        """Generate Python pytest tests."""
        module_name = file_path.replace("/", ".").replace(".py", "")
        func = function_name or "your_function"

        return f"""import pytest
from {module_name} import {func}


class Test{func.title()}:
    \"\"\"Test suite for {func}.\"\"\"

    def test_{func}_basic(self):
        \"\"\"Test basic functionality.\"\"\"
        result = {func}()
        assert result is not None

    def test_{func}_with_valid_input(self):
        \"\"\"Test with valid input.\"\"\"
        result = {func}("test_input")
        assert result == "expected_output"

    def test_{func}_with_invalid_input(self):
        \"\"\"Test with invalid input.\"\"\"
        with pytest.raises(ValueError):
            {func}(None)

    def test_{func}_edge_cases(self):
        \"\"\"Test edge cases.\"\"\"
        assert {func}("") == ""
        assert {func}([]) == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""

    def _generate_js_tests(self, file_path: str, function_name: Optional[str]) -> str:
        """Generate JavaScript/TypeScript Jest tests."""
        func = function_name or "yourFunction"

        return f"""import {{ {func} }} from './{file_path}';

describe('{func}', () => {{
  test('should work with basic input', () => {{
    const result = {func}('test');
    expect(result).toBeDefined();
  }});

  test('should handle valid input', () => {{
    const result = {func}('valid_input');
    expect(result).toBe('expected_output');
  }});

  test('should throw error on invalid input', () => {{
    expect(() => {{
      {func}(null);
    }}).toThrow();
  }});

  test('should handle edge cases', () => {{
    expect({func}('')).toBe('');
    expect({func}([])).toEqual([]);
  }});
}});
"""

    async def _func_create_dockerfile(
        self,
        project_id: str,
        base_image: Optional[str] = None
    ) -> Dict:
        """Generate Dockerfile for project."""
        project = self.db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {"error": f"Project {project_id} not found"}

        language = project.languages[0] if project.languages else "python"

        if language == "python":
            base = base_image or "python:3.11-slim"
            dockerfile = self._generate_python_dockerfile(base, project)
        elif language in ["node", "javascript", "typescript"]:
            base = base_image or "node:18-alpine"
            dockerfile = self._generate_node_dockerfile(base, project)
        else:
            dockerfile = f"FROM {base_image or 'ubuntu:22.04'}\n# TODO: Configure for {language}"

        return {
            "project_name": project.name,
            "base_image": base_image or "auto-detected",
            "dockerfile_content": dockerfile,
            "estimated_size": "50-100MB"
        }

    def _generate_python_dockerfile(self, base_image: str, project: Project) -> str:
        """Generate Python Dockerfile."""
        return f"""FROM {base_image}

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt .
COPY pyproject.toml* .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "main.py"]
"""

    def _generate_node_dockerfile(self, base_image: str, project: Project) -> str:
        """Generate Node.js Dockerfile."""
        return f"""FROM {base_image}

WORKDIR /app

# Copy dependency files
COPY package*.json ./
COPY pnpm-lock.yaml* ./

# Install dependencies
RUN npm install --production
# Or for pnpm: RUN pnpm install --frozen-lockfile --prod

# Copy application code
COPY . .

# Build if needed
# RUN npm run build

# Expose port
EXPOSE 3000

# Run application
CMD ["npm", "start"]
"""

    async def _func_fix_security_issue(
        self,
        project_id: str,
        issue_description: str
    ) -> Dict:
        """Generate security patch for identified issue."""
        project = self.db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return {"error": f"Project {project_id} not found"}

        # Common security patterns
        patches = []

        if "sql injection" in issue_description.lower():
            patches.append({
                "issue": "SQL Injection",
                "fix": "Użyj prepared statements lub ORM",
                "code_example": "# BAD\\nquery = f'SELECT * FROM users WHERE id = {user_id}'\\n\\n# GOOD\\nquery = 'SELECT * FROM users WHERE id = ?'\\ncursor.execute(query, (user_id,))"
            })

        if "xss" in issue_description.lower():
            patches.append({
                "issue": "Cross-Site Scripting (XSS)",
                "fix": "Sanityzuj input i escape output",
                "code_example": "import html\\n\\nsafe_input = html.escape(user_input)"
            })

        if "password" in issue_description.lower():
            patches.append({
                "issue": "Weak Password Storage",
                "fix": "Użyj bcrypt lub argon2 do hashowania",
                "code_example": "import bcrypt\\n\\nhashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())"
            })

        if "secret" in issue_description.lower() or "api key" in issue_description.lower():
            patches.append({
                "issue": "Hardcoded Secrets",
                "fix": "Użyj zmiennych środowiskowych",
                "code_example": "import os\\n\\nAPI_KEY = os.getenv('API_KEY')\\nif not API_KEY:\\n    raise ValueError('API_KEY not set')"
            })

        return {
            "project_name": project.name,
            "issue_description": issue_description,
            "patches": patches,
            "priority": "high",
            "estimated_fix_time": "30-60 minutes"
        }


# Created by The Collective Borg.tools
