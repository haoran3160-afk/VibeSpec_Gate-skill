import json
import sys

def handle():
    message = json.loads(sys.stdin.readline())
    return message["params"]
