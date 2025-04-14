#!/usr/bin/env python3

"""
C REPL

A simple REPL for the C programming language.

Author: Laszlo Szathmary (jabba.laci@gmail.com), 2025
"""

import os
import re
import readline
import shutil
from pathlib import Path

from yachalk import chalk

from lib import ascii, fs, process
from lib.cmanagers import ChDir

VERSION = "0.0.2"

ROOT = os.path.dirname(os.path.realpath(__file__))
TMP_DIR = os.path.join(ROOT, "tmp")
SNIPPETS_DIR = os.path.join(ROOT, "snippets")

CC = "gcc"  # in package 'gcc'
CLANG_FORMAT = "clang-format"  # in package 'clang'
# under Ubuntu, it's "batcat"; under Manjaro, it's "bat"; "cat" is the fallback option
CAT = "batcat,bat,cat"
EDITOR = "micro"  # in package 'micro' ; can be replaced with vim/nvim too
PYTHON3 = "python3"  # in package 'python'
VALGRIND = "valgrind"  # in package 'valgrind'

# verify upon startup if these programs are available:
REQUIRED_COMMANDS = [CC, CLANG_FORMAT, EDITOR, PYTHON3, VALGRIND]
##############################################################################


def add_semicolon_if_needed(line: str) -> str:
    if Parser.is_for_loop(line) or Parser.is_while_loop(line):
        if Parser.has_curly_brace(line):
            return line
    #
    if "//" in line:
        left, right = line.split("//")
        left, right = left.strip(), right.strip()
        if not left.endswith(";"):
            return f"{left}; // {right}"
        else:
            return line
    else:
        if not line.endswith(";"):
            line += ";"
        #
        return line


def remove_prefix(s: str, options: tuple[str, ...]) -> str:
    for pre in options:
        if s.startswith(pre):
            return s.removeprefix(pre)
        #
    #
    return s


# modify the list in-place
def remove_leading_empty_strings(li: list[str]) -> None:
    while li and li[0].strip() == "":
        li.pop(0)


# modify the list in-place
def remove_trailing_empty_strings(li: list[str]) -> None:
    while li and li[-1].strip() == "":
        li.pop()


def cat_command() -> str:
    options = CAT.split(",")
    for opt in options:
        if fs.which(opt):
            return opt
        #
    #
    return "cat"


##############################################################################


class FileSystem:
    @staticmethod
    def copy_prog1():
        d = {
            f"{SNIPPETS_DIR}/prog1.h": f"{TMP_DIR}/prog1.h",
            f"{SNIPPETS_DIR}/prog1.c": f"{TMP_DIR}/prog1.c",
        }
        for from_here, to_here in d.items():
            if not os.path.isfile(to_here):
                shutil.copy(from_here, to_here)


##############################################################################


