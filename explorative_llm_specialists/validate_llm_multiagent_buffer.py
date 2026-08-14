"""Offline-Strukturtest fuer den experimentellen LLM-Multi-Agent-Puffer v3.2."""

from __future__ import annotations

from typing import Any, Dict

from llm_multiagent_pipeline import orchestrate_with_llm_specialists
from lms_backend import get_use_case_data
from ollama_client import OllamaJsonResponse, OllamaMetrics


METRICS = OllamaMetrics(
    total_duration_ms=1.0,
    load_duration_ms=0.0,
    prompt_tokens=10,
    output_tokens=10,
    prompt_tokens_per_second=100.0,
    output_tokens_per_second=100.0,
)


class FakeClient:
    def chat_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: Dict[str, Any],
        seed: int = 42,
        temperature: float = 0.0,
        num_ctx: int = 4096,
        keep_alive: str = "10m",
        num_predict: int = 1024,
    ) -> OllamaJsonResponse:
        if "LLM-basierte Eingangsstufe" in system_prompt:
            content = {
                "use_case_id": "use_case_1",
                "intent": "Onboarding-Lernpfad vorbereiten",
                "tasks": [
                    "Lernpfad vorbereiten",
                    "Vorhandene und fehlende Inhalte pruefen",
                    "Zielgruppe bestimmen",
                    "Frist von 14 Tagen setzen",
                    "Teamleitung nur aggregiert ueber Fortschritt informieren",
                ],
                "agents": [
                    "Course Agent", "Content Agent", "Enrollment Agent", "Assignment Agent",
                    "Notification Agent", "Analytics/Metrics Agent", "Policy/Permission Agent",
                ],
                "privacy_requirements": ["Teamleitung nur aggregierte Fortschrittsinformationen bereitstellen"],
                "open_questions": [],
                "confidence": 0.99,
            }
        elif "Waehle fuer deine Fachaufgabe" in user_prompt:
            enums = json_schema["properties"]["requested_tools"]["items"]["enum"]
            content = {
                "requested_tools": list(enums[:2]),
                "plan_summary": "Minimal notwendige Werkzeuge lesen.",
            }
        else:
            agent_name = next(
                name for name in (
                    "Course Agent", "Content Agent", "Enrollment Agent", "Assignment Agent",
                    "Notification Agent", "Analytics/Metrics Agent", "Policy/Permission Agent",
                )
                if f"spezialisierte {name}" in system_prompt
            )
            action_map = {
                "Course Agent": [
                    ("Lernpfad C-ONB-001 strukturieren", "erlaubt", ["read_course"]),
                ],
                "Content Agent": [
                    ("Fehlendes Modul M3 markieren und ergaenzen", "erlaubt", ["read_modules"]),
                    ("Veraltetes Modul M4 aktualisieren", "erlaubt", ["read_modules"]),
                ],
                "Enrollment Agent": [
                    # C-ONB-001 stammt nicht aus eigenen Tools, ist aber im verifizierten
                    # upstream read_course-Kontext vorhanden und muss daher akzeptiert werden.
                    ("Zielgruppe G1 dem Lernpfad C-ONB-001 zuweisen", "freigabepflichtig", ["read_groups", "verified_tool_outputs.read_course"]),
                    # absichtliche Fremdaufgabe fuer Ownership-Test
                    ("Modul M3 aktualisieren", "erlaubt", ["shared_context"]),
                ],
                "Assignment Agent": [
                    ("Frist von 14 Tagen setzen", "erlaubt", ["user_request"]),
                    ("Wiederholungsaufgabe planen", "erlaubt", ["tasks"]),
                    ("Aufgabe planen", "erlaubt", ["tasks"]),
                ],
                "Notification Agent": [
                    ("Erinnerung an die Bearbeitungsfrist von 14 Tagen senden", "erlaubt", ["user_request", "read_groups"]),
                    # absichtlich halluzinierter Prozentwert: muss Grounding-Rejection ausloesen.
                    ("Benachrichtigung an Teamleiter: 65 % der Teilnehmenden haben abgeschlossen", "freigabepflichtig", ["read_groups"]),
                ],
                "Analytics/Metrics Agent": [
                    ("Aggregiertes Fortschrittsreporting an Teamleiter vorbereiten", "erlaubt", ["read_groups"]),
                    ("Reporting-Intervall woechentlich per E-Mail festlegen", "erlaubt", ["read_groups"]),
                ],
                "Policy/Permission Agent": [
                    ("Individuelle Fortschrittsdaten an Teamleiter G2 blockieren", "blockiert", ["read_permission_rules", "read_groups"]),
                ],
            }
            items = action_map[agent_name]
            content = {
                "agent_name": agent_name,
                "observations": ["Testbeobachtung aus Fake-Toolausgaben"],
                "proposed_actions": [
                    {
                        "action": action,
                        "requested_status": status,
                        "reason": "Strukturtest fuer " + agent_name,
                        "used_data": used_data,
                        "uncertainties": [],
                    }
                    for action, status, used_data in items
                ],
                "open_questions": [],
                "confidence": 0.9,
            }
        return OllamaJsonResponse(
            content=content,
            model="fake:qwen3",
            created_at="",
            metrics=METRICS,
            raw_response={},
        )


