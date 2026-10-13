"""Unified multi-provider model gateway backed by LiteLLM.

Model profiles contain routing information, never credentials. LiteLLM reads
provider credentials from their standard environment variables.
"""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, AsyncIterator, Iterator, Mapping, Sequence

from .config import Settings, settings


class ModelCapability(StrEnum):
    CHAT = "chat"
    STREAM = "stream"
    STRUCTURED = "structured"
    TOOLS = "tools"
    MULTIMODAL = "multimodal"
    IMAGE = "image"
    EMBEDDING = "embedding"


class LLMGatewayError(RuntimeError):
    """Base error with safe provider/model context."""

    def __init__(
        self,
        message: str,
        *,
        capability: str | None = None,
        attempts: Sequence[str] = (),
    ):
        super().__init__(message)
        self.capability = capability
        self.attempts = tuple(attempts)


class ModelConfigurationError(LLMGatewayError):
    pass


class ModelCapabilityError(LLMGatewayError):
    pass


@dataclass(frozen=True)
class ModelProfile:
    name: str
    model: str
    capabilities: frozenset[ModelCapability]
    api_base: str | None = None
    api_key_env: str | None = None
    timeout: float | None = None
    max_retries: int | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, name: str, data: Mapping[str, Any]) -> "ModelProfile":
        model = str(data.get("model") or "").strip()
        if not model:
            raise ModelConfigurationError(f"Model profile {name!r} has no model")
        try:
            capabilities = frozenset(ModelCapability(value) for value in data.get("capabilities", []))
        except ValueError as exc:
            raise ModelConfigurationError(f"Model profile {name!r} has an invalid capability") from exc
        known = {"model", "capabilities", "api_base", "api_key_env", "timeout", "max_retries"}
        return cls(
            name=name,
            model=model,
            capabilities=capabilities,
            api_base=data.get("api_base"),
            api_key_env=data.get("api_key_env"),
            timeout=float(data["timeout"]) if data.get("timeout") is not None else None,
            max_retries=int(data["max_retries"]) if data.get("max_retries") is not None else None,
            extra={key: value for key, value in data.items() if key not in known},
        )


@dataclass
class ModelUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float | None = None


@dataclass
class ModelResult:
    content: Any
    model: str
    provider: str | None
    profile: str
    usage: ModelUsage
    latency_ms: int
    finish_reason: str | None = None
    raw: Any = None


