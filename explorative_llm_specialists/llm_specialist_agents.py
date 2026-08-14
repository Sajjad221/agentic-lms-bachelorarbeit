"""LLM-basierte Fachagenten fuer den experimentellen Multi-Agent-Puffer v3.2.

WICHTIG:
- Diese Erweiterung ist NICHT Teil des eingefrorenen v4-Holdout-Artefakts.
- Alle Fachagenten verwenden dasselbe lokal geladene Qwen3-Modell ueber Ollama,
  aber mit getrennten Rollenprompts, Tool-Budgets und strukturierten Ausgaben.
- Agenten duerfen nur lesende LMS-Werkzeuge anfordern und keine produktive
  Aktion ausfuehren. Die finale Governance bleibt deterministisch.
- v3 behaelt die strikte Rollenabgrenzung bei und nutzt einen verifizierten
  geteilten Tool-Kontext; explizite Fakten werden zusaetzlich deterministisch
  gegen Anfrage und gelesene Daten geprueft.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Mapping

from ollama_client import OllamaClient, OllamaJsonResponse


AGENT_NAMES: tuple[str, ...] = (
    "Course Agent",
    "Content Agent",
    "Enrollment Agent",
    "Assignment Agent",
    "Notification Agent",
    "Analytics/Metrics Agent",
    "Policy/Permission Agent",
)


TOOL_FUNCTIONS: Dict[str, Callable[[Dict[str, Any]], Any]] = {
    "read_course": lambda data: data.get("course", {}),
    "read_modules": lambda data: data.get("modules", []),
    "read_groups": lambda data: data.get("groups", []),
    "read_users": lambda data: data.get("users", []),
    "read_test_results": lambda data: data.get("test_results", {}),
    "read_permission_rules": lambda data: data.get("permission_rules", []),
    "read_compliance_requirement": lambda data: data.get("compliance_requirement", {}),
}


@dataclass(frozen=True)
class SpecialistConfig:
    name: str
    goal: str
    scope: str
    ownership_contract: str
    allowed_tools: tuple[str, ...]
    status_guidance: str
    max_actions: int = 3


AGENT_CONFIGS: Dict[str, SpecialistConfig] = {
    "Course Agent": SpecialistConfig(
        name="Course Agent",
        goal="Plane ausschliesslich Kursstruktur und Lernpfadstruktur.",
        scope=(
            "Du darfst Reihenfolge, Aufbau und Struktur eines Kurses/Lernpfads bearbeiten. "
            "Keine Content-Pflege, keine Zielgruppen-/Einschreibungsaktion, keine Nachricht, "
            "keine Analyse und keine Rechteentscheidung."
        ),
        ownership_contract=(
            "Eigene Aktionen: Kurs/Lernpfad anlegen oder strukturieren, Kursstruktur anpassen. "
            "Nicht deine Aktionen: Module inhaltlich aktualisieren, Zielgruppen definieren, Fristen, "
            "Benachrichtigungen, Reporting oder Governance-Entscheidungen."
        ),
        allowed_tools=("read_course", "read_modules"),
        status_guidance=(
            "Vorbereitende Strukturvorschlaege koennen erlaubt sein. Produktive Kursaenderungen "
            "oder Veroeffentlichungen sind mindestens freigabepflichtig."
        ),
    ),
    "Content Agent": SpecialistConfig(
        name="Content Agent",
        goal="Pruefe ausschliesslich Lerninhalte/Module auf Vorhandensein, Luecken und Aktualitaet.",
        scope=(
            "Du darfst Inhalte einbinden, fehlende Inhalte markieren und veraltete Inhalte zur "
            "Aktualisierung vorschlagen. Keine Zielgruppen, Fristen, Benachrichtigungen, Reports "
            "oder Rechteentscheidungen."
        ),
        ownership_contract=(
            "Eigene Aktionen: vorhandene Module einbinden, fehlende Module markieren/ergaenzen, "
            "veraltete Module markieren/aktualisieren. Nicht deine Aktionen: Zielgruppe, Frist, "
            "Lernenden-Kommunikation, Reporting, Einschreibung."
        ),
        allowed_tools=("read_course", "read_modules"),
        status_guidance=(
            "Markierungen und redaktionelle Vorschlaege koennen vorbereitend erlaubt sein. "
            "Produktive Publikation oder Aenderung ist mindestens freigabepflichtig."
        ),
    ),
    "Enrollment Agent": SpecialistConfig(
        name="Enrollment Agent",
        goal="Bestimme ausschliesslich Zielgruppen und plane Einschreibungen/Zuweisungen.",
        scope=(
            "Du darfst Gruppen/Zielgruppen bestimmen und Zuweisungen/Einschreibungen vorschlagen. "
            "Keine Kursstruktur, Content-Pflege, Fristen, Nachrichten, Analysen oder Rechtefreigaben."
        ),
        ownership_contract=(
            "Eigene Aktionen: Zielgruppe bestimmen, Einschreibung/Zuweisung planen. "
            "Nicht deine Aktionen: Lernpfad erstellen, Inhalte einbinden, Module aktualisieren, "
            "Fristen setzen, Reporting oder Nachrichten."
        ),
        allowed_tools=("read_groups", "read_users", "read_permission_rules", "read_compliance_requirement"),
        status_guidance=(
            "Reine Zielgruppenbestimmung kann erlaubt sein. Personenwirksame Einschreibung oder "
            "Zuweisung ist mindestens freigabepflichtig."
        ),
    ),
    "Assignment Agent": SpecialistConfig(
        name="Assignment Agent",
        goal="Plane ausschliesslich Aufgaben, Fristen und Wiederholungsaktivitaeten.",
        scope=(
            "Du darfst Fristen, Aufgaben und Wiederholungsaufgaben vorschlagen. Eine Wiederholungsaufgabe "
            "darfst du nur vorschlagen, wenn Wiederholung/erneute Bearbeitung in der Nutzeranfrage oder in DEINEN "
            "zugewiesenen Teilaufgaben explizit verlangt wird; fehlender oder veralteter Content allein reicht nicht. "
            "Wenn nur fremde Aufgaben vorliegen, gib 0 Aktionen aus. Keine Kursstruktur, Content-Pflege, "
            "Zielgruppenbestimmung, Nachrichten, Reporting oder Rechteentscheidung."
        ),
        ownership_contract=(
            "Eigene Aktionen: Frist setzen, Wiederholungsaufgabe/Aufgabe planen. "
            "Nicht deine Aktionen: Lernpfad erstellen, Module aktualisieren, Zielgruppe definieren, "
            "Benachrichtigungen oder Reporting."
        ),
        allowed_tools=("read_course", "read_test_results", "read_compliance_requirement"),
        status_guidance=(
            "Frist-/Aufgabenvorschlaege koennen vorbereitend erlaubt sein. Leistungsabhaengige oder "
            "personenwirksame Zuweisungen sind mindestens freigabepflichtig."
        ),
    ),
    "Notification Agent": SpecialistConfig(
        name="Notification Agent",
        goal="Plane ausschliesslich Benachrichtigungen, Lernhinweise und Erinnerungen.",
        scope=(
            "Du darfst nur Kommunikationsaktionen vorschlagen. Keine Kurs-/Content-Aenderungen, "
            "Zielgruppenanlage, Analyse oder Rechteentscheidung. Keine individuellen Leistungsdaten "
            "an unberechtigte Rollen offenlegen."
        ),
        ownership_contract=(
            "Eigene Aktionen: informieren, benachrichtigen, erinnern. Nicht deine Aktionen: "
            "Lernpfad erstellen, Inhalte pruefen, Fristen festlegen, Reports analysieren."
        ),
        allowed_tools=("read_groups", "read_permission_rules", "read_compliance_requirement"),
        status_guidance=(
            "Nachrichten an Personen oder Eskalationen sind grundsaetzlich freigabepflichtig. "
            "Unzulaessige personenbezogene Offenlegung ist zu blockieren."
        ),
    ),
    "Analytics/Metrics Agent": SpecialistConfig(
        name="Analytics/Metrics Agent",
        goal="Fuehre ausschliesslich Analyse, Kennzahlenbildung, Gruppenvergleich und Reportingplanung durch.",
        scope=(
            "Du darfst Ergebnisse analysieren und aggregiertes Reporting vorschlagen. Keine Kursstruktur, "
            "Content-Pflege, Zielgruppenanlage, Fristen oder Nachrichten. Bevorzuge aggregierte Aussagen. "
            "Erfinde keine Reporting-Intervalle oder Kommunikationskanaele. Wenn diese nicht vorgegeben sind, "
            "formuliere sie als offene Rueckfrage statt als Aktionsparameter."
        ),
        ownership_contract=(
            "Eigene Aktionen: Testergebnisse analysieren, Gruppen vergleichen, Kennzahlen/aggregierte Reports "
            "erstellen. Nicht deine Aktionen: Lernpfad erstellen, Inhalte aktualisieren, Zielgruppe definieren, "
            "Fristen setzen oder Benachrichtigungen senden."
        ),
        allowed_tools=("read_test_results", "read_groups", "read_permission_rules", "read_compliance_requirement"),
        status_guidance=(
            "Interne aggregierte Analyse kann erlaubt sein. Personenbezogenes Reporting an Dritte kann "
            "freigabepflichtig oder blockiert sein."
        ),
    ),
    "Policy/Permission Agent": SpecialistConfig(
        name="Policy/Permission Agent",
        goal="Pruefe ausschliesslich Rollen, Rechte, Datenschutz, Freigaben und Blockierungsbedarf.",
        scope=(
            "Du darfst nur Governance-Kontrollen/Restriktionen vorschlagen. Wiederhole keine operative Aktion "
            "eines anderen Fachagenten. Bewerte keine didaktische Qualitaet und pflege keine Inhalte."
        ),
        ownership_contract=(
            "Eigene Aktionen: Offenlegung blockieren, Aggregation erzwingen, Freigabe verlangen, "
            "Datenminimierung/Rollenrechte festhalten. Nicht deine Aktionen: Kurs, Content, Zielgruppe, "
            "Frist oder Nachricht selbst anlegen."
        ),
        allowed_tools=("read_permission_rules", "read_compliance_requirement", "read_groups"),
        status_guidance=(
            "Bei klarem Verbot: blockiert. Bei Freigabepflicht oder personenwirksamer Wirkung: "
            "freigabepflichtig. Governance-Kontrollen duerfen keine operative Aktion duplizieren."
        ),
    ),
}


TOOL_SELECTION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "requested_tools": {
            "type": "array",
            "uniqueItems": True,
            "maxItems": 4,
            "items": {"type": "string", "enum": list(TOOL_FUNCTIONS)},
        },
        "plan_summary": {"type": "string", "minLength": 3, "maxLength": 220},
    },
    "required": ["requested_tools", "plan_summary"],
}


SPECIALIST_OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "agent_name": {"type": "string", "enum": list(AGENT_NAMES)},
        "observations": {
            "type": "array",
            "maxItems": 3,
            "items": {"type": "string", "minLength": 3, "maxLength": 220},
        },
        "proposed_actions": {
            "type": "array",
            "maxItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "action": {"type": "string", "minLength": 3, "maxLength": 180},
                    "requested_status": {
                        "type": "string",
                        "enum": ["erlaubt", "freigabepflichtig", "blockiert"],
                    },
                    "reason": {"type": "string", "minLength": 3, "maxLength": 320},
                    "used_data": {
                        "type": "array",
                        "uniqueItems": True,
                        "maxItems": 6,
                        "items": {"type": "string", "minLength": 2, "maxLength": 80},
                    },
                    "uncertainties": {
                        "type": "array",
                        "maxItems": 2,
                        "items": {"type": "string", "minLength": 3, "maxLength": 220},
                    },
                },
                "required": ["action", "requested_status", "reason", "used_data", "uncertainties"],
            },
        },
        "open_questions": {
            "type": "array",
            "maxItems": 2,
            "items": {"type": "string", "minLength": 3, "maxLength": 220},
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["agent_name", "observations", "proposed_actions", "open_questions", "confidence"],
}


@dataclass(frozen=True)
class SpecialistAction:
    action: str
    requested_status: str
    reason: str
    used_data: List[str]
    uncertainties: List[str]


@dataclass(frozen=True)
class SpecialistResult:
    agent_name: str
    requested_tools: List[str]
    plan_summary: str
    observations: List[str]
    proposed_actions: List[SpecialistAction]
    open_questions: List[str]
    confidence: float
    tool_metrics: OllamaJsonResponse
    action_metrics: OllamaJsonResponse


class LLMSpecialistAgent:
    """LLM-Fachagent mit eigenem Ziel, Tool-Budget und zwei LLM-Schritten."""

    def __init__(self, config: SpecialistConfig, client: OllamaClient) -> None:
        self.config = config
        self.client = client

    def _system_prompt(self) -> str:
        allowed = ", ".join(self.config.allowed_tools)
        return f"""
