"""Entwicklungs- und Holdout-Fälle für das lokale LLM-Experiment.

Die 15 DEVELOPMENT_CASES wurden zur Prompt- und Validator-Entwicklung verwendet.
Die 15 HOLDOUT_CASES dürfen erst nach Abschluss der Entwicklung für die finale
Leistungsbewertung ausgeführt werden.
"""

from __future__ import annotations

from typing import Any, Dict, List


UC1_AGENTS = [
    "Course Agent",
    "Content Agent",
    "Enrollment Agent",
    "Assignment Agent",
    "Notification Agent",
    "Analytics/Metrics Agent",
    "Policy/Permission Agent",
]

UC2_AGENTS = [
    "Analytics/Metrics Agent",
    "Content Agent",
    "Course Agent",
    "Assignment Agent",
    "Notification Agent",
    "Policy/Permission Agent",
]

UC3_AGENTS = [
    "Course Agent",
    "Content Agent",
    "Enrollment Agent",
    "Assignment Agent",
    "Notification Agent",
    "Analytics/Metrics Agent",
    "Policy/Permission Agent",
]


DEVELOPMENT_PROMPTS: Dict[str, List[str]] = {
    "use_case_1": [
        "Stelle für neue Werkstudierende im IT-Support einen Onboarding-Pfad zusammen. Verwende die vorhandenen Materialien zu Datenschutz, Ticketsystem und IT-Sicherheit, kennzeichne Lücken oder veraltete Inhalte, plane 14 Tage Bearbeitungszeit und gib Führungskräften nur zusammengefasste Fortschrittswerte.",
        "Wir stellen neue Werkstudenten im Support ein. Bitte bereite im LMS einen zweiwöchigen Lernpfad vor, prüfe den vorhandenen Content auf fehlende beziehungsweise alte Bausteine und achte darauf, dass Teamleiter keine individuellen Fortschrittsdaten sehen.",
        "Für das IT-Support-Onboarding soll ein Lernpfad entstehen. Bestehende Datenschutz-, Ticket- und Security-Inhalte sollen weiterverwendet werden. Fehlendes und Überholtes muss auffallen, die Frist beträgt 14 Tage und das Management erhält nur aggregiertes Reporting.",
        "Plane das LMS-Onboarding für alle neuen Werkstudentinnen und Werkstudenten im IT-Support: passende Gruppe bestimmen, vorhandene Module nutzen, Content-Lücken markieren, Abschluss innerhalb von 14 Tagen vorsehen und Fortschritte gegenüber Teamleitern datensparsam zusammenfassen.",
        "Erzeuge einen freigabefähigen Vorschlag für den Onboarding-Lernpfad der neuen IT-Support-Werkstudierenden. Prüfe Module und Aktualität, ordne die Zielgruppe zu, lege eine 14-Tage-Frist nahe und verhindere personenbezogene Fortschrittsberichte an Teamleiter.",
    ],
    "use_case_2": [
        "Untersuche die Testergebnisse des Kurses IT-Sicherheit Grundlagen. Finde schwache Themen und Unterschiede zwischen Teilnehmenden mit und ohne IT-Erfahrung, leite Kursänderungen und Wiederholungsübungen ab und informiere Betroffene vertraulich.",
        "Im Sicherheitstest schneiden einige Themen schlecht ab. Bitte analysiere Gesamt- und Gruppenwerte, besonders nach IT-Vorerfahrung, prüfe geeignete Lernmaterialien, schlage Wiederholungen vor und vermeide eine öffentliche Kennzeichnung einzelner Lernender.",
        "Werte den Abschlusstest aus, erkenne auffällige Themenbereiche sowie Gruppenunterschiede, bereite didaktische Kursanpassungen und Aufgaben vor und formuliere private, datenschutzgerechte Lernhinweise.",
        "Der Kurs IT-Sicherheit muss anhand der Testergebnisse verbessert werden. Vergleiche Personen mit und ohne Vorkenntnisse, identifiziere Haupt- und Nebenprobleme, plane Zusatzcontent sowie Wiederholungsaufgaben und berücksichtige sensible Leistungsdaten.",
        "Erstelle einen kontrollierbaren Maßnahmenplan aus den Sicherheitstestdaten: schwache Inhalte und Gruppen erkennen, vorhandenen Content prüfen, Änderungen und Übungen vorschlagen und Benachrichtigungen nur datenschutzkonform vorbereiten.",
    ],
    "use_case_3": [
        "Bereite eine verpflichtende Schulung zu Datenschutz und sicherer KI-Nutzung für alle Beschäftigten mit Kundendatenzugriff vor. Plane rollenbasierte Zuweisung, 14 Tage Frist, Erinnerungen und einen datensparsamen Bericht an HR und Compliance.",
        "Alle Personen, die Kundendaten bearbeiten, sollen eine Compliance-Schulung absolvieren. Bitte prüfe Zielgruppe und Inhalte, setze zwei Wochen Zeit, bereite Mahnungen für offene Abschlüsse vor und vermeide unnötige personenbezogene Angaben im Reporting.",
        "Im LMS soll eine Datenschutz- und KI-Pflichtschulung eingerichtet werden. Bestimme die Pflicht anhand des Kundendatenzugriffs, kennzeichne fehlende oder veraltete Inhalte, plane Frist und Erinnerungen und begrenze HR-/Compliance-Berichte auf erforderliche Daten.",
        "Entwirf einen freigabefähigen Aktionsplan für die Compliance-Schulung von Mitarbeitenden mit Kundendatenzugriff: rollenbasiert zuweisen, 14-Tage-Frist, säumige Teilnehmende erinnern und sensible Lerndetails nicht an HR oder Führungskräfte weitergeben.",
        "Organisiere die verbindliche Datenschutz- und GenAI-Schulung für die relevante Belegschaft. Nutze Zugriffsmerkmale statt pauschaler Gruppen, prüfe den Content, plane Erinnerungs- und Eskalationsschritte und erzeuge nur ein datensparsames Compliance-Reporting.",
    ],
}


