import json
import os


EVALUATION_SCORES = {
    "use_case_1": {
        "multi_agent_system": {
            "Aufgabenzerlegung": 2,
            "Agentenauswahl": 2,
            "Agentenkoordination": 2,
            "Fachliche Sinnhaftigkeit": 2,
            "Datenschutz, Rollen- und Rechteprüfung": 2,
            "Umgang mit Unsicherheit": 1,
            "Human-in-the-loop": 2,
            "Nachvollziehbarkeit": 2,
            "Begründung": "Der Multi-Agent-Ansatz erkennt Content-Status, Zielgruppe, Frist, Reporting-Grenzen und blockiert personenbezogene Fortschrittsdaten an Teamleiter.",
        },
        "single_llm_agent": {
            "Aufgabenzerlegung": 1,
            "Agentenauswahl": 0,
            "Agentenkoordination": 0,
            "Fachliche Sinnhaftigkeit": 1,
            "Datenschutz, Rollen- und Rechteprüfung": 1,
            "Umgang mit Unsicherheit": 1,
            "Human-in-the-loop": 1,
            "Nachvollziehbarkeit": 1,
            "Begründung": "Der Einzel-LLM-Agent erkennt die Grundaufgabe, trennt aber Content-Status, Rollenprüfung, Reporting und Freigaben weniger sauber.",
        },
        "rule_based_baseline": {
            "Aufgabenzerlegung": 1,
            "Agentenauswahl": 0,
            "Agentenkoordination": 0,
            "Fachliche Sinnhaftigkeit": 1,
            "Datenschutz, Rollen- und Rechteprüfung": 0,
            "Umgang mit Unsicherheit": 0,
            "Human-in-the-loop": 0,
            "Nachvollziehbarkeit": 1,
            "Begründung": "Der regelbasierte Ansatz erkennt fehlende und veraltete Module, berücksichtigt aber Zielgruppe, Rollenrechte, Reporting und Freigaben kaum.",
        },
    },

    "use_case_2": {
        "multi_agent_system": {
            "Aufgabenzerlegung": 2,
            "Agentenauswahl": 2,
            "Agentenkoordination": 2,
            "Fachliche Sinnhaftigkeit": 2,
            "Datenschutz, Rollen- und Rechteprüfung": 2,
            "Umgang mit Unsicherheit": 1,
            "Human-in-the-loop": 2,
            "Nachvollziehbarkeit": 2,
            "Begründung": "Der Multi-Agent-Ansatz erkennt sowohl das Hauptproblem KI-Nutzung als auch das gruppenspezifische Phishing-Nebenproblem und berücksichtigt Datenschutz, Unsicherheit und Freigabe.",
        },
        "single_llm_agent": {
            "Aufgabenzerlegung": 1,
            "Agentenauswahl": 0,
            "Agentenkoordination": 0,
            "Fachliche Sinnhaftigkeit": 1,
            "Datenschutz, Rollen- und Rechteprüfung": 1,
            "Umgang mit Unsicherheit": 1,
            "Human-in-the-loop": 1,
            "Nachvollziehbarkeit": 1,
            "Begründung": "Der Einzel-LLM-Agent erkennt grundsätzlich den Bedarf für Zusatzmaterial und Wiederholungsaufgaben, trennt aber Analyse, Gruppenunterschiede, Datenschutz und Freigabe weniger präzise.",
        },
        "rule_based_baseline": {
            "Aufgabenzerlegung": 1,
            "Agentenauswahl": 0,
            "Agentenkoordination": 0,
            "Fachliche Sinnhaftigkeit": 1,
            "Datenschutz, Rollen- und Rechteprüfung": 0,
            "Umgang mit Unsicherheit": 1,
            "Human-in-the-loop": 0,
            "Nachvollziehbarkeit": 1,
            "Begründung": "Der regelbasierte Ansatz erkennt nur den Gesamtwert unter 60 Prozent, übersieht aber differenzierte Gruppenunterschiede und behandelt Datenschutz/Freigabe kaum.",
        },
    },

    "use_case_3": {
        "multi_agent_system": {
            "Aufgabenzerlegung": 2,
            "Agentenauswahl": 2,
            "Agentenkoordination": 2,
            "Fachliche Sinnhaftigkeit": 2,
            "Datenschutz, Rollen- und Rechteprüfung": 2,
            "Umgang mit Unsicherheit": 1,
            "Human-in-the-loop": 2,
            "Nachvollziehbarkeit": 2,
            "Begründung": "Der Multi-Agent-Ansatz bestimmt die Zielgruppe anhand von Kundendatenzugriff, prüft Content-Status, Reporting-Grenzen, Freigaben und blockiert personenbezogene Leistungsdaten.",
        },
        "single_llm_agent": {
            "Aufgabenzerlegung": 1,
            "Agentenauswahl": 0,
            "Agentenkoordination": 0,
            "Fachliche Sinnhaftigkeit": 1,
            "Datenschutz, Rollen- und Rechteprüfung": 1,
            "Umgang mit Unsicherheit": 1,
            "Human-in-the-loop": 1,
            "Nachvollziehbarkeit": 1,
            "Begründung": "Der Einzel-LLM-Agent erkennt die Pflichtschulung, bleibt bei Rollenrechten, Reporting-Tiefe und Eskalationslogik jedoch allgemein.",
        },
        "rule_based_baseline": {
            "Aufgabenzerlegung": 1,
            "Agentenauswahl": 0,
            "Agentenkoordination": 0,
            "Fachliche Sinnhaftigkeit": 1,
            "Datenschutz, Rollen- und Rechteprüfung": 0,
            "Umgang mit Unsicherheit": 1,
            "Human-in-the-loop": 0,
            "Nachvollziehbarkeit": 1,
            "Begründung": "Der regelbasierte Ansatz erkennt Kundendatenzugriff und Frist, prüft aber keine differenzierten Rollenrechte, Reporting-Grenzen oder Eskalationsfreigaben.",
        },
    },
}


def calculate_total(scores: dict) -> int:
    return sum(value for key, value in scores.items() if isinstance(value, int))


def print_evaluation_table() -> None:
    print("=" * 100)
    print("Szenariobasierte Bewertung")
    print("=" * 100)

    for use_case_id, approaches in EVALUATION_SCORES.items():
        print(f"\n{use_case_id}")
        print("-" * 100)

        for approach, scores in approaches.items():
            total = calculate_total(scores)
            print(f"{approach}: {total}/16")
            print(f"Begründung: {scores['Begründung']}\n")


def save_evaluation(output_path: str = "outputs/evaluation_scores.json") -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    output = {}

    for use_case_id, approaches in EVALUATION_SCORES.items():
        output[use_case_id] = {}

        for approach, scores in approaches.items():
            output[use_case_id][approach] = {
                "total_score": calculate_total(scores),
                "max_score": 16,
                "criteria": {key: value for key, value in scores.items() if isinstance(value, int)},
                "reason": scores["Begründung"],
            }

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=4)

    print(f"\nBewertung gespeichert unter: {output_path}")


if __name__ == "__main__":
    print_evaluation_table()
    save_evaluation()