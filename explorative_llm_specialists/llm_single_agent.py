"""Realer zentralisierter LLM-Vergleichsansatz über dasselbe lokale Modell."""

from __future__ import annotations

import json
from typing import Any, Dict

from action_plan import ActionPlan
from lms_backend import get_use_case_data
from ollama_client import OllamaClient, OllamaJsonResponse


CENTRAL_PLAN_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
        "tasks": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "actions": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "action": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["erlaubt", "freigabepflichtig", "blockiert"],
                    },
                    "reason": {"type": "string"},
                    "used_data": {"type": "array", "items": {"type": "string"}},
                    "uncertainties": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["action", "status", "reason", "used_data", "uncertainties"],
            },
        },
        "open_questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "tasks", "actions", "open_questions"],
}

SYSTEM_PROMPT = """
Du bist ein einzelner zentralisierter KI-Agent für ein Learning Management System.
Du erhältst eine Nutzeranfrage und ausschließlich simulierte LMS-Daten.
Erzeuge einen nachvollziehbaren ActionPlan, ohne Informationen zu erfinden.

Statusregeln:
- erlaubt: reine Analyse oder vorbereitende, nicht eingreifende Aktion
- freigabepflichtig: Veröffentlichung, Einschreibung, Zuweisung, individuelle Nachricht, Eskalation oder sensible Auswertung
- blockiert: unzulässige personenbezogene Weitergabe oder Aktion bei unzureichender Berechtigung

Berücksichtige Datenschutz, Rollenrechte, Unsicherheit und menschliche Freigabe.
Gib ausschließlich das vom JSON-Schema verlangte Objekt zurück.
""".strip()


def _backend_context(use_case_id: str) -> Dict[str, Any]:
    data = get_use_case_data(use_case_id)
    # Nur die für die Entscheidung relevanten simulierten Daten werden übergeben.
    return {
        key: value
        for key, value in data.items()
        if key not in {"user_request"}
    }


def run_real_single_llm_baseline(
    use_case_id: str,
    user_request: str,
    *,
    client: OllamaClient | None = None,
    seed: int = 42,
) -> tuple[ActionPlan, OllamaJsonResponse]:
    ollama = client or OllamaClient()
    context = _backend_context(use_case_id)
    response = ollama.chat_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=(
            f"Nutzeranfrage:\n{user_request}\n\n"
            "Simulierte LMS-Daten:\n"
            f"{json.dumps(context, ensure_ascii=False, indent=2)}"
        ),
        json_schema=CENTRAL_PLAN_SCHEMA,
        seed=seed,
        temperature=0.0,
        num_ctx=8192,
    )

    value = response.content
    plan = ActionPlan(
        use_case_id=f"{use_case_id}_real_single_llm",
        title=str(value["title"]),
        user_request=user_request,
    )
    plan.add_agent("Zentralisierter LLM-Agent")
    for task in value["tasks"]:
        plan.add_task(str(task))
    for action in value["actions"]:
        plan.add_action(
            action=str(action["action"]),
            status=str(action["status"]),
            reason=str(action["reason"]),
            used_data=[str(item) for item in action["used_data"]],
            uncertainties=[str(item) for item in action["uncertainties"]],
        )
    for question in value["open_questions"]:
        plan.add_open_question(str(question))
    return plan, response
