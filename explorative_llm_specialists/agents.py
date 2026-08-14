from typing import Any, Dict, List

from action_plan import ActionPlan


def run_content_agent(use_case_id: str, data: Dict[str, Any], plan: ActionPlan) -> None:
    plan.add_agent("Content Agent")

    modules = data.get("modules", [])
    missing_modules = [module for module in modules if module.get("status") == "fehlt"]
    outdated_modules = [module for module in modules if module.get("status") == "veraltet"]

    if missing_modules:
        titles = ", ".join(module["title"] for module in missing_modules)
        plan.add_action(
            action=f"Fehlende Inhalte markieren: {titles}",
            status="erlaubt",
            reason="Fehlende Inhalte müssen vor Veröffentlichung oder Kursanpassung sichtbar gemacht werden.",
            used_data=["Module", "ContentItem"],
        )

    if outdated_modules:
        titles = ", ".join(module["title"] for module in outdated_modules)
        plan.add_action(
            action=f"Veraltete Inhalte zur Aktualisierung markieren: {titles}",
            status="erlaubt",
            reason="Veraltete Inhalte sollten vor Nutzung oder Veröffentlichung fachlich geprüft werden.",
            used_data=["Module", "ContentItem"],
        )

    if not missing_modules and not outdated_modules:
        plan.add_action(
            action="Content-Status prüfen",
            status="erlaubt",
            reason="Es wurden keine fehlenden oder veralteten Inhalte erkannt.",
            used_data=["Module", "ContentItem"],
        )


def run_course_agent(use_case_id: str, data: Dict[str, Any], plan: ActionPlan) -> None:
    plan.add_agent("Course Agent")

    course_title = data.get("course", {}).get("title", "Unbekannter Kurs")

    if use_case_id == "use_case_1":
        plan.add_action(
            action=f"Lernpfadstruktur für Kurs '{course_title}' vorbereiten",
            status="erlaubt",
            reason="Die Erstellung eines Kursstrukturvorschlags ist eine vorbereitende Aktion.",
            used_data=["Course", "Module"],
        )
        plan.add_action(
            action=f"Kurs '{course_title}' veröffentlichen",
            status="freigabepflichtig",
            reason="Die Veröffentlichung eines Kurses hat organisatorische Auswirkungen und benötigt menschliche Freigabe.",
            used_data=["Course", "PermissionRule"],
        )

    elif use_case_id == "use_case_2":
        plan.add_action(
            action=f"Kursanpassung für '{course_title}' vorbereiten",
            status="freigabepflichtig",
            reason="Kursänderungen auf Basis von Testergebnissen müssen fachlich geprüft und freigegeben werden.",
            used_data=["Course", "Module", "TestResult"],
        )

    elif use_case_id == "use_case_3":
        plan.add_action(
            action=f"Pflichtschulung '{course_title}' als Kursentwurf vorbereiten",
            status="freigabepflichtig",
            reason="Eine Pflichtschulung betrifft Zielgruppen, Fristen und Nachweispflichten und benötigt Freigabe.",
            used_data=["Course", "Module", "ComplianceRequirement"],
        )


def run_enrollment_agent(use_case_id: str, data: Dict[str, Any], plan: ActionPlan) -> None:
    plan.add_agent("Enrollment Agent")

    if use_case_id == "use_case_1":
        target_group = "Neue Werkstudenten IT-Support"
        plan.add_action(
            action=f"Zielgruppe identifizieren: {target_group}",
            status="erlaubt",
            reason="Die Zielgruppe ergibt sich aus der simulierten Gruppenzuordnung.",
            used_data=["Group", "User"],
        )
        plan.add_action(
            action=f"Lernende aus Zielgruppe '{target_group}' automatisch einschreiben",
            status="freigabepflichtig",
            reason="Automatische Einschreibungen verändern den Kursstatus für Nutzerinnen und Nutzer und benötigen Freigabe.",
            used_data=["User", "Group", "PermissionRule"],
        )

    elif use_case_id == "use_case_2":
        affected_group = "Werkstudenten ohne IT-Vorerfahrung"
        plan.add_action(
            action=f"Betroffene Gruppe identifizieren: {affected_group}",
            status="erlaubt",
            reason="Die Gruppe zeigt auffällig schwache Ergebnisse bei KI-Nutzung und Phishing-Erkennung.",
            used_data=["Group", "TestResult"],
        )

    elif use_case_id == "use_case_3":
        users = data.get("users", [])
        target_users = [user for user in users if user.get("customer_data_access") is True]
        target_count = len(target_users)

        plan.add_action(
            action=f"Zielgruppe für Pflichtschulung bestimmen: {target_count} Personen mit Kundendatenzugriff",
            status="erlaubt",
            reason="Die Zielgruppe wird anhand des Merkmals Kundendatenzugriff bestimmt und nicht pauschal aus einer Gruppe abgeleitet.",
            used_data=["User", "AccessAttribute", "ComplianceRequirement"],
        )
        plan.add_action(
            action="Pflichtschulung rollenbasiert zuweisen",
            status="freigabepflichtig",
            reason="Die Zuweisung einer Pflichtschulung hat organisatorische Auswirkungen und benötigt Freigabe.",
            used_data=["User", "Role", "PermissionRule", "ComplianceRequirement"],
        )


