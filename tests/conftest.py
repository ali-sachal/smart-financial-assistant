import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AUTH_MODE", "local")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("DATABASE_URL_OVERRIDE", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("FEATURE_USERS", "false")
os.environ.setdefault("FEATURE_SUBSCRIPTION", "false")
os.environ.setdefault("FEATURE_KAFKA", "false")
os.environ.setdefault("FEATURE_TEAMS", "false")
