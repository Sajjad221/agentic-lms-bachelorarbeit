# Human Evaluation – reproduzierbare Auswertungsdaten

Dieser Ordner enthält die bereinigten, anonymisierten Daten zur Personenbewertung der Bachelorarbeit sowie ein Reproduktionsskript für die in Kapitel 7 berichteten Kennzahlen.

## Dateien

- `anonymized_ratings.csv`: Long-Format der 0–2-Bewertungen für alle 15 Rückläufe; P01 ist als aus der Hauptanalyse ausgeschlossen markiert.
- `participant_metadata.csv`: minimale Metadaten zur Ein-/Ausschlusslogik, Bearbeitungsdauer und Kontrollfrage zur Verständlichkeit.
- `questionnaire_structure.md`: Kriterien, Skala, Varianten-Zuordnung und Auswertungslogik.
- `analysis.py`: reproduziert Datenqualitätskennzahlen, Tabelle 24, Tabelle 25, Friedman-Test, Kendall W, Wilcoxon-Tests, Holm-Korrektur, rang-biseriale Korrelation und Sensitivitätsanalyse.
- `requirements.txt`: Python-Abhängigkeit für die inferenzstatistischen Tests.
- `statistical_results.txt`: Referenzausgabe des Skripts.
- `SHA256SUMS.txt`: Prüfsummen der Dateien in diesem Ordner.

## Ausführung

```bash
cd human_evaluation
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python analysis.py
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python3 analysis.py
```

## Methodischer Hinweis

Es liegen 15 anonymisierte Rückläufe vor. P01 war als einzige Person an Entwicklung/Erstbewertung des Systems beteiligt und wird deshalb aus der unabhängigen Hauptanalyse ausgeschlossen. Die Hauptanalyse umfasst damit 14 unabhängige Personen. P01 bleibt im veröffentlichten Datensatz ausschließlich zur transparenten Dokumentation der Ausschlussentscheidung enthalten.

Fehlende Einzelratings werden nicht imputiert. Tabelle 24 aggregiert alle gültigen Einzelratings; Tabelle 25 verdichtet zunächst pro Person und Ansatz über die drei Szenarien, sodass jede Person im Gesamtwert dasselbe Gewicht erhält.

Die Veröffentlichung dient der quantitativen Nachvollziehbarkeit. Wörtliche Freitextantworten, absolute Zeitstempel und nicht für die Reproduktion erforderliche identifizierende Metadaten sind bewusst nicht enthalten.
