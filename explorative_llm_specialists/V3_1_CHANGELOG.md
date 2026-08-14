# v3.1 Finalisierung des experimentellen LLM-Multi-Agent-Puffers

Diese Version bleibt **separat** vom eingefrorenen v4-Holdout-Artefakt der Bachelorarbeit.

## Gegenueber v3 geaendert

1. **Provenienz-Normalisierung**
   - `verified_tool_outputs.read_modules`, `shared_context.verified_tool_outputs.read_modules` und `tool:read_modules` werden kanonisch als `read_modules` behandelt.
   - Dadurch werden belegte Upstream-Tooldaten nicht mehr wegen eines reinen Namensformats verworfen.

2. **Assignment Agent enger gefasst**
   - 0 Aktionen sind ausdruecklich korrekt, wenn keine eigene Frist-/Aufgaben-/Wiederholungsanforderung vorliegt.
   - Fehlender oder veralteter Content allein darf keine Wiederholungsaufgabe ausloesen.

3. **Negative Governance-Regeln als direkte blockierte Aktionen**
   - Eine Schutzanforderung wie „Keine individuellen Daten an Teamleiter“ wird im finalen ActionPlan als Handlung „Individuelle Fortschrittsdaten an Teamleiter uebermitteln“ mit Status `blockiert` abgebildet.
   - Das vermeidet missverstaendliche Eintraege wie „Keine individuellen Daten ... = erlaubt“.

4. **Keine Aenderung am offiziellen Thesis-Holdout**
   - Die v4-Freeze-/Holdout-Dateien und deren Ergebnisse bleiben unberuehrt.
