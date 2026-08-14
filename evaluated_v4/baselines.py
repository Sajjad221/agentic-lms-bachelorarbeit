from action_plan import ActionPlan
from lms_backend import get_use_case_data, list_use_cases


def run_single_llm_baseline(use_case_id: str) -> ActionPlan:
    """
    Simuliert einen einzelnen LLM-Agenten.
    Der Ansatz erzeugt direkte Vorschläge, trennt aber Aufgaben,
    Rechteprüfung und Freigaben weniger sauber.
    """
    data = get_use_case_data(use_case_id)

    plan = ActionPlan(
        use_case_id=f"{use_case_id}_single_llm",
        title=f"{data['title']} - Einzelner LLM-Agent",
        user_request=data["user_request"],
    )

    plan.add_agent("Einzelner LLM-Agent")
    plan.add_task("Nutzeranfrage als Gesamtaufgabe interpretieren")
    plan.add_task("Direkten Vorschlag erzeugen")

    if use_case_id == "use_case_1":
        plan.add_action(
            action="Onboarding-Lernpfad mit vorhandenen Modulen vorschlagen",
            status="erlaubt",
            reason="Der LLM-Agent erkennt die grundsätzliche Aufgabe und erstellt einen Lernpfadvorschlag.",
            used_data=["Course", "Module"],
        )
        plan.add_action(
            action="Neue Werkstudentinnen und Werkstudenten als Zielgruppe vorschlagen",
            status="erlaubt",
            reason="Die Zielgruppe wird aus der Anfrage abgeleitet.",
            used_data=["Group"],
        )
        plan.add_action(
            action="Teamleiter über Fortschritt informieren",
            status="freigabepflichtig",
            reason="Die genaue Datentiefe des Reportings wird nicht sauber getrennt.",
            used_data=["Group"],
            uncertainties=["Personenbezogenes oder aggregiertes Reporting nicht eindeutig getrennt"],
        )

    elif use_case_id == "use_case_2":
        plan.add_action(
            action="Zusatzmaterial für schwache Testergebnisse vorschlagen",
            status="erlaubt",
            reason="Der LLM-Agent erkennt allgemein, dass Kursanpassungen sinnvoll sind.",
            used_data=["TestResult"],
        )
        plan.add_action(
            action="Wiederholungsaufgabe für betroffene Lernende vorschlagen",
            status="freigabepflichtig",
            reason="Die Aufgabe basiert auf Leistungsdaten und sollte freigegeben werden.",
            used_data=["TestResult"],
        )
        plan.add_action(
            action="Betroffene Lernende informieren",
            status="freigabepflichtig",
            reason="Individuelle Hinweise können sensible Leistungsdaten betreffen.",
            used_data=["TestResult"],
            uncertainties=["Gruppenbezogene und personenbezogene Daten werden nicht sauber getrennt"],
        )

    elif use_case_id == "use_case_3":
        plan.add_action(
            action="Pflichtschulung für Personen mit Kundendatenzugriff vorbereiten",
            status="freigabepflichtig",
            reason="Der LLM-Agent erkennt die Pflichtschulungslogik, prüft Rollenrechte aber nur allgemein.",
            used_data=["User", "ComplianceRequirement"],
        )
        plan.add_action(
            action="Erinnerungen für säumige Teilnehmende vorschlagen",
            status="freigabepflichtig",
            reason="Erinnerungen können personenbezogene Teilnahmeinformationen enthalten.",
            used_data=["ComplianceRequirement"],
        )
        plan.add_action(
            action="Bericht für HR und Compliance vorbereiten",
            status="freigabepflichtig",
            reason="Die erlaubte Berichtstiefe wird nur allgemein berücksichtigt.",
            used_data=["ReportRequest"],
            uncertainties=["Aggregiertes und personenbezogenes Reporting nicht präzise abgegrenzt"],
        )

    return plan


