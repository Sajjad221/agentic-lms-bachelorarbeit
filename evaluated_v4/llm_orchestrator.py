"""LLM-basierte Eingangsstufe und dynamische Agentenkoordination.

Version 3 trennt ausdrücklich zwischen roher Modellentscheidung und
nachgelagerter deterministischer Validierung. Dadurch bleiben LLM-Leistung und
Sicherheitsbeitrag der kontrollierenden Architektur getrennt auswertbar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from action_plan import ActionPlan
from agents import (
    run_analytics_agent,
    run_assignment_agent,
    run_content_agent,
    run_course_agent,
    run_enrollment_agent,
    run_notification_agent,
    run_policy_permission_agent,
)
from lms_backend import get_use_case_data
from ollama_client import OllamaClient, OllamaJsonResponse


ALLOWED_AGENTS: tuple[str, ...] = (
    "Course Agent",
    "Content Agent",
    "Enrollment Agent",
    "Assignment Agent",
    "Notification Agent",
    "Analytics/Metrics Agent",
    "Policy/Permission Agent",
)

AGENT_RUNNERS = {
    "Course Agent": run_course_agent,
    "Content Agent": run_content_agent,
    "Enrollment Agent": run_enrollment_agent,
    "Assignment Agent": run_assignment_agent,
    "Notification Agent": run_notification_agent,
    "Analytics/Metrics Agent": run_analytics_agent,
    "Policy/Permission Agent": run_policy_permission_agent,
}

CANONICAL_AGENT_ORDER: tuple[str, ...] = (
    "Analytics/Metrics Agent",
    "Content Agent",
    "Course Agent",
    "Enrollment Agent",
    "Assignment Agent",
    "Notification Agent",
    "Policy/Permission Agent",
)

# Use-Case-spezifische Trigger verhindern, dass z. B. ein reiner Gruppenvergleich
# in Use Case 2 fälschlich den Enrollment Agent aktiviert.
AGENT_TRIGGER_TERMS: Dict[str, Dict[str, tuple[str, ...]]] = {
    "use_case_1": {
        "Course Agent": ("lernpfad", "onboarding", "kursstruktur", "kursaufbau"),
        "Content Agent": ("inhalt", "content", "modul", "material", "veraltet", "fehlend", "lücke", "aktual"),
        "Enrollment Agent": ("zielgruppe", "gruppe", "einschreib", "zuord", "werkstudent", "werkstud"),
        "Assignment Agent": ("frist", "14 tag", "zwei woch", "abschluss"),
        "Notification Agent": ("benachr", "informier", "meldung", "lernendeninformation"),
        "Analytics/Metrics Agent": ("fortschritt", "report", "bericht", "auswertung", "zusammengefasst", "aggreg"),
        "Policy/Permission Agent": ("datenschutz", "personenbez", "aggreg", "berechtig", "rolle", "freigabe", "blockier", "datenspar"),
    },
    "use_case_2": {
        "Analytics/Metrics Agent": ("testergebnis", "testdaten", "testresult", "abschlusstest", "sicherheitstest", "auswert", "analyse", "gruppenvergleich", "gruppenunterschied", "gesamtwert"),
        "Content Agent": ("inhalt", "content", "material", "modul", "lernmaterial"),
        "Course Agent": ("kursanpass", "kursänder", "kursverbesser", "verbessere den kurs", "didaktische anpass"),
        "Assignment Agent": ("wiederholung", "aufgabe", "übung"),
        "Notification Agent": ("informier", "hinweis", "benachr", "privat", "vertraulich"),
        "Policy/Permission Agent": ("datenschutz", "personenbez", "leistungsdaten", "öffentlich", "freigabe", "vertraulich", "bloßstellung"),
    },
    "use_case_3": {
        "Course Agent": ("pflichtschulung", "compliance schulung", "kursentwurf", "schulung", "kurs"),
        "Content Agent": ("inhalt", "content", "modul", "richtlinie", "veraltet", "fehlend", "lücke", "aktual"),
        "Enrollment Agent": ("zielgruppe", "kundendatenzugriff", "zugriffsmerkmal", "rollenbasiert", "zuweis", "beschäftigt", "mitarbeit"),
        "Assignment Agent": ("frist", "14 tag", "zwei woch", "abschluss"),
        "Notification Agent": ("erinner", "mahnung", "eskal", "benachr"),
        "Analytics/Metrics Agent": ("report", "bericht", "hr", "compliance", "teilnahmeinformation", "weitergabe", "auswertung"),
        "Policy/Permission Agent": ("datenschutz", "personenbez", "datenspar", "berechtig", "rolle", "freigabe", "blockier", "compliance", "hr", "sensible"),
    },
}

CLASSIFICATION_TERMS: Dict[str, tuple[str, ...]] = {
    "use_case_1": (
        "onboarding", "werkstudent", "werkstud", "lernpfad", "it support", "support onboarding",
    ),
    "use_case_2": (
        "testergebnis", "testdaten", "testresult", "abschlusstest", "sicherheitstest",
        "gruppenunterschied", "gruppenvergleich", "vorerfahrung", "wiederholungsaufgabe",
        "wiederholungsübung", "schwache themen", "schwache inhalte",
    ),
    "use_case_3": (
        "pflichtschulung", "compliance schulung", "kundendatenzugriff", "kundendaten",
        "hr", "compliance reporting", "compliance bericht", "genai schulung",
    ),
}

REQUEST_ANALYSIS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "use_case_id": {
            "type": "string",
            "enum": ["use_case_1", "use_case_2", "use_case_3", "unknown"],
        },
        "intent": {"type": "string", "minLength": 3},
        "tasks": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 3},
        },
        "agents": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"type": "string", "enum": list(ALLOWED_AGENTS)},
        },
        "privacy_requirements": {
            "type": "array",
            "items": {"type": "string", "minLength": 3},
        },
        "open_questions": {
            "type": "array",
            "items": {"type": "string", "minLength": 3},
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "use_case_id",
        "intent",
        "tasks",
        "agents",
        "privacy_requirements",
        "open_questions",
        "confidence",
    ],
}

SYSTEM_PROMPT = """
Du bist die LLM-basierte Eingangsstufe eines agentenbasierten Learning-Management-Systems.
Deine Aufgabe ist ausschließlich die strukturierte Analyse einer deutschsprachigen Nutzeranfrage.