class Source:
    def __init__(self) -> None:
        auto_includes: list[str] = ["ctype.h", "math.h", "stdio.h", "stdlib.h", "string.h"]
        self.include_lines: list[str] = []
        for header in auto_includes:
            self.include_lines.append(f"#include <{header}>")
        self.compiler_arguments: list[str] = ["-lm"]  # "-lm" is for math.h
        #
        self.define_lines: list[str] = []
        self.global_variable_lines: list[str] = []
        self.typedef_struct_lines: list[str] = ["typedef char* string;"]
        self.function_definitions: list[str] = []
        self.main_body_lines: list[str] = []
        self.exit_code: str = "0"

    def get_source_code_path(self) -> str:
        return os.path.join(TMP_DIR, "main.c")

    def reload_source_code(self) -> None:
        all_lines = self.read_source_code().splitlines()
        #
        self.include_lines = []
        self.define_lines = []
        self.typedef_struct_lines = []
        self.global_variable_lines = []
        self.function_definitions = []
        self.main_body_lines = []
        idx = 0
        while idx < len(all_lines):
            line = all_lines[idx]
            if line.strip() == "":
                pass
            elif line.startswith("#include"):
                self.include_lines.append(line)
            elif line.startswith("#define "):
                self.define_lines.append(line)
            elif line.startswith("typedef "):
                if line.endswith(";"):
                    self.typedef_struct_lines.append(line)
                else:
                    result, idx = self.get_blocks_lines(all_lines, idx)
                    self.typedef_struct_lines.extend(result)
            elif line.startswith("struct "):
                if line.endswith(";"):
                    self.typedef_struct_lines.append(line)
                else:
                    result, idx = self.get_blocks_lines(all_lines, idx)
                    self.typedef_struct_lines.extend(result)
            elif line.endswith("// def"):
                result, idx = self.get_functions_lines(all_lines, idx)
                snippet = "\n".join(result)
                self.function_definitions.append(snippet)
            elif line.startswith("int main("):
                result, idx = self.get_mains_body(all_lines, idx + 2)
                self.main_body_lines.extend(result)
            else:
                self.global_variable_lines.append(line)
            #
            idx += 1
        # endwhile

    def get_functions_lines(self, lines: list[str], idx: int) -> tuple[list[str], int]:
        result: list[str] = []
        #
        while True:
            line = lines[idx]
            result.append(line)
            if line.strip() == "}":
                break
            # else
            idx += 1
        #
        return result, idx

    def get_blocks_lines(self, lines: list[str], idx: int) -> tuple[list[str], int]:
        result: list[str] = []
        #
        while True:
            line = lines[idx]
            result.append(line)
            if line.startswith("}") and line.endswith(";"):
                break
            # else
            idx += 1
        #
        return result, idx

    def get_mains_body(self, lines: list[str], idx: int) -> tuple[list[str], int]:
        result: list[str] = []
        #
        while lines[idx] != "}":
            result.append(lines[idx])
            idx += 1
        #
        remove_leading_empty_strings(result)
        remove_trailing_empty_strings(result)
        #
        if result:
            m = re.search(r"return (.*);", result[-1].strip())
            if m:
                self.exit_code = m.group(1)
        #
        return result, idx

    def add_include_lines(self, lines: list[str]) -> None:
        for l in self.include_lines:  # noqa
            lines.append(l)
        if self.include_lines:
            lines.append("")

    def add_define_lines(self, lines: list[str]) -> None:
        for l in self.define_lines:  # noqa
            lines.append(l)
        if self.define_lines:
            lines.append("")

    def add_typedef_lines(self, lines: list[str]) -> None:
        for l in self.typedef_struct_lines:  # noqa
            lines.append(l)
        if self.typedef_struct_lines:
            lines.append("")

    def add_global_lines(self, lines: list[str]) -> None:
        for l in self.global_variable_lines:  # noqa
            lines.append(l)
        if self.global_variable_lines:
            lines.append("")

    def add_function_definitions(self, lines: list[str]) -> None:
        for l in self.function_definitions:  # noqa
            lines.append(l)
        if self.function_definitions:
            lines.append("")

    def add_main_header(self, lines: list[str]) -> None:
        lines.append("int main()")
        lines.append("{")

    def remove_exit_code(self):
        remove_trailing_empty_strings(self.main_body_lines)
        #
        if self.main_body_lines:
            last_line = self.main_body_lines[-1]
            if last_line.lstrip().startswith("return"):
                self.main_body_lines.pop()
            #
        #
        remove_trailing_empty_strings(self.main_body_lines)

    def add_exit_code(self):
        remove_trailing_empty_strings(self.main_body_lines)
        #
        self.main_body_lines.append("")
        self.main_body_lines.append(f"    return {self.exit_code};")

    def add_main_body(self, lines: list[str]) -> None:
        self.remove_exit_code()
        self.add_exit_code()
        for l in self.main_body_lines:  # noqa
            lines.append(l)

    def add_main_footer(self, lines: list[str]) -> None:
        lines.append("}")

    def put_together(self) -> str:
        lines: list[str] = []
        #
        self.add_include_lines(lines)
        self.add_define_lines(lines)
        self.add_global_lines(lines)
        self.add_typedef_lines(lines)
        self.add_function_definitions(lines)
        self.add_main_header(lines)
        self.add_main_body(lines)
        self.add_main_footer(lines)
        #
        return "\n".join(lines)

    def get_lines(self) -> list[str]:
        return self.put_together().splitlines()

    def read_source_code(self) -> str:
        with ChDir(TMP_DIR):
            with open("main.c") as f:
                return f.read().rstrip("\n")

    def cat(self) -> None:
        """
        Pretty print with "bat".
        """
        binary = cat_command()
        cmd = "cat main.c"
        if "bat" in binary:
            cmd = f"{binary} -p main.c"
        self.save_and_format_source_code()
        with ChDir(TMP_DIR):
            os.system(cmd)

    def save_source_code(self) -> None:
        text = self.put_together()
        with ChDir(TMP_DIR):
            Path("main.c").write_text(text)

    def save_and_format_source_code(self) -> None:
        self.save_source_code()
        cmd = f"{CLANG_FORMAT} --style=Microsoft -i main.c"
        with ChDir(TMP_DIR):
            os.system(cmd)

    def write_source_code(self, text: str) -> None:
        with ChDir(TMP_DIR):
            Path("main.c").write_text(text)

    def edit(self) -> None:
        self.save_and_format_source_code()
        with ChDir(TMP_DIR):
            cmd = f"{EDITOR} main.c"
            os.system(cmd)
        #
        self.reload_source_code()

    def try_to_add_line(self, line: str, where: list[str], remove_add_exit_code=False) -> bool:
        if remove_add_exit_code:
            self.remove_exit_code()
        where.append(line)
        if remove_add_exit_code:
            self.add_exit_code()
        self.save_and_format_source_code()
        return Compiler.try_to_compile(self.is_prog1_included())

    def rollback(self, old_code: str) -> None:
        self.write_source_code(old_code)
        self.reload_source_code()

    def add_line_to(
        self, line: str, where: list[str], add_semicolon=False, inside_main=False
    ) -> bool:
        backup = self.put_together()
        #
        remove_add_exit_code = inside_main
        if inside_main:
            add_semicolon = True
        #
        if add_semicolon:
            line = add_semicolon_if_needed(line)
        #
        ok = self.try_to_add_line(line, where, remove_add_exit_code=remove_add_exit_code)
        if not ok:
            self.rollback(backup)
        #
        return ok

    def build_printf(self, line: str) -> str:
        if "//" in line:
            left, _ = line.split("//")
            line = left.strip()
        #
        left, right = line.split(" ", maxsplit=1)
        return 'printf("{0}\\n", {1}); // tmp'.format(left, right)

    def remove_previous_tmp_lines(self) -> None:
        lines: list[str] = self.get_lines()
        tmp_indexes: list[int] = []
        for idx, line in enumerate(lines):
            if line.endswith("// tmp"):
                tmp_indexes.append(idx)
            #
        #
        if len(tmp_indexes) >= 2:
            tmp_indexes.pop()
            result: list[str] = []
            for idx, line in enumerate(lines):
                if idx in tmp_indexes:
                    continue
                # else
                result.append(line)
            #
            new_src = "\n".join(result)
            self.write_source_code(new_src)
            self.reload_source_code()

    def is_prog1_included(self) -> bool:
        return "prog1.c" in self.compiler_arguments

    def include_prog1(self) -> None:
        line = '#include "prog1.h"'
        if line not in self.include_lines:
            self.include_lines.append(line)
        arg = "prog1.c"
        if arg not in self.compiler_arguments:
            self.compiler_arguments.append(arg)
        FileSystem.copy_prog1()

    def add_stdlib_header(self, header_file: str) -> None:
        line = f"#include <{header_file}>"
        if line not in self.include_lines:
            self.include_lines.append(line)

    def remove_prog1(self) -> None:
        line = '#include "prog1.h"'
        if line in self.include_lines:
            self.include_lines.remove(line)
        arg = "prog1.c"
        if arg in self.compiler_arguments:
            self.compiler_arguments.remove(arg)

    def remove_stdlib_header(self, header_file: str) -> None:
        line = f"#include <{header_file}>"
        if line in self.include_lines:
            self.include_lines.remove(line)

    def contains(self, text) -> bool:
        return text in self.put_together()

    def contains_get_string(self) -> bool:
        return self.contains("get_string(")

    def auto_include(self, line: str) -> None:
        if ("get_string(" in line) or self.contains_get_string():
            self.include_prog1()
        else:
            self.remove_prog1()
        #
        if (text := "time(") in line or self.contains(text):
            self.add_stdlib_header("time.h")
        else:
            self.remove_stdlib_header("time.h")


