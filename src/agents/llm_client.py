"""Interface mínima entre os agentes e qualquer provedor de LLM."""

import asyncio
import hashlib
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

from pydantic import BaseModel
import time

@dataclass
class LLMTelemetry:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    retries: int = 0
    model: str = ""


@dataclass(frozen=True)
class LLMCall:
    system_prompt: str
    user_prompt: str
    response_schema: type[BaseModel] | None
    options: dict[str, Any]


class LLMClient(ABC):
    def __init__(self) -> None:
        self.telemetry_logs: list[LLMTelemetry] = []
        self._retries_context: int = 0

    @property
    def all_telemetry(self) -> list[LLMTelemetry]:
        logs = list(self.telemetry_logs)
        if hasattr(self, "client") and isinstance(self.client, LLMClient):
            logs.extend(self.client.all_telemetry)
        return logs

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
        options: dict[str, Any] | None = None,
    ) -> BaseModel | str:
        """Gera uma resposta, opcionalmente validada por um schema."""


class MockLLMClient(LLMClient):
    """Cliente determinístico para testes, sem rede ou chave de API."""

    def __init__(self, responses: dict[type[BaseModel] | None, Any] | None = None):
        super().__init__()
        self.responses = responses or {}
        self.calls: list[LLMCall] = []
        self._response_positions: dict[type[BaseModel] | None, int] = {}

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
        options: dict[str, Any] | None = None,
    ) -> BaseModel | str:
        self.calls.append(
            LLMCall(system_prompt, user_prompt, response_schema, options or {})
        )
        response = self.responses.get(response_schema, "MANTER")
        if isinstance(response, list):
            if not response:
                response = "MANTER"
            else:
                position = self._response_positions.get(response_schema, 0)
                response = response[position % len(response)]
                self._response_positions[response_schema] = position + 1
        if response_schema is None or isinstance(response, response_schema):
            return response
        if isinstance(response, str):
            return response_schema.model_validate_json(response)
        return response_schema.model_validate(response)


class RetryingLLMClient(LLMClient):
    """Repete falhas transitórias de qualquer cliente concreto."""

    def __init__(
        self,
        client: LLMClient,
        max_attempts: int = 3,
        base_delay: float = 0.5,
        retry_exceptions: tuple[type[Exception], ...] = (
            TimeoutError,
            ConnectionError,
            OSError,
        ),
    ):
        if max_attempts < 1 or base_delay < 0 or not retry_exceptions:
            raise ValueError("invalid retry configuration")
        super().__init__()
        self.client = client
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.retry_exceptions = retry_exceptions

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
        options: dict[str, Any] | None = None,
    ) -> BaseModel | str:
        for attempt in range(self.max_attempts - 1):
            try:
                self.client._retries_context = attempt
                return await self.client.generate(
                    system_prompt, user_prompt, response_schema, options
                )
            except self.retry_exceptions:
                await asyncio.sleep(self.base_delay * (2**attempt))
        
        self.client._retries_context = self.max_attempts - 1
        return await self.client.generate(
            system_prompt, user_prompt, response_schema, options
        )


