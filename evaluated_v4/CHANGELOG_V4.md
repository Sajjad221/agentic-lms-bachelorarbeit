# Änderungen gegenüber Version 3

Die Prüfung des Development-Laufs zeigte, dass die technische Modellleistung stabil war, die damalige Bewertungslogik jedoch mehrere methodische Verzerrungen enthielt.

## Behoben

- Sollagenten werden nicht mehr pauschal je Use Case, sondern aus den tatsächlich erwarteten Aufgaben der einzelnen Anfrage abgeleitet.
- Datenschutzkategorien sind pro Anfrage annotiert; nicht genannte Anforderungen werden nicht mehr automatisch als Fehler gewertet.
- Governance-Kontrollen sind pro Anfrage definiert und berücksichtigen nur tatsächlich geforderte Aktionen.
- Kurze Begriffe wie `HR` werden mit Wortgrenzen geprüft und erzeugen keine Treffer innerhalb anderer Wörter.
- Weitere sprachliche Varianten wie `zusammengefasster`, `Unterschiede zwischen`, `Vorkenntnisse` und `Änderungen vorschlagen` werden korrekt erkannt.
- Rohe LLM-Abdeckung und ActionPlan-Abdeckung werden getrennt ausgewiesen.
- Der tatsächlich erzeugte ActionPlan wird in jedem Ergebnisdatensatz gespeichert.
- Die Governance-Aktionsabdeckung prüft sowohl den Inhalt als auch den Status `erlaubt`, `freigabepflichtig` oder `blockiert`.
- Modell-Digest, Ollama-Version, Plattformdaten und SHA-256-Fingerprints werden protokolliert.
- Der Holdout-Lauf ist durch einen expliziten Bestätigungsparameter und Überschreibschutz abgesichert.

## Unverändert

- Die 15 Holdout-Anfragen wurden nicht anhand ihrer Ergebnisse optimiert oder ausgeführt.
- Das Modell bleibt `qwen3:14b`.
- Thinking bleibt deaktiviert.
- Temperatur und Kontextfenster bleiben bei `0` beziehungsweise `4096`.