Du bist der spezialisierte {self.config.name} eines agentenbasierten Learning-Management-Systems.

Dein Ziel:
{self.config.goal}

Deine fachliche Grenze:
{self.config.scope}

Verbindlicher Ownership-Vertrag:
{self.config.ownership_contract}

Zulaessige lesende Werkzeuge:
{allowed}

Governance-Hinweis:
{self.config.status_guidance}

Regeln:
1. Bleibe strikt in deiner Rolle. Uebernimm keine Aufgabe eines anderen Fachagenten.
2. Fordere nur Werkzeuge an, die fuer DEINE konkrete Fachaufgabe notwendig sind.
3. Du darfst keine produktive LMS-Aktion selbst ausfuehren; du erzeugst nur strukturierte Vorschlaege.
4. Erfinde keine Daten, Rechte, Nutzerinformationen oder Tool-Ergebnisse.
5. Wenn fuer deine Rolle keine Aktion notwendig ist, gib proposed_actions als leere Liste zurueck.
6. Erzeuge hoechstens {self.config.max_actions} unterschiedliche Aktionsvorschlaege und keine Synonym-Duplikate.
7. Wenn Daten fehlen, nutze uncertainties/open_questions statt fremde Aufgaben zu uebernehmen.
8. Der Status ist nur dein Vorschlag; eine deterministische Governance-Schicht darf ihn verschaerfen.
9. Trage in used_data kanonische Tool-Namen ein (z. B. read_modules, nicht verified_tool_outputs.read_modules). Alternativ sind user_request, tasks, privacy_requirements oder shared_context zulaessig.
10. Fuer den Assignment Agent gilt besonders: Jede Aktion muss direkt einer DEINER zugewiesenen Teilaufgaben entsprechen. Eine Frist-Aufgabe erlaubt nur Fristaktionen; sie legitimiert keine generische Aufgabe oder Wiederholungsaufgabe. Fehlt ein expliziter Assignment-/Frist-/Wiederholungsauftrag, gib 0 Aktionen aus.
11. Fuer Analytics gilt: Keine frei gewaehlteten Reporting-Intervalle oder Kanaele (z. B. woechentlich, E-Mail, Dashboard) als Aktionen erfinden; bei fehlender Vorgabe open_questions nutzen.
12. Erfinde insbesondere keine Prozentwerte, Fristen, IDs oder konkreten Fortschrittswerte.
13. Gib ausschliesslich das jeweils angeforderte JSON-Objekt zurueck.
14. Formuliere Beobachtungen, Begruendungen und Rueckfragen knapp; keine langen Erklaerungen oder Wiederholungen.
""".strip()

    def plan_tools(
        self,
        *,
        user_request: str,
        use_case_id: str,
        tasks: Iterable[str],
        privacy_requirements: Iterable[str],
        seed: int,
        temperature: float,
    ) -> tuple[List[str], str, OllamaJsonResponse]:
        allowed_schema = json.loads(json.dumps(TOOL_SELECTION_SCHEMA))
        allowed_schema["properties"]["requested_tools"]["items"]["enum"] = list(self.config.allowed_tools)
        allowed_schema["properties"]["requested_tools"]["maxItems"] = len(self.config.allowed_tools)
        response = self.client.chat_json(
            system_prompt=self._system_prompt(),
            user_prompt=(
                "Waehle fuer deine Fachaufgabe die minimal notwendigen lesenden Werkzeuge.\n"
                f"Use Case: {use_case_id}\n"
                f"Nutzeranfrage: {user_request}\n"
                f"DEINE zugewiesenen Teilaufgaben: {json.dumps(list(tasks), ensure_ascii=False)}\n"
                f"Governance-Anforderungen: {json.dumps(list(privacy_requirements), ensure_ascii=False)}"
            ),
            json_schema=allowed_schema,
            seed=seed,
            temperature=temperature,
            num_ctx=4096,
            num_predict=160,
        )
        requested = [str(item) for item in response.content.get("requested_tools", [])]
        invalid = [tool for tool in requested if tool not in self.config.allowed_tools]
        if invalid:
            raise ValueError(f"{self.config.name} forderte unzulaessige Tools an: {invalid}")
        return requested, str(response.content.get("plan_summary", "")), response

    def execute_tools(self, requested_tools: Iterable[str], data: Dict[str, Any]) -> Dict[str, Any]:
        observations: Dict[str, Any] = {}
        for tool_name in requested_tools:
            if tool_name not in self.config.allowed_tools:
                raise ValueError(f"Tool {tool_name} ist fuer {self.config.name} nicht freigegeben.")
            observations[tool_name] = TOOL_FUNCTIONS[tool_name](data)
        return observations

    def propose_actions(
        self,
        *,
        user_request: str,
        use_case_id: str,
        tasks: Iterable[str],
        privacy_requirements: Iterable[str],
        requested_tools: Iterable[str],
        tool_outputs: Dict[str, Any],
        shared_context: Mapping[str, Any] | None,
        seed: int,
        temperature: float,
    ) -> tuple[SpecialistResult, OllamaJsonResponse]:
        shared_text = ""
        if shared_context:
            shared_text = (
                "\nVerifizierter geteilter Tool-Kontext aus bereits ausgefuehrten lesenden Werkzeugen (nur als Fakten-/Governance-Kontext; "
                "deren operative Aktionen NICHT wiederholen):\n"
                + json.dumps(dict(shared_context), ensure_ascii=False, indent=2)
            )
        response = self.client.chat_json(
            system_prompt=self._system_prompt(),
            user_prompt=(
                "Erstelle jetzt nur die Beobachtungen und Aktionsvorschlaege, die zu deiner Rolle gehoeren.\n"
                f"Use Case: {use_case_id}\n"
                f"Nutzeranfrage: {user_request}\n"
                f"DEINE zugewiesenen Teilaufgaben: {json.dumps(list(tasks), ensure_ascii=False)}\n"
                f"Governance-Anforderungen: {json.dumps(list(privacy_requirements), ensure_ascii=False)}\n"
                f"Verwendete Tools: {json.dumps(list(requested_tools), ensure_ascii=False)}\n"
                "Tool-Ausgaben:\n"
                f"{json.dumps(tool_outputs, ensure_ascii=False, indent=2)}"
                f"{shared_text}"
            ),
            json_schema=SPECIALIST_OUTPUT_SCHEMA,
            seed=seed,
            temperature=temperature,
            num_ctx=4096,
            num_predict=1536,
        )
        content = response.content
        if str(content.get("agent_name")) != self.config.name:
            raise ValueError(
                f"Agentenidentitaet stimmt nicht: erwartet {self.config.name}, erhalten {content.get('agent_name')}"
            )
        actions = [
            SpecialistAction(
                action=str(item["action"]),
                requested_status=str(item["requested_status"]),
                reason=str(item["reason"]),
                used_data=[str(x) for x in item.get("used_data", [])],
                uncertainties=[str(x) for x in item.get("uncertainties", [])],
            )
            for item in content.get("proposed_actions", [])[: self.config.max_actions]
        ]
        result = SpecialistResult(
            agent_name=self.config.name,
            requested_tools=list(requested_tools),
            plan_summary="",
            observations=[str(x) for x in content.get("observations", [])[:5]],
            proposed_actions=actions,
            open_questions=[str(x) for x in content.get("open_questions", [])[:2]],
            confidence=float(content.get("confidence", 0.0)),
            tool_metrics=response,  # Controller ersetzt dies durch echte Tool-Plan-Metrik
            action_metrics=response,
        )
        return result, response

    def run(
        self,
        *,
        user_request: str,
        use_case_id: str,
        tasks: Iterable[str],
        privacy_requirements: Iterable[str],
        data: Dict[str, Any],
        shared_context: Mapping[str, Any] | None = None,
        seed: int = 42,
        temperature: float = 0.0,
    ) -> SpecialistResult:
        print(f"[LLM] {self.config.name}: Tool-Auswahl startet ...", flush=True)
        requested_tools, summary, tool_response = self.plan_tools(
            user_request=user_request,
            use_case_id=use_case_id,
            tasks=tasks,
            privacy_requirements=privacy_requirements,
            seed=seed,
            temperature=temperature,
        )
        print(f"[LLM] {self.config.name}: Tool-Auswahl fertig ({tool_response.metrics.total_duration_ms/1000:.2f}s)", flush=True)
        outputs = self.execute_tools(requested_tools, data)
        print(f"[LLM] {self.config.name}: Aktionsplanung startet ...", flush=True)
        result, action_response = self.propose_actions(
            user_request=user_request,
            use_case_id=use_case_id,
            tasks=tasks,
            privacy_requirements=privacy_requirements,
            requested_tools=requested_tools,
            tool_outputs=outputs,
            shared_context=shared_context,
            seed=seed + 1000,
            temperature=temperature,
        )
        print(f"[LLM] {self.config.name}: Aktionsplanung fertig ({action_response.metrics.total_duration_ms/1000:.2f}s)", flush=True)
        return SpecialistResult(
            agent_name=result.agent_name,
            requested_tools=requested_tools,
            plan_summary=summary,
            observations=result.observations,
            proposed_actions=result.proposed_actions,
            open_questions=result.open_questions,
            confidence=result.confidence,
            tool_metrics=tool_response,
            action_metrics=action_response,
        )


def build_specialist_agents(client: OllamaClient) -> Dict[str, LLMSpecialistAgent]:
    return {name: LLMSpecialistAgent(config, client) for name, config in AGENT_CONFIGS.items()}
