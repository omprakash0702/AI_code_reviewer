import json
import subprocess


def run_command(cmd):
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return result.stdout, result.stderr
    except Exception as e:
        return "", str(e)
