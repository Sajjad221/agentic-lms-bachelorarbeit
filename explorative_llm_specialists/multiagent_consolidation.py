"""Deterministische Rollenpruefung und Konsolidierung fuer den LLM-Multi-Agent-Puffer v3.2."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Sequence, Tuple

from llm_specialist_agents import SpecialistAction


STATUS_RANK = {"erlaubt": 0, "freigabepflichtig": 1, "blockiert": 2}


@dataclass(frozen=True)
class OwnershipDecision:
    agent_name: str
    action: str
    accepted: bool
    reason: str


@dataclass(frozen=True)
class GovernedProposal:
    agent_name: str
    proposal: SpecialistAction
    final_status: str
    governance_rule: str


@dataclass
class ConsolidatedAction:
    canonical_key: str
    action: str
    status: str
    reason: str
    used_data: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    source_agents: List[str] = field(default_factory=list)
    source_actions: List[str] = field(default_factory=list)


OWNED_TERMS: Dict[str, tuple[str, ...]] = {
    "Course Agent": ("kurs", "lernpath", "lern pfad", "lernpfad", "schulung", "struktur", "reihenfolge", "anpass"),
    "Content Agent": ("inhalt", "modul", "content", "lernmaterial", "material", "themenbereich", "veraltet", "fehlend", "aktualis", "einbind", "ueberarbeit"),
    "Enrollment Agent": ("zielgruppe", "gruppe", "einschreib", "zuweis", "teilnehm", "rolle"),
    "Assignment Agent": ("frist", "aufgabe", "wiederholung", "deadline", "14 tag"),
    "Notification Agent": ("benachr", "erinner", "informier", "nachricht", "kommunik"),
    "Analytics/Metrics Agent": ("analys", "auswert", "kennzahl", "durchschnitt", "report", "fortschritt", "testergebnis", "gruppenvergleich", "vergleich", "aggreg"),
    "Policy/Permission Agent": ("datenschutz", "berechtig", "recht", "freigabe", "block", "aggregation", "aggregiert", "individuell", "personenbez", "compliance"),
}


FORBIDDEN_TERMS: Dict[str, tuple[str, ...]] = {
    "Course Agent": ("modul", "inhalt", "veraltet", "fehlend", "aktualis", "zielgruppe", "einschreib", "zuordn", "frist", "benachr", "erinner", "report", "testergebnis analys", "berechtig"),
    "Content Agent": ("zielgruppe defin", "einschreib", "frist", "benachr", "erinner", "report", "teamleiter", "berechtig"),
    "Enrollment Agent": ("lernpath erstellen", "lern pfad erstellen", "lernpfad erstellen", "modul", "inhalt einbind", "frist", "benachr", "report"),
    "Assignment Agent": ("lernpath erstellen", "lernpfad erstellen", "modul aktual", "modul ergaenz", "zielgruppe", "benachr", "report"),
    "Notification Agent": ("lernpath erstellen", "lernpfad erstellen", "modul", "inhalt pruef", "zielgruppe defin", "report analys"),
    "Analytics/Metrics Agent": ("lernpath erstellen", "lernpfad erstellen", "modul", "inhalt", "zielgruppe defin", "frist setzen", "benachr", "erinner"),
    "Policy/Permission Agent": ("lernpath erstellen", "lernpfad erstellen", "modul", "inhalt identifiz", "zielgruppe defin", "frist", "benachrichtigung erstellen"),
}


STOPWORDS = {
    "der", "die", "das", "den", "dem", "des", "und", "oder", "fuer", "für", "von", "an", "im", "in", "auf",
    "zu", "zur", "zum", "mit", "ohne", "ein", "eine", "einen", "einer", "eines", "als", "ist", "sind", "werden",
    "wird", "soll", "sollen", "deshalb", "dabei", "bereits", "vorhanden", "planen", "setzen", "erstellen",
}


def normalize(text: str) -> str:
    text = text.lower().replace("-", " ")
    text = (
        text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    )
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    return any(normalize(term) in text for term in terms)


def _assignment_task_alignment(proposal_text: str, assigned_tasks: Sequence[str] | None) -> tuple[bool, str]:
    """Prueft Assignment-Aktionen gegen die tatsaechlich zugewiesenen Teilaufgaben.

    Der LLM-Agent darf nicht aus einer vorhandenen Frist zusaetzlich eine generische
    Aufgabe oder Wiederholungsaufgabe erfinden. Jede Aktionsklasse braucht einen
    expliziten Anker in den zugewiesenen Teilaufgaben.
    """
    if not assigned_tasks:
        return False, "keine konkrete Assignment-Teilaufgabe zugewiesen"

    tasks_text = normalize(" ".join(assigned_tasks))
    action = normalize(proposal_text)

    has_deadline_task = any(term in tasks_text for term in ("frist", "deadline", "14 tag", "bearbeitungsfrist"))
    has_repeat_task = any(term in tasks_text for term in ("wiederholung", "wiederholungsaufgabe", "erneut", "noch einmal"))
    has_generic_task = any(term in tasks_text for term in ("aufgabe", "assignment")) and not has_deadline_task and not has_repeat_task

    is_deadline_action = any(term in action for term in ("frist", "deadline", "14 tag", "bearbeitungsfrist"))
    is_repeat_action = any(term in action for term in ("wiederholung", "wiederholungsaufgabe", "erneut"))
    is_generic_task_action = "aufgabe" in action and not is_repeat_action

    if is_repeat_action and not has_repeat_task:
        return False, "Wiederholungsaktion nicht durch zugewiesene Teilaufgabe gedeckt"
    if is_deadline_action and not has_deadline_task:
        return False, "Fristaktion nicht durch zugewiesene Teilaufgabe gedeckt"
    if is_generic_task_action and not (has_generic_task or has_repeat_task):
        return False, "generische Aufgabe nicht durch zugewiesene Assignment-Teilaufgabe gedeckt"
    if not (is_deadline_action or is_repeat_action or is_generic_task_action):
        return False, "Assignment-Aktion ohne erkennbaren Bezug zur zugewiesenen Teilaufgabe"
    return True, "Assignment-Aktion durch zugewiesene Teilaufgabe gedeckt"


def validate_ownership(
    agent_name: str,
    proposal: SpecialistAction,
    assigned_tasks: Sequence[str] | None = None,
) -> OwnershipDecision:
    text = normalize(proposal.action)
    forbidden = [term for term in FORBIDDEN_TERMS.get(agent_name, ()) if normalize(term) in text]
    owned = [term for term in OWNED_TERMS.get(agent_name, ()) if normalize(term) in text]

    # Klare Fremdaufgabe: ablehnen. Ein eigener Begriff kann eine Fremdaufgabe nicht einfach legitimieren,
    # wenn der Aktionskern explizit in einer anderen Domäne liegt.
    if forbidden:
        return OwnershipDecision(
            agent_name=agent_name,
            action=proposal.action,
            accepted=False,
            reason="klare Rollenueberschreitung: " + ", ".join(forbidden[:3]),
        )

    # Assignment-Aktionen muessen zusaetzlich durch die wirklich zugewiesene
    # Assignment-/Frist-/Wiederholungsaufgabe gedeckt sein.
    if agent_name == "Assignment Agent":
        aligned, alignment_reason = _assignment_task_alignment(proposal.action, assigned_tasks)
        if not aligned:
            return OwnershipDecision(
                agent_name=agent_name,
                action=proposal.action,
                accepted=False,
                reason=alignment_reason,
            )

    # Bei Policy muss eine Aktion zwingend einen Governance-Kern haben.
    if agent_name == "Policy/Permission Agent" and not owned:
        return OwnershipDecision(
            agent_name=agent_name,
            action=proposal.action,
            accepted=False,
            reason="Policy-Aktion ohne erkennbaren Governance-/Rechtebezug",
        )

    # Fuer alle anderen Agenten: wenn keinerlei Rollenbezug erkennbar ist, wird konservativ verworfen.
    if agent_name != "Policy/Permission Agent" and not owned:
        return OwnershipDecision(
            agent_name=agent_name,
            action=proposal.action,
            accepted=False,
            reason="kein hinreichend klarer Bezug zur eigenen Fachrolle",
        )

    return OwnershipDecision(agent_name=agent_name, action=proposal.action, accepted=True, reason="Rollenbezug plausibel")


def _entity_suffix(text: str) -> str:
    n = normalize(text)
    ids = sorted(set(re.findall(r"\bm[1-9][0-9]*\b", n)))
    if ids:
        return ":" + ",".join(ids)
    return ""


def canonical_action_key(text: str) -> str:
    n = normalize(text)
    suffix = _entity_suffix(text)

    if ("individuell" in n or "personenbez" in n) and any(x in n for x in ("teamleiter", "teamleitung", "hr", "compliance")):
        return "privacy:block_individual_reporting"
    if "aggreg" in n and any(x in n for x in ("report", "fortschritt", "teamleiter", "teamleitung", "hr", "compliance")):
        return "analytics:aggregate_reporting"
    if "zielgruppe" in n or "gruppe bestimmen" in n or "gruppe defin" in n:
        return "enrollment:target_group"
    if "einschreib" in n or ("zuweis" in n and "pflichtschulung" not in n and "wiederholung" not in n):
        return "enrollment:assignment"
    if "wiederholung" in n or "wiederholungsaufgabe" in n:
        return "assignment:repetition"
    if "erinner" in n:
        return "notification:reminder"
    if "benachr" in n or "informier" in n or "nachricht" in n:
        return "notification:message"
    if "14 tag" in n or "frist" in n or "deadline" in n:
        return "assignment:deadline"
    if "testergebnis" in n and ("analys" in n or "auswert" in n):
        return "analytics:test_analysis"
    if "gruppenvergleich" in n or ("gruppe" in n and "vergleich" in n):
        return "analytics:group_comparison"
    if "pflichtschulung" in n and ("zuweis" in n or "rollenbasiert" in n):
        return "enrollment:compliance_assignment"
    if "eskal" in n and any(x in n for x in ("hr", "compliance", "teamleiter", "teamleitung")):
        return "policy:escalation"
    if any(x in n for x in ("berechtig", "freigabe", "datenschutz", "datenminim", "block")):
        return "policy:governance" + suffix
    if ("modul" in n or "inhalt" in n) and any(x in n for x in ("fehl", "ergaenz", "hinzufueg")):
        return "content:missing" + suffix
    if ("modul" in n or "inhalt" in n) and any(x in n for x in ("veraltet", "aktualis")):
        return "content:update" + suffix
    if ("modul" in n or "inhalt" in n) and any(x in n for x in ("einbind", "integrier")):
        return "content:include" + suffix
    if "lernpfad" in n or (("kurs" in n or "schulung" in n) and any(x in n for x in ("struktur", "erstell", "anleg", "aufbau", "anpass", "vorbereit"))):
        return "course:path"

    tokens = [t for t in n.split() if t not in STOPWORDS][:8]
    return "generic:" + "_".join(tokens)


def _unique(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        key = normalize(item)
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _strictest_status(statuses: Sequence[str]) -> str:
    return max(statuses, key=lambda s: STATUS_RANK.get(s, 1))


def _best_action_title(actions: Sequence[str]) -> str:
    # Bevorzuge eine praezise, nicht uebermaessig lange Formulierung.
    return min(actions, key=lambda x: (abs(len(x) - 70), len(x)))


def consolidate_governed_proposals(proposals: Sequence[GovernedProposal]) -> List[ConsolidatedAction]:
    groups: Dict[str, List[GovernedProposal]] = {}
    for item in proposals:
        key = canonical_action_key(item.proposal.action)
        groups.setdefault(key, []).append(item)

    consolidated: List[ConsolidatedAction] = []
    for key, items in groups.items():
        actions = [x.proposal.action for x in items]
        reasons = _unique(x.proposal.reason for x in items)
        gov_rules = _unique(x.governance_rule for x in items if x.governance_rule)
        source_agents = _unique(x.agent_name for x in items)
        used_data = _unique(data for x in items for data in x.proposal.used_data)
        uncertainties = _unique(u for x in items for u in x.proposal.uncertainties)
        status = _strictest_status([x.final_status for x in items])

        reason_parts = reasons[:2]
        if len(items) > 1:
            reason_parts.append("Konsolidiert aus Vorschlaegen von " + ", ".join(source_agents) + ".")
        strict_rules = [r for r in gov_rules if "beibehalten" not in normalize(r)]
        if strict_rules:
            reason_parts.append("Deterministische Governance: " + " | ".join(strict_rules[:2]) + ".")

        controller_actions = [
            x.proposal.action for x in items
            if x.agent_name == "Deterministic Governance Controller"
        ]
        chosen_action = controller_actions[0] if controller_actions else _best_action_title(actions)

        consolidated.append(
            ConsolidatedAction(
                canonical_key=key,
                action=chosen_action,
                status=status,
                reason=" ".join(reason_parts),
                used_data=used_data,
                uncertainties=uncertainties,
                source_agents=source_agents,
                source_actions=_unique(actions),
            )
        )

    # Stabile, fachlich sinnvolle Reihenfolge.
    order_prefix = {
        "course": 10,
        "content": 20,
        "enrollment": 30,
        "assignment": 40,
        "analytics": 50,
        "notification": 60,
        "policy": 70,
        "privacy": 80,
        "generic": 90,
    }
    consolidated.sort(key=lambda x: (order_prefix.get(x.canonical_key.split(":", 1)[0], 99), x.canonical_key))
    return consolidated


def dedupe_questions(questions: Iterable[str], threshold: float = 0.78) -> List[str]:
    out: List[str] = []
    norms: List[str] = []
    for question in questions:
        n = normalize(question)
        if not n:
            continue
        if any(SequenceMatcher(None, n, prev).ratio() >= threshold for prev in norms):
            continue
        norms.append(n)
        out.append(question)
    return out
