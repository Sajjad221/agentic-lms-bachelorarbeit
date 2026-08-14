# Agentenbasierter LMS-Prototyp – Bachelorarbeit

Repository: <https://github.com/Sajjad221/agentic-lms-bachelorarbeit>

Dieses Repository enthält den Python-Prototyp und die Reproduktionsartefakte zur Bachelorarbeit von **Mohammad Rezai** im Studiengang Wirtschaftsinformatik (HTW Berlin, Fachbereich 4):

> **Wie kann ein agentenbasiertes System für ein Learning Management System gestaltet werden, das komplexe Nutzeranfragen durch die Koordination mehrerer spezialisierter KI-Agenten verarbeitet?**

## Wichtig: zwei technisch getrennte Stände

Das Repository trennt bewusst zwischen dem **formal evaluierten Artefakt** und einer **nachgelagerten explorativen Erweiterung**.

- `evaluated_v4/`: eingefrorener, quantitativ evaluierter v4-Prototyp. Dieser Stand ist maßgeblich für die in der Bachelorarbeit berichteten Holdout-Kennzahlen.
- `evaluation_artifacts/`: unveränderte Development- und Holdout-Ergebnisdateien des v4-Experiments.
- `explorative_llm_specialists/`: erst nach dem v4-Freeze entwickelte Variante mit LLM-basierten Fachagenten. Sie ist **nicht Teil der formalen quantitativen Evaluation**.
- `explorative_artifacts/`: Ergebnis- und Konsolenartefakte des explorativen Demonstrationslaufs.

Die sieben spezialisierten Fachrollen des evaluierten v4-Prototyps sind deterministische Python-Komponenten. Qwen3 übernimmt dort die natürlichsprachliche Interpretation und initiale Orchestrierung. Die explorative Erweiterung verwendet zusätzliche Qwen3-Aufrufe für die Fachrollen und bleibt methodisch getrennt.

## Architektur des evaluierten v4-Prototyps

```text
Freie natürlichsprachliche LMS-Anfrage
        |
        v
Qwen3:14b über lokale Ollama-API
        |
        v
Strukturierte Analyse (JSON-Schema)
        |
        v
Deterministische Klassifikations- und Agentenvalidierung
        |
        v
7 spezialisierte Fachrollen
        |
        v
Deterministische Governance
        |
        v
ActionPlan: erlaubt / freigabepflichtig / blockiert
```

Fachrollen: Course Agent, Content Agent, Enrollment Agent, Assignment Agent, Notification Agent, Analytics/Metrics Agent und Policy/Permission Agent. Die Verarbeitung wird durch einen Orchestrator koordiniert. Das LMS-Backend ist simuliert; es werden keine produktiven LMS-Aktionen ausgeführt.

## Voraussetzungen

Für die **exakte Reproduktion des formalen v4-Experiments**:

- Python 3.10 oder neuer (der archivierte Holdout-Lauf wurde mit Python 3.14.6 durchgeführt)
- Ollama lokal gestartet
- Modell `qwen3:14b`
- ausreichend Arbeitsspeicher für das lokale 14B-Modell
- keine zusätzlichen Python-Pakete erforderlich

Archivierte Laufzeitumgebung des finalen Holdouts:

- Modell: `qwen3:14b`
- Modell-Digest: `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`
- Quantisierung: `Q4_K_M`
- Modellgröße: ca. 9,3 GB
- Ollama: `0.32.5`
- Python: `3.14.6`
- Plattform: Windows 11
- Kontextfenster im Experiment: `4096`
- Thinking: `false`
- Temperatur: `0`
- Holdout: 15 Prompts × 3 Wiederholungen = 45 Läufe

## 1. Repository klonen

```bash
git clone https://github.com/Sajjad221/agentic-lms-bachelorarbeit.git
cd agentic-lms-bachelorarbeit
```

Alternativ kann das Repository als ZIP heruntergeladen und entpackt werden.

## 2. Ollama installieren und Modell laden

Ollama installieren und starten. Anschließend:

```bash
ollama pull qwen3:14b
```

Prüfen:

```bash
ollama list
```

Die lokale API wird standardmäßig unter `http://localhost:11434` angesprochen.

## 3. Optional: Python-Umgebung anlegen

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Es gibt keine externen Python-Abhängigkeiten; `evaluated_v4/requirements.txt` dokumentiert dies.

## 4. Evaluierten v4-Stand prüfen

```bash
cd evaluated_v4
python3 validate_frozen_package.py
```

Unter Windows kann statt `python3` auch `py` verwendet werden:

```powershell
py validate_frozen_package.py
```

Die Prüfung kontrolliert unter anderem Development-/Holdout-Datensatz und Hashwerte des eingefrorenen Pakets.

## 5. End-to-End-Smoke-Test starten

Ollama muss laufen und `qwen3:14b` muss lokal vorhanden sein.

