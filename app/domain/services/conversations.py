from __future__ import annotations

from app.domain.models import Handoff, Message, SessionInfo
from app.domain.ports import ConversationRepository


class ConversationService:
    def __init__(self, repository: ConversationRepository, max_history: int = 12) -> None:
        self.repository = repository
        self.max_history = max_history

    def create_session(self) -> SessionInfo:
        return self.repository.create_session()

    def get_or_create(self, session_id: str | None) -> SessionInfo:
        return self.repository.get_or_create_session(session_id)

    def session_exists(self, session_id: str) -> bool:
        return self.repository.session_exists(session_id)

    def append_user(self, session_id: str, content: str) -> Message:
        return self.repository.append_message(session_id, "user", content)

    def append_assistant(
        self,
        session_id: str,
        content: str,
        citations: list[dict] | None = None,
    ) -> Message:
        return self.repository.append_message(session_id, "assistant", content, citations=citations)

    def append_tool(
        self,
        session_id: str,
        content: str,
        tool_calls: list[dict] | None = None,
    ) -> Message:
        return self.repository.append_message(session_id, "tool", content, tool_calls=tool_calls)

    def history(self, session_id: str, limit: int = 50) -> list[Message]:
        return self.repository.list_messages(session_id, limit=limit)

    def history_for_prompt(self, session_id: str) -> list[dict]:
        messages = self.repository.list_messages(session_id, limit=self.max_history * 4)
        relevant = [m for m in messages if m.role in ("user", "assistant")]
        relevant = relevant[-self.max_history :]
        return [{"role": m.role, "content": m.content} for m in relevant]

    def record_handoff(self, session_id: str, reason: str, summary: str) -> Handoff:
        return self.repository.record_handoff(session_id, reason, summary)
