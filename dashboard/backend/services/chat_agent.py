"""Chat Agent service for AI-powered project advice using OpenRouter."""

import json
import uuid
import httpx
from typing import Optional
from sqlalchemy.orm import Session

from models.project import Project
from models.chat import ChatMessage


SYSTEM_PROMPT_TEMPLATE = """Jesteś doświadczonym architektem oprogramowania analizującym portfolio projektów.

{context}

Udzielaj rad w języku polskim. Twoje odpowiedzi powinny być:
1. Zwięzłe (max 3-4 zdania analizy)
2. Konkretne z konkretnymi zadaniami i czasem (format: "- [30min] Zrób X")
3. Techniczne i precyzyjne
4. ADHD-friendly (koncentruj się na zadaniach 45-90min)
5. Priorytetyzowane (najpierw najważniejsze)

Gdy użytkownik pyta o projekt, skup się na:
- Błędach fundamentalnych (brak testów, CI, dokumentacji)
- Bezpieczeństwie (jeśli są problemy)
- Konkretnych plikach do edycji
- Szybkich wygranych (quick wins)"""


class ChatAgent:
    """AI Chat Agent powered by OpenRouter."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "meta-llama/llama-4-scout:free"
        self.fallback_model = "deepseek/deepseek-r1:free"

    def send_message(
        self,
        message: str,
        session_id: str,
        project_id: Optional[str],
        db: Session,
    ) -> tuple[str, str]:
        """
        Send a message and get AI response.

        Returns:
            tuple: (response_text, message_id)
        """
        # Build context if project specified
        context = ""
        if project_id:
            context = self._build_context(project_id, db)

        # Format system prompt
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

        # Call OpenRouter
        response_text = self._call_openrouter(system_prompt, message)

        # Save messages to database
        message_id = self._save_messages(
            session_id, message, response_text, project_id, db
        )

        return response_text, message_id

    def _build_context(self, project_id: str, db: Session) -> str:
        """Build context string from project data."""
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return ""

        # Create concise JSON summary
        context_data = {
            "name": project.name,
            "path": project.path,
            "stage": project.stage,
            "code_quality": f"{project.code_quality_score}/10",
            "value_score": f"{project.value_score}/10",
            "risk_score": f"{project.risk_score}/10",
            "priority": f"{project.priority}/20",
            "has_tests": project.has_tests,
            "has_ci": project.has_ci,
            "has_readme": project.has_readme,
            "has_license": project.has_license,
            "languages": project.languages,
            "fundamental_errors": project.fundamental_errors,
            "todo_now": project.todo_now[:3] if project.todo_now else [],
            "todo_next": project.todo_next[:3] if project.todo_next else [],
            "deps_count": (
                sum(len(v) if isinstance(v, list) else 0 for v in project.deps.values())
                if project.deps
                else 0
            ),
        }

        return f"\nKONTEKST PROJEKTU:\n```json\n{json.dumps(context_data, indent=2, ensure_ascii=False)}\n```\n"

    def _call_openrouter(self, system_prompt: str, user_message: str) -> str:
        """Call OpenRouter API and return response text."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Borg Scanner Dashboard",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": 800,
            "temperature": 0.7,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            # Try fallback model
            print(f"Primary model failed, trying fallback: {e}")
            payload["model"] = self.fallback_model

            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(self.base_url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
            except Exception as fallback_error:
                return f"Przepraszam, wystąpił błąd przy łączeniu z AI: {str(fallback_error)}"

    def _save_messages(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        project_id: Optional[str],
        db: Session,
    ) -> str:
        """Save both user and assistant messages to database."""

        # User message
        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=user_message,
            project_id=project_id,
        )
        db.add(user_msg)

        # Assistant message
        assistant_msg_id = str(uuid.uuid4())
        assistant_msg = ChatMessage(
            id=assistant_msg_id,
            session_id=session_id,
            role="assistant",
            content=assistant_message,
            project_id=project_id,
        )
        db.add(assistant_msg)

        db.commit()

        return assistant_msg_id
