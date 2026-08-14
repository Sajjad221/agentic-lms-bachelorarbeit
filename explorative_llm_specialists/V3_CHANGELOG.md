# v3 Changelog – experimenteller LLM-Multi-Agent-Puffer

Ausgangspunkt war der reale v2-UC1-Lauf. Die offizielle eingefrorene v4-Pipeline wurde nicht veraendert.

## Beobachtung aus dem realen v2-Lauf

v2 reduzierte 19 Rohvorschlaege durch Ownership und Konsolidierung auf 10 finale Aktionen. Dabei blieb jedoch ein wichtiger Restfehler sichtbar: Der Notification Agent erzeugte eine konkrete Fortschrittsangabe von `65 %`, obwohl fuer UC1 keine entsprechenden Fortschrittsdaten im Backend vorliegen. Zudem erfand er eine Erinnerung nach `7 Tagen`, obwohl nur eine 14-Tage-Frist vorgegeben war.

## Aenderungen in v3

1. Neue deterministische Grounding-/Evidence-Schicht (`grounding_validation.py`).
2. Geprueft werden explizite Prozent-/Kennzahlen, Fristen/Zeitangaben, LMS-IDs, benannte LMS-Entitaeten und `used_data`-Provenienz.
3. Eine Aktion passiert die Pipeline nur, wenn sowohl Ownership als auch Grounding bestanden werden.
4. Grounding- und Ownership-Entscheidungen werden getrennt in JSON protokolliert.
5. Alle nachgelagerten Fachagenten erhalten verifizierte Tool-Ausgaben bereits ausgefuehrter Agenten als gemeinsamen Kontext; freie LLM-Beobachtungen werden nicht als Fakten geteilt.
6. Dadurch kann z. B. der Enrollment Agent eine zuvor gelesene Kurs-ID verwenden, ohne selbst das Course-Tool zu besitzen.
7. Der CLI-Runner zeigt Grounding-Rejections separat an (`--show-grounding` oder `--show-rejections`).
8. Der Offline-Test enthaelt absichtlich einen erfundenen `65 %`-Wert und prueft, dass dieser verworfen wird.

## Retrospektiver Check des realen v2-UC1-Laufs

Die v3-Grounding-Logik wurde offline gegen die gespeicherte reale v2-Ausgabe geprueft. Von 19 Rohvorschlaegen wurden genau zwei wegen nicht belegter expliziter Fakten markiert:

- Erinnerung nach `7 Tagen` – die Zahl 7 war nicht durch Anfrage oder Tool-Daten belegt.
- Fortschrittsmeldung `65 %` – fuer UC1 existiert kein entsprechender Fortschrittswert.

Damit adressiert v3 genau den im realen Lauf beobachteten Halluzinations-/Grounding-Fall.

## Wissenschaftlicher Status

v3 ist weiterhin ein nachgelagerter technischer Puffer. Er besitzt keine neue Holdout-Evaluation und darf die in der Bachelorarbeit berichteten v4-Ergebnisse nicht ersetzen.
