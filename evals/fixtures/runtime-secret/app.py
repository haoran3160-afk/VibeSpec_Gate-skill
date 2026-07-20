import os


SERVICE_API_KEY = "sk-test-vibespec-eval-not-a-real-credential-123456789"


def call_service() -> str:
    return os.getenv("SERVICE_API_KEY", SERVICE_API_KEY)
