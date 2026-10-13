# Unified AI model gateway

The existing `GeminiClient`, `NanoBananaClient`, resume prompt, and compatibility globals remain available. New code can use `ai.llms.gateway.llm_gateway` to switch providers through configuration rather than application changes.

## Named profiles

`LLM_PROFILES_JSON` is a JSON object. Each key is an application-facing profile name and each `model` is a LiteLLM model identifier:

```json
{
  "general": {
    "model": "openai/gpt-5-mini",
    "api_key_env": "OPENAI_API_KEY",
    "capabilities": ["chat", "stream", "structured", "tools", "multimodal"]
  },
  "backup_one": {
    "model": "anthropic/claude-sonnet-4-5",
    "api_key_env": "ANTHROPIC_API_KEY",
    "capabilities": ["chat", "stream", "structured", "tools", "multimodal"]
  },
  "embedding": {
    "model": "openai/text-embedding-3-small",
    "api_key_env": "OPENAI_API_KEY",
    "capabilities": ["embedding"]
  },
  "image": {
    "model": "openai/gpt-image-1",
    "api_key_env": "OPENAI_API_KEY",
    "capabilities": ["image"]
  }
}
```

Set `LLM_DEFAULT_MODEL`, `LLM_IMAGE_MODEL`, `LLM_EMBEDDING_MODEL`, and the comma-separated `LLM_FALLBACK_MODELS` to those profile names. Never put a key directly in profile JSON; `api_key_env` names the environment variable that contains it.

LiteLLM model identifiers cover OpenAI, Azure OpenAI, Anthropic, Gemini/Vertex AI, Bedrock, Mistral, Cohere, Groq, OpenRouter, Ollama, and OpenAI-compatible endpoints. For compatible servers, set `api_base` in the profile.

## Operations

The gateway exposes `chat`, `achat`, `stream`, `astream`, `structured`, `multimodal`, `image`, and `embeddings`. `chat(..., tools=[...])` enables tool/function calling. Results normalize content, model/profile/provider, input/output/total tokens, estimated cost, latency, finish reason, and the raw provider response.

Profiles declare capabilities. An unsupported operation raises `ModelCapabilityError` before contacting a provider. Missing profiles or credentials raise `ModelConfigurationError`; exhausted fallbacks raise `LLMGatewayError` with safe attempt metadata.
