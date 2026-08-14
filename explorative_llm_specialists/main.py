import json
import os

from baselines import run_rule_based_baseline, run_single_llm_baseline
from lms_backend import list_use_cases
from orchestrator import orchestrate_use_case


def run_all_scenarios():
    results = {}

    for use_case_id in list_use_cases():
        print("\n" + "#" * 100)
        print(f"ERGEBNISSE FÜR {use_case_id}")
        print("#" * 100 + "\n")

        multi_agent_plan = orchestrate_use_case(use_case_id)
        single_llm_plan = run_single_llm_baseline(use_case_id)
        rule_based_plan = run_rule_based_baseline(use_case_id)

        print("\n--- Multi-Agent-System ---")
        multi_agent_plan.print_summary()

        print("\n--- Einzelner LLM-Agent ---")
        single_llm_plan.print_summary()

        print("\n--- Regelbasierter Ansatz ---")
        rule_based_plan.print_summary()

        results[use_case_id] = {
            "multi_agent_system": multi_agent_plan.to_dict(),
            "single_llm_agent": single_llm_plan.to_dict(),
            "rule_based_baseline": rule_based_plan.to_dict(),
        }

    return results


def save_results(results, output_path="outputs/evaluation_results.json"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=4)

    print("\n" + "=" * 100)
    print(f"Ergebnisse wurden gespeichert unter: {output_path}")
    print("=" * 100)


if __name__ == "__main__":
    all_results = run_all_scenarios()
    save_results(all_results)