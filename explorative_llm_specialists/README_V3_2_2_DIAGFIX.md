# v3.2.2 Diagnose-/Generationslimit-Fix

Experimenteller Puffer, nicht Teil des eingefrorenen Thesis-v4-Holdouts.

Änderungen gegenüber v3.2.1:
- `num_predict` ist nun explizit begrenzt: Tool-Auswahl 160 Tokens, Fachaktionsausgabe 768 Tokens, Standard 1024.
- HTTP-Timeout 300 s, kein automatischer Retry.
- Konsolen-Stage-Logging vor/nach Tool-Auswahl und Aktionsplanung je Fachagent.
- `diagnose_ollama.py` prüft API, Modell und einen kleinen Qwen3-Chat.

Motivation: In v3.2.1 war `num_predict` nicht gesetzt. Ollama verwendet dann modell-/serverseitig den Default; die Ollama-Modelfile-Dokumentation nennt `-1` als unbegrenzte Generierung. Ein pathologischer strukturierter Lauf kann dadurch bis zum Client-Timeout laufen.

Vor dem Volltest:
`py diagnose_ollama.py`

Dann:
`py run_llm_multiagent_demo.py --use-case use_case_1 --output outputs\\multiagent_uc1_v322.json --show-rejections --show-grounding`
