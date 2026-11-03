from __future__ import annotations

import json
import logging

from app.adapters.llm.base import LLMUnavailableError
from app.agent.guardrails import (
    general_out_of_scope_response,
    is_accessory_request,
    is_out_of_scope_topic,
    needs_policy_retrieval,
    out_of_scope_response,
    safe_fallback_response,
    sanitize_response,
)
from app.agent.prompts import build_system_prompt
from app.agent.tools import ToolRegistry
from app.config import Settings
from app.domain.models import AgentReply, Citation, ToolResult
from app.domain.services.conversations import ConversationService

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    def __init__(
        self,
        *,
        llm,
        tools: ToolRegistry,
        conversations: ConversationService,
        settings: Settings,
        system_prompt: str | None = None,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.conversations = conversations
        self.settings = settings
        self.system_prompt = system_prompt or build_system_prompt(
            settings.store_today_date, tools.policies.store_info()
        )

    def _extract_citations(self, tool_results: list[ToolResult]) -> list[Citation]:
        citations: list[Citation] = []
        seen: set[tuple[str, int]] = set()
        for result in tool_results:
            for raw in result.result.get("citacoes", []) if isinstance(result.result, dict) else []:
                try:
                    citation = Citation(**raw)
                except Exception:  # noqa: BLE001
                    continue
                key = (citation.section, citation.page)
                if key not in seen:
                    seen.add(key)
                    citations.append(citation)
        return citations

    def _record_blocked_handoff(self, session_id: str) -> None:
        try:
            self.conversations.record_handoff(
                session_id=session_id,
                reason="guardrail",
                summary="Resposta bloqueada por falta de consulta ou por conter dado sensível.",
            )
        except Exception:  # noqa: BLE001
            logger.exception("Falha ao registrar handoff de guardrail")

    def chat(self, session_id: str | None, message: str) -> AgentReply:
        session = self.conversations.get_or_create(session_id)
        self.conversations.append_user(session.session_id, message)

        if is_accessory_request(message):
            reply = out_of_scope_response()
            self.conversations.append_assistant(session.session_id, reply)
            return AgentReply(reply=reply, session_id=session.session_id)

        if is_out_of_scope_topic(message):
            reply = general_out_of_scope_response()
            self.conversations.append_assistant(session.session_id, reply)
            return AgentReply(reply=reply, session_id=session.session_id)

        messages: list[dict] = [
            {"role": "system", "content": self.system_prompt},
            *self.conversations.history_for_prompt(session.session_id),
        ]
        tool_results: list[ToolResult] = []
        seen_tool_calls: dict[tuple[str, str], ToolResult] = {}
        policy_auto_retrieved = False
        final_text: str | None = None
        handoff = False

        try:
            for _ in range(self.settings.max_tool_iterations):
                response = self.llm.complete(messages, self.tools.schemas)
                if response.tool_calls:
                    messages.append(
                        {
                            "role": "assistant",
                            "content": response.content,
                            "tool_calls": [
                                {
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": tool_call.name,
                                        "arguments": json.dumps(
                                            tool_call.arguments, ensure_ascii=False
                                        ),
                                    },
                                }
                                for tool_call in response.tool_calls
                            ],
                        }
                    )
                    for tool_call in response.tool_calls:
                        cache_key = (
                            tool_call.name,
                            json.dumps(tool_call.arguments, sort_keys=True, ensure_ascii=False),
                        )
                        if cache_key in seen_tool_calls:
                            result = seen_tool_calls[cache_key]
                        else:
                            result = self.tools.execute(
                                tool_call.name, tool_call.arguments, session.session_id
                            )
                            seen_tool_calls[cache_key] = result
                        tool_results.append(result)
                        if result.name == "escalar_atendimento" and result.ok:
                            handoff = True
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.name,
                                "content": json.dumps(
                                    result.result, ensure_ascii=False, default=str
                                ),
                            }
                        )
                        self.conversations.append_tool(
                            session.session_id,
                            content=json.dumps(result.result, ensure_ascii=False, default=str),
                            tool_calls=[
                                {
                                    "name": tool_call.name,
                                    "arguments": tool_call.arguments,
                                    "ok": result.ok,
                                }
                            ],
                        )
                    if (
                        needs_policy_retrieval(message)
                        and not any(item.name == "consultar_politicas" for item in tool_results)
                        and not policy_auto_retrieved
                    ):
                        policy_result = self.tools.execute(
                            "consultar_politicas",
                            {"pergunta": message},
                            session.session_id,
                        )
                        policy_auto_retrieved = True
                        if policy_result.ok and policy_result.result.get("trechos"):
                            tool_results.append(policy_result)
                            context_lines = [
                                f"[seção {trecho['secao']}, p. {trecho['pagina']}] "
                                f"{trecho['trecho']}"
                                for trecho in policy_result.result["trechos"]
                            ]
                            messages.append(
                                {
                                    "role": "system",
                                    "content": (
                                        "Contexto de políticas recuperado automaticamente. "
                                        "Use somente estes trechos e cite a seção correspondente:\n"
                                        + "\n".join(context_lines)
                                    ),
                                }
                            )
                            self.conversations.append_tool(
                                session.session_id,
                                content=json.dumps(
                                    policy_result.result, ensure_ascii=False, default=str
                                ),
                                tool_calls=[
                                    {
                                        "name": "consultar_politicas",
                                        "arguments": {"pergunta": message},
                                        "ok": True,
                                    }
                                ],
                            )
                    continue
                final_text = response.content
                break
            else:
                final_text = safe_fallback_response()
                handoff = True
                self._record_blocked_handoff(session.session_id)

            if not final_text:
                final_text = safe_fallback_response()
                handoff = True
                self._record_blocked_handoff(session.session_id)

            has_tool_history = bool(tool_results) or any(
                m.role == "tool" for m in self.conversations.history(session.session_id, limit=20)
            )
            final_text, blocked = sanitize_response(
                final_text, tool_results, has_tool_history=has_tool_history
            )
            if blocked:
                handoff = True
                self._record_blocked_handoff(session.session_id)

            citations = self._extract_citations(tool_results)
            mentioned = [citation for citation in citations if citation.section in final_text]
            if mentioned:
                citations = mentioned
            self.conversations.append_assistant(
                session.session_id,
                final_text,
                citations=[citation.model_dump() for citation in citations],
            )
            return AgentReply(
                reply=final_text,
                citations=citations,
                handoff=handoff,
                tool_calls=tool_results,
                session_id=session.session_id,
            )
        except LLMUnavailableError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("Falha inesperada no agente")
            reply = safe_fallback_response()
            self._record_blocked_handoff(session.session_id)
            self.conversations.append_assistant(session.session_id, reply)
            return AgentReply(
                reply=reply,
                handoff=True,
                session_id=session.session_id,
            )