### macOS / Linux

```bash
python3 run_llm_smoke_test.py
```

### Windows

```powershell
py run_llm_smoke_test.py
```

Der Smoke-Test verarbeitet eine Beispielanfrage vollständig von der LLM-Analyse über die deterministische Validierung bis zum ActionPlan.

## 6. Development-Lauf ausführen

```bash
python3 run_llm_experiment.py \
  --dataset development \
  --repetitions 1 \
  --temperature 0 \
  --output outputs/llm_development_reproduction.json
```

Windows PowerShell:

```powershell
py run_llm_experiment.py --dataset development --repetitions 1 --temperature 0 --output outputs/llm_development_reproduction.json
```

## 7. Formalen Holdout reproduzieren

**Hinweis:** Die in der Bachelorarbeit berichtete Ergebnisdatei wird im Repository unverändert unter `evaluation_artifacts/llm_holdout_v4_frozen_final.json` archiviert. Eine erneute Ausführung ist eine Reproduktion und ersetzt nicht den historischen Originallauf.

```bash
python3 run_llm_experiment.py \
  --dataset holdout \
  --repetitions 3 \
  --temperature 0 \
  --confirm-frozen-holdout \
  --output outputs/llm_holdout_reproduction.json
```

## 8. Explorative LLM-Fachagenten-Erweiterung

Diese Variante wurde **nach Abschluss des eingefrorenen v4-Holdouts** entwickelt. Sie darf nicht als Quelle der v4-Kennzahlen interpretiert werden.

```bash
cd ../explorative_llm_specialists
python3 validate_llm_multiagent_buffer.py
```

Der Offline-Test benötigt kein Ollama. Für einen realen Demonstrationslauf mit lokalem Qwen3:

```bash
python3 run_llm_multiagent_demo.py \
  --use-case use_case_1 \
  --output outputs/multiagent_uc1_demo.json \
  --show-rejections \
  --show-grounding
```

## Demo auf hardwarebeschränkten Geräten

Die formale Evaluation verwendet ausschließlich `qwen3:14b`. Auf Geräten mit zu wenig Arbeitsspeicher kann für eine **reine Funktionsdemonstration** eine kleinere Qwen3-Variante verwendet werden. Solche Läufe sind **keine Reproduktion der in der Bachelorarbeit berichteten Evaluation** und müssen entsprechend gekennzeichnet werden.

Beispiel für einen Development-Demolauf:

```bash
cd evaluated_v4
python3 run_llm_experiment.py \
  --dataset development \
  --repetitions 1 \
  --temperature 0 \
  --model qwen3:4b \
  --output outputs/demo_qwen3_4b.json
```

## Zentrale Dateien

### `evaluated_v4/`

- `ollama_client.py`: lokale Kommunikation mit der Ollama-API
- `llm_orchestrator.py`: LLM-Analyse sowie Klassifikations- und Agentenvalidierung
- `agents.py`: sieben deterministische Fachrollen
- `lms_backend.py`: simuliertes LMS-Backend
- `action_plan.py`: ActionPlan und Governance-Status
- `experiment_cases.py`: Development- und Holdout-Fälle mit Sollannotationen
- `run_llm_experiment.py`: reproduzierbare technische Evaluation
- `run_llm_smoke_test.py`: einzelner End-to-End-Test
- `validate_frozen_package.py`: Integritätsprüfung
- `FROZEN_PROTOCOL.md`: eingefrorenes Versuchsprotokoll

### Ergebnisartefakte

- `evaluation_artifacts/llm_development_v4_frozen.json`
- `evaluation_artifacts/llm_holdout_v4_frozen_final.json`
- `explorative_artifacts/multiagent_uc1_v323.json`
- `explorative_artifacts/console_uc1_v323.txt`

## Methodischer Hinweis

Die rohen LLM-Metriken werden von den Kennzahlen des hybriden Gesamtsystems getrennt. Insbesondere dürfen validierte Agentenwerte und ActionPlan-Kennzahlen nicht als alleinige Leistung des LLM interpretiert werden. Der finale Holdout umfasst 45 Läufe aus 15 unabhängigen Anfrageformulierungen mit jeweils drei Wiederholungen; die 45 Läufe sind daher nicht 45 unabhängige Testprompts.

## Datenschutz und Ausführung

Der Prototyp verwendet ein simuliertes LMS-Backend und keine realen produktiven LMS-Zugänge. Die Ollama-Anbindung erfolgt lokal über `localhost`. Der Code enthält keine API-Schlüssel für externe LLM-Dienste.

## Wissenschaftlicher Kontext

Dieses Repository dient der Nachvollziehbarkeit und Reproduzierbarkeit des im Rahmen der Bachelorarbeit entwickelten Designartefakts. Für Interpretation, Forschungsdesign, Evaluation und Limitationen ist die schriftliche Bachelorarbeit maßgeblich.
