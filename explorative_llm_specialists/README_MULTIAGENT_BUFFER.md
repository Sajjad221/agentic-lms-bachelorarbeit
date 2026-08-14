# Experimenteller LLM-Multi-Agent-Puffer v3.2

## Status

Diese Variante ist **eine separate experimentelle Erweiterung** und **nicht Teil des eingefrorenen v4-Holdout-Artefakts**. Die in der Bachelorarbeit berichteten v4-Ergebnisse werden dadurch nicht ersetzt oder nachtraeglich umgedeutet.

## Warum v3.2?

Der reale v2-Lauf zeigte bereits eine deutliche Verbesserung: 19 Rohvorschlaege wurden durch Rollenpruefung und Konsolidierung auf 10 finale Aktionen reduziert. Gleichzeitig wurden zwei typische LLM-Probleme sichtbar:

- eine frei erfundene Fortschrittsangabe von `65 %`, obwohl UC1 keine Fortschrittsdaten enthaelt,
- eine frei gewaehlte Erinnerung nach `7 Tagen`, obwohl nur eine 14-Tage-Frist vorgegeben war.

v3 fuegte deshalb eine explizite Grounding-/Evidence-Schicht hinzu und verbesserte den geteilten Kontext. v3.2 haertet darauf aufbauend die Task-Zuordnung, produktive Governance-Verben sowie optionale Reporting-Parameter.

## Architektur v3.2

```text
Freie Nutzeranfrage
        |
        v
Qwen3-Orchestrator
        |
        v
Deterministische Klassifikations-/Agentenvalidierung
        |
        v
Deterministische Task-Zuordnung pro Fachrolle
        |
        v
LLM-Fachagenten (Qwen3, strikt getrennte Rollen)
        |
        +--> Tool-Planung (nur lesende, erlaubte Tools)
        +--> Tool-Ausfuehrung durch Controller
        +--> verifizierter Tool-Kontext fuer nachgelagerte Agenten
        +--> max. 3 rollenbezogene Aktionsvorschlaege
        |
        v
Deterministische Ownership-Pruefung
        |
        v
Deterministische Grounding-/Evidence-Pruefung
        |
        v
Deterministische Governance-Statusverschaerfung
        |
        v
Deterministische Aktionskonsolidierung / Deduplizierung
        |
        v
Finaler ActionPlan
```

## Grounding-Pruefung

v3.2 versucht bewusst **nicht**, beliebigen Freitext semantisch vollautomatisch als wahr/falsch zu klassifizieren. Stattdessen werden explizite, maschinell nachvollziehbare Fakten geprueft:

- Prozent-/Kennzahlenwerte,
- Fristen und Zeitangaben,
- Kurs-/Modul-/Gruppen-/Nutzer-IDs,
- explizit benannte Kurs-/Modul-/Gruppenentitaeten,
- `used_data`-Quellen.

Die Evidenz darf aus drei Bereichen stammen:

1. Nutzeranfrage / zugewiesene Tasks / Governance-Anforderungen,
2. eigene lesende Tool-Ausgaben des Fachagenten,
3. verifizierte Tool-Ausgaben vorheriger Fachagenten im Shared Context.

Nicht belegte Fakten werden verworfen, bevor Governance und Konsolidierung ausgefuehrt werden.

## Geteilter Kontext

Anders als v2 teilt v3.2 nicht freie LLM-Beobachtungen als vermeintliche Fakten. Stattdessen werden nur echte, bereits durch den Controller ausgefuehrte Tool-Ausgaben weitergegeben. Dadurch koennen nachgelagerte Agenten z. B. eine vorhandene Kurs-ID oder Modulstatus kennen, ohne dieselben Tools erneut aufzurufen.

## Start

```powershell
py run_llm_multiagent_demo.py --use-case use_case_1 --output outputs\multiagent_uc1_v32.json --show-rejections --show-grounding
```

Weitere Szenarien:

```powershell
py run_llm_multiagent_demo.py --use-case use_case_2 --output outputs\multiagent_uc2_v32.json --show-rejections --show-grounding
py run_llm_multiagent_demo.py --use-case use_case_3 --output outputs\multiagent_uc3_v32.json --show-rejections --show-grounding
```

Freie Anfrage:

```powershell
py run_llm_multiagent_demo.py --request "Bereite fuer neue Werkstudierende einen Onboarding-Lernpfad vor und informiere Teamleiter nur aggregiert ueber den Fortschritt." --output outputs\custom_v32.json --show-rejections --show-grounding
```

## Offline-Test

Ohne Ollama:

```powershell
py validate_llm_multiagent_buffer.py
```

Der Test prueft u. a.:

- sieben LLM-Fachrollen,
- Ownership-Rejection,
- Grounding-Rejection eines erfundenen `65 %`-Werts,
- Nutzung einer upstream gelesenen Kurs-ID im Shared Context,
- Governance und finalen ActionPlan.

## Wissenschaftlicher Hinweis

v3.2 ist ein **technischer Puffer / nachgelagerte experimentelle Erweiterung**. Fuer eine Aufnahme als primaeres Ergebnis der Bachelorarbeit waeren eine neue Development-Phase, erneuter Freeze und ein neuer unabhaengiger Holdout notwendig. Die bereits berichteten v4-Metriken duerfen nicht auf v3.2 uebertragen werden.


## v3.1-Finalisierung

Die v3.1-Version normalisiert Provenienzpfade, begrenzt den Assignment Agent strenger auf echte Assignment-/Fristaufgaben und bildet explizite negative Datenschutzanforderungen als direkt `blockiert` bewertete Handlungen ab. Sie ist weiterhin nur ein experimenteller Puffer und nicht Bestandteil des eingefrorenen Thesis-Holdouts.


## v3.2 – finale Puffer-Haertung

V3.2 ergaenzt eine deterministische Task-Alignment-Pruefung fuer den Assignment Agent, verschaerft produktive Governance-Verben und verwirft nicht belegte Reporting-Intervalle bzw. Kommunikationskanaele. Die Version bleibt ein **experimenteller Puffer** und ist nicht Bestandteil der eingefrorenen Thesis-Evaluation.