def run_assignment_agent(use_case_id: str, data: Dict[str, Any], plan: ActionPlan) -> None:
    plan.add_agent("Assignment Agent")

    if use_case_id == "use_case_1":
        plan.add_action(
            action="Bearbeitungsfrist von 14 Tagen vorschlagen",
            status="erlaubt",
            reason="Die Frist wird nur als Vorschlag vorbereitet und nicht automatisch angewendet.",
            used_data=["Course", "Group"],
        )

    elif use_case_id == "use_case_2":
        plan.add_action(
            action="Wiederholungsaufgaben zu KI-Nutzung und Phishing-Erkennung vorschlagen",
            status="freigabepflichtig",
            reason="Wiederholungsaufgaben auf Basis von Testergebnissen sollten vor Zuweisung fachlich geprüft werden.",
            used_data=["TestResult", "Module", "ContentItem"],
        )

    elif use_case_id == "use_case_3":
        deadline_days = data.get("compliance_requirement", {}).get("deadline_days", 14)
        plan.add_action(
            action=f"Frist von {deadline_days} Tagen für Pflichtschulung vorschlagen",
            status="erlaubt",
            reason="Die Frist wird aus der Pflichtschulungslogik übernommen und als Vorschlag vorbereitet.",
            used_data=["ComplianceRequirement"],
        )
        plan.add_action(
            action="Erinnerungslogik für säumige Teilnehmende vorbereiten",
            status="freigabepflichtig",
            reason="Erinnerungen und Eskalationen können personenbezogene Informationen offenlegen und benötigen Freigabe.",
            used_data=["ComplianceRequirement", "PermissionRule"],
        )


def run_notification_agent(use_case_id: str, data: Dict[str, Any], plan: ActionPlan) -> None:
    plan.add_agent("Notification Agent")

    if use_case_id == "use_case_1":
        plan.add_action(
            action="Benachrichtigung für neue Werkstudentinnen und Werkstudenten vorbereiten",
            status="freigabepflichtig",
            reason="Der Versand von Nachrichten an Lernende soll vorab freigegeben werden.",
            used_data=["User", "Group", "ActionPlan"],
        )
        plan.add_action(
            action="Aggregierte Fortschrittsinformation für Teamleiter vorbereiten",
            status="erlaubt",
            reason="Aggregierte Informationen vermeiden unnötige personenbezogene Offenlegung.",
            used_data=["PermissionRule", "ActionPlan"],
        )

    elif use_case_id == "use_case_2":
        plan.add_action(
            action="Private Lernhinweise für betroffene Lernende vorbereiten",
            status="freigabepflichtig",
            reason="Individuelle Hinweise auf Basis von Testergebnissen sind sensibel und benötigen Freigabe.",
            used_data=["TestResult", "PermissionRule"],
        )

    elif use_case_id == "use_case_3":
        plan.add_action(
            action="Datenschutzfreundliche Erinnerungstexte für säumige Teilnehmende vorbereiten",
            status="freigabepflichtig",
            reason="Erinnerungen zu Pflichtschulungen können personenbezogene Teilnahmeinformationen betreffen.",
            used_data=["User", "ComplianceRequirement", "PermissionRule"],
        )

