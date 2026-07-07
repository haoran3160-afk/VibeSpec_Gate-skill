HOST = "127.0.0.1"


def status_endpoint():
    return {"scope": "local-only same-user process owner", "host": HOST}
