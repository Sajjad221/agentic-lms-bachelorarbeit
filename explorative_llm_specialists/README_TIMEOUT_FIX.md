# v3.2.1 Timeout-Fix

Diese Variante ändert **nur die Robustheit der lokalen Ollama-Kommunikation**.
Die Multi-Agent-, Ownership-, Grounding-, Konsolidierungs- und Governance-Logik aus v3.2 bleibt unverändert.

Änderungen in `ollama_client.py`:
- Request-Timeout von 180 s auf 600 s erhöht.
- Ein automatischer Retry bei `TimeoutError`/`socket.timeout`.
- Klarere Fehlermeldung mit Hinweis auf `ollama ps` und Ollama `server.log`.

Der Retry ist für die hier verwendeten reinen LLM-Analyseaufrufe unkritisch, weil der API-Aufruf selbst keine LMS-Schreiboperation ausführt.

Empfohlener Test:
```powershell
py run_llm_multiagent_demo.py --use-case use_case_1 --output outputs\multiagent_uc1_v321.json --show-rejections --show-grounding
```

Vorher optional:
```powershell
ollama run qwen3:14b ""
ollama ps
```
