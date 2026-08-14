"""CLI-Demo fuer den experimentellen LLM-Multi-Agent-Puffer v3.2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from llm_multiagent_pipeline import orchestrate_with_llm_specialists
from lms_backend import get_use_case_data
from ollama_client import OllamaClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Experimenteller v3.2-Puffer: Qwen3-Orchestrator + LLM-Fachagenten + "
            "Ownership + Grounding/Evidence + Konsolidierung + deterministische Governance."
        )
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--request", help="Freie deutschsprachige LMS-Anfrage")
    source.add_argument(
        "--use-case",
        choices=["use_case_1", "use_case_2", "use_case_3"],
        help="Verwendet die im simulierten Backend hinterlegte Standardanfrage.",
    )
    parser.add_argument("--model", default="qwen3:14b")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--output", help="Optionaler JSON-Ausgabepfad")
    parser.add_argument("--show-rejections", action="store_true", help="Zeigt Ownership- und Grounding-Rejections.")
    parser.add_argument("--show-grounding", action="store_true", help="Zeigt Grounding-Details auch ohne Ownership-Rejections.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    request = args.request or get_use_case_data(args.use_case)["user_request"]

    client = OllamaClient(model=args.model)
    client.health_check()
    result = orchestrate_with_llm_specialists(
        request,
        client=client,
        seed=args.seed,
        temperature=args.temperature,
    )

    print("\n" + "=" * 96)
    print("EXPERIMENTELLER LLM-MULTI-AGENT-PUFFER v3.2")
    print("Nicht Teil des eingefrorenen finalen v4-Holdout-Artefakts.")
    print("=" * 96)
    print(f"Rohe Klassifikation:       {result.analysis.use_case_id}")
    print(f"Validierte Klassifikation: {result.validation['validated_use_case_id']}")
    print(f"Rohe Agentenauswahl:       {', '.join(result.analysis.agents)}")
    print(f"Effektive Agenten:         {', '.join(result.validation['effective_agents'])}")
    print(f"Ausfuehrungsreihenfolge:   {', '.join(result.validation['execution_order'])}")

    print("\nLLM-Fachagenten:")
    for specialist in result.specialist_results:
        total_ms = specialist.tool_metrics.metrics.total_duration_ms + specialist.action_metrics.metrics.total_duration_ms
        print(
            f"- {specialist.agent_name}: Tools={specialist.requested_tools or ['keine']}, "
            f"Roh-Aktionen={len(specialist.proposed_actions)}, Confidence={specialist.confidence:.2f}, "
            f"LLM-Zeit~{total_ms/1000:.2f}s"
        )

    c = result.consolidation
    print("\nFilter/Konsolidierung:")
    print(f"- Roh-Aktionsvorschlaege:         {c['raw_specialist_action_count']}")
    print(f"- Ownership-Rejections:           {c['ownership_rejected_count']}")
    print(f"- Grounding-Rejections:           {c['grounding_rejected_count']}")
    print(f"- Beide Filter bestanden:         {c['passed_ownership_and_grounding_count']}")
    print(f"- Deterministische Privacy-Controls:{c.get('deterministic_privacy_control_count', 0)}")
    print(f"- Finale konsolidierte Aktionen:  {c['final_consolidated_action_count']}")

    if args.show_rejections:
        rejected = [d for d in result.ownership_decisions if not d.accepted]
        print("\nVerworfene Rollenueberschreitungen:")
        if not rejected:
            print("- Keine.")
        else:
            for item in rejected:
                print(f"- {item.agent_name}: {item.action}")
                print(f"  Grund: {item.reason}")

    if args.show_rejections or args.show_grounding:
        rejected = [d for d in result.grounding_decisions if not d.accepted]
        print("\nVerworfene ungeerdete/unbelegte Vorschlaege:")
        if not rejected:
            print("- Keine.")
        else:
            for item in rejected:
                print(f"- {item.agent_name}: {item.action}")
                print(f"  Grund: {item.reason}")

    print("\nFinaler ActionPlan nach Ownership, Grounding, Konsolidierung und Governance v3.2:")
    result.plan.print_summary()

    changed = [item for item in result.governance_decisions if item.changed]
    print("\nGovernance-Statuskorrekturen:")
    if not changed:
        print("- Keine Statusverschaerfung erforderlich.")
    else:
        for item in changed:
            print(f"- {item.agent_name}: {item.requested_status} -> {item.final_status}: {item.action}")
            print(f"  Regel: {item.rule}")

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON gespeichert: {output}")


if __name__ == "__main__":
    main()
