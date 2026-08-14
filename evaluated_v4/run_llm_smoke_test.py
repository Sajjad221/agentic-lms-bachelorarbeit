"""Einzelner End-to-End-Test der LLM-Eingangsstufe und Validierung."""

from __future__ import annotations

import json
from dataclasses import asdict

from llm_orchestrator import orchestrate_natural_language_request


REQUEST = (
    "Bereite für alle neuen Werkstudentinnen und Werkstudenten im IT-Support "
    "einen Onboarding-Lernpfad vor. Nutze vorhandene Inhalte zu Datenschutz, "
    "Ticketsystem und IT-Sicherheit, markiere fehlende oder veraltete Inhalte, "
    "setze eine Frist von 14 Tagen und informiere Teamleiter nur aggregiert "
    "über den Fortschritt."
)


def main() -> None:
    plan, analysis, response, validation = orchestrate_natural_language_request(REQUEST)

    print("\nLLM-Analyse (rohe Modellausgabe):")
    print(json.dumps(asdict(analysis), ensure_ascii=False, indent=2))

    print("\nValidierung:")
    print(json.dumps(validation, ensure_ascii=False, indent=2))

    print("\nActionPlan:")
    plan.print_summary()

    print("\nLaufzeitmetriken:")
    print(
        json.dumps(
            {
                "total_duration_ms": response.metrics.total_duration_ms,
                "load_duration_ms": response.metrics.load_duration_ms,
                "prompt_tokens": response.metrics.prompt_tokens,
                "output_tokens": response.metrics.output_tokens,
                "output_tokens_per_second": response.metrics.output_tokens_per_second,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
