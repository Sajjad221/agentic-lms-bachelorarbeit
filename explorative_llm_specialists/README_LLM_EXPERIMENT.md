# Lokales LLM-Experiment – Version 4 (eingefroren)

Diese Version erweitert den agentenbasierten LMS-Prototyp um eine reale, lokal ausgeführte LLM-Eingangsstufe mit `qwen3:14b` über Ollama. Die Auswertung trennt konsequent zwischen der rohen Modellleistung und der Leistung des hybriden Gesamtsystems.

## Methodische Trennung

1. **Rohe LLM-Leistung**
   - Schemaerfolg
   - Use-Case-Klassifikation
   - Aufgabenabdeckung
   - Datenschutzextraktion
   - Agenten-Precision, -Recall und -F1

2. **Deterministisch validierte Agentenauswahl**
   - hinzugefügte Agenten
   - validierte Precision, Recall und F1

3. **Hybrider ActionPlan**
   - Aufgabenabdeckung des Plans
   - Datenschutzabdeckung des Plans
   - Abdeckung der erwarteten Governance-Aktionen und Statuswerte

Die Entwicklungsfälle wurden für Prompt-, Validator- und Rubrikentwicklung verwendet. Die Holdout-Fälle bleiben bis zur finalen Ausführung ungenutzt.

## Technische Konfiguration

- Modell: `qwen3:14b`
- lokale Ollama-API: `http://localhost:11434`
- Thinking: deaktiviert
- JSON-Schema: technisch erzwungen
- Kontextfenster: 4096 Tokens
- Temperatur: 0
- Seeds: 42, 43 und 44 bei drei Wiederholungen
- keine externen Python-Pakete erforderlich

Die Ergebnisdatei speichert zusätzlich Modell-Digest, Ollama-Version, Python-/Plattformdaten sowie SHA-256-Fingerprints von Prompt, Schema, Datensatz, Rubrik und Quellcode.

## 1. Paketprüfung

```powershell
py validate_frozen_package.py
```

## 2. Smoke-Test

```powershell
py run_llm_smoke_test.py
```

## 3. Letzte Development-Verifikation

Diese Ausführung dient nur der technischen Prüfung der eingefrorenen Version. Danach werden Prompt, Validator, Labels und Rubrik nicht mehr verändert.

```powershell
py run_llm_experiment.py --dataset development --repetitions 1 --temperature 0 --output outputs/llm_development_v4_frozen.json
```

## 4. Finaler Holdout-Lauf

Erst nach erfolgreicher Development-Verifikation ausführen:

```powershell
py run_llm_experiment.py --dataset holdout --repetitions 3 --temperature 0 --confirm-frozen-holdout --output outputs/llm_holdout_v4_frozen.json
```

Eine bestehende Ergebnisdatei wird nicht automatisch überschrieben. Dadurch wird ein versehentlicher zweiter Holdout-Lauf vermieden.

## Zentrale Dateien

- `ollama_client.py`: lokale API-Kommunikation und Laufzeitmetriken
- `llm_orchestrator.py`: LLM-Analyse, Klassifikations- und Agentenvalidierung
- `experiment_cases.py`: Development-/Holdout-Anfragen und vorab definierte Sollannotationen
- `run_llm_experiment.py`: reproduzierbare Auswertung aller Ebenen
- `run_llm_smoke_test.py`: einzelner End-to-End-Test
- `validate_frozen_package.py`: statische Integritätsprüfung
- `FROZEN_PROTOCOL.md`: Regeln für die finale Ausführung

## Wissenschaftlicher Hinweis

Die validierten und ActionPlan-basierten Kennzahlen dürfen nicht als Eigenleistung des LLMs dargestellt werden. Sie zeigen den zusätzlichen Beitrag der deterministischen Agenten- und Governance-Schicht. Die Holdout-Ergebnisse sind die primäre Leistungsbewertung; Development-Ergebnisse dokumentieren ausschließlich den Entwicklungsprozess.
