"""Evidência por chamada de LLM: gravação ao vivo e replay determinístico.

Uma execução com provedor externo **não é reprodutível por configuração**.
Mesma ``ExperimentSpec``, mesmo snapshot, mesmo ``model`` e mesma
``temperature`` podem devolver textos diferentes, e ``seed`` sequer é
transmitido pelo cliente HTTP atual. A garantia forte que este módulo
estabelece é outra, e em dois tempos::

    run ao vivo  --> trace (o que foi perguntado e o que voltou)
    trace        --> replay determinístico, sem rede, mesmas decisões

``RecordingLLMClient`` é a fronteira que o grafo enxerga; ``ReplayLLMClient``
ocupa o lugar do provedor e devolve exatamente as respostas registradas,
recusando-se a responder se a chamada corrente não for a chamada registrada.
"""

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd
from pydantic import BaseModel

from src.agents.llm_client import (
    LLMCallMetadata,
    LLMCallTelemetry,
    LLMClient,
    call_telemetry_slot,
)
from src.artifacts import RunArtifact, canonical_json

#: Contrato do arquivo de trace. Não tem relação com
#: ``RUN_MANIFEST_SCHEMA_VERSION`` nem com ``SPEC_SCHEMA_VERSION``: são três
#: contratos independentes, versionados separadamente.
#:
#: Versão 2: a identidade da chamada passa a incluir
#: ``response_schema_sha256``. Sem ele, dois schemas de mesmo nome e estrutura
#: diferente produziam requisições HTTP diferentes e identidades iguais — o
#: replay aceitava em silêncio. Traces versão 1 não são relidos por isso.
LLM_TRACE_SCHEMA_VERSION = 2

#: Nome lógico e nome de arquivo do artefato publicado junto do run.
LLM_TRACE_ARTIFACT = "llm_calls"
LLM_TRACE_FILENAME = "llm_calls.jsonl"

STAGE_TECHNICAL_ANALYST = "technical_analyst"
STAGE_RISK_MANAGER = "risk_manager"
STAGE_PORTFOLIO_MANAGER = "portfolio_manager"
#: Chamada que chegou sem metadado declarado; nunca é inferida a partir do
#: texto do prompt, apenas marcada como não declarada.
STAGE_UNDECLARED = "undeclared"

STATUS_OK = "ok"
STATUS_ERROR = "error"

#: Exceções que o replay sabe reconstruir com o tipo original. O tipo importa:
#: ``RetryingLLMClient`` decide o que repetir por tipo e os nós do grafo
#: capturam ``TypeError``/``ValueError``. Fora desta lista o replay levanta
#: ``RuntimeError``, que não é repetível e não é engolido como decisão.
_REPLAYABLE_ERRORS: Mapping[str, type[BaseException]] = MappingProxyType(
    {
        "ConnectionError": ConnectionError,
        "OSError": OSError,
        "TimeoutError": TimeoutError,
        "TypeError": TypeError,
        "ValueError": ValueError,
    }
)


class LLMTraceError(RuntimeError):
    """A gravação não pode descrever a chamada corrente."""


class ReplayMismatchError(RuntimeError):
    """A execução corrente divergiu do trace gravado.

    Levantada em vez de devolver "a próxima resposta assim mesmo": um replay
    que aceita divergência não reproduz execução nenhuma, apenas produz
    números com aparência de reprodução.
    """


