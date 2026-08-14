"""Statische Integritätsprüfung der eingefrorenen Experimentversion."""

from __future__ import annotations

from experiment_cases import build_cases
from run_llm_experiment import (
    GOVERNANCE_CONTROLS,
    PRIVACY_CATEGORY_TERMS,
    TASK_CATEGORY_TERMS,
    reproducibility_info,
)


def main() -> None:
    development = build_cases("development")
    holdout = build_cases("holdout")
    assert len(development) == 15
    assert len(holdout) == 15
    ids = [case["case_id"] for case in [*development, *holdout]]
    assert len(ids) == len(set(ids)), "Case-IDs sind nicht eindeutig."

    known_controls = {
        control["id"]
        for controls in GOVERNANCE_CONTROLS.values()
        for control in controls
    }
    for case in [*development, *holdout]:
        for category in case["expected_task_categories"]:
            assert category in TASK_CATEGORY_TERMS, f"Unbekannte Aufgabenkategorie: {category}"
        for category in case["expected_privacy_categories"]:
            assert category in PRIVACY_CATEGORY_TERMS, f"Unbekannte Datenschutzkategorie: {category}"
        for control in case["expected_governance_controls"]:
            assert control in known_controls, f"Unbekannte Governance-Kontrolle: {control}"
        assert case["expected_agents"], f"Keine Sollagenten für {case['case_id']}"

    dev_info = reproducibility_info(development)
    holdout_info = reproducibility_info(holdout)
    print("Integritätsprüfung erfolgreich.")
    print(f"Development-Fälle: {len(development)}")
    print(f"Holdout-Fälle: {len(holdout)}")
    print(f"Development-Datensatz-Hash: {dev_info['dataset_sha256']}")
    print(f"Holdout-Datensatz-Hash: {holdout_info['dataset_sha256']}")
    print(f"System-Prompt-Hash: {holdout_info['system_prompt_sha256']}")
    print(f"Rubrik-Hash: {holdout_info['scoring_configuration_sha256']}")


if __name__ == "__main__":
    main()
