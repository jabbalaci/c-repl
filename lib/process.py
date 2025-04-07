import shlex
import subprocess
from subprocess import PIPE, Popen


def get_exitcode_stdout_stderr(cmd):
    """
    Execute the external command and get its exitcode, stdout and stderr.
    """
    args = shlex.split(cmd)

    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    out, err = out.decode("utf8"), err.decode("utf8")
    exitcode = proc.returncode
    #
    return exitcode, out.rstrip("\n"), err.rstrip("\n")


def capture_crash_message(cmd):
    """
    Absolutely captures segfault messages by:
    1. Forcing shell output through a pipe
    2. Merging stdout/stderr
    3. Using bash explicitly for consistent behavior
    """
    proc = subprocess.Popen(
        f"bash -c '{cmd} 2>&1'",  # Force all output to stdout
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Merge stderr into stdout
        universal_newlines=True,
    )
    output, _ = proc.communicate()
    exitcode = proc.returncode

    # Normalize signal exits (e.g., -11 → 139)
    if exitcode < 0:
        exitcode = 128 + (-exitcode)

    return exitcode, output.strip()