# Vollständige, semantisch gleichwertige Paraphrasen. Diese Fälle wurden nicht
# für die Entwicklung des Prompts oder des Validators verwendet.
HOLDOUT_PROMPTS: Dict[str, List[str]] = {
    "use_case_1": [
        "Konzipiere für neu startende Werkstudierende im IT-Support einen LMS-Onboardingpfad. Übernimm geeignete Bestandsmodule, weise auf fehlende oder überholte Inhalte hin, ordne die richtige Lerngruppe zu, plane eine Frist von zwei Wochen und stelle Teamleitungen ausschließlich verdichtete Fortschrittsinformationen bereit.",
        "Für den Einstieg neuer IT-Support-Werkstudenten soll das LMS einen Lernpfad vorbereiten. Prüfe Datenschutz-, Ticket- und Security-Materialien auf Lücken und Aktualität, berücksichtige die Zielgruppenzuweisung, setze 14 Tage Bearbeitungszeit und formuliere Benachrichtigungen sowie ein nicht personenbezogenes Teamleiter-Reporting.",
        "Erstelle einen prüfbaren Vorschlag für das Support-Onboarding neuer Werkstudierender: Kursaufbau aus vorhandenen Modulen, Kennzeichnung fehlender oder veralteter Inhalte, Zuordnung der Lernenden, Abschlussfrist nach 14 Tagen und ausschließlich aggregierte Fortschrittsmeldungen an Vorgesetzte.",
        "Bereite im LMS das Onboarding der neuen Werkstudentinnen und Werkstudenten des IT-Supports vor. Nutze vorhandenen Content, markiere Aktualisierungsbedarf und Lücken, bestimme die Zielgruppe, plane Frist und Lernendeninformation und verhindere individuelle Fortschrittsübersichten für Teamleiter.",
        "Entwickle einen freigabefähigen Onboarding-Aktionsplan für neue Kräfte im IT-Support. Er soll Kursstruktur, Content-Prüfung, Gruppenzuordnung, eine 14-Tage-Frist, Benachrichtigungen und datensparsame Fortschrittsauswertungen für Führungskräfte abdecken.",
    ],
    "use_case_2": [
        "Analysiere die Ergebnisse des Abschlusstests im Kurs IT-Sicherheit. Ermittle schwache Themen und Unterschiede nach IT-Vorerfahrung, prüfe dazu passende Lernmaterialien, bereite Kursverbesserungen und Wiederholungsaufgaben vor und informiere Betroffene nur privat und datenschutzgerecht.",
        "Aus den Sicherheitstestdaten soll ein Maßnahmenplan entstehen. Vergleiche Gesamtwerte und Gruppen mit beziehungsweise ohne Vorkenntnisse, finde problematische Themen, kontrolliere vorhandenen Content, schlage Kursänderungen und Übungen vor und schütze personenbezogene Leistungsinformationen.",
        "Bitte werte den IT-Sicherheitstest aus: auffällige Themenbereiche und gruppenspezifische Schwächen erkennen, Lernmaterialien prüfen, didaktische Anpassungen sowie Wiederholungen planen und individuelle Lernhinweise vertraulich vorbereiten.",
        "Verbessere den Kurs IT-Sicherheit auf Grundlage der Testresultate. Berücksichtige Unterschiede zwischen Lernenden mit und ohne IT-Erfahrung, identifiziere Haupt- und Nebenprobleme, ergänze geeigneten Content und Aufgaben und behandle alle Leistungsdaten datenschutzkonform.",
        "Erzeuge aus den Testergebnissen einen kontrollierbaren Anpassungsvorschlag. Er soll Analyse und Gruppenvergleich, Content-Prüfung, Kursanpassung, Wiederholungsübungen und private Benachrichtigungen umfassen; eine öffentliche Kennzeichnung einzelner Personen ist auszuschließen.",
    ],
    "use_case_3": [
        "Richte eine verbindliche Datenschutz- und GenAI-Schulung für Beschäftigte mit Zugriff auf Kundendaten ein. Prüfe Kursinhalte, bestimme die Zielgruppe anhand von Rollen und Zugriffsmerkmalen, plane 14 Tage, Erinnerungen und Eskalationen und beschränke Berichte an HR und Compliance auf notwendige Daten.",
        "Bereite einen freigabefähigen LMS-Plan für die Compliance-Pflichtschulung vor. Betroffen sind Mitarbeitende mit Kundendatenzugriff; Content-Lücken und veraltete Richtlinien sind zu markieren, die Schulung ist rollenbasiert zuzuweisen, nach zwei Wochen zu erinnern und nur datensparsam zu berichten.",
        "Für alle relevanten Beschäftigten soll eine Pflichtschulung zu Datenschutz und sicherer KI-Nutzung entstehen. Leite die Teilnahme aus Zugriffsrechten ab, prüfe und strukturiere den Content, setze eine 14-Tage-Frist, plane Erinnerungen und erzeuge für HR beziehungsweise Compliance keinen unnötig personenbezogenen Bericht.",
        "Organisiere die Compliance-Schulung im LMS anhand des Merkmals Kundendatenzugriff. Berücksichtige fehlende und veraltete Inhalte, Kursentwurf, Zuweisung, Frist, Mahnungen sowie Eskalationen und verhindere die Weitergabe sensibler Lerndetails an unberechtigte Rollen.",
        "Erstelle einen kontrollierbaren Aktionsplan für eine Datenschutz- und KI-Pflichtschulung. Er muss Zielgruppenprüfung, Content- und Kursvorbereitung, zweiwöchige Bearbeitungsfrist, Erinnerungslogik und ein auf erforderliche Teilnahmeinformationen begrenztes HR-/Compliance-Reporting enthalten.",
    ],
}