def run_rule_based_baseline(use_case_id: str) -> ActionPlan:
    """
    Simuliert einen einfachen regelbasierten Ansatz.
    Der Ansatz nutzt feste Wenn-Dann-Regeln und erkennt nur einfache Muster.
    """
    data = get_use_case_data(use_case_id)

    plan = ActionPlan(
        use_case_id=f"{use_case_id}_rule_based",
        title=f"{data['title']} - Regelbasierter Ansatz",
        user_request=data["user_request"],
    )

    plan.add_agent("Regelbasierter Ansatz")
    plan.add_task("Feste Regeln auf simulierte LMS-Daten anwenden")

    if use_case_id == "use_case_1":
        modules = data.get("modules", [])

        for module in modules:
            if module.get("status") == "fehlt":
                plan.add_action(
                    action=f"Fehlendes Modul markieren: {module['title']}",
                    status="erlaubt",
                    reason="Regel: Wenn Modulstatus = fehlt, dann Modul markieren.",
                    used_data=["Module"],
                )

            if module.get("status") == "veraltet":
                plan.add_action(
                    action=f"Veraltetes Modul markieren: {module['title']}",
                    status="erlaubt",
                    reason="Regel: Wenn Modulstatus = veraltet, dann Aktualisierung markieren.",
                    used_data=["Module"],
                )

        plan.add_action(
            action="Frist von 14 Tagen setzen",
            status="erlaubt",
            reason="Regel: Bei Onboarding-Lernpfad Standardfrist 14 Tage verwenden.",
            used_data=["Course"],
        )

    elif use_case_id == "use_case_2":
        results = data.get("test_results", {}).get("overall", {})

        for topic, score in results.items():
            if score < 60:
                plan.add_action(
                    action=f"Zusatzmaterial für Thema '{topic}' empfehlen",
                    status="erlaubt",
                    reason="Regel: Wenn Testergebnis unter 60 Prozent liegt, dann Zusatzmaterial empfehlen.",
                    used_data=["TestResult"],
                )

        plan.add_action(
            action="Gruppenspezifische Nebenprobleme nicht weiter auswerten",
            status="blockiert",
            reason="Der regelbasierte Ansatz prüft nur Gesamtwerte und keine differenzierten Gruppenunterschiede.",
            used_data=["TestResult"],
            uncertainties=["Phishing-Schwäche bei Werkstudenten ohne IT-Vorerfahrung wird durch reine Gesamtwertregel nicht zuverlässig erkannt"],
        )

    elif use_case_id == "use_case_3":
        users = data.get("users", [])
        target_users = [user for user in users if user.get("customer_data_access") is True]

        plan.add_action(
            action=f"Pflichtschulung für {len(target_users)} Personen mit Kundendatenzugriff markieren",
            status="erlaubt",
            reason="Regel: Wenn Kundendatenzugriff = ja, dann Pflichtschulung erforderlich.",
            used_data=["User", "AccessAttribute"],
        )

        plan.add_action(
            action="Frist von 14 Tagen verwenden",
            status="erlaubt",
            reason="Regel: Standardfrist aus ComplianceRequirement übernehmen.",
            used_data=["ComplianceRequirement"],
        )

        plan.add_action(
            action="Differenzierte Reporting- und Eskalationsgrenzen nicht prüfen",
            status="blockiert",
            reason="Der regelbasierte Ansatz berücksichtigt keine komplexen Rollenrechte, Berichtstiefen oder Freigabepflichten.",
            used_data=["PermissionRule"],
            uncertainties=["Datensparsamkeit, HR-Bericht und Eskalationen werden nicht differenziert bewertet"],
        )

    return plan


if __name__ == "__main__":
    for use_case_id in list_use_cases():
        single_llm_plan = run_single_llm_baseline(use_case_id)
        single_llm_plan.print_summary()
        print("\n\n")

        rule_based_plan = run_rule_based_baseline(use_case_id)
        rule_based_plan.print_summary()
        print("\n\n")