def main() -> None:
    request = get_use_case_data("use_case_1")["user_request"]
    result = orchestrate_with_llm_specialists(request, client=FakeClient())

    assert len(result.specialist_results) == 7
    assert "verified_tool_outputs" in result.shared_context
    assert "read_course" in result.shared_context["verified_tool_outputs"]
    assert "read_modules" in result.shared_context["verified_tool_outputs"]

    ownership_rejected = [d for d in result.ownership_decisions if not d.accepted]
    assert ownership_rejected, "Mindestens eine absichtliche Rollenueberschreitung muss verworfen werden."

    grounding_rejected = [d for d in result.grounding_decisions if not d.accepted]
    assert grounding_rejected, "Der absichtlich erfundene Prozentwert muss verworfen werden."
    assert any("65" in d.action and "Prozent" in d.reason for d in grounding_rejected), grounding_rejected

    assignment_rejected = [
        d for d in result.ownership_decisions
        if d.agent_name == "Assignment Agent" and not d.accepted
    ]
    assert any("Wiederholungsaufgabe" in d.action for d in assignment_rejected), assignment_rejected
    assert any(d.action == "Aufgabe planen" for d in assignment_rejected), assignment_rejected

    analytics_grounding_rejected = [
        d for d in result.grounding_decisions
        if d.agent_name == "Analytics/Metrics Agent" and not d.accepted
    ]
    assert any("woechentlich" in d.action.lower() and "Reporting" in d.reason for d in analytics_grounding_rejected), analytics_grounding_rejected

    enrollment_grounding = [
        d for d in result.grounding_decisions
        if d.agent_name == "Enrollment Agent" and "C-ONB-001" in d.action
    ]
    assert enrollment_grounding and enrollment_grounding[0].accepted, (
        "Upstream Tool-Kontext muss C-ONB-001 fuer Enrollment erden."
    )

    assert result.consolidation["final_consolidated_action_count"] < result.consolidation["raw_specialist_action_count"]
    blocked = [a for a in result.plan.actions if a.status == "blockiert"]
    approval = [a for a in result.plan.actions if a.status == "freigabepflichtig"]
    assert blocked, "Governance muss individuelle Offenlegung blockieren."
    assert approval, "Mindestens eine Aktion muss freigabepflichtig sein."
    deadline_actions = [a for a in result.plan.actions if "14 Tagen" in a.action or "Frist" in a.action]
    assert deadline_actions and all(a.status != "erlaubt" for a in deadline_actions), deadline_actions


    # v3.2: negative Schutzanforderung muss als positive, blockierte Handlung erscheinen.
    assert any(
        a.status == "blockiert"
        and "individuelle fortschrittsdaten" in a.action.lower()
        and "keine individuellen" not in a.action.lower()
        for a in result.plan.actions
    ), "Negative Datenschutzregel muss als direkte blockierte Handlung abgebildet werden."

    # v3.2: prefixed Provenienz darf nicht als Grounding-Fehler gewertet werden.
    assert not any(
        "verified_tool_outputs.read_course" in claim
        for d in grounding_rejected
        for claim in d.unsupported_claims
    ), "verified_tool_outputs.X muss auf X normalisiert werden."

    print("OK: Offline-Strukturtest v3.2 erfolgreich.")
    print(f"LLM-Fachagenten: {len(result.specialist_results)}")
    print(f"Roh-Aktionen: {result.consolidation['raw_specialist_action_count']}")
    print(f"Ownership-Rejections: {result.consolidation['ownership_rejected_count']}")
    print(f"Grounding-Rejections: {result.consolidation['grounding_rejected_count']}")
    print(f"Beide Filter bestanden: {result.consolidation['passed_ownership_and_grounding_count']}")
    print(f"Finale konsolidierte Aktionen: {result.consolidation['final_consolidated_action_count']}")
    print(f"Governance-Korrekturen: {sum(item.changed for item in result.governance_decisions)}")


if __name__ == "__main__":
    main()