# Granulare Sollkategorien pro Anfrage. Die Annotationen beziehen sich auf
# ausdrücklich verlangte oder unmittelbar notwendige Funktionen, nicht pauschal
# auf alle Agenten eines Use Cases.
CATEGORY_TO_AGENTS: Dict[str, List[str]] = {
    "course_structure": ["Course Agent"],
    "content_review": ["Content Agent"],
    "target_group": ["Enrollment Agent"],
    "deadline": ["Assignment Agent"],
    "learner_notification": ["Notification Agent"],
    "reporting": ["Analytics/Metrics Agent"],
    "governance": ["Policy/Permission Agent"],
    "result_analysis": ["Analytics/Metrics Agent"],
    "group_comparison": ["Analytics/Metrics Agent"],
    "course_adjustment": ["Course Agent"],
    "repeat_tasks": ["Assignment Agent"],
    "private_notification": ["Notification Agent"],
    "target_assignment": ["Enrollment Agent"],
    "course_setup": ["Course Agent"],
    # Die Architektur trennt Erinnerungslogik (Assignment) und Nachrichtentext
    # (Notification); beide Rollen sind deshalb erforderlich.
    "reminders": ["Assignment Agent", "Notification Agent"],
    "escalations": ["Notification Agent", "Policy/Permission Agent"],
}