##############################################################################


class Compiler:
    def __init__(self) -> None:
        self.src: Source = None  # will be set later in self.process()

    def get_compile_cmd(self) -> str:
        cmd = f"{CC} main.c"
        for arg in self.src.compiler_arguments:
            cmd += f" {arg}"
        return cmd

    def compile(self) -> None:
        with ChDir(TMP_DIR):
            cmd = self.get_compile_cmd()
            os.system(cmd)
            assert os.path.isfile("a.out")

    @staticmethod
    def try_to_compile(is_prog1_included: bool = False) -> bool:
        result = True  # OK
        with ChDir(TMP_DIR):
            cmd = f"{CC} main.c"
            if is_prog1_included:
                cmd += " prog1.c"
            exitcode, out, err = process.get_exitcode_stdout_stderr(cmd)
            if exitcode:
                result = False  # didn't compile -> there is an error
                print(err)
            #
        #
        return result

    def execute(self, show_error=False, valgrind=False) -> None:
        with ChDir(TMP_DIR):
            cmd = "./a.out"
            if not show_error:
                if valgrind:
                    cmd = f"{VALGRIND} {cmd}"
                #
                os.system(cmd)
            else:
                if self.src.contains_get_string():
                    os.system(cmd)  # we need interactivity in this case
                else:
                    # if infinite loop happens, this hangs without any output
                    exitcode, out, err = process.get_exitcode_stdout_stderr(cmd)
                    if exitcode and err:
                        print("exit code:", exitcode)
                    if out:
                        print(out)
                    if err:
                        print("err:")
                        print(err)
                    if exitcode and err == "":
                        exitcode, output = process.capture_crash_message(cmd)
                        print("exit code:", exitcode)
                        print(output)
                #
            #
        #

    def process(self, src: Source, show_error=False, valgrind=False) -> None:
        self.src = src
        self.src.save_source_code()
        self.compile()
        self.execute(show_error, valgrind)


