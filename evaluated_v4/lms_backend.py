from copy import deepcopy
from typing import Any, Dict, List


LMS_BACKEND: Dict[str, Dict[str, Any]] = {
    "use_case_1": {
        "title": "Onboarding-Lernpfad",
        "user_request": (
            "Bereite für alle neuen Werkstudentinnen und Werkstudenten im IT-Support "
            "einen Onboarding-Lernpfad vor. Nutze vorhandene Inhalte zu Datenschutz, "
            "Ticketsystem und IT-Sicherheitsbasics, markiere fehlende oder veraltete Inhalte, "
            "identifiziere die passende Zielgruppe, setze eine Bearbeitungsfrist von 14 Tagen "
            "und informiere Teamleiter nur aggregiert über den Fortschritt."
        ),
        "course": {
            "course_id": "C-ONB-001",
            "title": "Onboarding IT-Support",
            "description": "Onboarding-Kurs für neue Werkstudentinnen und Werkstudenten im IT-Support",
        },
        "modules": [
            {"module_id": "M1", "title": "Datenschutzgrundlagen", "topic": "Datenschutz / Compliance", "status": "vorhanden"},
            {"module_id": "M2", "title": "Ticketsystem-Nutzung", "topic": "IT-Support-Prozess", "status": "vorhanden"},
            {"module_id": "M3", "title": "Eskalationsprozess", "topic": "Incident- und Eskalationslogik", "status": "fehlt"},
            {"module_id": "M4", "title": "Kommunikationsregeln", "topic": "Interne Kommunikation", "status": "veraltet"},
            {"module_id": "M5", "title": "IT-Sicherheitsbasics", "topic": "IT-Sicherheit", "status": "vorhanden"},
        ],
        "groups": [
            {"group_id": "G1", "name": "Neue Werkstudenten IT-Support", "role": "Lernende"},
            {"group_id": "G2", "name": "Teamleiter", "role": "Informationsrolle"},
            {"group_id": "G3", "name": "HR / Onboarding-Verantwortliche", "role": "Freigaberolle"},
        ],
        "users": [
            {"user_id": "U1", "name": "Person A", "group": "Neue Werkstudenten IT-Support", "role": "Lernende", "onboarding_status": "neu"},
            {"user_id": "U2", "name": "Person B", "group": "Neue Werkstudenten IT-Support", "role": "Lernende", "onboarding_status": "neu"},
            {"user_id": "U3", "name": "Person C", "group": "Teamleiter", "role": "Teamleiter", "onboarding_status": "nicht_relevant"},
        ],
        "permission_rules": [
            {"role": "Teamleiter", "can_view_individual_progress": False, "can_view_aggregated_progress": True},
            {"role": "HR", "can_view_individual_progress": False, "can_view_aggregated_progress": True},
            {"role": "Kursverantwortlicher", "can_approve_course_publication": True},
        ],
    },

    "use_case_2": {
        "title": "Kursanpassung nach schlechten Testergebnissen",
        "user_request": (
            "Analysiere die Testergebnisse im Kurs IT-Sicherheit Grundlagen. Identifiziere "
            "Themenbereiche mit auffällig schlechten Ergebnissen, prüfe Unterschiede zwischen "
            "Gruppen mit und ohne IT-Vorerfahrung, schlage passende Kursanpassungen und "
            "Wiederholungsaufgaben vor und informiere die betroffenen Lernenden datenschutzkonform "
            "über empfohlene Wiederholungen."
        ),
        "course": {
            "course_id": "C-SEC-001",
            "title": "IT-Sicherheit Grundlagen",
            "description": "Grundlagenkurs zur IT-Sicherheit für neue Werkstudentinnen und Werkstudenten",
        },
        "modules": [
            {"module_id": "M1", "title": "Passwortsicherheit", "topic": "Passwortsicherheit", "status": "vorhanden"},
            {"module_id": "M2", "title": "Phishing-Erkennung", "topic": "Phishing", "status": "vorhanden"},
            {"module_id": "M3", "title": "Datenschutzgrundlagen", "topic": "Datenschutz", "status": "vorhanden"},
            {"module_id": "M4", "title": "Sichere Nutzung von KI-Tools", "topic": "KI-Nutzung", "status": "fehlt"},
            {"module_id": "M5", "title": "Incident Reporting", "topic": "Incident Reporting", "status": "vorhanden"},
        ],
        "groups": [
            {"group_id": "G1", "name": "Neue Werkstudenten IT-Support"},
            {"group_id": "G2", "name": "Werkstudenten ohne IT-Vorerfahrung"},
            {"group_id": "G3", "name": "Werkstudenten mit IT-Vorerfahrung"},
            {"group_id": "G4", "name": "Teamleiter / Kursverantwortliche"},
        ],
        "test_results": {
            "overall": {
                "Passwortsicherheit": 82,
                "Phishing-Erkennung": 61,
                "Datenschutzgrundlagen": 74,
                "Sichere Nutzung von KI-Tools": 43,
                "Incident Reporting": 68,
            },
            "by_group": {
                "Werkstudenten ohne IT-Vorerfahrung": {
                    "Sichere Nutzung von KI-Tools": 35,
                    "Phishing-Erkennung": 54,
                },
                "Werkstudenten mit IT-Vorerfahrung": {
                    "Sichere Nutzung von KI-Tools": 58,
                    "Phishing-Erkennung": 71,
                },
            },
        },
        "permission_rules": [
            {"role": "Kursverantwortlicher", "can_view_group_results": True, "can_view_individual_results": True},
            {"role": "Teamleiter", "can_view_group_results": True, "can_view_individual_results": False},
            {"role": "Lernende", "can_receive_private_feedback": True},
        ],
    },

    "use_case_3": {
        "title": "Compliance-Pflichtschulung",
        "user_request": (
            "Bereite eine verpflichtende Datenschutz- und KI-Nutzungs-Schulung für alle Mitarbeitenden "
            "mit Zugriff auf Kundendaten vor. Weise die Schulung rollenbasiert zu, setze eine Frist "
            "von 14 Tagen, erstelle Erinnerungen für säumige Teilnehmende und bereite einen Bericht "
            "für HR und Compliance vor, ohne unnötige personenbezogene Lerndaten offenzulegen."
        ),
        "course": {
            "course_id": "C-COMP-001",
            "title": "Datenschutz und sichere KI-Nutzung",
            "description": "Pflichtschulung zu Datenschutz und sicherer Nutzung generativer KI",
            "mandatory": True,
        },
        "modules": [
            {"module_id": "M1", "title": "Datenschutzgrundlagen", "topic": "Datenschutz", "status": "vorhanden"},
            {"module_id": "M2", "title": "Umgang mit Kundendaten", "topic": "Kundendaten", "status": "vorhanden"},
            {"module_id": "M3", "title": "Sichere Nutzung generativer KI", "topic": "KI-Nutzung", "status": "fehlt"},
            {"module_id": "M4", "title": "Meldepflichten bei Datenschutzvorfällen", "topic": "Datenschutzvorfälle", "status": "vorhanden"},
            {"module_id": "M5", "title": "Interne KI-Richtlinie", "topic": "KI-Richtlinie", "status": "veraltet"},
        ],
        "groups": [
            {"group_id": "G1", "name": "Mitarbeitende IT-Support"},
            {"group_id": "G2", "name": "Mitarbeitende Customer Service"},
            {"group_id": "G3", "name": "Werkstudenten mit Kundendatenzugriff"},
            {"group_id": "G4", "name": "Teamleiter"},
            {"group_id": "G5", "name": "HR / Compliance"},
        ],
        "users": [
            {"user_id": "U1", "name": "Person A", "role": "Lernende", "group": "Mitarbeitende IT-Support", "customer_data_access": True, "ai_tool_usage_allowed": True},
            {"user_id": "U2", "name": "Person B", "role": "Lernende", "group": "Mitarbeitende Customer Service", "customer_data_access": True, "ai_tool_usage_allowed": True},
            {"user_id": "U3", "name": "Person C", "role": "Lernende", "group": "Werkstudenten mit Kundendatenzugriff", "customer_data_access": True, "ai_tool_usage_allowed": False},
            {"user_id": "U4", "name": "Person D", "role": "Lernende", "group": "Sonstige Mitarbeitende", "customer_data_access": False, "ai_tool_usage_allowed": False},
        ],
        "compliance_requirement": {
            "mandatory_if_customer_data_access": True,
            "deadline_days": 14,
            "reporting_preference": "aggregated",
            "individual_reporting_requires_approval": True,
            "escalation_requires_approval": True,
        },
        "permission_rules": [
            {"role": "HR", "can_view_completion_status": True, "can_view_individual_scores": False},
            {"role": "Compliance", "can_view_aggregated_completion": True, "can_view_individual_scores": False},
            {"role": "Teamleiter", "can_view_individual_completion": False, "can_receive_escalations": "approval_required"},
        ],
    },
}


def get_use_case_data(use_case_id: str) -> Dict[str, Any]:
    """
    Gibt eine Kopie der simulierten LMS-Daten für einen Use Case zurück.
    Dadurch werden die Originaldaten nicht versehentlich verändert.
    """
    if use_case_id not in LMS_BACKEND:
        raise ValueError(f"Unbekannter Use Case: {use_case_id}")

    return deepcopy(LMS_BACKEND[use_case_id])


def list_use_cases() -> List[str]:
    """
    Gibt alle verfügbaren Use-Case-IDs zurück.
    """
    return list(LMS_BACKEND.keys())


if __name__ == "__main__":
    print("Verfügbare Use Cases:")
    for use_case in list_use_cases():
        data = get_use_case_data(use_case)
        print(f"- {use_case}: {data['title']}")