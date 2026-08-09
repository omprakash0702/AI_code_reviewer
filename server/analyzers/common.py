import subprocess

# Static analyzers occasionally hang on a specific file (malformed syntax,
# a plugin resolving something over the network, a pathological input) —
# without a timeout, one hung subprocess call blocks whichever caller is
# awaiting it forever. In the async job pipeline that means the ENTIRE
# analysis (all files) never completes, since asyncio.gather waits for
# every file's task to finish.
COMMAND_TIMEOUT = 30


def run_command(cmd, timeout=COMMAND_TIMEOUT):
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout
        )
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return "", f"timed out after {timeout}s: {' '.join(cmd)}"
    except Exception as e:
        return "", str(e)
