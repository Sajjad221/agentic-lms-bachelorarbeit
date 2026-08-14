# v3.2.3 JSON-Fix

Diese Version behebt den im realen v3.2.2-Lauf beobachteten Fehler
`JSONDecodeError: Unterminated string` bei der Aktionsplanung.

Ursache: Das harte Output-Budget von 768 Tokens konnte eine an sich schema-gebundene
Antwort abschneiden, bevor das JSON-Objekt geschlossen war.

Aenderungen gegenueber v3.2.2:
- Aktionsplanung: `num_predict` 768 -> 1536.
- Kompaktere JSON-Schemata mit `maxLength`/`maxItems` fuer Freitextfelder.
- Prompt verlangt kurze Beobachtungen/Begruendungen ohne Wiederholungen.
- `OllamaClient.chat_json()` erkennt unvollstaendiges JSON und fuehrt genau einen
  JSON-Retry mit groesserem Tokenbudget (max. 2048) und Kompaktheitsanweisung aus.
- Netzwerk-Timeout-Logik bleibt unveraendert.

Nicht veraendert: Ownership, Grounding, Konsolidierung, Governance und das eingefrorene
v4-Thesis-Artefakt.

Test:
`--use-case use_case_1 --output outputs\\multiagent_uc1_v323.json --show-rejections --show-grounding`