class AgentRouterLLMClient(LLMClient):
    """Cliente compatível com a API OpenAI-style do Agent Router/OpenRouter."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        transport: Any | None = None,
        timeout: float = 30.0,
        extra_headers: dict[str, str] | None = None,
    ):
        super().__init__()
        from src.config import settings

        self.api_key = api_key if api_key is not None else (settings.llm_api_key or os.getenv("LLM_API_KEY") or "")
        configured_url = settings.llm_base_url or os.getenv("LLM_BASE_URL") or "https://openrouter.ai/api/v1"
        self.base_url = (base_url or configured_url).rstrip("/")
        configured_model = settings.llm_model or os.getenv("LLM_MODEL") or "openai/gpt-4o-mini"
        self.model = model or configured_model
        self.timeout = timeout if timeout != 30.0 else settings.llm_timeout
        self.extra_headers = extra_headers or {}
        self.transport = transport or self._default_transport

    def _default_transport(self, method: str, url: str, headers: dict[str, str], body: dict[str, Any]):
        payload = json.dumps(body).encode("utf-8")
        req = request.Request(url, data=payload, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                return response.read()
        except error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            raise ConnectionError(f"HTTP {exc.code}: {exc.reason} - {err_body}") from exc
        except error.URLError as exc:
            raise ConnectionError(str(exc.reason)) from exc

    def _endpoint_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
        options: dict[str, Any] | None = None,
    ) -> BaseModel | str:
        if not self.api_key:
            raise ConnectionError("LLM_API_KEY não configurada")

        sys_prompt = system_prompt
        if response_schema:
            schema_json = json.dumps(response_schema.model_json_schema(), ensure_ascii=False)
            sys_prompt += f"\n\nResponda estritamente em JSON válido seguindo a estrutura:\n{schema_json}"

        payload: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        if options:
            for key in ("temperature", "top_p", "max_tokens"):
                if key in options and options[key] is not None:
                    payload[key] = options[key]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        headers.update(self.extra_headers)

        start_time = time.time()
        raw = await asyncio.to_thread(self.transport, "POST", self._endpoint_url(), headers, payload)
        latency_ms = (time.time() - start_time) * 1000.0

        if hasattr(raw, "read"):
            raw = raw.read()
        if isinstance(raw, bytearray):
            raw = bytes(raw)
        if isinstance(raw, str):
            body = json.loads(raw)
        else:
            body = json.loads(raw.decode("utf-8"))

        usage = body.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
        cost_usd = 0.0 # TODO: implement dynamic pricing if needed

        self.telemetry_logs.append(
            LLMTelemetry(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
                retries=self._retries_context,
                model=self.model,
            )
        )
        self._retries_context = 0

        message_content = body["choices"][0]["message"]["content"]
        if isinstance(message_content, list):
            message_content = "".join(str(item) for item in message_content)
        if response_schema is None:
            return message_content if isinstance(message_content, str) else str(message_content)

        if isinstance(message_content, str):
            content = message_content.strip()
            if content.startswith("```"):
                lines = [line for line in content.splitlines() if not line.strip().startswith("```")]
                content = "\n".join(lines).strip()
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as exc:
                raise ValueError(f"resposta não é JSON válido: {message_content!r}") from exc
            return response_schema.model_validate(parsed)
        return response_schema.model_validate(message_content)


class CachedLLMClient(LLMClient):
    """Cache JSON persistente por prompt e schema, sem dependência externa."""

    def __init__(self, client: LLMClient, cache_path: str | Path):
        super().__init__()
        self.client = client
        self.cache_path = Path(cache_path)
        self._cache = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.cache_path.exists():
            return {}
        try:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _key(
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None,
        options: dict[str, Any] | None,
    ) -> str:
        schema_name = response_schema.__qualname__ if response_schema else "str"
        content = json.dumps(
            [system_prompt, user_prompt, schema_name, options or {}],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def _save(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.cache_path.with_suffix(self.cache_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self._cache, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(self.cache_path)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
        options: dict[str, Any] | None = None,
    ) -> BaseModel | str:
        key = self._key(system_prompt, user_prompt, response_schema, options)
        if key in self._cache:
            cached = self._cache[key]
            
            # Log cache hit as 0 cost, 0 latency
            self.telemetry_logs.append(
                LLMTelemetry(
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    cost_usd=0.0,
                    latency_ms=0.0,
                    retries=0,
                    model="cached",
                )
            )

            return response_schema.model_validate(cached) if response_schema else cached

        response = await self.client.generate(
            system_prompt, user_prompt, response_schema, options
        )
        self._cache[key] = (
            response.model_dump(mode="json")
            if isinstance(response, BaseModel)
            else response
        )
        self._save()
        return response
