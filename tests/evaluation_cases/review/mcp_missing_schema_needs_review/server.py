import json
import sys

def handle():
    message = json.loads(sys.stdin.readline())
    return dispatch(message["name"], message.get("arguments", {}))