def _value(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


class LLMGateway:
    def __init__(self, profiles: Mapping[str, ModelProfile], config: Settings = settings, backend: Any = None):
        self.profiles = dict(profiles)
        self.config = config
        self._backend = backend

    @classmethod
    def from_settings(cls, config: Settings = settings, backend: Any = None) -> "LLMGateway":
        profiles = {
            name: ModelProfile.from_mapping(name, definition)
            for name, definition in config.model_profiles().items()
        }
        return cls(profiles, config=config, backend=backend)

    @property
    def backend(self):
        if self._backend is None:
            try:
                import litellm
            except ImportError as exc:
                raise ModelConfigurationError("Install the 'ai' dependencies to use the unified model gateway") from exc
            self._backend = litellm
        return self._backend

    def profile(self, name: str | None, capability: ModelCapability) -> ModelProfile:
        profile_name = name or self.config.LLM_DEFAULT_MODEL
        profile = self.profiles.get(profile_name)
        if profile is None:
            raise ModelConfigurationError(f"Unknown model profile: {profile_name}")
        if capability not in profile.capabilities:
            raise ModelCapabilityError(
                f"Model profile {profile_name!r} does not support {capability.value!r}"
            )
        return profile

    def _candidates(self, name: str | None, capability: ModelCapability) -> list[ModelProfile]:
        primary = self.profile(name, capability)
        candidates = [primary]
        for fallback_name in self.config.fallback_models:
            if fallback_name == primary.name:
                continue
            fallback = self.profiles.get(fallback_name)
            if fallback and capability in fallback.capabilities:
                candidates.append(fallback)
        return candidates

    def _kwargs(self, profile: ModelProfile) -> dict[str, Any]:
        import os

        kwargs = dict(profile.extra)
        kwargs["model"] = profile.model
        kwargs["timeout"] = profile.timeout or self.config.LLM_TIMEOUT_SECONDS
        kwargs["num_retries"] = profile.max_retries if profile.max_retries is not None else self.config.LLM_MAX_RETRIES
        if profile.api_base:
            kwargs["api_base"] = profile.api_base
        if profile.api_key_env:
            api_key = os.getenv(profile.api_key_env)
            if not api_key:
                raise ModelConfigurationError(
                    f"Environment variable {profile.api_key_env!r} is required by profile {profile.name!r}"
                )
            kwargs["api_key"] = api_key
        return kwargs

    def _run_with_fallback(self, name: str | None, capability: ModelCapability, operation):
        failures: list[str] = []
        for profile in self._candidates(name, capability):
            try:
                return operation(profile)
            except ModelConfigurationError:
                raise
            except Exception as exc:
                failures.append(f"{profile.name}: {type(exc).__name__}")
        raise LLMGatewayError(
            "All model profiles failed (" + ", ".join(failures) + ")",
            capability=capability.value,
            attempts=failures,
        )

    async def _arun_with_fallback(self, name: str | None, capability: ModelCapability, operation):
        failures: list[str] = []
        for profile in self._candidates(name, capability):
            try:
                return await operation(profile)
            except ModelConfigurationError:
                raise
            except Exception as exc:
                failures.append(f"{profile.name}: {type(exc).__name__}")
        raise LLMGatewayError(
            "All model profiles failed (" + ", ".join(failures) + ")",
            capability=capability.value,
            attempts=failures,
        )

    def _normalize(self, response: Any, profile: ModelProfile, started: float, content: Any = None) -> ModelResult:
        choices = _value(response, "choices", []) or []
        first = choices[0] if choices else None
        message = _value(first, "message", None)
        if content is None:
            content = _value(message, "content", None)
        usage = _value(response, "usage", {}) or {}
        hidden = _value(response, "_hidden_params", {}) or {}
        model = str(_value(response, "model", profile.model))
        provider = _value(response, "llm_provider", None) or _value(hidden, "custom_llm_provider", None)
        return ModelResult(
            content=content,
            model=model,
            provider=provider,
            profile=profile.name,
            usage=ModelUsage(
                input_tokens=int(_value(usage, "prompt_tokens", 0) or 0),
                output_tokens=int(_value(usage, "completion_tokens", 0) or 0),
                total_tokens=int(_value(usage, "total_tokens", 0) or 0),
                cost=_value(hidden, "response_cost", None),
            ),
            latency_ms=int((time.perf_counter() - started) * 1000),
            finish_reason=_value(first, "finish_reason", None),
            raw=response,
        )

    def chat(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        profile: str | None = None,
        tools: Sequence[Mapping[str, Any]] | None = None,
        **kwargs: Any,
    ) -> ModelResult:
        capability = ModelCapability.TOOLS if tools else ModelCapability.CHAT
        def call(candidate: ModelProfile):
            started = time.perf_counter()
            params = {**self._kwargs(candidate), "messages": list(messages), **kwargs}
            if tools:
                params["tools"] = list(tools)
            return self._normalize(self.backend.completion(**params), candidate, started)
        return self._run_with_fallback(profile, capability, call)

    async def achat(self, messages: Sequence[Mapping[str, Any]], *, profile: str | None = None, **kwargs: Any) -> ModelResult:
        async def call(candidate: ModelProfile):
            started = time.perf_counter()
            response = await self.backend.acompletion(
                **self._kwargs(candidate), messages=list(messages), **kwargs
            )
            return self._normalize(response, candidate, started)
        return await self._arun_with_fallback(profile, ModelCapability.CHAT, call)

    def structured(self, messages: Sequence[Mapping[str, Any]], *, schema: Mapping[str, Any] | None = None, profile: str | None = None, **kwargs: Any) -> ModelResult:
        def call(candidate: ModelProfile):
            started = time.perf_counter()
            response_format = {"type": "json_object"}
            if schema:
                response_format = {"type": "json_schema", "json_schema": schema}
            response = self.backend.completion(
                **self._kwargs(candidate), messages=list(messages), response_format=response_format, **kwargs
            )
            result = self._normalize(response, candidate, started)
            if isinstance(result.content, str):
                result.content = json.loads(result.content)
            return result
        return self._run_with_fallback(profile, ModelCapability.STRUCTURED, call)

    def stream(self, messages: Sequence[Mapping[str, Any]], *, profile: str | None = None, **kwargs: Any) -> Iterator[str]:
        response = self._run_with_fallback(
            profile,
            ModelCapability.STREAM,
            lambda candidate: self.backend.completion(
                **self._kwargs(candidate), messages=list(messages), stream=True, **kwargs
            ),
        )
        for chunk in response:
            choices = _value(chunk, "choices", []) or []
            if choices:
                content = _value(_value(choices[0], "delta", {}), "content", None)
                if content:
                    yield str(content)

    async def astream(self, messages: Sequence[Mapping[str, Any]], *, profile: str | None = None, **kwargs: Any) -> AsyncIterator[str]:
        async def start(candidate: ModelProfile):
            return await self.backend.acompletion(
                **self._kwargs(candidate), messages=list(messages), stream=True, **kwargs
            )
        response = await self._arun_with_fallback(
            profile, ModelCapability.STREAM, start
        )
        async for chunk in response:
            choices = _value(chunk, "choices", []) or []
            if choices:
                content = _value(_value(choices[0], "delta", {}), "content", None)
                if content:
                    yield str(content)

    def multimodal(self, prompt: str, data: bytes, mime_type: str, *, profile: str | None = None, **kwargs: Any) -> ModelResult:
        encoded = base64.b64encode(data).decode("ascii")
        if mime_type.startswith("image/"):
            attachment = {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}}
        else:
            attachment = {"type": "file", "file": {"file_data": f"data:{mime_type};base64,{encoded}"}}
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                attachment,
            ],
        }]
        def call(candidate: ModelProfile):
            started = time.perf_counter()
            response = self.backend.completion(
                **self._kwargs(candidate), messages=messages, **kwargs
            )
            return self._normalize(response, candidate, started)
        return self._run_with_fallback(profile, ModelCapability.MULTIMODAL, call)

    def embeddings(self, inputs: str | Sequence[str], *, profile: str | None = None, **kwargs: Any) -> ModelResult:
        name = profile or self.config.LLM_EMBEDDING_MODEL
        def call(candidate: ModelProfile):
            started = time.perf_counter()
            response = self.backend.embedding(
                **self._kwargs(candidate), input=inputs, **kwargs
            )
            vectors = [_value(item, "embedding", []) for item in (_value(response, "data", []) or [])]
            return self._normalize(response, candidate, started, vectors)
        return self._run_with_fallback(name, ModelCapability.EMBEDDING, call)

    def image(self, prompt: str, *, profile: str | None = None, **kwargs: Any) -> ModelResult:
        name = profile or self.config.LLM_IMAGE_MODEL
        def call(candidate: ModelProfile):
            started = time.perf_counter()
            response = self.backend.image_generation(
                **self._kwargs(candidate), prompt=prompt, **kwargs
            )
            images = [
                {"url": _value(item, "url", None), "b64_json": _value(item, "b64_json", None)}
                for item in (_value(response, "data", []) or [])
            ]
            return self._normalize(response, candidate, started, images)
        return self._run_with_fallback(name, ModelCapability.IMAGE, call)


llm_gateway = LLMGateway.from_settings()
