# ai/llms/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
import os 
import json

BASEDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE_PATH = os.path.join(BASEDIR, '.env')

class Settings(BaseSettings):
    # App Configuration
    APP_NAME: str = "FastAPI Platform"
    
    # Gemini Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0.2
    GEMINI_MAX_OUTPUT_TOKENS: int = 8192
    GEMINI_TOP_P: float = 0.95
    GEMINI_TOP_K: int = 40
    #NANOBANANA CONFIGURATION
    NANOBANANA_INPUT_TOKEN_PRICE: float = 0.0
    NANOBANANA_OUTPUT_TOKEN_PRICE: float = 0.0
    NANOBANANA_MODEL: str = "gemini-3-pro-image-preview"
    
    # Resume Parser Configuration
    RESUME_PARSER_SYSTEM_PROMPT: str = """You are a professional resume parser. Your task is to extract all information from the provided resume PDF and structure it into a comprehensive JSON format.

Rules:
1. Use main headings as primary keys (e.g., "Personal Information", "Education", "Experience", "Skills", etc.)
2. Use sub-headings and relevant categories as sub-keys
3. Preserve all information accurately - do not omit any details
4. If a section doesn't have clear sub-headings, create logical sub-categories
5. For dates, preserve the original format but also provide a standardized format when possible
6. For contact information, extract phone, email, address, LinkedIn, portfolio links separately
7. For experience and education, include all details like dates, descriptions, achievements, etc.
8. Return only valid JSON - no additional text or explanations

Expected JSON structure example:
{
  "personal_information": {
    "name": "...",
    "email": "...",
    "phone": "...",
    "address": "...",
    "linkedin": "...",
    "portfolio": "..."
  },
  "professional_summary": "...",
  "experience": [
    {
      "title": "...",
      "company": "...",
      "duration": "...",
      "location": "...",
      "responsibilities": [...],
      "achievements": [...]
    }
  ],
  "education": [...],
  "skills": {...},
  "certifications": [...],
  "projects": [...],
  "additional_sections": {...}
}"""

    # Unified model profiles. Values are LiteLLM model identifiers. API keys
    # stay in provider environment variables (OPENAI_API_KEY, ANTHROPIC_API_KEY,
    # GEMINI_API_KEY, AWS credentials, etc.) and are never stored in profiles.
    LLM_DEFAULT_MODEL: str = "general"
    LLM_IMAGE_MODEL: str = "image"
    LLM_EMBEDDING_MODEL: str = "embedding"
    LLM_FALLBACK_MODELS: str = ""
    LLM_TIMEOUT_SECONDS: float = 60.0
    LLM_MAX_RETRIES: int = 2
    LLM_PROFILES_JSON: str = ""

    def model_profiles(self) -> dict[str, dict]:
        defaults = {
            "general": {
                "model": f"gemini/{self.GEMINI_MODEL_NAME}",
                "capabilities": ["chat", "stream", "structured", "tools", "multimodal"],
            },
            "image": {
                "model": f"gemini/{self.NANOBANANA_MODEL}",
                "capabilities": ["image", "multimodal"],
            },
            "embedding": {
                "model": "gemini/text-embedding-004",
                "capabilities": ["embedding"],
            },
        }
        if not self.LLM_PROFILES_JSON.strip():
            return defaults
        configured = json.loads(self.LLM_PROFILES_JSON)
        if not isinstance(configured, dict):
            raise ValueError("LLM_PROFILES_JSON must be a JSON object")
        return {**defaults, **configured}

    @property
    def fallback_models(self) -> list[str]:
        return [name.strip() for name in self.LLM_FALLBACK_MODELS.split(",") if name.strip()]
    
    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, extra='ignore')

settings = Settings()