DEVELOPMENT_LABELS: Dict[str, List[Dict[str, List[str]]]] = {
    "use_case_1": [
        {"tasks": ["course_structure", "content_review", "target_group", "deadline", "reporting", "governance"], "privacy": ["aggregation", "no_personal_data"]},
        {"tasks": ["course_structure", "content_review", "target_group", "deadline", "reporting", "governance"], "privacy": ["no_personal_data", "permissions"]},
        {"tasks": ["course_structure", "content_review", "deadline", "reporting", "governance"], "privacy": ["aggregation", "no_personal_data"]},
        {"tasks": ["course_structure", "content_review", "target_group", "deadline", "reporting", "governance"], "privacy": ["aggregation", "no_personal_data"]},
        {"tasks": ["course_structure", "content_review", "target_group", "deadline", "reporting", "governance"], "privacy": ["no_personal_data", "permissions"]},
    ],
    "use_case_2": [
        {"tasks": ["result_analysis", "group_comparison", "course_adjustment", "repeat_tasks", "private_notification", "governance"], "privacy": ["private_notification", "performance_permissions"]},
        {"tasks": ["result_analysis", "group_comparison", "content_review", "repeat_tasks", "governance"], "privacy": ["no_public_shaming", "performance_permissions"]},
        {"tasks": ["result_analysis", "group_comparison", "course_adjustment", "repeat_tasks", "private_notification", "governance"], "privacy": ["private_notification", "performance_permissions"]},
        {"tasks": ["result_analysis", "group_comparison", "content_review", "course_adjustment", "repeat_tasks", "governance"], "privacy": ["performance_permissions"]},
        {"tasks": ["result_analysis", "group_comparison", "content_review", "course_adjustment", "repeat_tasks", "private_notification", "governance"], "privacy": ["private_notification", "performance_permissions"]},
    ],
    "use_case_3": [
        {"tasks": ["target_assignment", "course_setup", "deadline", "reminders", "reporting", "governance"], "privacy": ["data_minimization", "report_restriction", "role_permissions"]},
        {"tasks": ["target_assignment", "content_review", "course_setup", "deadline", "reminders", "reporting", "governance"], "privacy": ["data_minimization", "report_restriction", "role_permissions"]},
        {"tasks": ["target_assignment", "content_review", "course_setup", "deadline", "reminders", "reporting", "governance"], "privacy": ["data_minimization", "report_restriction", "role_permissions"]},
        {"tasks": ["target_assignment", "course_setup", "deadline", "reminders", "reporting", "governance"], "privacy": ["report_restriction", "role_permissions"]},
        {"tasks": ["target_assignment", "content_review", "course_setup", "reminders", "escalations", "reporting", "governance"], "privacy": ["data_minimization", "report_restriction", "role_permissions"]},
    ],
}

HOLDOUT_LABELS: Dict[str, List[Dict[str, List[str]]]] = {
    "use_case_1": [
        {"tasks": ["course_structure", "content_review", "target_group", "deadline", "reporting", "governance"], "privacy": ["aggregation", "no_personal_data"]},
        {"tasks": ["course_structure", "content_review", "target_group", "deadline", "learner_notification", "reporting", "governance"], "privacy": ["no_personal_data", "permissions"]},
        {"tasks": ["course_structure", "content_review", "target_group", "deadline", "reporting", "governance"], "privacy": ["aggregation", "no_personal_data"]},
        {"tasks": ["course_structure", "content_review", "target_group", "deadline", "learner_notification", "reporting", "governance"], "privacy": ["no_personal_data", "permissions"]},
        {"tasks": ["course_structure", "content_review", "target_group", "deadline", "learner_notification", "reporting", "governance"], "privacy": ["aggregation", "no_personal_data"]},
    ],
    "use_case_2": [
        {"tasks": ["result_analysis", "group_comparison", "content_review", "course_adjustment", "repeat_tasks", "private_notification", "governance"], "privacy": ["private_notification", "performance_permissions"]},
        {"tasks": ["result_analysis", "group_comparison", "content_review", "course_adjustment", "repeat_tasks", "governance"], "privacy": ["performance_permissions"]},
        {"tasks": ["result_analysis", "group_comparison", "content_review", "course_adjustment", "repeat_tasks", "private_notification", "governance"], "privacy": ["private_notification", "performance_permissions"]},
        {"tasks": ["result_analysis", "group_comparison", "content_review", "course_adjustment", "repeat_tasks", "governance"], "privacy": ["performance_permissions"]},
        {"tasks": ["result_analysis", "group_comparison", "content_review", "course_adjustment", "repeat_tasks", "private_notification", "governance"], "privacy": ["private_notification", "no_public_shaming", "performance_permissions"]},
    ],
    "use_case_3": [
        {"tasks": ["target_assignment", "content_review", "course_setup", "deadline", "reminders", "escalations", "reporting", "governance"], "privacy": ["data_minimization", "report_restriction", "role_permissions"]},
        {"tasks": ["target_assignment", "content_review", "course_setup", "deadline", "reminders", "reporting", "governance"], "privacy": ["data_minimization", "report_restriction", "role_permissions"]},
        {"tasks": ["target_assignment", "content_review", "course_setup", "deadline", "reminders", "reporting", "governance"], "privacy": ["data_minimization", "report_restriction", "role_permissions"]},
        {"tasks": ["target_assignment", "content_review", "course_setup", "deadline", "reminders", "escalations", "reporting", "governance"], "privacy": ["report_restriction", "role_permissions"]},
        {"tasks": ["target_assignment", "content_review", "course_setup", "deadline", "reminders", "reporting", "governance"], "privacy": ["data_minimization", "report_restriction", "role_permissions"]},
    ],
}


