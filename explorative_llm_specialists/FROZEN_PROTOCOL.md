# Eingefrorenes Versuchsprotokoll

**Version:** v4-frozen-2026-08-04

Vor dem finalen Holdout-Lauf sind folgende Bestandteile eingefroren:

- System-Prompt
- JSON-Schema
- Use-Case-Klassifikationslogik
- Agenten-Trigger und Validator
- Holdout-Anfragen
- Sollannotationen pro Anfrage
- Aufgaben- und Datenschutzrubrik
- Governance-Kontrollen
- Modellname `qwen3:14b`
- Temperatur `0`
- Kontextfenster `4096`
- Wiederholungsseeds `42`, `43`, `44`

## Ausführungsregel

1. `validate_frozen_package.py` ausführen.
2. Development-Verifikation mit einer Wiederholung ausführen.
3. Nach erfolgreicher technischer Prüfung keine inhaltliche Änderung mehr vornehmen.
4. Holdout genau einmal mit drei Wiederholungen ausführen.
5. Original-JSON unverändert archivieren.
6. Modell-Digest, Ollama-Version und alle ausgegebenen SHA-256-Werte in der Dokumentation festhalten.

## Auswertungsregel

- Rohe Modellwerte werden separat berichtet.
- Validator- und ActionPlan-Werte werden als Leistung des hybriden Systems bezeichnet.
- Development-Werte sind keine finale Leistungsbewertung.
- Fehlversuche, Schemafehler und Validator-Eingriffe werden nicht entfernt oder nachträglich korrigiert.