def sha256_text(text: str) -> str:
    """SHA-256 do texto exato, em UTF-8, sem normalizar espaço em branco.

    Dois prompts que diferem em espaço em branco **efetivamente enviado** são
    prompts diferentes e precisam ter hashes diferentes.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def session_key(session: Any) -> str:
    """Chave textual estável da sessão de decisão (``close(t)``)."""
    stamp = pd.Timestamp(session)
    if pd.isna(stamp):
        raise LLMTraceError("decision session cannot be NaT")
    return str(stamp.date())


def schema_name(response_schema: type[BaseModel] | None) -> str | None:
    return response_schema.__qualname__ if response_schema is not None else None


def schema_digest(response_schema: type[BaseModel] | None) -> str | None:
    """SHA-256 do JSON Schema do modelo, em forma canônica.

    O nome da classe não identifica o contrato: mudar um campo, um default ou
    um limite de ``Field`` mantém ``__qualname__`` e muda o schema. E o schema
    **vai junto na requisição** — o ``AgentRouterLLMClient`` serializa
    ``model_json_schema()`` dentro do system prompt de transporte. Sem este
    digest, duas execuções que perguntaram coisas diferentes ao provedor teriam
    a mesma identidade.
    """
    if response_schema is None:
        return None
    return sha256_text(canonical_json(response_schema.model_json_schema()))


def _jsonable_options(options: Mapping[str, Any] | None) -> dict[str, Any]:
    """Opções em forma canônica; valor não serializável vira texto explícito."""
    canonical: dict[str, Any] = {}
    for key, value in dict(options or {}).items():
        if value is None or isinstance(value, (str, int, float, bool)):
            canonical[str(key)] = value
        else:
            canonical[str(key)] = repr(value)
    return canonical


@dataclass(frozen=True)
class LLMCallRequest:
    """Identidade canônica de **uma chamada lógica** ao provedor.

    "Lógica" é a distinção importante: uma chamada aqui pode ter custado três
    tentativas HTTP. Só entram campos materiais à inferência — papel, sessão,
    provedor, modelo, prompts, schema e opções solicitadas. Relógio e duração
    ficam de fora de propósito (ver :meth:`identity`).
    """

    stage: str
    analyst_id: int | None
    decision_session: str
    provider: str
    requested_model: str
    system_prompt: str
    user_prompt: str
    response_schema: str | None
    response_schema_sha256: str | None
    requested_options: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "requested_options", MappingProxyType(dict(self.requested_options))
        )

    @property
    def system_prompt_sha256(self) -> str:
        return sha256_text(self.system_prompt)

    @property
    def user_prompt_sha256(self) -> str:
        return sha256_text(self.user_prompt)

    @property
    def combined_prompt_sha256(self) -> str:
        """Hash do par, não da concatenação.

        Mover texto de um prompt para o outro não pode produzir o mesmo
        digest.
        """
        return sha256_text(canonical_json([self.system_prompt, self.user_prompt]))

    def identity(self) -> dict[str, Any]:
        """Campos que **definem** a chamada, para casar request e replay.

        Os prompts aqui são os **lógicos** — o que a stack de agentes pediu. O
        adaptador ainda os transforma antes do transporte (ver
        :meth:`LLMCallRecord.to_json_dict`), e por isso o digest do schema
        entra na identidade: ele é a outra metade da requisição efetivamente
        enviada. Prompt lógico + schema determinam o prompt de transporte.

        Timestamp, duração e uso de tokens não estão aqui: são medições da
        execução, não da pergunta. Um replay não pode falhar porque o relógio
        andou. ``transport_options`` também fica fora — é consequência do
        cliente concreto, que no replay não existe.
        """
        return {
            "stage": self.stage,
            "analyst_id": self.analyst_id,
            "decision_session": self.decision_session,
            "provider": self.provider,
            "requested_model": self.requested_model,
            "response_schema": self.response_schema,
            "response_schema_sha256": self.response_schema_sha256,
            "requested_options": dict(self.requested_options),
            "system_prompt_sha256": self.system_prompt_sha256,
            "user_prompt_sha256": self.user_prompt_sha256,
        }

    @property
    def identity_digest(self) -> str:
        return sha256_text(canonical_json(self.identity()))


@dataclass(frozen=True)
class LLMCallRecord:
    """Uma chamada lógica inteira: o que foi perguntado e o que aconteceu."""

    call_id: str
    sequence: int
    request: LLMCallRequest
    started_at: str
    duration_ms: float
    attempt_count: int
    status: str
    validated_response: Any = None
    error_type: str | None = None
    error_message: str | None = None
    token_usage: Mapping[str, Any] | None = None
    raw_response: str | None = None
    provider_endpoint: str | None = None
    transport_options: Mapping[str, Any] = MappingProxyType({})
    #: Hash do system prompt que o cliente concreto realmente colocou no corpo
    #: HTTP, quando ele reporta isso. ``None`` para provedores que não
    #: transformam nada (mock) ou que não expõem o texto final.
    transport_system_prompt_sha256: str | None = None

    @property
    def retry_count(self) -> int:
        return max(0, self.attempt_count - 1)

    def to_json_dict(self) -> dict[str, Any]:
        """Forma publicada de um registro.

        **Prompt lógico e prompt de transporte são coisas diferentes.**
        ``system_prompt``/``user_prompt`` são o que a stack de agentes pediu.
        O ``AgentRouterLLMClient`` ainda acrescenta ao system prompt o
        ``model_json_schema()`` serializado do ``response_schema`` antes de
        montar o corpo HTTP, de modo que o texto publicado aqui **não é**, para
        esse provedor, literalmente o texto enviado.

        O que é publicado determina o que foi enviado: o prompt lógico está
        aqui na íntegra, a estrutura do schema está em
        ``response_schema_sha256``, e o molde que junta os dois é código, coberto
        pelo ``git_commit`` do run. ``transport_system_prompt_sha256`` fecha a
        volta quando o cliente concreto reporta o texto final.

        O prompt inteiro é gravado, e não só o hash, porque o trace precisa
        permitir reconstruir a chamada e nenhum prompt do projeto carrega
        segredo. Cabeçalho HTTP e credencial jamais entram aqui —
        ``LLMCallRequest`` não tem campo para eles.
        """
        request = self.request
        return {
            "schema_version": LLM_TRACE_SCHEMA_VERSION,
            "call_id": self.call_id,
            "sequence": self.sequence,
            "decision_session": request.decision_session,
            "stage": request.stage,
            "analyst_id": request.analyst_id,
            "provider": request.provider,
            "requested_model": request.requested_model,
            "provider_endpoint": self.provider_endpoint,
            "system_prompt": request.system_prompt,
            "user_prompt": request.user_prompt,
            "system_prompt_sha256": request.system_prompt_sha256,
            "user_prompt_sha256": request.user_prompt_sha256,
            "combined_prompt_sha256": request.combined_prompt_sha256,
            "response_schema": request.response_schema,
            "response_schema_sha256": request.response_schema_sha256,
            "requested_options": dict(request.requested_options),
            "transport_options": dict(self.transport_options),
            "transport_system_prompt_sha256": self.transport_system_prompt_sha256,
            "identity_digest": request.identity_digest,
            "started_at": self.started_at,
            "duration_ms": self.duration_ms,
            "attempt_count": self.attempt_count,
            "retry_count": self.retry_count,
            "status": self.status,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "validated_response": self.validated_response,
            "raw_response": self.raw_response,
            "token_usage": dict(self.token_usage) if self.token_usage else None,
        }

    @classmethod
    def from_json_dict(cls, payload: Mapping[str, Any]) -> "LLMCallRecord":
        version = payload.get("schema_version")
        if version != LLM_TRACE_SCHEMA_VERSION:
            raise ReplayMismatchError(
                f"llm trace schema_version {version!r} is not supported; "
                f"this build reads version {LLM_TRACE_SCHEMA_VERSION}"
            )
        request = LLMCallRequest(
            stage=payload["stage"],
            analyst_id=payload["analyst_id"],
            decision_session=payload["decision_session"],
            provider=payload["provider"],
            requested_model=payload["requested_model"],
            system_prompt=payload["system_prompt"],
            user_prompt=payload["user_prompt"],
            response_schema=payload["response_schema"],
            response_schema_sha256=payload["response_schema_sha256"],
            requested_options=payload["requested_options"],
        )
        return cls(
            call_id=payload["call_id"],
            sequence=payload["sequence"],
            request=request,
            started_at=payload["started_at"],
            duration_ms=payload["duration_ms"],
            attempt_count=payload["attempt_count"],
            status=payload["status"],
            validated_response=payload.get("validated_response"),
            error_type=payload.get("error_type"),
            error_message=payload.get("error_message"),
            token_usage=payload.get("token_usage"),
            raw_response=payload.get("raw_response"),
            provider_endpoint=payload.get("provider_endpoint"),
            transport_options=payload.get("transport_options") or {},
            transport_system_prompt_sha256=payload.get("transport_system_prompt_sha256"),
        )


def dump_trace(records: Iterable[LLMCallRecord]) -> bytes:
    """Serializa o trace em JSONL UTF-8, uma linha por chamada lógica.

    Chaves ordenadas e fim de linha LF: o arquivo é determinístico,
    inspecionável linha a linha e concatenável.
    """
    lines = [canonical_json(record.to_json_dict()) for record in records]
    text = "\n".join(lines) + "\n" if lines else ""
    return text.encode("utf-8")


def load_trace(source: str | bytes | Path) -> tuple[LLMCallRecord, ...]:
    """Lê um trace de texto, bytes ou caminho de arquivo."""
    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8")
    elif isinstance(source, bytes):
        text = source.decode("utf-8")
    else:
        text = source
    return tuple(
        LLMCallRecord.from_json_dict(json.loads(line))
        for line in text.splitlines()
        if line.strip()
    )


def trace_artifact(records: Sequence[LLMCallRecord]) -> RunArtifact:
    """Congela o trace como evidência publicável do run."""
    return RunArtifact(
        name=LLM_TRACE_ARTIFACT,
        filename=LLM_TRACE_FILENAME,
        schema_version=LLM_TRACE_SCHEMA_VERSION,
        content=dump_trace(records),
        summary={
            "call_count": len(records),
            "error_count": sum(1 for record in records if record.status == STATUS_ERROR),
        },
    )


def _validated_payload(response: BaseModel | str) -> Any:
    """``model_dump(mode="json")`` para Pydantic, literal para texto.

    Nunca ``repr(objeto)``: o trace precisa ser relido e revalidado, não lido
    por um humano adivinhando o formato.
    """
    if isinstance(response, BaseModel):
        return response.model_dump(mode="json")
    return response


class RecordingLLMClient(LLMClient):
    """Grava toda interação com o provedor sem alterar a semântica do retorno.

    Fica **acima** do resto da pilha::

        grafo -> Recording -> FailureRecording -> retry -> provedor

    A ordem é material. Acima do retry, cada registro descreve uma chamada
    lógica e sabe quantas tentativas ela custou (``attempt_count``), em vez de
    produzir um registro por tentativa. Acima do ``FailureRecordingClient``, a
    falha final é gravada antes de subir para o participante — e uma tentativa
    que o retry recuperou continua não sendo falha, apenas ``attempt_count``
    maior que um.
    """

    def __init__(
        self,
        client: LLMClient,
        *,
        provider: str,
        requested_model: str,
    ) -> None:
        super().__init__()
        self.client = client
        self.provider = provider
        self.requested_model = requested_model
        self._records: dict[int, LLMCallRecord] = {}
        self._sequence = 0
        self._decision_session: str | None = None

    def begin_session(self, session: Any) -> None:
        """Abre o contexto de decisão de ``close(t)``.

        Chamado pelo participante, que conhece ``observation.session``. A
        sessão nunca é deduzida da ordem das chamadas ao final do run.
        """
        self._decision_session = session_key(session)
        super().begin_session(session)

    @property
    def decision_session(self) -> str | None:
        return self._decision_session

    @property
    def records(self) -> tuple[LLMCallRecord, ...]:
        """Registros em ordem de ``sequence``.

        A ordem de *conclusão* das chamadas do ensemble depende do
        escalonador; a ordem de *emissão* não. Publicar por ``sequence`` torna
        o arquivo determinístico e é a mesma ordem que o replay consome.
        """
        return tuple(self._records[key] for key in sorted(self._records))

    def artifact(self) -> RunArtifact:
        return trace_artifact(self.records)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
        options: dict[str, Any] | None = None,
        *,
        metadata: LLMCallMetadata | None = None,
    ) -> BaseModel | str:
        if self._decision_session is None:
            raise LLMTraceError(
                "no decision session is open; call begin_session(session) "
                "before invoking the agent graph"
            )
        sequence = self._sequence
        self._sequence += 1
        declared = metadata or LLMCallMetadata(stage=STAGE_UNDECLARED)
        request = LLMCallRequest(
            stage=declared.stage,
            analyst_id=declared.analyst_id,
            decision_session=self._decision_session,
            provider=self.provider,
            requested_model=self.requested_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=schema_name(response_schema),
            response_schema_sha256=schema_digest(response_schema),
            requested_options=_jsonable_options(options),
        )
        call_id = "|".join(
            (
                request.decision_session,
                request.stage,
                "-" if declared.analyst_id is None else str(declared.analyst_id),
                f"{sequence:06d}",
            )
        )
        started_at = datetime.now(timezone.utc)
        # Duração por relógio monotônico; ``started_at`` é UTC e serve só para
        # auditoria. Nenhum dos dois entra na identidade da chamada.
        started = time.perf_counter()
        with call_telemetry_slot() as slot:
            try:
                response = await self.client.generate(
                    system_prompt,
                    user_prompt,
                    response_schema,
                    options,
                    metadata=metadata,
                )
            except BaseException as exc:
                self._records[sequence] = LLMCallRecord(
                    call_id=call_id,
                    sequence=sequence,
                    request=request,
                    started_at=_isoformat(started_at),
                    duration_ms=(time.perf_counter() - started) * 1000.0,
                    attempt_count=slot.attempts,
                    status=STATUS_ERROR,
                    error_type=type(exc).__name__,
                    # Só a mensagem: stack trace completo é instável entre
                    # execuções e não acrescenta evidência sobre a inferência.
                    error_message=str(exc),
                    token_usage=slot.usage,
                    raw_response=slot.raw_response,
                    provider_endpoint=self.client.provider_endpoint(),
                    transport_options=self.client.transport_options(options),
                    transport_system_prompt_sha256=_transport_prompt_digest(slot),
                )
                raise
            self._records[sequence] = LLMCallRecord(
                call_id=call_id,
                sequence=sequence,
                request=request,
                started_at=_isoformat(started_at),
                duration_ms=(time.perf_counter() - started) * 1000.0,
                attempt_count=slot.attempts,
                status=STATUS_OK,
                validated_response=_validated_payload(response),
                token_usage=slot.usage,
                raw_response=slot.raw_response,
                provider_endpoint=self.client.provider_endpoint(),
                transport_options=self.client.transport_options(options),
                transport_system_prompt_sha256=_transport_prompt_digest(slot),
            )
        return response


class ReplayLLMClient(LLMClient):
    """Responde a partir de um trace gravado, sem rede e sem provedor.

    ``provider`` e ``requested_model`` são declarados pelo chamador e **não**
    lidos do trace: é justamente a comparação entre a configuração corrente e
    a registrada que detecta um replay feito com outro modelo.
    """

    def __init__(
        self,
        records: Sequence[LLMCallRecord],
        *,
        provider: str,
        requested_model: str,
    ) -> None:
        super().__init__()
        self.records = tuple(records)
        self.provider = provider
        self.requested_model = requested_model
        self._cursor = 0
        self._decision_session: str | None = None

    @classmethod
    def from_trace(
        cls,
        source: str | bytes | Path,
        *,
        provider: str,
        requested_model: str,
    ) -> "ReplayLLMClient":
        return cls(load_trace(source), provider=provider, requested_model=requested_model)

    def begin_session(self, session: Any) -> None:
        self._decision_session = session_key(session)
        super().begin_session(session)

    @property
    def consumed(self) -> int:
        return self._cursor

    @property
    def pending(self) -> tuple[LLMCallRecord, ...]:
        return self.records[self._cursor :]

    def assert_complete(self) -> None:
        """Exige que o trace tenha sido consumido inteiro.

        Sobra de registro significa que esta execução deixou de fazer uma
        chamada que a execução gravada fez — código diferente, não reprodução.
        """
        if self._cursor != len(self.records):
            missing = self.records[self._cursor]
            raise ReplayMismatchError(
                f"replay consumed {self._cursor} of {len(self.records)} recorded "
                f"call(s); the run stopped short of {missing.call_id!r}. The "
                "current code makes fewer LLM calls than the recorded run"
            )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
        options: dict[str, Any] | None = None,
        *,
        metadata: LLMCallMetadata | None = None,
    ) -> BaseModel | str:
        if self._decision_session is None:
            raise LLMTraceError(
                "no decision session is open; call begin_session(session) "
                "before replaying the agent graph"
            )
        declared = metadata or LLMCallMetadata(stage=STAGE_UNDECLARED)
        current = LLMCallRequest(
            stage=declared.stage,
            analyst_id=declared.analyst_id,
            decision_session=self._decision_session,
            provider=self.provider,
            requested_model=self.requested_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=schema_name(response_schema),
            response_schema_sha256=schema_digest(response_schema),
            requested_options=_jsonable_options(options),
        )
        if self._cursor >= len(self.records):
            raise ReplayMismatchError(
                f"the recorded trace has {len(self.records)} call(s) and is "
                f"exhausted, but the run asked for another one ({current.stage}, "
                f"session {current.decision_session}). The current code makes "
                "more LLM calls than the recorded run"
            )
        expected = self.records[self._cursor]
        differences = _identity_differences(expected.request, current)
        if differences:
            raise ReplayMismatchError(
                f"replayed call #{self._cursor} does not match recorded call "
                f"{expected.call_id!r}: " + "; ".join(differences)
            )
        self._cursor += 1

        if expected.status == STATUS_ERROR:
            raise _rebuild_error(expected)
        if response_schema is None:
            payload = expected.validated_response
            return payload if isinstance(payload, str) else str(payload)
        # Revalidado contra o schema corrente: um trace cujo payload não
        # satisfaz mais o contrato não é reproduzível em silêncio. Cada replay
        # devolve um objeto novo, nunca uma instância compartilhada.
        return response_schema.model_validate(expected.validated_response)


def _transport_prompt_digest(slot: LLMCallTelemetry) -> str | None:
    """Hash do system prompt final, quando o cliente concreto o reportou."""
    transported = slot.transport_system_prompt
    return sha256_text(transported) if transported is not None else None


def _identity_differences(expected: LLMCallRequest, actual: LLMCallRequest) -> list[str]:
    expected_identity = expected.identity()
    actual_identity = actual.identity()
    differences = []
    for key, wanted in expected_identity.items():
        found = actual_identity[key]
        if found != wanted:
            differences.append(f"{key} recorded={wanted!r} replayed={found!r}")
    return differences


def _rebuild_error(record: LLMCallRecord) -> BaseException:
    """Reconstrói a falha gravada preservando o tipo quando ele é conhecido."""
    name = record.error_type or ""
    error_type = _REPLAYABLE_ERRORS.get(name, RuntimeError)
    message = record.error_message or ""
    if error_type is RuntimeError and name:
        message = f"{name}: {message}"
    return error_type(message)


def _isoformat(moment: datetime) -> str:
    return moment.isoformat(timespec="microseconds").replace("+00:00", "Z")
