import subprocess


def call_tool(message):
    command = message["command"]
    return subprocess.check_output(command, shell=True)
