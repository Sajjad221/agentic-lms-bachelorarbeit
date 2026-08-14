"""Minimaler Ollama-Client auf Basis der Python-Standardbibliothek.

Der Client verwendet die lokale Ollama-API unter http://localhost:11434.
Es werden keine Daten an einen externen Cloud-Dienst gesendet.
"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict


class OllamaError(RuntimeError):
    """Fehler bei Kommunikation oder Validierung der Ollama-Antwort."""


@dataclass(frozen=True)
class OllamaMetrics:
    total_duration_ms: float
    load_duration_ms: float
    prompt_tokens: int
    output_tokens: int
    prompt_tokens_per_second: float | None
    output_tokens_per_second: float | None


@dataclass(frozen=True)
class OllamaJsonResponse:
    content: Dict[str, Any]
    model: str
    created_at: str
    metrics: OllamaMetrics
    raw_response: Dict[str, Any]


class OllamaClient:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:14b",
        timeout_seconds: int = 300,
        max_retries: int = 0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(0, int(max_retries))

    def _request(self, path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="GET" if payload is None else "POST",
        )
        body = None
        last_exc: BaseException | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    body = response.read().decode("utf-8")
                break
            except (TimeoutError, socket.timeout) as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    print(
                        f"[Ollama] Anfrage-Timeout nach {self.timeout_seconds}s; "
                        f"Wiederholungsversuch {attempt + 1}/{self.max_retries} ...",
                        flush=True,
                    )
                    time.sleep(2.0)
                    continue
                raise OllamaError(
                    f"Ollama hat innerhalb von {self.timeout_seconds}s nicht geantwortet. "
                    "Prüfe 'ollama ps', GPU-Auslastung und server.log; "
                    "danach den Lauf erneut starten."
                ) from exc
            except urllib.error.URLError as exc:
                last_exc = exc
                reason = getattr(exc, "reason", None)
                if isinstance(reason, (TimeoutError, socket.timeout)) and attempt < self.max_retries:
                    print(
                        f"[Ollama] Netzwerk-Timeout; Wiederholungsversuch "
                        f"{attempt + 1}/{self.max_retries} ...",
                        flush=True,
                    )
                    time.sleep(2.0)
                    continue
                raise OllamaError(
                    "Ollama ist nicht erreichbar. Prüfe, ob Ollama läuft und "
                    "http://localhost:11434 verfügbar ist."
                ) from exc

        if body is None:
            raise OllamaError("Ollama-Anfrage blieb ohne Antwort.") from last_exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise OllamaError("Ollama lieferte keine gültige JSON-API-Antwort.") from exc

        if isinstance(parsed, dict) and parsed.get("error"):
            raise OllamaError(str(parsed["error"]))
        if not isinstance(parsed, dict):
            raise OllamaError("Unerwartetes Antwortformat der Ollama-API.")
        return parsed

    def health_check(self) -> Dict[str, Any]:
        """Prüft, ob Ollama erreichbar ist und das konfigurierte Modell vorhanden ist."""
        response = self._request("/api/tags")
        models = response.get("models", [])
        names = {model.get("name") for model in models if isinstance(model, dict)}
        if self.model not in names:
            # Ollama kann Varianten als model:latest melden; daher Präfix prüfen.
            base = self.model.split(":", 1)[0]
            if not any(isinstance(name, str) and name.startswith(base + ":") for name in names):
                raise OllamaError(
                    f"Modell '{self.model}' wurde nicht gefunden. "
                    f"Installiere es mit: ollama pull {self.model}"
                )
        return response

    def version_info(self) -> Dict[str, Any]:
        """Liest die lokale Ollama-Version für das Versuchsprotokoll aus."""
        return self._request("/api/version")

    def configured_model_info(self, tags_response: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Gibt den lokalen Modelleintrag inklusive Digest zurück."""
        response = tags_response or self.health_check()
        models = response.get("models", [])
        exact = [m for m in models if isinstance(m, dict) and m.get("name") == self.model]
        if exact:
            return exact[0]
        base = self.model.split(":", 1)[0]
        candidates = [
            m for m in models
            if isinstance(m, dict) and isinstance(m.get("name"), str)
            and m["name"].startswith(base + ":")
        ]
        return candidates[0] if candidates else {"name": self.model}

    def chat_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: Dict[str, Any],
        seed: int = 42,
        temperature: float = 0.0,
        num_ctx: int = 4096,
        keep_alive: str = "10m",
        num_predict: int = 1024,
        json_retries: int = 1,
    ) -> OllamaJsonResponse:
        """Erzeugt eine nicht-streamende, schema-gebundene JSON-Antwort.

        Falls eine schema-gebundene Antwort wegen eines zu kleinen Output-Budgets
        abgeschnitten/ungueltig ist, wird genau einmal mit groesserem Tokenbudget
        und einer Kompaktheitsanweisung neu angefragt. Das ist nur Robustheitslogik
        fuer den experimentellen Multi-Agent-Puffer.
        """

        def make_payload(prompt: str, predict: int) -> Dict[str, Any]:
            return {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "think": False,
                "format": json_schema,
                "keep_alive": keep_alive,
                "options": {
                    "temperature": temperature,
                    "seed": seed,
                    "num_ctx": num_ctx,
                    "num_predict": predict,
                },
            }

        attempts = max(0, int(json_retries)) + 1
        current_predict = max(64, int(num_predict))
        current_prompt = user_prompt
        last_exc: json.JSONDecodeError | None = None
        response: Dict[str, Any] | None = None
        content: Dict[str, Any] | None = None
        elapsed_ms = 0.0

        for attempt in range(attempts):
            payload = make_payload(current_prompt, current_predict)
            started = time.perf_counter()
            response = self._request("/api/chat", payload)
            elapsed_ms += (time.perf_counter() - started) * 1000

            message = response.get("message")
            if not isinstance(message, dict):
                raise OllamaError("Ollama-Antwort enthält kein gültiges message-Objekt.")
            content_text = message.get("content")
            if not isinstance(content_text, str):
                raise OllamaError("Ollama-Antwort enthält keinen Textinhalt.")

            try:
                parsed_content = json.loads(content_text)
            except json.JSONDecodeError as exc:
                last_exc = exc
                done_reason = str(response.get("done_reason", ""))
                eval_count = int(response.get("eval_count", 0) or 0)
                likely_truncated = (
                    done_reason == "length"
                    or eval_count >= max(1, current_predict - 2)
                    or content_text.count("{") > content_text.count("}")
                    or content_text.count("[") > content_text.count("]")
                )
                if attempt + 1 < attempts:
                    next_predict = min(max(current_predict * 2, 1024), 2048)
                    why = "wahrscheinlich abgeschnitten" if likely_truncated else "ungueltiges JSON"
                    print(
                        f"[Ollama] Strukturierte Antwort {why} "
                        f"(done_reason={done_reason or 'n/a'}, eval_count={eval_count}, "
                        f"num_predict={current_predict}). JSON-Retry mit num_predict={next_predict} ...",
                        flush=True,
                    )
                    current_predict = next_predict
                    current_prompt = (
                        user_prompt
                        + "\n\nWICHTIG FUER DEN RETRY: Gib das verlangte JSON jetzt vollstaendig "
                          "und sehr kompakt aus. Kurze Beobachtungen und Begruendungen, keine "
                          "Wiederholungen, keine Zusatztexte ausserhalb des JSON-Objekts."
                    )
                    continue
                detail = (
                    f" done_reason={done_reason or 'n/a'}, eval_count={eval_count}, "
                    f"num_predict={current_predict}."
                )
                raise OllamaError(
                    "Das Modell lieferte trotz Schema kein gültiges JSON." + detail
                ) from exc

            if not isinstance(parsed_content, dict):
                raise OllamaError("Die strukturierte Modellantwort muss ein JSON-Objekt sein.")
            content = parsed_content
            break

        if response is None or content is None:
            raise OllamaError("Keine verwertbare strukturierte Ollama-Antwort erhalten.") from last_exc

        total_ns = int(response.get("total_duration", 0) or 0)
        load_ns = int(response.get("load_duration", 0) or 0)
        prompt_count = int(response.get("prompt_eval_count", 0) or 0)
        output_count = int(response.get("eval_count", 0) or 0)
        prompt_ns = int(response.get("prompt_eval_duration", 0) or 0)
        output_ns = int(response.get("eval_duration", 0) or 0)

        prompt_tps = (
            prompt_count / (prompt_ns / 1_000_000_000)
            if prompt_count and prompt_ns
            else None
        )
        output_tps = (
            output_count / (output_ns / 1_000_000_000)
            if output_count and output_ns
            else None
        )

        metrics = OllamaMetrics(
            total_duration_ms=total_ns / 1_000_000 if total_ns else elapsed_ms,
            load_duration_ms=load_ns / 1_000_000,
            prompt_tokens=prompt_count,
            output_tokens=output_count,
            prompt_tokens_per_second=prompt_tps,
            output_tokens_per_second=output_tps,
        )
        return OllamaJsonResponse(
            content=content,
            model=str(response.get("model", self.model)),
            created_at=str(response.get("created_at", "")),
            metrics=metrics,
            raw_response=response,
        )