Ordne die Anfrage einem der folgenden Szenariotypen zu:
- use_case_1: Onboarding neuer Werkstudierender im IT-Support; Lernpfad, Content-Status, Zielgruppe, Frist und Fortschrittsreporting.
- use_case_2: Testergebnisse oder Testdaten analysieren; schwache Themen, Gruppenunterschiede, Kursanpassungen und Wiederholungsaufgaben.
- use_case_3: Compliance-Pflichtschulung; Kundendatenzugriff, rollenbasierte Zuweisung, Frist, Erinnerungen und HR-/Compliance-Bericht.
- unknown: nur wenn keine der drei Beschreibungen inhaltlich ausreichend passt.

Wichtige Abgrenzung:
- Sobald Testergebnisse, Testdaten, ein Sicherheitstest, schwache Themen oder Gruppenunterschiede ausgewertet und daraus Lernmaßnahmen abgeleitet werden sollen, wähle use_case_2 — auch wenn kein konkreter Kursname genannt ist.
- Eine Gruppe in einer Ergebnisanalyse wird durch den Analytics/Metrics Agent ausgewertet. Der Enrollment Agent ist in use_case_2 nur nötig, wenn tatsächlich Einschreibung, Zuweisung oder eine neue Zielgruppe verlangt wird.

Du darfst ausschließlich diese Agentenrollen auswählen:
- Course Agent: Kurs- und Lernpfadstruktur oder Kursanpassung
- Content Agent: vorhandene, fehlende oder veraltete Lerninhalte
- Enrollment Agent: Zielgruppen, Einschreibung und Zuweisung
- Assignment Agent: Aufgaben, Fristen und Wiederholungen
- Notification Agent: Nachrichten, Lernhinweise und Erinnerungen
- Analytics/Metrics Agent: Testergebnisse, Kennzahlen, Gruppenvergleiche und Berichte
- Policy/Permission Agent: Rollen, Rechte, Datenschutz, Freigaben und Blockierungen

