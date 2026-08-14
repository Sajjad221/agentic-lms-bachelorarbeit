# v2 Changelog – experimenteller LLM-Multi-Agent-Puffer

Ausgangspunkt war der funktionsfaehige v1-Puffer. Die offizielle eingefrorene v4-Pipeline wurde nicht veraendert.

## Beobachtung aus dem realen v1-UC1-Lauf

Der reale Lauf mit `qwen3:14b` zeigte sieben aktive LLM-Fachagenten, aber auch 34 Roh-Aktionsvorschlaege. Mehrere Vorschlaege waren redundant oder lagen ausserhalb der vorgesehenen Fachrolle. Zudem hatte der Policy-Agent nicht automatisch Zugriff auf Erkenntnisse anderer Agenten.

## Aenderungen in v2

1. Strengere Rollenprompts und explizite Ownership-Vertraege.
2. Maximal drei Aktionsvorschlaege pro Fachagent.
3. Deterministische Task-Zuordnung je Agentenrolle.
4. Deterministische Ownership-Pruefung; klare Rollenueberschreitungen werden verworfen und protokolliert.
5. Operative Agenten laufen vor dem Policy/Permission Agent.
6. Policy/Permission Agent erhaelt einen kompakten, geteilten Kontext aus akzeptierten Vorschlaegen und Beobachtungen der operativen Agenten.
7. Deterministische Konsolidierung fachlich gleicher Aktionen ueber kanonische Aktionsklassen.
8. Bei zusammengefuehrten Vorschlaegen gewinnt immer der strengste Status.
9. Agentenbeobachtungen bleiben in der JSON-Dokumentation, werden aber nicht mehr als scheinbare Tasks in den ActionPlan geschrieben.
10. `compare_buffer_outputs.py` ermoeglicht einen einfachen v1/v2-Vergleich.

## Wissenschaftlicher Status

v2 ist ein nachgelagerter technischer Puffer. Er besitzt keine neue Holdout-Evaluation und darf die in der Bachelorarbeit berichteten v4-Ergebnisse nicht ersetzen.
