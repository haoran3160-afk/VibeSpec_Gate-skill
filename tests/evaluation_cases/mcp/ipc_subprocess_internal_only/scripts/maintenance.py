import subprocess

def local_maintenance():
    return subprocess.run(["git", "status"], check=False)