Regeln:
1. Erfinde keine weiteren Agentenrollen.
2. Zerlege jede ausdrücklich genannte Anforderung in eine konkrete Teilaufgabe.
3. Wähle für jede Teilaufgabe mindestens den fachlich zuständigen Agenten.
4. Wähle den Policy/Permission Agent, sobald Datenschutz, personenbezogene Daten, Rollenrechte, Freigaben oder Blockierungen relevant sind.
5. Nenne Datenschutz-, Rollen- und Freigabeanforderungen ausdrücklich und konkret.
6. Gib jede eigenständige Schutzanforderung als separaten Eintrag in privacy_requirements aus. Fasse beispielsweise Aggregation, Verbot personenbezogener Detaildaten und rollenbasierte Berechtigung nicht zu einer allgemeinen DSGVO-Aussage zusammen.
7. Übernimm auch direkt formulierte Einschränkungen wie „nur aggregiert“, „keine individuellen Daten“, „nur erforderliche Angaben“, „privat“ oder „nicht an HR/Teamleiter“ jeweils explizit.
8. Formuliere offene Fragen nur, wenn eine Information tatsächlich fehlt oder unklar ist.
9. Gib ausschließlich das vom JSON-Schema verlangte Objekt zurück.
""".strip()


@dataclass(frozen=True)
class RequestAnalysis:
    use_case_id: str
    intent: str
    tasks: List[str]
    agents: List[str]
    privacy_requirements: List[str]
    open_questions: List[str]
    confidence: float

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "RequestAnalysis":
        required = {
            "use_case_id", "intent", "tasks", "agents",
            "privacy_requirements", "open_questions", "confidence",
        }
        missing = required - value.keys()
        if missing:
            raise ValueError(f"Fehlende Felder in LLM-Analyse: {sorted(missing)}")

        use_case_id = str(value["use_case_id"])
        if use_case_id not in {"use_case_1", "use_case_2", "use_case_3", "unknown"}:
            raise ValueError(f"Ungültige use_case_id: {use_case_id}")

        agents = list(dict.fromkeys(str(agent) for agent in value["agents"]))
        invalid_agents = [agent for agent in agents if agent not in ALLOWED_AGENTS]
        if invalid_agents:
            raise ValueError(f"Nicht erlaubte Agentenrollen: {invalid_agents}")

        return cls(
            use_case_id=use_case_id,
            intent=str(value["intent"]),
            tasks=[str(task) for task in value["tasks"]],
            agents=agents,
            privacy_requirements=[str(item) for item in value["privacy_requirements"]],
            open_questions=[str(item) for item in value["open_questions"]],
            confidence=float(value["confidence"]),
        )


def _normalize(text: str) -> str:
    return " ".join(text.lower().replace("-", " ").split())


def analyze_natural_language_request(
    user_request: str,
    *,
    client: OllamaClient | None = None,
    seed: int = 42,
    temperature: float = 0.0,
) -> tuple[RequestAnalysis, OllamaJsonResponse]:
    if not user_request.strip():
        raise ValueError("Die Nutzeranfrage darf nicht leer sein.")
    ollama = client or OllamaClient()
    response = ollama.chat_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=(
            "Analysiere die folgende LMS-Nutzeranfrage. Nutze nur die erlaubten Agentenrollen.\n\n"
            f"Nutzeranfrage:\n{user_request.strip()}"
        ),
        json_schema=REQUEST_ANALYSIS_SCHEMA,
        seed=seed,
        temperature=temperature,
        num_ctx=4096,
    )
    return RequestAnalysis.from_dict(response.content), response


def validate_use_case_selection(
    analysis: RequestAnalysis,
    user_request: str,
) -> tuple[str, bool, Dict[str, int]]:
    """Validiert nur unsichere bzw. unbekannte Modellklassifikationen.

    Eine bereits eindeutige LLM-Zuordnung wird nicht überschrieben. Bei `unknown`
    oder einer Konfidenz unter 0,70 kann ein transparenter Keyword-Score einen
    Szenariotyp ergänzen. Rohe und validierte Entscheidung werden getrennt gespeichert.
    """
    text = _normalize(
        " ".join([
            user_request,
            analysis.intent,
            *analysis.tasks,
            *analysis.privacy_requirements,
        ])
    )
    scores = {
        use_case_id: sum(1 for term in terms if term in text)
        for use_case_id, terms in CLASSIFICATION_TERMS.items()
    }

    if analysis.use_case_id != "unknown" and analysis.confidence >= 0.70:
        return analysis.use_case_id, False, scores

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_id, best_score = ranked[0]
    second_score = ranked[1][1]
    if best_score >= 2 and best_score > second_score:
        return best_id, best_id != analysis.use_case_id, scores
    return analysis.use_case_id, False, scores


def _ordered_selected_agents(selected_agents: Iterable[str]) -> List[str]:
    selected = set(selected_agents)
    return [agent for agent in CANONICAL_AGENT_ORDER if agent in selected]


def complete_agent_selection(
    analysis: RequestAnalysis,
    user_request: str,
    validated_use_case_id: str | None = None,
) -> tuple[List[str], List[str]]:
    """Ergänzt erkennbare Zuständigkeiten deterministisch und nachvollziehbar."""
    use_case_id = validated_use_case_id or analysis.use_case_id
    selected = set(analysis.agents)
    text = _normalize(
        " ".join([
            user_request,
            analysis.intent,
            *analysis.tasks,
            *analysis.privacy_requirements,
        ])
    )

    added: List[str] = []
    for agent_name, terms in AGENT_TRIGGER_TERMS.get(use_case_id, {}).items():
        if agent_name not in selected and any(term in text for term in terms):
            selected.add(agent_name)
            added.append(agent_name)

    return _ordered_selected_agents(selected), _ordered_selected_agents(added)


def build_action_plan_from_analysis(
    user_request: str,
    analysis: RequestAnalysis,
    *,
    validated_use_case_id: str | None = None,
    classification_changed: bool | None = None,
    classification_scores: Dict[str, int] | None = None,
) -> tuple[ActionPlan, Dict[str, Any]]:
    """Erzeugt den hybriden ActionPlan ohne einen zweiten LLM-Aufruf.

    Diese Funktion ermöglicht eine faire Auswertung: dieselbe rohe Modellantwort
    wird einmal als LLM-Leistung und anschließend als Eingabe der deterministischen
    Validierungs- und Agentenschicht verwendet.
    """
    if validated_use_case_id is None or classification_changed is None or classification_scores is None:
        resolved_id, changed, scores = validate_use_case_selection(analysis, user_request)
        validated_use_case_id = resolved_id
        classification_changed = changed
        classification_scores = scores

    if validated_use_case_id == "unknown":
        raise ValueError(
            "Die Anfrage konnte keinem unterstützten LMS-Szenario sicher zugeordnet werden. "
            f"Offene Fragen: {analysis.open_questions}"
        )

    data = get_use_case_data(validated_use_case_id)
    plan = ActionPlan(
        use_case_id=validated_use_case_id,
        title=data["title"],
        user_request=user_request,
    )
    plan.add_agent("Orchestrator Agent")
    for task in analysis.tasks:
        plan.add_task(task)
    for question in analysis.open_questions:
        plan.add_open_question(question)
    for privacy_requirement in analysis.privacy_requirements:
        plan.add_task(f"Governance-Anforderung berücksichtigen: {privacy_requirement}")

    selected_agents, added_agents = complete_agent_selection(
        analysis, user_request, validated_use_case_id
    )
    if classification_changed:
        plan.add_task(
            "Deterministische Klassifikationsvalidierung ergänzte: "
            f"{validated_use_case_id}"
        )
    if added_agents:
        plan.add_task(
            "Deterministische Agentenvalidierung ergänzte: " + ", ".join(added_agents)
        )
    for agent_name in selected_agents:
        AGENT_RUNNERS[agent_name](validated_use_case_id, data, plan)

    validation = {
        "raw_use_case_id": analysis.use_case_id,
        "validated_use_case_id": validated_use_case_id,
        "classification_changed": bool(classification_changed),
        "classification_scores": classification_scores,
        "raw_agents": analysis.agents,
        "agents_added_by_validator": added_agents,
        "effective_agents": selected_agents,
    }
    return plan, validation


def orchestrate_natural_language_request(
    user_request: str,
    *,
    client: OllamaClient | None = None,
    seed: int = 42,
    temperature: float = 0.0,
) -> tuple[ActionPlan, RequestAnalysis, OllamaJsonResponse, Dict[str, Any]]:
    analysis, response = analyze_natural_language_request(
        user_request,
        client=client,
        seed=seed,
        temperature=temperature,
    )
    validated_use_case_id, class_changed, class_scores = validate_use_case_selection(
        analysis, user_request
    )
    plan, validation = build_action_plan_from_analysis(
        user_request,
        analysis,
        validated_use_case_id=validated_use_case_id,
        classification_changed=class_changed,
        classification_scores=class_scores,
    )
    return plan, analysis, response, validation
