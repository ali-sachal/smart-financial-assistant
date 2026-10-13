# app/core/config.py
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
import os

BASEDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE_PATH = os.path.join(BASEDIR, ".env")


class Settings(BaseSettings):
    """Platform settings. Feature flags keep every service in the tree while
    letting a project boot with only the integrations it needs.
    """

    APP_NAME: str = "FastAPI Platform"
    APP_TAGLINE: str = "Secure and observable REST APIs"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "local"

    # --- Feature flags (code stays; flags control boot + routes) ---
    FEATURE_AUTH: bool = True
    FEATURE_USERS: bool = True
    FEATURE_SUBSCRIPTION: bool = True
    FEATURE_PAYMENTS: bool = True
    FEATURE_PAYPAL: bool = False
    FEATURE_INVOICES: bool = True
    FEATURE_EMAIL: bool = True
    FEATURE_KAFKA: bool = False
    FEATURE_S3: bool = False
    FEATURE_TEAMS: bool = True
    FEATURE_LLM: bool = False

    # jwt_rs256 = Laravel Passport / any RS256 issuer
    # local     = HS256 tokens issued by this API
    # laravel   = RS256 + Laravel profile API required
    # none      = auth dependency injects a synthetic dev user
    AUTH_MODE: str = "local"
    ADMIN_OPEN: bool = False

    PASSPORT_PUBLIC_KEY: str = ""
    JWT_SECRET: str = "change-me-in-production"
    EXPECTED_AUD: str = "1"
    CLOCK_SKEW_LEEWAY: int = 10

    LARAVEL_API_URL: str = ""
    LARAVEL_CLIENT_ID: int = 0
    LARAVEL_CLIENT_SECRET: str = ""

    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8080"
    API_PREFIX: str = "/api"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    CORS_ALLOW_CREDENTIALS: bool = True
    ENABLED_DOMAINS: str = "example"

    TEAMS_WEBHOOK_URL: str = ""

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "app"
    POSTGRES_SERVER: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_URL_OVERRIDE: str = ""

    PAYMENT_CURRENCY: str = "usd"
    INVOICE_BUSINESS_NAME: str = "Example Company"
    INVOICE_BUSINESS_IDENTIFIER: str = ""
    INVOICE_BUSINESS_EMAIL: str = "billing@example.com"
    INVOICE_BUSINESS_ADDRESS: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    PAYPAL_CLIENT_ID: str = "sandbox"
    PAYPAL_SECRET: str = "sandbox"
    PAYPAL_MODE: str = "sandbox"

    INPUT_TOKEN_PRICE: float = 0.0
    OUTPUT_TOKEN_PRICE: float = 0.0
    NANOBANANA_INPUT_TOKEN_PRICE: float = 0.0
    NANOBANANA_OUTPUT_TOKEN_PRICE: float = 0.0
    NANOBANANA_MODEL: str = "gemini-2.5-flash-image"

    S3_usage: bool = False
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-southeast-2"
    AWS_S3_BUCKET_NAME: str = ""
    AWS_USE_IAM_ROLE: bool = False
    AWS_S3_CUSTOM_DOMAIN: str = ""

    MAIL_MAILER: str = "smtp"
    MAIL_HOST: str = ""
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_ENCRYPTION: str = "tls"
    MAIL_FROM_ADDRESS: str = "noreply@example.com"

    KAFKA_SERVER: str = ""
    KAFKA_EMAIL_TOPIC: str = "email"

    @field_validator("PASSPORT_PUBLIC_KEY")
    @classmethod
    def format_public_key(cls, v: str) -> str:
        if v and "\\n" in v:
            v = v.replace("\\n", "\n")
        return v

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.ENVIRONMENT.lower() in {"production", "prod"}:
            if self.AUTH_MODE == "local" and self.JWT_SECRET == "change-me-in-production":
                raise ValueError("JWT_SECRET must be changed in production")
            if self.CORS_ALLOW_CREDENTIALS and "*" in self.cors_origins:
                raise ValueError("Wildcard CORS cannot be used with credentials in production")
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [value.strip() for value in self.CORS_ORIGINS.split(",") if value.strip()]

    @property
    def enabled_domains(self) -> list[str]:
        return [value.strip() for value in self.ENABLED_DOMAINS.split(",") if value.strip()]

    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        return (
            f"postgresql+psycopg://{quote_plus(self.POSTGRES_USER)}:{quote_plus(self.POSTGRES_PASSWORD)}"
            f"@{self.POSTGRES_SERVER}:{self.DATABASE_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, extra="ignore")


settings = Settings()
