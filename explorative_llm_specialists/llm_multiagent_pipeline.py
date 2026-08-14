"""Experimentelle LLM-Multi-Agent-Pipeline v3.2.

v3.2 bleibt ein separater technischer Puffer und veraendert das eingefrorene
v4-Holdout-Artefakt nicht.

Finalisierungen aus v3.1 plus v3.2-Haertung:
- Provenienz-Normalisierung fuer Varianten wie verified_tool_outputs.read_modules,
- strengere Assignment-Regeln; bei fehlender eigener Aufgabe sind 0 Aktionen erlaubt,
- deterministische negative Datenschutzanforderungen werden als direkte
  blockierte Handlungen im ActionPlan abgebildet,
- Ownership, Grounding, Konsolidierung und Governance bleiben getrennt sichtbar,
- Assignment-Vorschlaege werden deterministisch gegen die konkret zugewiesenen Teilaufgaben geprueft,
- produktive Verben wie setzen/aktivieren/einrichten/zuordnen werden mindestens freigabepflichtig,
- nicht belegte Reporting-Intervalle und Kommunikationskanaele werden im Grounding verworfen.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from action_plan import ActionPlan
from grounding_validation import (
    GroundingDecision,
    normalize_used_data_references,
    validate_grounding,
)
from llm_orchestrator import (
    RequestAnalysis,
    analyze_natural_language_request,
    complete_agent_selection,
    validate_use_case_selection,
)
from llm_specialist_agents import (
    AGENT_CONFIGS,
    TOOL_FUNCTIONS,
    SpecialistAction,
    SpecialistResult,
    build_specialist_agents,
)
from lms_backend import get_use_case_data
from multiagent_consolidation import (
    GovernedProposal,
    OwnershipDecision,
    consolidate_governed_proposals,
    dedupe_questions,
    validate_ownership,
)
from ollama_client import OllamaClient, OllamaJsonResponse


STATUS_RANK = {"erlaubt": 0, "freigabepflichtig": 1, "blockiert": 2}


@dataclass(frozen=True)
class GovernanceDecision:
    agent_name: str
    action: str
    requested_status: str
    final_status: str
    changed: bool
    rule: str


@dataclass(frozen=True)
class MultiAgentRun:
    plan: ActionPlan
    analysis: RequestAnalysis
    orchestrator_response: OllamaJsonResponse
    validation: Dict[str, Any]
    specialist_results: List[SpecialistResult]
    ownership_decisions: List[OwnershipDecision]
    grounding_decisions: List[GroundingDecision]
    governance_decisions: List[GovernanceDecision]
    consolidation: Dict[str, Any]
    shared_context: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "analysis": {
                "use_case_id": self.analysis.use_case_id,
                "intent": self.analysis.intent,
                "tasks": self.analysis.tasks,
                "agents": self.analysis.agents,
                "privacy_requirements": self.analysis.privacy_requirements,
                "open_questions": self.analysis.open_questions,
                "confidence": self.analysis.confidence,
            },
            "validation": self.validation,
            "specialist_results": [
                {
                    "agent_name": result.agent_name,
                    "requested_tools": result.requested_tools,
                    "plan_summary": result.plan_summary,
                    "observations": result.observations,
                    "proposed_actions": [asdict(action) for action in result.proposed_actions],
                    "open_questions": result.open_questions,
                    "confidence": result.confidence,
                    "tool_call_metrics": {
                        "total_duration_ms": result.tool_metrics.metrics.total_duration_ms,
                        "prompt_tokens": result.tool_metrics.metrics.prompt_tokens,
                        "output_tokens": result.tool_metrics.metrics.output_tokens,
                    },
                    "action_call_metrics": {
                        "total_duration_ms": result.action_metrics.metrics.total_duration_ms,
                        "prompt_tokens": result.action_metrics.metrics.prompt_tokens,
                        "output_tokens": result.action_metrics.metrics.output_tokens,
                    },
                }
                for result in self.specialist_results
            ],
            "ownership_decisions": [asdict(item) for item in self.ownership_decisions],
            "grounding_decisions": [asdict(item) for item in self.grounding_decisions],
            "governance_decisions": [asdict(item) for item in self.governance_decisions],
            "consolidation": self.consolidation,
            "shared_context": self.shared_context,
            "orchestrator_metrics": {
                "total_duration_ms": self.orchestrator_response.metrics.total_duration_ms,
                "prompt_tokens": self.orchestrator_response.metrics.prompt_tokens,
                "output_tokens": self.orchestrator_response.metrics.output_tokens,
            },
        }


def _normalize(text: str) -> str:
    return " ".join(
        text.lower()
        .replace("-", " ")
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
        .split()
    )


def _escalate(current: str, candidate: str) -> str:
    return candidate if STATUS_RANK[candidate] > STATUS_RANK[current] else current


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    return any(_normalize(term) in text for term in terms)


def enforce_governance(*, use_case_id: str, agent_name: str, proposal: SpecialistAction) -> Tuple[str, str]:
    """Deterministische Minimal-Governance; Status kann nur strenger werden."""
    requested = proposal.requested_status if proposal.requested_status in STATUS_RANK else "freigabepflichtig"
    final = requested
    text = _normalize(" ".join([proposal.action, proposal.reason, *proposal.uncertainties]))
    rules: List[str] = []

    approval_terms = (
        "veroeffentlich", "einschreib", "zuweis", "zuordn", "versend", "senden", "benachr", "erinner",
        "eskal", "kurs aender", "kurs anpassen", "kursanpass", "hinzufueg", "einbind", "integrier", "aktualis",
        "setzen", "aktivier", "einricht", "konfigurier", "aender",
        "wiederholungsaufgabe zuweis", "pflichtschulung zuweis",
    )
    if _contains_any(text, approval_terms):
        next_status = _escalate(final, "freigabepflichtig")
        if next_status != final:
            final = next_status
            rules.append("personenwirksame/produktive Aktion => mindestens freigabepflichtig")

    if use_case_id == "use_case_1":
        if _contains_any(text, ("personenbezogene fortschritt", "individuelle fortschritt")) and _contains_any(text, ("teamleiter", "teamleitung")):
            final = "blockiert"
            rules.append("UC1: Teamleitung darf nur aggregierten Fortschritt erhalten")
    elif use_case_id == "use_case_2":
        if _contains_any(text, ("personenbezogene testergebnis", "individuelle testergebnis", "individuelle leistungs")) and _contains_any(text, ("teamleiter", "teamleitung")):
            final = "blockiert"
            rules.append("UC2: individuelle Testergebnisse nicht an Teamleitung")
    elif use_case_id == "use_case_3":
        if _contains_any(text, ("personenbezogene leistungs", "individuelle score", "individuelle testergebnis")) and _contains_any(text, ("hr", "teamleiter", "teamleitung", "compliance")):
            final = "blockiert"
            rules.append("UC3: keine unnoetigen individuellen Leistungsdaten an HR/Teamleitung/Compliance")
        if "eskal" in text:
            next_status = _escalate(final, "freigabepflichtig")
            if next_status != final:
                final = next_status
            rules.append("UC3: Eskalation benoetigt Freigabe")

    if proposal.uncertainties and _contains_any(text, ("berechtig", "datenschutz", "personenbez", "freigabe", "unklar")):
        next_status = _escalate(final, "freigabepflichtig")
        if next_status != final:
            final = next_status
            rules.append("Governance-Unsicherheit => mindestens freigabepflichtig")

    if not rules:
        rules.append("LLM-Status beibehalten; keine strengere deterministische Regel ausgeloest")
    return final, "; ".join(rules)


TASK_ROUTE_TERMS: Dict[str, tuple[str, ...]] = {
    "Course Agent": ("kurs", "lernpath", "lern pfad", "lernpfad", "schulung", "struktur", "anpass"),
    "Content Agent": ("inhalt", "modul", "lernmaterial", "material", "themenbereich", "veraltet", "fehlend", "aktualis", "einbind", "ueberarbeit"),
    "Enrollment Agent": ("zielgruppe", "gruppe", "einschreib", "zuweis", "rollenbasiert", "mitarbeit", "werkstudent"),
    "Assignment Agent": ("frist", "aufgabe", "wiederholung", "14 tag"),
    "Notification Agent": ("inform", "benachr", "erinner", "nachricht"),
    "Analytics/Metrics Agent": ("analys", "auswert", "testergebnis", "fortschritt", "report", "kennzahl", "durchschnitt", "vergleich", "aggreg"),
    "Policy/Permission Agent": ("datenschutz", "aggreg", "individuell", "personenbez", "rolle", "recht", "berechtig", "freigab", "compliance"),
}


def _tasks_for_agent(analysis: RequestAnalysis, agent_name: str) -> List[str]:
    terms = tuple(_normalize(t) for t in TASK_ROUTE_TERMS[agent_name])
    assigned = [task for task in analysis.tasks if any(term in _normalize(task) for term in terms)]
    if agent_name == "Policy/Permission Agent":
        assigned.extend(f"Governance: {r}" for r in analysis.privacy_requirements)
    if not assigned:
        assigned = [f"Rollenfokus: {AGENT_CONFIGS[agent_name].goal}"]
    out: List[str] = []
    seen = set()
    for task in assigned:
        key = _normalize(task)
        if key not in seen:
            seen.add(key)
            out.append(task)
    return out


def _execute_verified_tools(result: SpecialistResult, data: Dict[str, Any]) -> Dict[str, Any]:
    """Fuehrt nur bereits vom Controller freigegebene lesende Tools deterministisch aus."""
    return {tool: TOOL_FUNCTIONS[tool](data) for tool in result.requested_tools if tool in TOOL_FUNCTIONS}


def _compact_verified_context(tool_cache: Mapping[str, Any]) -> Dict[str, Any]:
    if not tool_cache:
        return {}
    # Es werden ausschliesslich echte Tool-Ausgaben geteilt, keine freien LLM-Beobachtungen.
    return {"verified_tool_outputs": dict(tool_cache)}


def _normalize_proposal_provenance(proposal: SpecialistAction) -> SpecialistAction:
    """Kanonisiert used_data, ohne Inhalt/Status des LLM-Vorschlags zu veraendern."""
    normalized = normalize_used_data_references(proposal.used_data)
    if normalized == proposal.used_data:
        return proposal
    return replace(proposal, used_data=normalized)


def _deterministic_privacy_controls(
    *,
    use_case_id: str,
    user_request: str,
    privacy_requirements: Iterable[str],
) -> List[GovernedProposal]:
    """Uebersetzt explizite negative Schutzregeln in direkt blockierte Handlungen.

    Damit steht im ActionPlan nicht ``Keine individuellen Daten ... = erlaubt``,
    sondern die tatsaechlich untersagte Handlung mit Status ``blockiert``.
    Die Regeln werden nur aus expliziten Anforderungen der Anfrage/LLM-Analyse
    abgeleitet und nicht als neue fachliche Annahmen erfunden.
    """
    combined = _normalize(" ".join([user_request, *list(privacy_requirements)]))
    controls: List[GovernedProposal] = []

    def add(action: str, reason: str) -> None:
        proposal = SpecialistAction(
            action=action,
            requested_status="blockiert",
            reason=reason,
            used_data=["privacy_requirements"],
            uncertainties=[],
        )
        controls.append(
            GovernedProposal(
                agent_name="Deterministic Governance Controller",
                proposal=proposal,
                final_status="blockiert",
                governance_rule="Explizite negative Datenschutzanforderung => blockiert",
            )
        )

    if use_case_id == "use_case_1":
        if (
            _contains_any(combined, ("teamleiter", "teamleitung"))
            and _contains_any(combined, ("nur aggregiert", "keine individuell", "keine personenbez"))
        ):
            add(
                "Individuelle Fortschrittsdaten an Teamleiter uebermitteln",
                "Die Anfrage erlaubt gegenueber Teamleitern nur aggregierte Fortschrittsinformationen.",
            )
    elif use_case_id == "use_case_2":
        if (
            _contains_any(combined, ("teamleiter", "teamleitung"))
            and _contains_any(combined, ("individuell", "personenbez"))
            and _contains_any(combined, ("testergebnis", "leistungs"))
        ):
            add(
                "Individuelle Testergebnisse oder Leistungsdaten an Teamleiter uebermitteln",
                "Individuelle Testergebnisse duerfen im betrachteten Szenario nicht an die Teamleitung offengelegt werden.",
            )
    elif use_case_id == "use_case_3":
        if (
            _contains_any(combined, ("hr", "compliance", "teamleiter", "teamleitung"))
            and _contains_any(combined, ("personenbez", "individuell", "lerndaten", "leistungsdaten"))
        ):
            add(
                "Nicht erforderliche individuelle Lern- oder Leistungsdaten an HR, Compliance oder Teamleitung uebermitteln",
                "Die Anfrage verlangt Datenminimierung und untersagt unnoetige personenbezogene Lerndaten in diesem Reportingkontext.",
            )

    return controls


def orchestrate_with_llm_specialists(
    user_request: str,
    *,
    client: OllamaClient | None = None,
    seed: int = 42,
    temperature: float = 0.0,
) -> MultiAgentRun:
    ollama = client or OllamaClient()

    analysis, orchestrator_response = analyze_natural_language_request(
        user_request, client=ollama, seed=seed, temperature=temperature
    )
    validated_use_case_id, class_changed, class_scores = validate_use_case_selection(analysis, user_request)
    if validated_use_case_id == "unknown":
        raise ValueError(
            "Die Anfrage konnte keinem unterstuetzten Szenario zugeordnet werden. "
            f"Offene Fragen: {analysis.open_questions}"
        )

    selected_agents, added_agents = complete_agent_selection(analysis, user_request, validated_use_case_id)
    data = get_use_case_data(validated_use_case_id)

    plan = ActionPlan(use_case_id=validated_use_case_id, title=data["title"], user_request=user_request)
    plan.add_agent("Orchestrator Agent (Qwen3)")
    for task in analysis.tasks:
        plan.add_task(task)
    for requirement in analysis.privacy_requirements:
        plan.add_task(f"Governance-Anforderung: {requirement}")

    specialists = build_specialist_agents(ollama)
    specialist_results: List[SpecialistResult] = []
    ownership_decisions: List[OwnershipDecision] = []
    grounding_decisions: List[GroundingDecision] = []
    governance_decisions: List[GovernanceDecision] = []
    governed: List[GovernedProposal] = []

    operational_agents = [a for a in selected_agents if a != "Policy/Permission Agent"]
    execution_order = operational_agents + (["Policy/Permission Agent"] if "Policy/Permission Agent" in selected_agents else [])

    # Cache enthaelt nur echte Backend-/Toolausgaben. Dadurch erhalten spaetere
    # Agenten mehr Kontext, ohne ungepruefte LLM-Beobachtungen als Fakten zu erben.
    verified_tool_cache: Dict[str, Any] = {}

    for index, agent_name in enumerate(execution_order):
        shared_context = _compact_verified_context(verified_tool_cache)
        agent = specialists[agent_name]
        agent_seed = seed + (index + 1) * 100
        assigned_tasks = _tasks_for_agent(analysis, agent_name)

        result = agent.run(
            user_request=user_request,
            use_case_id=validated_use_case_id,
            tasks=assigned_tasks,
            privacy_requirements=analysis.privacy_requirements,
            data=data,
            shared_context=shared_context or None,
            seed=agent_seed,
            temperature=temperature,
        )
        specialist_results.append(result)
        plan.add_agent(f"{agent_name} (Qwen3)")

        own_tool_outputs = _execute_verified_tools(result, data)

        for raw_proposal in result.proposed_actions:
            proposal = _normalize_proposal_provenance(raw_proposal)
            grounding = validate_grounding(
                agent_name=agent_name,
                proposal=proposal,
                user_request=user_request,
                tasks=assigned_tasks,
                privacy_requirements=analysis.privacy_requirements,
                own_tool_outputs=own_tool_outputs,
                shared_context=shared_context,
            )
            grounding_decisions.append(grounding)

            ownership = validate_ownership(agent_name, proposal, assigned_tasks=assigned_tasks)
            ownership_decisions.append(ownership)

            # Beide Filter werden unabhaengig dokumentiert. Nur ein Vorschlag,
            # der fachlich zur Rolle passt UND explizit geerdet ist, darf weiter.
            if not grounding.accepted or not ownership.accepted:
                continue

            final_status, rule = enforce_governance(
                use_case_id=validated_use_case_id,
                agent_name=agent_name,
                proposal=proposal,
            )
            governance_decisions.append(
                GovernanceDecision(
                    agent_name=agent_name,
                    action=proposal.action,
                    requested_status=proposal.requested_status,
                    final_status=final_status,
                    changed=final_status != proposal.requested_status,
                    rule=rule,
                )
            )
            governed.append(
                GovernedProposal(
                    agent_name=agent_name,
                    proposal=proposal,
                    final_status=final_status,
                    governance_rule=rule,
                )
            )

        # Erst nach dem eigenen Lauf wird der verifizierte Tool-Cache fuer die
        # nachfolgenden Agenten erweitert.
        verified_tool_cache.update(own_tool_outputs)

    deterministic_controls = _deterministic_privacy_controls(
        use_case_id=validated_use_case_id,
        user_request=user_request,
        privacy_requirements=analysis.privacy_requirements,
    )
    for control in deterministic_controls:
        governed.append(control)
        governance_decisions.append(
            GovernanceDecision(
                agent_name=control.agent_name,
                action=control.proposal.action,
                requested_status="blockiert",
                final_status="blockiert",
                changed=False,
                rule=control.governance_rule,
            )
        )
    if deterministic_controls:
        plan.add_agent("Deterministic Governance Controller")

    consolidated = consolidate_governed_proposals(governed)
    for item in consolidated:
        plan.add_action(
            action=item.action,
            status=item.status,
            reason=item.reason,
            used_data=item.used_data,
            uncertainties=item.uncertainties,
        )

    all_questions = list(analysis.open_questions)
    for result in specialist_results:
        all_questions.extend(f"{result.agent_name}: {q}" for q in result.open_questions)
    for question in dedupe_questions(all_questions):
        plan.add_open_question(question)

    raw_action_count = sum(len(r.proposed_actions) for r in specialist_results)
    ownership_rejected = sum(1 for d in ownership_decisions if not d.accepted)
    grounding_rejected = sum(1 for d in grounding_decisions if not d.accepted)
    specialist_passed_both = sum(
        1
        for grounding, ownership in zip(grounding_decisions, ownership_decisions)
        if grounding.accepted and ownership.accepted
    )
    passed_both = len(governed)

    consolidation = {
        "raw_specialist_action_count": raw_action_count,
        "ownership_rejected_count": ownership_rejected,
        "grounding_rejected_count": grounding_rejected,
        "passed_ownership_and_grounding_count": specialist_passed_both,
        "deterministic_privacy_control_count": len(deterministic_controls),
        "rejected_by_any_filter_count": raw_action_count - specialist_passed_both,
        "post_governance_proposal_count": len(governed),
        "final_consolidated_action_count": len(consolidated),
        "merged_or_removed_after_filters_count": max(0, len(governed) - len(consolidated)),
        "groups": [
            {
                "canonical_key": item.canonical_key,
                "status": item.status,
                "source_agents": item.source_agents,
                "source_actions": item.source_actions,
            }
            for item in consolidated
        ],
    }

    final_shared_context = _compact_verified_context(verified_tool_cache)
    validation = {
        "raw_use_case_id": analysis.use_case_id,
        "validated_use_case_id": validated_use_case_id,
        "classification_changed": bool(class_changed),
        "classification_scores": class_scores,
        "raw_agents": analysis.agents,
        "agents_added_by_validator": added_agents,
        "effective_agents": selected_agents,
        "execution_order": execution_order,
        "specialist_implementation": "LLM-based Qwen3 specialist agents (v3.2 task-aligned/grounded buffer)",
        "ownership_layer": "deterministic role-boundary validation",
        "grounding_layer": "deterministic evidence checks for explicit numbers, IDs, named LMS entities and normalized used_data provenance",
        "shared_context_layer": "all downstream specialists receive verified upstream tool outputs only",
        "consolidation_layer": "deterministic canonical action merge",
        "governance_layer": "deterministic status escalation plus explicit negative privacy controls as blocked actions",
    }

    return MultiAgentRun(
        plan=plan,
        analysis=analysis,
        orchestrator_response=orchestrator_response,
        validation=validation,
        specialist_results=specialist_results,
        ownership_decisions=ownership_decisions,
        grounding_decisions=grounding_decisions,
        governance_decisions=governance_decisions,
        consolidation=consolidation,
        shared_context=final_shared_context,
    )
