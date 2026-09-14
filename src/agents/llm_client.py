"""Interface mínima entre os agentes e qualquer provedor de LLM."""

import asyncio
import hashlib
import json
import os
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Mapping
from urllib import error, request
from urllib.parse import urlsplit

from pydantic import BaseModel


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
class LLMCallMetadata:
    """Metadado técnico de *quem* está chamando, passado explicitamente.

    Existe para que a proveniência de uma chamada (papel no grafo e, no
    ensemble, qual analista) seja declarada pelo nó que chama, e não deduzida
    depois lendo o texto do prompt ou a ordem das chamadas. Não entra no
    prompt: observabilidade não contamina a entrada do modelo.
    """

    stage: str
    analyst_id: int | None = None


@dataclass
class LLMCallTelemetry:
    """Rascunho mutável de *uma única* invocação lógica de ``generate``.

    Substitui o antigo ``LLMClient._retries_context``, que era atributo de
    instância do cliente concreto e, portanto, compartilhado entre as chamadas
    concorrentes do ensemble: um analista podia publicar o número de tentativas
    de outro. Aqui o rascunho vive em ``ContextVar``, que ``asyncio`` copia por
    task — cada analista enxerga e escreve apenas o seu.
    """

    attempts: int = 1
    usage: dict[str, Any] | None = None
    raw_response: str | None = None
    #: System prompt **efetivamente** colocado no corpo HTTP, quando o cliente
    #: concreto transforma o prompt lógico antes de enviar. ``None`` quando não
    #: há transformação ou o cliente não a reporta.
    transport_system_prompt: str | None = None


_CALL_TELEMETRY: ContextVar[LLMCallTelemetry | None] = ContextVar(
    "llm_call_telemetry", default=None
)


def current_call_telemetry() -> LLMCallTelemetry | None:
    """Rascunho da invocação corrente, ou ``None`` fora de uma gravação."""
    return _CALL_TELEMETRY.get()


@contextmanager
def call_telemetry_slot() -> Iterator[LLMCallTelemetry]:
    """Abre um rascunho novo, isolado nesta task, e o fecha ao final."""
    slot = LLMCallTelemetry()
    token = _CALL_TELEMETRY.set(slot)
    try:
        yield slot
    finally:
        _CALL_TELEMETRY.reset(token)


@dataclass(frozen=True)
class LLMCall:
    system_prompt: str
    user_prompt: str
    response_schema: type[BaseModel] | None
    options: dict[str, Any]
    metadata: LLMCallMetadata | None = field(default=None)


class LLMClient(ABC):
    def __init__(self) -> None:
        self.telemetry_logs: list[LLMTelemetry] = []

    @property
    def all_telemetry(self) -> list[LLMTelemetry]:
        logs = list(self.telemetry_logs)
        if hasattr(self, "client") and isinstance(self.client, LLMClient):
            logs.extend(self.client.all_telemetry)
        return logs

    # ── Descrição do provedor, propagada pelos wrappers ──────────
    #
    # As três funções abaixo existem para que a camada de gravação possa
    # registrar o que *de fato* acontece no transporte sem conhecer o cliente
    # concreto. A implementação da base delega para o cliente embrulhado; só o
    # cliente que fala com o provedor sabe responder de verdade.

    def _inner(self) -> "LLMClient | None":
        inner = getattr(self, "client", None)
        return inner if isinstance(inner, LLMClient) else None

    def transport_options(
        self, options: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        """Subconjunto de ``options`` que este cliente realmente transmite.

        Separar isto de ``options`` solicitadas é o que impede confundir
        "opção registrada no pipeline" com "opção entregue ao provedor" —
        distinção que hoje importa para ``seed``.
        """
        inner = self._inner()
        return inner.transport_options(options) if inner is not None else {}

    def provider_endpoint(self) -> str | None:
        """Identidade não sensível do endpoint, sem credencial alguma."""
        inner = self._inner()
        return inner.provider_endpoint() if inner is not None else None

    def begin_session(self, session: Any) -> None:
        """Declara a sessão de decisão corrente e propaga para baixo.

        A sessão é constante durante toda a decisão de ``close(t)``, inclusive
        para as chamadas concorrentes do ensemble, por isso é atributo simples
        e não precisa de isolamento por task.
        """
        inner = self._inner()
        if inner is not None:
            inner.begin_session(session)

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
        options: dict[str, Any] | None = None,
        *,
        metadata: LLMCallMetadata | None = None,
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
        *,
        metadata: LLMCallMetadata | None = None,
    ) -> BaseModel | str:
        self.calls.append(
            LLMCall(
                system_prompt, user_prompt, response_schema, options or {}, metadata
            )
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
        *,
        metadata: LLMCallMetadata | None = None,
    ) -> BaseModel | str:
        # O contador de tentativas é o rascunho desta invocação, isolado por
        # task: duas chamadas concorrentes do ensemble não se sobrescrevem.
        slot = current_call_telemetry()
        for attempt in range(self.max_attempts - 1):
            if slot is not None:
                slot.attempts = attempt + 1
            try:
                return await self.client.generate(
                    system_prompt, user_prompt, response_schema, options,
                    metadata=metadata,
                )
            except self.retry_exceptions:
                await asyncio.sleep(self.base_delay * (2**attempt))

        if slot is not None:
            slot.attempts = self.max_attempts
        return await self.client.generate(
            system_prompt, user_prompt, response_schema, options, metadata=metadata
        )