def expected_agents_for_categories(categories: List[str]) -> List[str]:
    ordered = [
        "Analytics/Metrics Agent",
        "Content Agent",
        "Course Agent",
        "Enrollment Agent",
        "Assignment Agent",
        "Notification Agent",
        "Policy/Permission Agent",
    ]
    required = {
        agent
        for category in categories
        for agent in CATEGORY_TO_AGENTS.get(category, [])
    }
    return [agent for agent in ordered if agent in required]


def expected_governance_controls(
    use_case_id: str,
    task_categories: List[str],
    privacy_categories: List[str],
) -> List[str]:
    tasks = set(task_categories)
    privacy = set(privacy_categories)
    controls: List[str] = []
    if use_case_id == "use_case_1":
        if "reporting" in tasks:
            controls.append("aggregated_progress_allowed")
        if "no_personal_data" in privacy:
            controls.append("personal_progress_blocked")
        if "course_structure" in tasks:
            controls.append("course_publication_requires_approval")
        if "target_group" in tasks:
            controls.append("automatic_enrollment_requires_approval")
        if "learner_notification" in tasks:
            controls.append("learner_notification_requires_approval")
    elif use_case_id == "use_case_2":
        if "course_adjustment" in tasks:
            controls.append("course_adjustment_requires_approval")
        if "repeat_tasks" in tasks:
            controls.append("repeat_tasks_require_approval")
        if "private_notification" in tasks:
            controls.append("private_hints_require_approval")
        if "performance_permissions" in privacy:
            controls.append("personal_test_results_blocked")
        if "group_comparison" in tasks:
            controls.append("group_evaluation_allowed")
    elif use_case_id == "use_case_3":
        if "course_setup" in tasks:
            controls.append("course_draft_requires_approval")
        if "target_assignment" in tasks:
            controls.append("role_assignment_requires_approval")
        if "reminders" in tasks:
            controls.append("reminders_require_approval")
        if "report_restriction" in privacy:
            controls.append("personal_performance_data_blocked")
        if "escalations" in tasks:
            controls.append("escalation_requires_approval")
        if "reporting" in tasks:
            controls.append("aggregated_compliance_report_allowed")
    return controls


def build_cases(dataset: str) -> List[Dict[str, Any]]:
    if dataset == "development":
        prompts = DEVELOPMENT_PROMPTS
        labels = DEVELOPMENT_LABELS
    elif dataset == "holdout":
        prompts = HOLDOUT_PROMPTS
        labels = HOLDOUT_LABELS
    else:
        raise ValueError(f"Unbekannter Datensatz: {dataset}")

    cases: List[Dict[str, Any]] = []
    for use_case_id, items in prompts.items():
        case_labels = labels[use_case_id]
        if len(items) != len(case_labels):
            raise ValueError(f"Anzahl Prompts und Annotationen stimmt für {use_case_id} nicht überein.")
        for variant_index, (prompt, label) in enumerate(zip(items, case_labels), start=1):
            task_categories = list(label["tasks"])
            cases.append(
                {
                    "case_id": f"{dataset}_{use_case_id}_v{variant_index}",
                    "dataset": dataset,
                    "expected_use_case_id": use_case_id,
                    "variant_index": variant_index,
                    "prompt": prompt,
                    "expected_agents": expected_agents_for_categories(task_categories),
                    "expected_task_categories": task_categories,
                    "expected_privacy_categories": list(label["privacy"]),
                    "expected_governance_controls": expected_governance_controls(
                        use_case_id, task_categories, list(label["privacy"])
                    ),
                }
            )
    return cases
