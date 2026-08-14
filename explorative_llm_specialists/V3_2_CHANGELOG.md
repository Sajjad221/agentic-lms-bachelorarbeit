# v3.2 – letzte Haertung des experimentellen LLM-Multi-Agent-Puffers

Diese Version bleibt **vollstaendig getrennt vom eingefrorenen v4-Thesis-Holdout**.

## Aenderungen gegenueber v3.1

1. **Assignment-Task-Alignment:** Ein Fristauftrag legitimiert nur Fristaktionen. Generische Aufgaben oder Wiederholungsaufgaben werden deterministisch verworfen, wenn sie nicht explizit in den zugewiesenen Teilaufgaben vorkommen.
2. **Governance-Verben erweitert:** produktive Operationen wie `setzen`, `aktivieren`, `einrichten`, `zuordnen`, `aendern` und `konfigurieren` werden mindestens `freigabepflichtig`.
3. **Grounding fuer optionale Reporting-Parameter:** frei erfundene Frequenzen/Kanaele (z. B. `woechentlich`, `E-Mail`, `Dashboard`) werden verworfen, sofern sie nicht in Anfrage, Tasks oder verifizierten Tooldaten vorkommen.
4. **Analytics-Prompt geschaerft:** fehlende Intervalle/Kanaele sind als Rueckfrage zu behandeln, nicht als Aktion.
5. **Course-Ownership geschaerft:** Zielgruppen-/Zuordnungsaktionen gehoeren nicht zum Course Agent.

## Ziel

Redundanz und Halluzinationen weiter reduzieren, ohne die deterministische Governance-Schicht aufzuweichen.