class AgentRouterLLMClient(LLMClient):
    """Cliente compatível com a API OpenAI-style do Agent Router/OpenRouter.

    Proveniência declarada, e não presumida: ``TRANSMITTED_OPTION_KEYS`` é a
    lista **única** das opções que chegam ao corpo HTTP. Tudo o que o pipeline
    passa em ``options`` e não está nessa lista — hoje ``seed`` e
    ``analyst_id`` — é opção *solicitada*, nunca opção aplicada pelo modelo.
    """

    #: Fonte única da verdade sobre o que é transmitido; o payload e
    #: ``transport_options`` leem daqui para não poderem divergir.
    TRANSMITTED_OPTION_KEYS: tuple[str, ...] = ("temperature", "top_p", "max_tokens")

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

    def transport_options(
        self, options: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        if not options:
            return {}
        return {
            key: options[key]
            for key in self.TRANSMITTED_OPTION_KEYS
            if options.get(key) is not None
        }

    def provider_endpoint(self) -> str | None:
        """Esquema, host, porta e caminho — sem userinfo, query ou fragmento.

        ``base_url`` é configurável por ambiente, então o mesmo
        ``provider="agent_router"`` pode apontar para endpoints diferentes.
        Registrar esta identidade fecha a lacuna sem levar credencial junto.
        """
        parsed = urlsplit(self._endpoint_url())
        host = parsed.hostname or ""
        if not host:
            return None
        if parsed.port:
            host = f"{host}:{parsed.port}"
        return f"{parsed.scheme}://{host}{parsed.path}"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
        options: dict[str, Any] | None = None,
        *,
        metadata: LLMCallMetadata | None = None,
    ) -> BaseModel | str:
        if not self.api_key:
            raise ConnectionError("LLM_API_KEY não configurada")

        # O prompt lógico é transformado aqui: o JSON Schema do
        # ``response_schema`` entra no system prompt. É por isso que o trace não
        # pode tratar o prompt lógico como "texto exato enviado ao provedor", e
        # por isso que o digest do schema faz parte da identidade da chamada.
        sys_prompt = system_prompt
        if response_schema:
            schema_json = json.dumps(response_schema.model_json_schema(), ensure_ascii=False)
            sys_prompt += f"\n\nResponda estritamente em JSON válido seguindo a estrutura:\n{schema_json}"

        slot = current_call_telemetry()
        if slot is not None:
            # Reportado antes de qualquer I/O: mesmo uma chamada que falha no
            # transporte deixa registrado o que ela ia enviar.
            slot.transport_system_prompt = sys_prompt

        payload: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        # Mesma fonte que ``transport_options``: o que é registrado como
        # transmitido é literalmente o que vai no corpo.
        payload.update(self.transport_options(options))

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

        attempts = slot.attempts if slot is not None else 1
        self.telemetry_logs.append(
            LLMTelemetry(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
                retries=attempts - 1,
                model=self.model,
            )
        )
        if slot is not None and isinstance(body.get("usage"), dict):
            # Só o que o provedor devolveu de fato. Ausência vira ``null`` no
            # trace: zero apresentado como medição seria estimativa disfarçada.
            slot.usage = {
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
                "source": "provider",
            }

        message_content = body["choices"][0]["message"]["content"]
        if isinstance(message_content, list):
            message_content = "".join(str(item) for item in message_content)
        if slot is not None:
            # Gravado antes do parse: uma resposta que falha na validação
            # deixa mesmo assim o texto bruto como evidência.
            slot.raw_response = (
                message_content
                if isinstance(message_content, str)
                else str(message_content)
            )
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
    """Cache JSON persistente por prompt e schema, sem dependência externa.

    **Fora do caminho científico, deliberadamente.** Cache é otimização;
    evidência experimental é o trace de :mod:`src.agents.llm_trace`. O
    ``LLMParticipant`` não monta este cliente e o ``ExperimentRunner`` não o
    introduz — reprodução de um run se faz por replay explícito.

    Duas limitações ficam registradas em vez de corrigidas aqui, porque
    corrigi-las mudaria chaves de caches já gravados sem necessidade para a
    stack científica: a chave não inclui ``provider``/``model`` (trocar de
    modelo reaproveita a resposta anterior) e o arquivo é reescrito inteiro a
    cada gravação.
    """

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
        *,
        metadata: LLMCallMetadata | None = None,
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
            system_prompt, user_prompt, response_schema, options, metadata=metadata
        )
        self._cache[key] = (
            response.model_dump(mode="json")
            if isinstance(response, BaseModel)
            else response
        )
        self._save()
        return response
