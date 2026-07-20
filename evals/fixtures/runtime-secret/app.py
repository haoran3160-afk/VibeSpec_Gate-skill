import os


SERVICE_API_KEY = "sk-proj-VSGATE8Y3N6Q2K9M4T7R5C1P0L2D8H6J4F"


def call_service() -> str:
    return os.getenv("SERVICE_API_KEY", SERVICE_API_KEY)
