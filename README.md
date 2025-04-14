# C REPL

A simple REPL for the C programming language.

## Motivation

Python has an excellent REPL that is very useful
to try something quickly. I always wanted something
similar for the C programming language. If, for instance,
I want to evaluate a simple expression, then why should I
write a complete program?

## Demo

![demo](demo/demo.gif)

## Other Features

You can also use `struct`s and `typedef`s:

```text
>>> typedef struct {
...   int x;
...   int y;
... } Pont;
>>>
>>> Pont a = (Pont){1, 2}
>>> %d a.x
1
>>> %d a.y
2
```

A Python shell is also available if you need it.
Quit from the Python shell with `Ctrl + d`.

```text
>>> _py
Python 3.13.2 (main, Feb  5 2025, 08:05:21) [GCC 14.2.1 20250128] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> 2 ** 31 - 1
2147483647
>>>
# C REPL again:
>>> long n = 2147483647
>>> %ld n
2147483647
```

You can also use a Python one-liner:

```text
>>> (p) hex(2025)
0x7e9
>>> string s = "0x7e9"
>>> %s s
0x7e9
```

You can also write `while` loops:

```text
>>> int i = 0
>>> while (i < 3) {
...   puts("hello");
...   ++i;
... }
>>> _run
hello
hello
hello
```

It's also possible to check for memory leaks with `valgrind`:

```text
>>> _reset
>>> char *p = malloc(10)
>>> _val
...
==318347== HEAP SUMMARY:
==318347==     in use at exit: 10 bytes in 1 blocks
==318347==   total heap usage: 1 allocs, 0 frees, 10 bytes allocated
...
```

To simplify reading a text from the keyboard,
you can use a "built-in" function called `get_string()`:

```text
>>> string s = get_string("Name: ")
>>> printf("Hello %s!\n", s)
>>>
>>> _run
Name: Laszlo
Hello Laszlo!
```

If you use this function, then the necessary header
file (`prog1.h`) will be auto-included.

## Notes

When I generate the C source code, I add some special
comments (e.g. `// tmp`, `// def`). I need those
comments when I read the modified source code. When
you edit the C code with a text editor, I need to parse
and re-read the whole source code. These special comments
are there to facilitate the parsing. **So don't delete these comments!**

## Installation

I highly encourage using the [uv](https://docs.astral.sh/uv/) package manager. Then, it's enough
to just start `./start.sh`, which will **(1)** create
a virt. env. for you, and then **(2)** start the project.

For Debian-based distros, I made an installer script (`setup.sh`).
Before executing it, verify its content. It installs the uv
package manager via pipx, and it also installs some external
programs that are used by C REPL (e.g. `gcc`, `valgrind`, etc.).

Once everything is installed, just start the launcher script:

```shell
$ ./start.sh
```

## Supported Platforms

Tested on Linux only.

The program uses several external Linux commands.
They are collected in named constants at the beginning
of the source code. Make sure that they are all installed
on your system (e.g. `gcc`, `valgrind`, etc.)