def run_analytics_agent(use_case_id: str, data: Dict[str, Any], plan: ActionPlan) -> None:
    plan.add_agent("Analytics/Metrics Agent")

    if use_case_id == "use_case_1":
        plan.add_action(
            action="Aggregierte Fortschrittsübersicht vorbereiten",
            status="erlaubt",
            reason="Aggregierte Fortschrittsdaten sind für Teamleiter geeigneter als personenbezogene Detaildaten.",
            used_data=["User", "Group", "PermissionRule"],
        )

    elif use_case_id == "use_case_2":
        results = data.get("test_results", {}).get("overall", {})
        group_results = data.get("test_results", {}).get("by_group", {})

        weak_topics = [topic for topic, score in results.items() if score < 60]

        group_specific_weak_topics = []
        for group_name, topics in group_results.items():
            for topic, score in topics.items():
                if score < 60 and topic not in weak_topics:
                    group_specific_weak_topics.append(f"{topic} bei {group_name} ({score} %)")

        all_findings = weak_topics + group_specific_weak_topics

        if all_findings:
            plan.add_action(
                action=f"Schwache Themenbereiche identifizieren: {', '.join(all_findings)}",
                status="erlaubt",
                reason="Neben allgemeinen Schwellenwerten werden auch gruppenspezifische Auffälligkeiten berücksichtigt.",
                used_data=["TestResult", "Group"],
            )

        if group_results:
            plan.add_action(
                action="Gruppenunterschiede zwischen Personen mit und ohne IT-Vorerfahrung prüfen",
                status="erlaubt",
                reason="Gruppenspezifische Ergebnisse helfen, Schwächen differenzierter zu bewerten.",
                used_data=["TestResult", "Group"],
            )

        plan.add_open_question(
            "Wurden die Testfragen eindeutig formuliert und fachlich validiert?"
        )

    elif use_case_id == "use_case_3":
        plan.add_action(
            action="Aggregierten Bericht für HR und Compliance vorbereiten",
            status="erlaubt",
            reason="Aggregierte Teilnahmequoten erfüllen Nachweisanforderungen ohne unnötige personenbezogene Leistungsdaten.",
            used_data=["User", "ComplianceRequirement", "PermissionRule"],
        )

def run_policy_permission_agent(use_case_id: str, data: Dict[str, Any], plan: ActionPlan) -> None:
    plan.add_agent("Policy/Permission Agent")

    if use_case_id == "use_case_1":
        plan.add_action(
            action="Personenbezogene Fortschrittsdaten an Teamleiter senden",
            status="blockiert",
            reason="Teamleiter dürfen laut Berechtigungsregeln nur aggregierte Fortschrittsinformationen erhalten.",
            used_data=["PermissionRule", "User", "Group"],
        )

    elif use_case_id == "use_case_2":
        plan.add_action(
            action="Personenbezogene Testergebnisse an Teamleiter weitergeben",
            status="blockiert",
            reason="Personenbezogene Leistungsdaten dürfen nicht ohne klare Freigabe an Teamleiter weitergegeben werden.",
            used_data=["TestResult", "PermissionRule"],
            uncertainties=["Berechtigung für personenbezogenes Reporting unklar"],
        )
        plan.add_action(
            action="Gruppenbasierte Auswertung verwenden",
            status="erlaubt",
            reason="Gruppenbasierte Auswertungen reduzieren Datenschutzrisiken und vermeiden Bloßstellung einzelner Lernender.",
            used_data=["TestResult", "Group", "PermissionRule"],
        )

    elif use_case_id == "use_case_3":
        plan.add_action(
            action="Personenbezogene Leistungsdaten an HR oder Teamleiter senden",
            status="blockiert",
            reason="HR und Teamleiter dürfen keine unnötigen personenbezogenen Leistungsdaten erhalten.",
            used_data=["User", "Role", "PermissionRule", "ReportRequest"],
        )
        plan.add_action(
            action="Eskalation an Teamleiter oder HR vorbereiten",
            status="freigabepflichtig",
            reason="Eskalationen können sensible Teilnahmeinformationen offenlegen und benötigen menschliche Freigabe.",
            used_data=["ComplianceRequirement", "PermissionRule"],
        )


if __name__ == "__main__":
    from lms_backend import get_use_case_data

    test_data = get_use_case_data("use_case_1")

    test_plan = ActionPlan(
        use_case_id="use_case_1",
        title=test_data["title"],
        user_request=test_data["user_request"],
    )

    run_content_agent("use_case_1", test_data, test_plan)
    run_course_agent("use_case_1", test_data, test_plan)
    run_enrollment_agent("use_case_1", test_data, test_plan)
    run_assignment_agent("use_case_1", test_data, test_plan)
    run_notification_agent("use_case_1", test_data, test_plan)
    run_analytics_agent("use_case_1", test_data, test_plan)
    run_policy_permission_agent("use_case_1", test_data, test_plan)

    test_plan.print_summary()