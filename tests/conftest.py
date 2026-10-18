import os

# Tests must never inherit production storage or AI credentials from .env/the shell.
os.environ["ENVIRONMENT"] = "test"
os.environ["USE_IN_MEMORY_REPOSITORY"] = "true"
os.environ["COGNITO_USER_POOL_ID"] = "test-pool"
os.environ["COGNITO_APP_CLIENT_ID"] = "test-client"
os.environ["COGNITO_REGION"] = "us-east-1"
os.environ["GEMINI_API_KEY"] = ""
