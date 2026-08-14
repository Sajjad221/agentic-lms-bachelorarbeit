# Retrospektiver Check des realen v3.1-UC1-Laufs mit v3.2-Regeln

Basis: `multiagent_uc1_v31.json` aus dem realen lokalen Qwen3:14b-Lauf. Dieser Check ist **keine neue Thesis-Evaluation**, sondern prueft nur, ob die in v3.2 eingebauten Regeln genau die im v3.1-Lauf beobachteten Restprobleme adressieren.

## V3.2 wuerde zusaetzlich verwerfen

- Analytics/Metrics Agent: Reporting-Intervall `woechentlich` plus `E-Mail`/`Dashboard` – nicht durch Anfrage oder Tooldaten belegt.
- Course Agent: Zielgruppe G1 dem Lernpfad zuordnen – Rollenverletzung; Zielgruppen-/Zuordnungsaktionen gehoeren zum Enrollment Agent.
- Assignment Agent: `Wiederholungsaufgabe planen` – keine Wiederholungsaufgabe in den zugewiesenen UC1-Teilaufgaben.
- Assignment Agent: `Aufgabe planen` – generische Assignment-Aktion ohne passende zugewiesene Teilaufgabe.
- Notification Agent: Erinnerung nach `7 Tagen` – bereits durch Grounding als unbelegte Zeitangabe verworfen.

## V3.2 wuerde den Status verschaerfen

- `Frist setzen` -> mindestens `freigabepflichtig`.
- `... aktivieren` -> mindestens `freigabepflichtig`.
- `... zuordnen/einrichten/setzen/aktualisieren` -> bei produktiver LMS-Wirkung mindestens `freigabepflichtig`.

## Ergebnis

Die neuen Regeln adressieren die im realen v3.1-Lauf sichtbaren drei Restklassen: generische Assignment-Aktionen, nicht belegte optionale Reporting-Parameter und zu schwache Statusklassifikation produktiver Verben.
