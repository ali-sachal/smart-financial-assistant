import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("USE_IN_MEMORY_REPOSITORY", "true")
os.environ.setdefault("COGNITO_USER_POOL_ID", "test-pool")
os.environ.setdefault("COGNITO_APP_CLIENT_ID", "test-client")
os.environ.setdefault("COGNITO_REGION", "us-east-1")
