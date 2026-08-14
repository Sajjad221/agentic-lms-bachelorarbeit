# Retrospektiver v3-Grounding-Check auf dem realen v2-UC1-Lauf

Die neue v3-Grounding-Logik wurde offline auf die gespeicherte reale v2-Ausgabe `multiagent_uc1_v2.json` angewendet. Dabei wurden die damaligen Tool-Auswahlen erneut gegen das unveraenderte simulierte Backend als Evidenz herangezogen.

Ergebnis:

- 19 Roh-Aktionsvorschlaege im realen v2-Lauf
- 17 bestanden die neue explizite Grounding-Pruefung
- 2 wurden als nicht ausreichend belegt verworfen

Verworfene Fakten:

1. `Erinnerung an Werkstudenten nach 7 Tagen ...`
   - Grund: Die Zahl `7 Tage` war weder in der Nutzeranfrage noch in gelesenen Tool-Daten vorgegeben. Belegt war nur die 14-Tage-Frist.

2. `... 65% der Teilnehmenden haben den Lernpfad abgeschlossen.`
   - Grund: Im UC1-Backend existiert kein Fortschrittswert `65 %` und auch kein entsprechender anderer Fortschrittswert.

Der Check zeigt bewusst nur die deterministisch pruefbaren expliziten Fakten. Er ist keine vollstaendige automatische Wahrheitspruefung beliebiger LLM-Aussagen.
