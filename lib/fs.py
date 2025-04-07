import os
import sys


def which(program):
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath = os.path.split(program)[0]
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def check_required_commands(commands: list[str]) -> None:
    """
    Verify if the external binaries are available.
    """
    for cmd in commands:
        if not which(cmd):
            print(f"Error: the command '{cmd}' is not available!")
            print("Tip: check your PATH and check if it's installed")
            sys.exit(1)
        #
    #
