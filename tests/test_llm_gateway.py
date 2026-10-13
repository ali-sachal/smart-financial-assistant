import asyncio

import pytest

from ai.llms.config import Settings
from ai.llms.gateway import (
    LLMGateway,
    LLMGatewayError,
    ModelCapability,
    ModelCapabilityError,
    ModelProfile,
)


class FakeBackend:
    def __init__(self):
        self.calls = []

    def completion(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs["model"] == "provider/failing":
            raise RuntimeError("provider unavailable")
        if kwargs.get("stream"):
            return iter([
                {"choices": [{"delta": {"content": "hel"}}]},
                {"choices": [{"delta": {"content": "lo"}}]},
            ])
        content = '{"answer": 42}' if kwargs.get("response_format") else "hello"
        return {
            "model": kwargs["model"],
            "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
            "_hidden_params": {"custom_llm_provider": "fake", "response_cost": 0.01},
        }

    async def acompletion(self, **kwargs):
        if kwargs.get("stream"):
            async def chunks():
                for chunk in self.completion(**kwargs):
                    yield chunk
            return chunks()
        return self.completion(**kwargs)

    def embedding(self, **kwargs):
        return {"model": kwargs["model"], "data": [{"embedding": [0.1, 0.2]}], "usage": {}}

    def image_generation(self, **kwargs):
        return {"model": kwargs["model"], "data": [{"url": "https://example.test/image.png"}], "usage": {}}


def make_gateway(fallbacks=""):
    config = Settings(_env_file=None, LLM_FALLBACK_MODELS=fallbacks)
    profiles = {
        "primary": ModelProfile("primary", "provider/failing", frozenset({ModelCapability.CHAT})),
        "general": ModelProfile("general", "provider/chat", frozenset({
            ModelCapability.CHAT, ModelCapability.STREAM, ModelCapability.STRUCTURED,
            ModelCapability.TOOLS, ModelCapability.MULTIMODAL,
        })),
        "embedding": ModelProfile("embedding", "provider/embed", frozenset({ModelCapability.EMBEDDING})),
        "image": ModelProfile("image", "provider/image", frozenset({ModelCapability.IMAGE})),
    }
    return LLMGateway(profiles, config=config, backend=FakeBackend())


def test_normalizes_chat_usage_and_provider():
    gateway = make_gateway()
    result = gateway.chat([{"role": "user", "content": "hello"}], profile="general")
    assert result.content == "hello"
    assert result.provider == "fake"
    assert result.usage.total_tokens == 3
    assert result.usage.cost == 0.01


def test_falls_back_in_configured_order():
    gateway = make_gateway("general")
    result = gateway.chat([{"role": "user", "content": "hello"}], profile="primary")
    assert result.profile == "general"
    assert [call["model"] for call in gateway.backend.calls] == ["provider/failing", "provider/chat"]


def test_normalizes_exhausted_provider_errors_without_raw_details():
    gateway = make_gateway()
    with pytest.raises(LLMGatewayError) as captured:
        gateway.chat([], profile="primary")
    assert captured.value.capability == "chat"
    assert captured.value.attempts == ("primary: RuntimeError",)


def test_structured_stream_embedding_and_image_operations():
    gateway = make_gateway()
    assert gateway.structured([], profile="general").content == {"answer": 42}
    assert "".join(gateway.stream([], profile="general")) == "hello"
    assert gateway.embeddings("text").content == [[0.1, 0.2]]
    assert gateway.image("draw").content[0]["url"].endswith("image.png")


def test_tools_multimodal_async_and_retry_configuration():
    gateway = make_gateway()
    gateway.chat([], profile="general", tools=[{"type": "function", "function": {"name": "lookup"}}])
    tool_call = gateway.backend.calls[-1]
    assert tool_call["tools"][0]["function"]["name"] == "lookup"
    assert tool_call["num_retries"] == gateway.config.LLM_MAX_RETRIES

    gateway.multimodal("read", b"document", "application/pdf", profile="general")
    attachment = gateway.backend.calls[-1]["messages"][0]["content"][1]
    assert attachment["type"] == "file"
    assert attachment["file"]["file_data"].startswith("data:application/pdf;base64,")

    async def exercise_async():
        assert (await gateway.achat([], profile="general")).content == "hello"
        return "".join([part async for part in gateway.astream([], profile="general")])

    assert asyncio.run(exercise_async()) == "hello"


def test_rejects_unsupported_capability_before_provider_call():
    gateway = make_gateway()
    with pytest.raises(ModelCapabilityError):
        gateway.image("draw", profile="general")