##############################################################################


class Parser:
    @staticmethod
    def is_for_loop(line: str) -> bool:
        return line.startswith(("for(", "for ("))

    @staticmethod
    def is_while_loop(line: str) -> bool:
        return line.startswith(("while(", "while ("))

    @staticmethod
    def has_curly_brace(line: str) -> bool:
        return "{" in line

    @staticmethod
    def check_curly_braces(line: str) -> bool:
        cnt = 0
        for c in line:
            if c == "{":
                cnt += 1
            if c == "}":
                cnt -= 1
                if cnt < 0:
                    return False
                #
        #
        return cnt == 0

    @staticmethod
    def check(line: str) -> bool:
        return Parser.check_curly_braces(line)

    @staticmethod
    def add_def_comment(fn_def: str) -> str:
        return re.sub(r"\)\s*?{", r")  // def\n{", fn_def, count=1)


##############################################################################


def print_header() -> None:
    print(f"{chalk.bold('C REPL')} v{VERSION} by Jabba Laci (jabba.laci@gmail.com), 2025")
    print('Type "h" or "help" for more information.')


def print_help(msg: str, commands: list[str], spaces=0) -> None:
    print("{0}: {1}{2}".format(msg, " " * spaces, ", ".join(commands)))


def print_helps(commands: list[str], shortcuts: list[str]) -> None:
    print_help("Commands", commands, spaces=1)
    print_help("Shortcuts", shortcuts)


