import os

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")


class Settings(BaseSettings):
    APP_NAME: str = "Smart Personal Finance Assistant"
    APP_TAGLINE: str = "Explainable budgeting, receipt analysis, and cash-flow guidance"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "local"
    API_PREFIX: str = "/api"

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    CORS_ALLOW_CREDENTIALS: bool = True

    COGNITO_REGION: str = "us-east-1"
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_APP_CLIENT_ID: str = ""
    COGNITO_JWKS_TTL_SECONDS: int = 3600
    CLOCK_SKEW_LEEWAY: int = 10

    USE_IN_MEMORY_REPOSITORY: bool = True
    FINANCE_TABLE_NAME: str = "smart-finance"
    DYNAMODB_ENDPOINT_URL: str = ""
    AWS_REGION: str = "us-east-1"

    RECEIPTS_BUCKET_NAME: str = ""
    RECEIPT_MAX_BYTES: int = 10 * 1024 * 1024
    RECEIPT_AUTO_CREATE_CONFIDENCE: float = 0.80

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash"
    AGENT_MAX_TOOL_ROUNDS: int = 5

    @property
    def cors_origins(self) -> list[str]:
        return [value.strip() for value in self.CORS_ORIGINS.split(",") if value.strip()]

    @model_validator(mode="after")
    def validate_production_configuration(self):
        if self.ENVIRONMENT.lower() in {"production", "prod"}:
            if not self.COGNITO_USER_POOL_ID or not self.COGNITO_APP_CLIENT_ID:
                raise ValueError("Cognito User Pool and app client IDs are required in production")
            if self.USE_IN_MEMORY_REPOSITORY:
                raise ValueError("USE_IN_MEMORY_REPOSITORY must be false in production")
            if not self.RECEIPTS_BUCKET_NAME:
                raise ValueError("RECEIPTS_BUCKET_NAME is required in production")
            if self.CORS_ALLOW_CREDENTIALS and "*" in self.cors_origins:
                raise ValueError("Wildcard CORS cannot be used with credentials in production")
        return self

    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, extra="ignore")


settings = Settings()
