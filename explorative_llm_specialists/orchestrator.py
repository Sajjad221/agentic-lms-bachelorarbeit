from typing import Any, Dict, List

from action_plan import ActionPlan
from agents import (
    run_analytics_agent,
    run_assignment_agent,
    run_content_agent,
    run_course_agent,
    run_enrollment_agent,
    run_notification_agent,
    run_policy_permission_agent,
)
from lms_backend import get_use_case_data, list_use_cases


def get_tasks_for_use_case(use_case_id: str) -> List[str]:
    """
    Simuliert die Aufgabenzerlegung durch den Orchestrator Agent.
    """
    if use_case_id == "use_case_1":
        return [
            "Nutzeranfrage analysieren",
            "Content-Status vorhandener, fehlender und veralteter Inhalte prüfen",
            "Lernpfadstruktur vorbereiten",
            "Zielgruppe der neuen Werkstudentinnen und Werkstudenten identifizieren",
            "Bearbeitungsfrist vorschlagen",
            "Benachrichtigungen und Reporting vorbereiten",
            "Rollen-, Rechte- und Datenschutzprüfung durchführen",
            "Freigabefähigen ActionPlan erzeugen",
        ]

    if use_case_id == "use_case_2":
        return [
            "Nutzeranfrage analysieren",
            "Testergebnisse und schwache Themenbereiche auswerten",
            "Gruppenunterschiede prüfen",
            "Vorhandene und fehlende Lerninhalte prüfen",
            "Kursanpassungen und Wiederholungsaufgaben vorschlagen",
            "Datenschutzfreundliche Hinweise an Lernende vorbereiten",
            "Rollen-, Rechte- und Datenschutzprüfung durchführen",
            "Freigabefähigen ActionPlan erzeugen",
        ]

    if use_case_id == "use_case_3":
        return [
            "Nutzeranfrage analysieren",
            "Zielgruppe anhand von Kundendatenzugriff und Pflichtschulungsmerkmal bestimmen",
            "Content-Status der Compliance-Schulung prüfen",
            "Pflichtschulung und Frist vorbereiten",
            "Erinnerungs- und Eskalationslogik vorbereiten",
            "Bericht für HR und Compliance datensparsam vorbereiten",
            "Rollen-, Rechte- und Datenschutzprüfung durchführen",
            "Freigabefähigen ActionPlan erzeugen",
        ]

    raise ValueError(f"Unbekannter Use Case: {use_case_id}")


def orchestrate_use_case(use_case_id: str) -> ActionPlan:
    """
    Koordiniert die Verarbeitung eines Use Cases.
    """
    data: Dict[str, Any] = get_use_case_data(use_case_id)

    plan = ActionPlan(
        use_case_id=use_case_id,
        title=data["title"],
        user_request=data["user_request"],
    )

    plan.add_agent("Orchestrator Agent")

    for task in get_tasks_for_use_case(use_case_id):
        plan.add_task(task)

    if use_case_id == "use_case_1":
        run_content_agent(use_case_id, data, plan)
        run_course_agent(use_case_id, data, plan)
        run_enrollment_agent(use_case_id, data, plan)
        run_assignment_agent(use_case_id, data, plan)
        run_notification_agent(use_case_id, data, plan)
        run_analytics_agent(use_case_id, data, plan)
        run_policy_permission_agent(use_case_id, data, plan)

    elif use_case_id == "use_case_2":
        run_analytics_agent(use_case_id, data, plan)
        run_content_agent(use_case_id, data, plan)
        run_course_agent(use_case_id, data, plan)
        run_enrollment_agent(use_case_id, data, plan)
        run_assignment_agent(use_case_id, data, plan)
        run_notification_agent(use_case_id, data, plan)
        run_policy_permission_agent(use_case_id, data, plan)

    elif use_case_id == "use_case_3":
        run_enrollment_agent(use_case_id, data, plan)
        run_content_agent(use_case_id, data, plan)
        run_course_agent(use_case_id, data, plan)
        run_assignment_agent(use_case_id, data, plan)
        run_notification_agent(use_case_id, data, plan)
        run_analytics_agent(use_case_id, data, plan)
        run_policy_permission_agent(use_case_id, data, plan)

    else:
        raise ValueError(f"Unbekannter Use Case: {use_case_id}")

    return plan


if __name__ == "__main__":
    for use_case_id in list_use_cases():
        action_plan = orchestrate_use_case(use_case_id)
        action_plan.print_summary()
        print("\n\n")