def main() -> None:
    fs.check_required_commands(REQUIRED_COMMANDS)
    #
    print_header()
    src = Source()
    compiler = Compiler()

    readline.parse_and_bind('"\\C-h": "help\\n"')  # help
    readline.parse_and_bind('"\\C-a": "_ascii\\n"')  # ASCII table
    readline.parse_and_bind('"\\C-e": "_ed\\n"')  # edit main.c
    readline.parse_and_bind('"\\C-r": "_run\\n"')  # execute the program
    readline.parse_and_bind('"\\C-t": "_src\\n"')  # show the source code
    readline.parse_and_bind('"\\C-p": "_py\\n"')  # launch the Python shell
    readline.parse_and_bind('"\\C-v": "_val\\n"')  # execute the program with valgrind

    commands = [
        "qq",  # quit
        "h",  # help
        "help",  # help
        "_load",  # load main.c
        "_save",  # save to main.c
        "_src",  # show the source code
        "_run",  # run the program
        "_err",  # run the program and show the exit code + the error messages
        "_val",  # run the program with valgrind
        "_ed",  # edit main.c
        "_py",  # launch the Python shell
        "_ascii",  # print ASCII table
        "_reset",  # reset main.c
    ]
    shortcuts = [
        "Ctrl + e (edit), r (run), t (list), p (python), v (valgrind), a (ASCII), h (help)"
    ]
    print_helps(commands, shortcuts)

    read_next_line = False
    collected_lines: list[str] = []
    inside_typedef_struct = False
    inside_function_definition = False
    while True:
        prompt = ">>> "
        if read_next_line:
            prompt = "... "
        try:
            inp = input(chalk.blue.bold(prompt)).strip()
        except KeyboardInterrupt:  # Ctrl+c
            print()
            break
        except EOFError:  # Ctrl+d
            print()
            inp = "qq"  # same code must be executed as if we quit with "qq"
        #
        if read_next_line:
            collected_lines.append(inp)
            ok = Parser.check("\n".join(collected_lines))
            if not ok:
                continue
            else:
                snippet = "\n".join(collected_lines)
                read_next_line = False
                collected_lines = []
                if inside_typedef_struct:
                    src.add_line_to(snippet, src.typedef_struct_lines, add_semicolon=True)
                    inside_typedef_struct = False
                elif inside_function_definition:
                    snippet = Parser.add_def_comment(snippet)
                    # print("#", snippet)
                    src.add_line_to(snippet, src.function_definitions)
                    inside_function_definition = False
                else:
                    src.add_line_to(snippet, src.main_body_lines, inside_main=True)
                continue
        #
        src.auto_include(inp)  # ex.: if "get_string(" is present -> include "prog1.h"
        #
        if "//" in inp:
            left, _ = inp.split("//")
            left = left.strip()
            if left == "":
                inp = left
        #
        if inp == "":
            continue
        elif inp == "qq":
            src.save_and_format_source_code()
            print("saved to", src.get_source_code_path())
            break
        elif inp == "_save":
            src.save_and_format_source_code()
            print("saved to", src.get_source_code_path())
        elif inp == "_load":
            fname = src.get_source_code_path()
            if os.path.isfile(fname):
                src.reload_source_code()
                print("loaded")
            else:
                print(f"warning: {fname} not found")
        elif inp in ("h", "help"):
            print_helps(commands, shortcuts)
        elif inp == "_src":
            src.cat()
        elif inp in ("_run", "_err", "_val"):
            if inp == "_run":
                compiler.process(src)
            elif inp == "_val":
                compiler.process(src, valgrind=True)
            elif inp == "_err":
                compiler.process(src, show_error=True)
        # elif inp == "_fmt":
        # src.save_and_format_source_code()
        elif inp == "_ed":  # edit
            src.edit()
        elif inp == "_reset":
            src = Source()
        elif inp.startswith("%"):
            line = src.build_printf(inp)
            if src.add_line_to(line, src.main_body_lines, inside_main=True):
                src.remove_previous_tmp_lines()
                compiler.process(src)
        elif Parser.is_for_loop(inp):  # for (...)
            ok = Parser.check(inp)
            if ok:
                src.add_line_to(inp, src.main_body_lines, inside_main=True)
            else:
                collected_lines.append(inp)
                read_next_line = True
        elif Parser.is_while_loop(inp):  # while (...)
            ok = Parser.check(inp)
            if ok:
                src.add_line_to(inp, src.main_body_lines, inside_main=True)
            else:
                collected_lines.append(inp)
                read_next_line = True
        elif inp.startswith("(def)"):
            inp = inp.removeprefix("(def)")
            ok = Parser.has_curly_brace(inp) and Parser.check(inp)
            if ok:
                inp = Parser.add_def_comment(inp)
                src.add_line_to(inp, src.function_definitions)
            else:
                inside_function_definition = True
                collected_lines.append(inp)
                read_next_line = True
        elif inp.startswith("#include"):
            src.add_line_to(inp, src.include_lines)
        elif inp.startswith("#define "):
            src.add_line_to(inp, src.define_lines)
        elif inp.startswith("typedef "):
            ok = Parser.check(inp)
            if ok:
                src.add_line_to(inp, src.typedef_struct_lines, add_semicolon=True)
            else:
                inside_typedef_struct = True
                collected_lines.append(inp)
                read_next_line = True
        elif inp.startswith("struct "):
            if "{" not in inp:
                src.add_line_to(inp, src.main_body_lines, inside_main=True)
            else:
                ok = Parser.check(inp)
                if ok:
                    src.add_line_to(inp, src.typedef_struct_lines, add_semicolon=True)
                else:
                    inside_typedef_struct = True
                    collected_lines.append(inp)
                    read_next_line = True
                #
            #
        elif inp.startswith(("(g)", "(global)")):
            if inp.startswith("(g)"):
                inp = inp.removeprefix("(g)")
            if inp.startswith("(global)"):
                inp = inp.removeprefix("(global)")
            #
            if inp.strip():
                src.add_line_to(inp, src.global_variable_lines, add_semicolon=True)
        elif inp.startswith(options := ("(p)", "(p3)", "(py)", "(py3)", "(python)", "(python3)")):
            inp = remove_prefix(inp, options).strip()
            cmd = f"""{PYTHON3} -c 'print({inp})'"""
            # print("#", cmd)
            os.system(cmd)
        elif inp in ("_py", "_py3"):
            os.system(PYTHON3)
            print("# C REPL again:")
        elif inp == "_ascii":
            ascii.print_ascii_table()
        else:
            src.add_line_to(inp, src.main_body_lines, inside_main=True)


##############################################################################

if __name__ == "__main__":
    main()
