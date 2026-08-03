"""Interface mínima entre os agentes e qualquer provedor de LLM."""

import asyncio
import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True)
class LLMCall:
    system_prompt: str
    user_prompt: str
    response_schema: type[BaseModel] | None
    options: dict[str, Any]


class LLMClient(ABC):
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
                return await self.client.generate(
                    system_prompt, user_prompt, response_schema, options
                )
            except self.retry_exceptions:
                await asyncio.sleep(self.base_delay * (2**attempt))
        return await self.client.generate(
            system_prompt, user_prompt, response_schema, options
        )


class CachedLLMClient(LLMClient):
    """Cache JSON persistente por prompt e schema, sem dependência externa."""

    def __init__(self, client: LLMClient, cache_path: str | Path):
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
