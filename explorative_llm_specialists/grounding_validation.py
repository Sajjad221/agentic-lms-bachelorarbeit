"""Deterministische Grounding-/Evidence-Pruefung fuer den experimentellen v3.2-Puffer.

Ziel ist keine allgemeine Faktizitaetsbewertung von Freitext. Stattdessen werden
hochrisikoreiche, maschinell pruefbare Behauptungen kontrolliert:
- Prozent-/Kennzahlen,
- Fristen und Zeitangaben,
- LMS-IDs (Kurs/Modul/Gruppe/Nutzer),
- explizit benannte Kurs-/Modul-/Gruppenentitaeten,
- angegebene Datenquellen (used_data),
- nicht angeforderte Reporting-Intervalle und Kommunikationskanaele.

Eine Aktion wird nur weitergegeben, wenn diese expliziten Fakten in der
Nutzeranfrage, den eigenen Tool-Ausgaben oder dem verifizierten geteilten
Tool-Kontext vorkommen. Damit werden z. B. frei erfundene Werte wie "65 %"
verworfen, ohne vorzugeben, jede semantische Aussage automatisch beweisen zu
koennen.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from llm_specialist_agents import SpecialistAction


@dataclass(frozen=True)
class GroundingDecision:
    agent_name: str
    action: str
    accepted: bool
    reason: str
    unsupported_claims: List[str]
    evidence_sources: List[str]


def normalize(text: str) -> str:
    text = text.lower().replace("-", " ")
    text = (
        text.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    text = re.sub(r"[^a-z0-9%]+", " ", text)
    return " ".join(text.split())


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _flatten_shared_tool_outputs(shared_context: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not shared_context:
        return {}
    raw = shared_context.get("verified_tool_outputs", {})
    return dict(raw) if isinstance(raw, Mapping) else {}




def normalize_used_data_key(value: str) -> str:
    """Normalisiert Provenienz-Referenzen auf kanonische Tool-/Meta-Namen.

    LLMs schreiben gelegentlich z. B. ``verified_tool_outputs.read_modules``
    oder ``shared_context.verified_tool_outputs.read_modules`` statt nur
    ``read_modules``. Diese Varianten bezeichnen dieselbe verifizierte Quelle
    und duerfen nicht als Grounding-Fehler behandelt werden.
    """
    key = str(value).strip().strip("`'\"")
    lowered = key.lower()

    prefixes = (
        "shared_context.verified_tool_outputs.",
        "shared_context.verified_tool_outputs/",
        "verified_tool_outputs.",
        "verified_tool_outputs/",
        "tool:",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            key = key[len(prefix):].strip()
            break
    return key


def normalize_used_data_references(items: Sequence[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        key = normalize_used_data_key(str(item))
        marker = key.lower()
        if key and marker not in seen:
            seen.add(marker)
            out.append(key)
    return out

def _numeric_values(text: str) -> set[str]:
    # Zahlen aus IDs werden spaeter separat behandelt; fuer Grounding reicht die
    # konservative Frage, ob der konkrete Zahlenwert irgendwo in der Evidenz vorkommt.
    return {m.replace(",", ".") for m in re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?", text)}


def _extract_percent_claims(text: str) -> List[str]:
    return [m.group(0) for m in re.finditer(r"\b\d+(?:[.,]\d+)?\s*%", text)]


def _extract_duration_claims(text: str) -> List[str]:
    pattern = r"\b\d+\s*(?:tag|tage|tagen|woche|wochen|monat|monate|monaten|stunde|stunden|minute|minuten)\b"
    return [m.group(0) for m in re.finditer(pattern, text, flags=re.IGNORECASE)]


def _extract_frequency_claims(text: str) -> List[str]:
    terms = (
        r"\btaeglich\b", r"\btäglich\b", r"\bwoechentlich\b", r"\bwöchentlich\b",
        r"\bmonatlich\b", r"\bquartalsweise\b", r"\bjaehrlich\b", r"\bjährlich\b",
        r"\bhalbjaehrlich\b", r"\bhalbjährlich\b",
    )
    out: List[str] = []
    for pattern in terms:
        out.extend(m.group(0) for m in re.finditer(pattern, text, flags=re.IGNORECASE))
    return out


def _extract_channel_claims(text: str) -> List[str]:
    pattern = r"\b(?:e[- ]?mail|dashboard|sms|teams|slack)\b"
    return [m.group(0) for m in re.finditer(pattern, text, flags=re.IGNORECASE)]


def _contains_optional_reporting_parameter(text: str) -> List[str]:
    n = normalize(text)
    claims: List[str] = []
    if "reporting intervall" in n or "reportingintervall" in n:
        claims.append("Reporting-Intervall")
    if "kommunikationsform" in n or "kommunikations kanal" in n or "kommunikationskanal" in n:
        claims.append("Kommunikationsform/-kanal")
    return claims


def _extract_ids(text: str) -> List[str]:
    pattern = r"\b(?:C-[A-Z0-9-]+|M\d+|G\d+|U\d+)\b"
    return [m.group(0) for m in re.finditer(pattern, text, flags=re.IGNORECASE)]


def _extract_person_labels(text: str) -> List[str]:
    return [m.group(0) for m in re.finditer(r"\bPerson\s+[A-Z]\b", text, flags=re.IGNORECASE)]


def _extract_quoted_entities(text: str) -> List[str]:
    # Nur explizite LMS-Entitaeten pruefen. Freie Formulierungen sollen nicht
    # durch einen pseudo-semantischen Validator ueberinterpretiert werden.
    pattern = r"\b(?:gruppe|kurs|modul|lernpfad)\s+['\"]([^'\"]{2,100})['\"]"
    return [m.group(1) for m in re.finditer(pattern, text, flags=re.IGNORECASE)]


def _number_part(claim: str) -> str | None:
    match = re.search(r"\d+(?:[.,]\d+)?", claim)
    return match.group(0).replace(",", ".") if match else None


def build_evidence_bundle(
    *,
    user_request: str,
    tasks: Sequence[str],
    privacy_requirements: Sequence[str],
    own_tool_outputs: Mapping[str, Any],
    shared_context: Mapping[str, Any] | None,
) -> tuple[str, set[str], List[str]]:
    shared_tools = _flatten_shared_tool_outputs(shared_context)
    pieces = [
        user_request,
        _json_text(list(tasks)),
        _json_text(list(privacy_requirements)),
        _json_text(dict(own_tool_outputs)),
        _json_text(shared_tools),
    ]
    evidence_text = "\n".join(pieces)
    available_tools = set(own_tool_outputs) | set(shared_tools)
    sources = ["user_request", "tasks/privacy"]
    sources.extend(f"tool:{name}" for name in sorted(available_tools))
    return evidence_text, available_tools, sources


def validate_grounding(
    *,
    agent_name: str,
    proposal: SpecialistAction,
    user_request: str,
    tasks: Sequence[str],
    privacy_requirements: Sequence[str],
    own_tool_outputs: Mapping[str, Any],
    shared_context: Mapping[str, Any] | None,
) -> GroundingDecision:
    """Prueft explizite, deterministisch nachvollziehbare Fakten einer Aktion."""
    evidence_text, available_tools, sources = build_evidence_bundle(
        user_request=user_request,
        tasks=tasks,
        privacy_requirements=privacy_requirements,
        own_tool_outputs=own_tool_outputs,
        shared_context=shared_context,
    )
    evidence_norm = normalize(evidence_text)
    evidence_numbers = _numeric_values(evidence_text)
    evidence_ids = {normalize(x) for x in _extract_ids(evidence_text)}
    evidence_persons = {normalize(x) for x in _extract_person_labels(evidence_text)}

    claim_text = " ".join([proposal.action, proposal.reason, *proposal.uncertainties])
    unsupported: List[str] = []

    # 1) Prozentwerte / konkrete Kennzahlen: Der Zahlenwert muss in der Evidenz vorkommen.
    for claim in _extract_percent_claims(claim_text):
        value = _number_part(claim)
        if value and value not in evidence_numbers:
            unsupported.append(f"unbelegter Prozent-/Kennzahlenwert: {claim}")

    # 2) Zeit-/Fristangaben: keine frei erfundenen 7-Tage-/30-Tage-Regeln.
    for claim in _extract_duration_claims(claim_text):
        value = _number_part(claim)
        if value and value not in evidence_numbers:
            unsupported.append(f"unbelegte Zeit-/Fristangabe: {claim}")

    # 3) Optionale Reporting-Parameter/Kanaele duerfen nicht frei erfunden werden.
    # Fehlen sie in Anfrage/Tasks/Tooldaten, gehoeren sie in open_questions statt in eine Aktion.
    for claim in _extract_frequency_claims(claim_text):
        if normalize(claim) not in evidence_norm:
            unsupported.append(f"nicht angeforderte Reporting-Frequenz: {claim}")
    for claim in _extract_channel_claims(claim_text):
        if normalize(claim) not in evidence_norm:
            unsupported.append(f"nicht angeforderter Kommunikationskanal: {claim}")
    for claim in _contains_optional_reporting_parameter(claim_text):
        if normalize(claim) not in evidence_norm:
            unsupported.append(f"nicht angeforderter optionaler Reporting-Parameter: {claim}")

    # 4) Explizite LMS-IDs muessen in der Anfrage oder in gelesenen/verifizierten Daten vorkommen.
    for claim in _extract_ids(claim_text):
        if normalize(claim) not in evidence_ids:
            unsupported.append(f"unbekannte LMS-ID: {claim}")

    # 5) Explizite Person-A/B-Nennungen muessen aus Daten stammen.
    for claim in _extract_person_labels(claim_text):
        if normalize(claim) not in evidence_persons:
            unsupported.append(f"unbekannte Personenreferenz: {claim}")

    # 6) Benannte Kurs-/Modul-/Gruppenentitaeten muessen als Text in der Evidenz vorkommen.
    for entity in _extract_quoted_entities(claim_text):
        if normalize(entity) not in evidence_norm:
            unsupported.append(f"unbelegte benannte LMS-Entitaet: {entity}")

    # 7) used_data ist ein Provenienzfeld. Nur tatsaechlich verfuegbare Toolquellen
    # oder klar bezeichnete Nicht-Tool-Quellen sind zulaessig.
    allowed_meta = {"user_request", "shared_context", "analysis", "tasks", "privacy_requirements"}
    for item in proposal.used_data:
        raw_key = str(item).strip()
        key = normalize_used_data_key(raw_key)
        if key in available_tools or key in allowed_meta:
            continue
        unsupported.append(f"nicht verfuegbare Evidenzquelle in used_data: {raw_key}")

    # Deduplizieren bei stabiler Reihenfolge.
    unique: List[str] = []
    seen = set()
    for item in unsupported:
        marker = normalize(item)
        if marker not in seen:
            seen.add(marker)
            unique.append(item)

    if unique:
        return GroundingDecision(
            agent_name=agent_name,
            action=proposal.action,
            accepted=False,
            reason="Grounding fehlgeschlagen: " + "; ".join(unique[:4]),
            unsupported_claims=unique,
            evidence_sources=sources,
        )

    return GroundingDecision(
        agent_name=agent_name,
        action=proposal.action,
        accepted=True,
        reason="Explizite Zahlen/IDs/Entitaeten sind durch Anfrage oder verifizierte Tool-Daten gedeckt.",
        unsupported_claims=[],
        evidence_sources=sources,
    )
