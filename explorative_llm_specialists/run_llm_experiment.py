"""Finales, eingefrorenes LLM-Experiment für Development- und Holdout-Fälle.

Die Auswertung trennt vier Ebenen:
1. rohe LLM-Klassifikation und Aufgaben-/Datenschutzextraktion,
2. rohe Agentenauswahl,
3. deterministisch validierte Agentenauswahl,
4. tatsächliche Abdeckung im erzeugten hybriden ActionPlan.

Der Holdout-Datensatz darf erst nach Abschluss der Entwicklung ausgeführt werden.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import statistics
import sys
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

from action_plan import ActionPlan
from experiment_cases import build_cases
from llm_orchestrator import (
    REQUEST_ANALYSIS_SCHEMA,
    SYSTEM_PROMPT,
    analyze_natural_language_request,
    build_action_plan_from_analysis,
    complete_agent_selection,
    validate_use_case_selection,
)
from ollama_client import OllamaClient, OllamaError

CODE_VERSION = "v4-frozen-2026-08-04"

# Die Terme dienen nur der transparenten, deterministischen Rubrik-Auswertung.
# Sie wurden anhand des Development-Sets erweitert; der Holdout blieb unberührt.
TASK_CATEGORY_TERMS: Dict[str, tuple[str, ...]] = {
    "course_structure": (
        "lernpfad", "kursstruktur", "kursaufbau", "onboardingpfad", "onboarding",
        "kursentwurf", "kursvorbereitung",
    ),
    "content_review": (
        "content", "inhalt", "material", "modul", "lücke", "fehlend", "veraltet",
        "überholt", "aktual", "bestandsmodul", "richtlinie",
    ),
    "target_group": (
        "zielgruppe", "lerngruppe", "gruppe bestimmen", "gruppenzuord", "zuord",
        "einschreib", "werkstudent", "werkstud", "lernenden",
    ),
    "deadline": (
        "frist", "14 tag", "zwei woch", "zweiwöch", "zweiwöchig", "abschlussfrist",
        "bearbeitungszeit", "abschluss innerhalb",
    ),
    "notification_reporting": (
        "benachr", "informier", "meldung", "lernendeninformation", "fortschritt",
        "report", "bericht", "zusammenfass", "verdichtet", "aggreg", "bereitstell",
    ),
    "learner_notification": (
        "benachr", "lernendeninformation", "nachricht", "informiere lern", "meldung an lern",
    ),
    "reporting": (
        "fortschritt", "report", "bericht", "auswertung", "kennzahl", "zusammengefass",
        "verdichtet", "aggreg", "bereitstell", "hr", "compliance",
    ),
    "governance": (
        "datenschutz", "personenbez", "berechtig", "rolle", "freigabe", "blockier",
        "datenspar", "aggreg", "nicht weitergeben", "verhindere",
    ),
    "result_analysis": (
        "testergebnis", "testdaten", "testresult", "abschlusstest", "sicherheitstest",
        "auswert", "analys", "schwache themen", "schwache inhalte", "auffällig",
        "problematische themen", "haupt und nebenproblem",
    ),
    "group_comparison": (
        "gruppenunterschied", "gruppenvergleich", "gruppenwert", "gruppenspezif",
        "unterschiede zwischen", "mit und ohne", "mit beziehungsweise ohne",
        "vorerfahrung", "vorkennt", "gruppen erkennen",
    ),
    "course_adjustment": (
        "kursanpass", "kursänder", "kursverbesser", "didaktische anpass", "didaktisch",
        "verbessere den kurs", "änderungen vorschlagen", "anpassungsvorschlag",
        "maßnahmenplan", "kursverbesserungen",
    ),
    "repeat_tasks": (
        "wiederholung", "wiederholungsauf", "wiederholungsüb", "aufgabe", "übung",
    ),
    "governance_notification": (
        "privat", "vertraulich", "datenschutz", "personenbez", "öffentlich",
        "bloßstellung", "kennzeichnung", "lernhinweis", "benachr", "freigabe",
    ),
    "private_notification": (
        "privat", "vertraulich", "lernhinweis", "betroffene", "individuelle hinweis",
    ),
    "target_assignment": (
        "zielgruppe", "kundendatenzugriff", "zugriffsmerkmal", "zugriffsrecht",
        "rollenbasiert", "zuweis", "teilnahme", "relevante beschäft", "mitarbeit",
    ),
    "course_setup": (
        "pflichtschulung", "compliance schulung", "kursentwurf", "schulung", "kurs",
        "einrichten", "vorbereiten",
    ),
    "reminders": (
        "erinner", "mahnung", "säumig", "offene abschlüsse",
    ),
    "escalations": (
        "eskal", "eskalationsschritt", "weiterleitung an hr",
    ),
    "reporting_governance": (
        "report", "bericht", "hr", "compliance", "datenspar", "personenbez",
        "berechtig", "weitergabe", "notwendige daten", "erforderliche",
    ),
}

PRIVACY_CATEGORY_TERMS: Dict[str, tuple[str, ...]] = {
    "aggregation": (
        "aggreg", "zusammenfass", "zusammengefass", "zusammenfassung", "verdichtet", "nur zusammengefasste",
        "ausschließlich verdichtete",
    ),
    "no_personal_data": (
        "keine individuell", "nicht personenbez", "keine personenbez", "personenbezogene fortschritt",
        "individuelle fortschritt", "einzelperson", "nur aggregiert", "ausschließlich aggregiert",
        "verhindern von personenbez", "nicht an teamleiter",
    ),
    "permissions": (
        "berechtig", "rolle", "zugriff", "freigabe", "autoris", "nur berechtigte",
    ),
    "private_notification": (
        "privat", "vertraulich", "individuelle lernhinweis", "betroffene", "persönlich",
    ),
    "no_public_shaming": (
        "keine öffentliche", "nicht öffentlich", "bloßstellung", "kennzeichnung einzelner",
        "öffentliche kennzeichnung", "keine bloßstellung",
    ),
    "performance_permissions": (
        "leistungsdaten", "testergebnis", "personenbez", "berechtig", "freigabe",
        "datenschutz", "autoris", "zugriff auf test",
    ),
    "data_minimization": (
        "datenspar", "nur notwendige", "notwendige daten", "erforderliche daten",
        "nur erforderliche", "datenminim", "keine unnötigen", "unnötige personenbez",
    ),
    "report_restriction": (
        "hr", "compliance", "bericht", "report", "keine lerndetails", "sensible lerndetails",
        "nicht weitergegeben", "nicht an hr", "begrenz", "beschränk",
    ),
    "role_permissions": (
        "rollenbasiert", "berechtig", "zugriff", "rolle", "freigabe", "unberechtigte",
        "zugriffsrecht",
    ),
}

# Erwartete Governance-Kontrollen des finalen ActionPlans. Jede Kontrolle wird
# anhand von Status und semantischen Termgruppen geprüft.
GOVERNANCE_CONTROLS: Dict[str, List[Dict[str, Any]]] = {
    "use_case_1": [
        {"id": "aggregated_progress_allowed", "status": "erlaubt", "groups": [("aggreg",), ("fortschritt",)]},
        {"id": "personal_progress_blocked", "status": "blockiert", "groups": [("personenbez",), ("fortschritt",)]},
        {"id": "course_publication_requires_approval", "status": "freigabepflichtig", "groups": [("kurs",), ("veröffentlich",)]},
        {"id": "automatic_enrollment_requires_approval", "status": "freigabepflichtig", "groups": [("einschreib",)]},
        {"id": "learner_notification_requires_approval", "status": "freigabepflichtig", "groups": [("benachrichtigung",)]},
    ],
    "use_case_2": [
        {"id": "course_adjustment_requires_approval", "status": "freigabepflichtig", "groups": [("kursanpass",)]},
        {"id": "repeat_tasks_require_approval", "status": "freigabepflichtig", "groups": [("wiederholungsauf",)]},
        {"id": "private_hints_require_approval", "status": "freigabepflichtig", "groups": [("private lernhinweis",)]},
        {"id": "personal_test_results_blocked", "status": "blockiert", "groups": [("personenbez",), ("testergebnis",)]},
        {"id": "group_evaluation_allowed", "status": "erlaubt", "groups": [("gruppenbasierte auswertung",)]},
    ],
    "use_case_3": [
        {"id": "course_draft_requires_approval", "status": "freigabepflichtig", "groups": [("pflichtschulung",), ("kursentwurf",)]},
        {"id": "role_assignment_requires_approval", "status": "freigabepflichtig", "groups": [("rollenbasiert",), ("zuweis",)]},
        {"id": "reminders_require_approval", "status": "freigabepflichtig", "groups": [("erinner",)]},
        {"id": "personal_performance_data_blocked", "status": "blockiert", "groups": [("personenbez",), ("leistungsdaten",)]},
        {"id": "escalation_requires_approval", "status": "freigabepflichtig", "groups": [("eskalation",)]},
        {"id": "aggregated_compliance_report_allowed", "status": "erlaubt", "groups": [("aggreg",), ("bericht",)]},
    ],
}


def normalize(items: Iterable[str]) -> str:
    text = " ".join(str(item) for item in items)
    return " ".join(text.lower().replace("-", " ").split())


def term_present(term: str, text: str) -> bool:
    """Verhindert bei kurzen Kürzeln Treffer innerhalb anderer Wörter."""
    normalized_term = normalize([term])
    if len(normalized_term) <= 3 and " " not in normalized_term:
        return re.search(rf"(?<!\w){re.escape(normalized_term)}(?!\w)", text) is not None
    return normalized_term in text


def category_coverage(
    expected_categories: List[str],
    text_items: Iterable[str],
    category_terms: Dict[str, tuple[str, ...]],
) -> tuple[float, List[str], List[str]]:
    text = normalize(text_items)
    hit: List[str] = []
    missing: List[str] = []
    for category in expected_categories:
        terms = category_terms[category]
        if any(term_present(term, text) for term in terms):
            hit.append(category)
        else:
            missing.append(category)
    score = len(hit) / len(expected_categories) if expected_categories else 1.0
    return score, hit, missing


def set_metrics(expected: Iterable[str], predicted: Iterable[str]) -> Dict[str, Any]:
    expected_set: Set[str] = set(expected)
    predicted_set: Set[str] = set(predicted)
    true_positive = len(expected_set & predicted_set)
    precision = true_positive / len(predicted_set) if predicted_set else 0.0
    recall = true_positive / len(expected_set) if expected_set else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "missing": sorted(expected_set - predicted_set),
        "extra": sorted(predicted_set - expected_set),
    }


def plan_text_items(plan: ActionPlan) -> List[str]:
    values: List[str] = [*plan.tasks]
    for item in plan.actions:
        values.extend([item.action, item.reason, *item.used_data, *item.uncertainties])
    return values


def governance_control_coverage(
    expected_control_ids: List[str],
    plan: ActionPlan,
) -> tuple[float, List[str], List[str]]:
    control_index = {
        control["id"]: control
        for controls in GOVERNANCE_CONTROLS.values()
        for control in controls
    }
    hit: List[str] = []
    missing: List[str] = []
    for control_id in expected_control_ids:
        control = control_index[control_id]
        matched = False
        for action in plan.actions:
            if action.status != control["status"]:
                continue
            text = normalize([action.action, action.reason, *action.used_data, *action.uncertainties])
            if all(any(term_present(term, text) for term in group) for group in control["groups"]):
                matched = True
                break
        (hit if matched else missing).append(control_id)
    score = len(hit) / len(expected_control_ids) if expected_control_ids else 1.0
    return score, hit, missing


def mean(field: str, subset: List[Dict[str, Any]]) -> float:
    return statistics.fmean(record[field] for record in subset) if subset else 0.0


def summarize(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    successful = [record for record in records if record["success"]]
    by_use_case: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in successful:
        by_use_case[record["expected_use_case_id"]].append(record)

    fields = [
        "raw_classification_correct",
        "validated_classification_correct",
        "classification_changed",
        "raw_task_coverage",
        "plan_task_coverage",
        "raw_privacy_coverage",
        "plan_privacy_coverage",
        "governance_action_coverage",
        "raw_agent_precision",
        "raw_agent_recall",
        "raw_agent_f1",
        "validated_agent_precision",
        "validated_agent_recall",
        "validated_agent_f1",
        "agents_added_count",
        "total_duration_ms",
        "output_tokens_per_second",
    ]

    summary: Dict[str, Any] = {
        "runs_total": len(records),
        "runs_successful": len(successful),
        "schema_success_rate": len(successful) / len(records) if records else 0.0,
        "raw_classification_accuracy": mean("raw_classification_correct", successful),
        "validated_classification_accuracy": mean("validated_classification_correct", successful),
        "classification_validator_change_rate": mean("classification_changed", successful),
        "mean_raw_task_coverage": mean("raw_task_coverage", successful),
        "mean_plan_task_coverage": mean("plan_task_coverage", successful),
        "mean_raw_privacy_coverage": mean("raw_privacy_coverage", successful),
        "mean_plan_privacy_coverage": mean("plan_privacy_coverage", successful),
        "mean_governance_action_coverage": mean("governance_action_coverage", successful),
        "mean_raw_agent_precision": mean("raw_agent_precision", successful),
        "mean_raw_agent_recall": mean("raw_agent_recall", successful),
        "mean_raw_agent_f1": mean("raw_agent_f1", successful),
        "mean_validated_agent_precision": mean("validated_agent_precision", successful),
        "mean_validated_agent_recall": mean("validated_agent_recall", successful),
        "mean_validated_agent_f1": mean("validated_agent_f1", successful),
        "mean_agents_added_by_validator": mean("agents_added_count", successful),
        "mean_total_duration_ms": mean("total_duration_ms", successful),
        "mean_output_tokens_per_second": mean("output_tokens_per_second", successful),
        "by_use_case": {},
    }
    for use_case_id, subset in sorted(by_use_case.items()):
        summary["by_use_case"][use_case_id] = {
            "runs": len(subset),
            **{field: mean(field, subset) for field in fields},
        }
    return summary


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def reproducibility_info(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    base = Path(__file__).resolve().parent
    critical_files = [
        "run_llm_experiment.py",
        "llm_orchestrator.py",
        "experiment_cases.py",
        "agents.py",
        "lms_backend.py",
        "action_plan.py",
        "ollama_client.py",
    ]
    return {
        "code_version": CODE_VERSION,
        "system_prompt_sha256": sha256_text(SYSTEM_PROMPT),
        "json_schema_sha256": sha256_json(REQUEST_ANALYSIS_SCHEMA),
        "dataset_sha256": sha256_json(cases),
        "scoring_configuration_sha256": sha256_json(
            {
                "task_terms": TASK_CATEGORY_TERMS,
                "privacy_terms": PRIVACY_CATEGORY_TERMS,
                "governance_controls": GOVERNANCE_CONTROLS,
            }
        ),
        "source_files_sha256": {
            name: file_sha256(base / name) for name in critical_files
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3:14b")
    parser.add_argument("--dataset", choices=["development", "holdout"], default="development")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--output", default=None)
    parser.add_argument(
        "--confirm-frozen-holdout",
        action="store_true",
        help="Bestätigt, dass Prompt, Validator und Rubrik eingefroren sind.",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.repetitions < 1:
        raise SystemExit("--repetitions muss mindestens 1 sein.")
    if args.temperature < 0:
        raise SystemExit("--temperature darf nicht negativ sein.")
    if args.dataset == "holdout" and not args.confirm_frozen_holdout:
        raise SystemExit(
            "Der Holdout-Lauf ist geschützt. Ergänze --confirm-frozen-holdout erst nach dem Code-Freeze."
        )

    output = args.output or f"outputs/llm_{args.dataset}_{CODE_VERSION}.json"
    output_path = Path(output)
    if output_path.exists() and not args.overwrite:
        raise SystemExit(
            f"Ausgabedatei existiert bereits: {output}. Nutze bewusst --overwrite oder einen neuen Dateinamen."
        )

    cases = build_cases(args.dataset)
    client = OllamaClient(model=args.model, timeout_seconds=240)
    tags = client.health_check()
    model_info = client.configured_model_info(tags)
    try:
        version_info = client.version_info()
    except OllamaError:
        version_info = {"version": "nicht verfügbar"}

    records: List[Dict[str, Any]] = []
    total_runs = len(cases) * args.repetitions
    current = 0

    for case in cases:
        for repetition in range(1, args.repetitions + 1):
            current += 1
            run_seed = args.seed + repetition - 1
            print(
                f"[{current}/{total_runs}] {case['case_id']}, "
                f"Wiederholung {repetition}, Seed {run_seed}"
            )
            record: Dict[str, Any] = {
                **case,
                "repetition": repetition,
                "seed": run_seed,
                "temperature": args.temperature,
                "success": False,
            }
            try:
                analysis, response = analyze_natural_language_request(
                    case["prompt"],
                    client=client,
                    seed=run_seed,
                    temperature=args.temperature,
                )
                validated_id, class_changed, class_scores = validate_use_case_selection(
                    analysis, case["prompt"]
                )
                effective_agents, added_agents = complete_agent_selection(
                    analysis, case["prompt"], validated_id
                )
                plan, validation = build_action_plan_from_analysis(
                    case["prompt"],
                    analysis,
                    validated_use_case_id=validated_id,
                    classification_changed=class_changed,
                    classification_scores=class_scores,
                )

                raw_task_score, raw_task_hits, raw_task_missing = category_coverage(
                    case["expected_task_categories"],
                    [*analysis.tasks, *analysis.privacy_requirements],
                    TASK_CATEGORY_TERMS,
                )
                plan_task_score, plan_task_hits, plan_task_missing = category_coverage(
                    case["expected_task_categories"],
                    plan_text_items(plan),
                    TASK_CATEGORY_TERMS,
                )
                raw_privacy_score, raw_privacy_hits, raw_privacy_missing = category_coverage(
                    case["expected_privacy_categories"],
                    [*analysis.privacy_requirements, *analysis.tasks],
                    PRIVACY_CATEGORY_TERMS,
                )
                plan_privacy_score, plan_privacy_hits, plan_privacy_missing = category_coverage(
                    case["expected_privacy_categories"],
                    plan_text_items(plan),
                    PRIVACY_CATEGORY_TERMS,
                )
                governance_score, governance_hits, governance_missing = governance_control_coverage(
                    case["expected_governance_controls"], plan
                )
                raw_agent = set_metrics(case["expected_agents"], analysis.agents)
                validated_agent = set_metrics(case["expected_agents"], effective_agents)

                record.update(
                    {
                        "success": True,
                        "analysis": asdict(analysis),
                        "raw_use_case_id": analysis.use_case_id,
                        "validated_use_case_id": validated_id,
                        "classification_changed": int(class_changed),
                        "classification_scores": class_scores,
                        "raw_classification_correct": int(
                            analysis.use_case_id == case["expected_use_case_id"]
                        ),
                        "validated_classification_correct": int(
                            validated_id == case["expected_use_case_id"]
                        ),
                        "raw_task_coverage": raw_task_score,
                        "raw_task_categories_hit": raw_task_hits,
                        "raw_task_categories_missing": raw_task_missing,
                        "plan_task_coverage": plan_task_score,
                        "plan_task_categories_hit": plan_task_hits,
                        "plan_task_categories_missing": plan_task_missing,
                        "raw_privacy_coverage": raw_privacy_score,
                        "raw_privacy_categories_hit": raw_privacy_hits,
                        "raw_privacy_categories_missing": raw_privacy_missing,
                        "plan_privacy_coverage": plan_privacy_score,
                        "plan_privacy_categories_hit": plan_privacy_hits,
                        "plan_privacy_categories_missing": plan_privacy_missing,
                        "governance_action_coverage": governance_score,
                        "governance_controls_hit": governance_hits,
                        "governance_controls_missing": governance_missing,
                        "raw_agents": analysis.agents,
                        "effective_agents": effective_agents,
                        "agents_added_by_validator": added_agents,
                        "agents_added_count": len(added_agents),
                        "raw_agent_precision": raw_agent["precision"],
                        "raw_agent_recall": raw_agent["recall"],
                        "raw_agent_f1": raw_agent["f1"],
                        "raw_agents_missing": raw_agent["missing"],
                        "raw_agents_extra": raw_agent["extra"],
                        "validated_agent_precision": validated_agent["precision"],
                        "validated_agent_recall": validated_agent["recall"],
                        "validated_agent_f1": validated_agent["f1"],
                        "validated_agents_missing": validated_agent["missing"],
                        "validated_agents_extra": validated_agent["extra"],
                        "action_plan": plan.to_dict(),
                        "validation": validation,
                        "total_duration_ms": response.metrics.total_duration_ms,
                        "load_duration_ms": response.metrics.load_duration_ms,
                        "prompt_tokens": response.metrics.prompt_tokens,
                        "output_tokens": response.metrics.output_tokens,
                        "output_tokens_per_second": response.metrics.output_tokens_per_second or 0.0,
                        "response_model": response.model,
                        "response_created_at": response.created_at,
                    }
                )
            except (OllamaError, ValueError) as exc:
                record["error"] = str(exc)
            records.append(record)

    model_details = model_info.get("details") if isinstance(model_info.get("details"), dict) else {}
    result = {
        "experiment": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "model_requested": args.model,
            "model_local_name": model_info.get("name", args.model),
            "model_digest": model_info.get("digest", ""),
            "model_size_bytes": model_info.get("size", 0),
            "model_details": model_details,
            "ollama_version": version_info.get("version", "nicht verfügbar"),
            "dataset": args.dataset,
            "temperature": args.temperature,
            "base_seed": args.seed,
            "num_ctx": 4096,
            "think": False,
            "prompts": len(cases),
            "repetitions": args.repetitions,
            "runs": total_runs,
            "python_version": sys.version,
            "platform": platform.platform(),
            "method_note": (
                "Der Development-Datensatz wurde zur Prompt-, Validator- und Rubrikentwicklung verwendet. "
                "Der Holdout-Datensatz ist ausschließlich für die finale Leistungsbewertung vorgesehen. "
                "Rohe LLM-Metriken und hybride ActionPlan-Metriken werden getrennt ausgewiesen."
            ),
        },
        "reproducibility": reproducibility_info(cases),
        "summary": summarize(records),
        "records": records,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)

    print("\nZusammenfassung:")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print(f"\nGespeichert unter: {output}")
    print(f"Konfigurationsversion: {CODE_VERSION}")
    print(f"Datensatz-Hash: {result['reproducibility']['dataset_sha256']}")


if __name__ == "__main__":
    main()
