# `proclaunch`

> **We launch real OS processes. No shell. No abstraction. No guessing.**

This project provides a minimal interface over C for launching OS processes in Python 2 and 3 and across Windows and Unix, without:

- Invoking a shell
- Relying on Python's overly abstract `subprocess` module.

It uses native system calls via `ctypes` and `msvcrt`:

- `CreateProcessW` etc. on Windows
- `posix_spawnp` etc. on Unix

Wrapped in:

- `proclaunch.nt.Process` for Windows
- `proclaunch.posix.Process` on Unix.

## Quickrun

### Unix Quirks

```
Python 3.12.2 | packaged by conda-forge | (main, Feb 16 2024, 20:50:58) [GCC 12.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from proclaunch.posix import Process
>>> # Literally echoes `$HOME`
...
>>> p1 = Process.from_command_line(r'echo $HOME'); p1.run(); p1.wait()
$HOME
0
>>> p2 = Process.from_command_line(r'echo \$HOME'); p2.run(); p2.wait()
$HOME
0
>>> # Lists the contents of a directory literally named `$HOME`
...
>>> p3 = Process.from_command_line(r'ls "\$HOME"'); p3.run(); p3.wait()
ls: cannot access '$HOME': No such file or directory
2
>>> p4 = Process.from_command_line(r'ls "$HOME"'); p3.run(); p3.wait()
ls: cannot access '$HOME': No such file or directory
2
>>> # Literally echoes `"test" > $file`
...
>>> p5 = Process.from_command_line(r'echo "\"test\"" > $file'); p5.run(); p5.wait()
"test" > $file
0
>>> # Tries to remove a file literally named `*.txt`
...
>>> p6 = Process.from_command_line(r'rm *.txt'); p6.run(); p6.wait()
rm: cannot remove '*.txt': No such file or directory
1
```

### Windows Quirks

On Windows, `echo`, `dir`, `del`, etc. are `cmd.exe`'s **internal commands** and are not executable. Thus, we will run `print_argv.exe`, compiled from the following `print_argv.c`:

```c
#include <stdio.h>

int main(int argc, const char* argv[]) {
    for (int i = 0; i < argc; ++i) {
        printf("argv[%i] = %s\n", i, argv[i]);
    }
    return 0;
}
```

Test run of `proclaunch.nt.Process`:

```
Python 3.4.4 (v3.4.4:737efcadf5a6, Dec 20 2015, 19:28:18) [MSC v.1600 32 bit (Intel)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> from proclaunch.nt import Process
>>> # No `cmd.exe`'s handling of special characters:
...
>>> p1 = Process.from_command_line(u'print_argv %USERNAME%'); p1.run(); p1.wait()
argv[0] = print_argv
argv[1] = %USERNAME%
0
>>> p2 = Process.from_command_line(u'print_argv Hello & print_argv injected'); p2.run(); p2.wait()
argv[0] = print_argv
argv[1] = Hello
argv[2] = &
argv[3] = print_argv
argv[4] = injected
0
>>> p3 = Process.from_command_line(u'print_argv *.txt'); p3.run(); p3.wait()
argv[0] = print_argv
argv[1] = *.txt
0
>>> # But there's still MSVCRT's `GetCommandLine()` at work (note the raw strings below):
...
>>> p4 = Process.from_command_line(r'print_argv "\"\\\""'); p4.run(); p4.wait()
argv[0] = print_argv
argv[1] = "\"
0
>>> p5 = Process.from_command_line(r'print_argv "\\\\\"\""'); p5.run(); p5.wait()
argv[0] = print_argv
argv[1] = \\""
0
>>> p6 = Process.from_command_line(r'print_argv "\"abc\" & \"def\""'); p6.run(); p6.wait()
argv[0] = print_argv
argv[1] = "abc" & "def"
0
>>> # Note that `cmd.exe` would handle the `&` outside of parentheses below:
...
>>> p7 = Process.from_command_line(r'print_argv "\"a&\"b\"c\"d\"\""'); p7.run(); p7.wait()
argv[0] = print_argv
argv[1] = "a&"b"c"d""
0
```

### ⚠ Important Warning: File Descriptor Redirection and Encoding

We pass the **file descriptors** of the opened files for redirection - just as in the Unix C API or the Win32 API (with a file descriptor to file handle conversion).

**The launched process MIGHT NOT respect the encodings you specified when opening the files in text mode - and it is NOT the responsibility of our library to interfere with that.**

This means that **you should always open files in binary mode** (`'rb'`, `'wb'`, etc.) to make that explicit.

#### Example

```
# Runs `coverage` on the script `test.py`
# Reads STDIN from `test_stdin.txt`
# Writes STDOUT and STDERR to `test_stdout.txt`, `test_stderr.txt`
# Saves coverage data to `test_coverage.sqlite3`
from proclaunch.posix import get_env_dict

# Doesn't modify `os.environ`
env_dict = get_env_dict()
env_dict[u'COVERAGE_FILE'] = u'test_coverage.sqlite3'

with open('test_stdin.txt', 'rb') as fp0, open('test_stdout.txt', 'wb') as fp1, open('test_stderr.txt', 'wb') as fp2:
    p = Process.from_command_line(
        u'coverage run test.py',
        env_dict=env_dict,
        stdin_fd=fp0.fileno(),
        stdout_fd=fp1.fileno(),
        stderr_fd=fp2.fileno(),
    )
    p.run()
    p.wait()
```

## Why Use This?

- Like `os.system`:
    - Launch processes from a single Python 2 `unicode` or Python 3 `str` (a list of arguments is also OK).
- Unlike `os.system`:
    - No shell interpretation
    - No variable substitution (`$VAR`, `%VAR%`)
    - No file redirection (`>`, `<`, `>>`)
    - No command chaining (`&&`, `||`, `;`)
    - No wildcards (`*`, `?`)
    - Explicit control over stdio FDs
    - Explicit environment overrides
- Small, transparent library, no `subprocess` complexity:
    - Pure Python + ctypes
    - Learn how to start processes in C
    - Modification-friendly, hack at will

## API Reference

### `get_env_dict()`

Returns the current environment variables as a Unicode dictionary. Does not sync with `os.environ`.

### *classmethod* `Process.from_command_line(command_line, env_dict=None, stdin_fd=None, stdout_fd=None, stderr_fd=None)`

### *classmethod* `Process.from_arguments(arguments, env_dict=None, stdin_fd=None, stdout_fd=None, stderr_fd=None)`

Creates a new process instance.

- `command_line: unicode` or `arguments: List[unicode]`: The command to execute
- `env_dict: Optional[Dict[unicode, unicode]]`: Environment variables dictionary (None for current env)
- `stdin_fd: Optional[int]`: File descriptor for stdin redirection
- `stdout_fd: Optional[int]`: File descriptor for stdout redirection
- `stderr_fd: Optional[int]`: File descriptor for stderr redirection

These class methods provide a platform-independent interface for process creation, abstracting over key OS-specific differences:

- On Windows (NT), process creation via `CreateProcessW` expects a single command line string, not a list of arguments. `from_command_line()` uses this directly, and `from_arguments()` converts the argument list into a properly quoted command line.
- On POSIX systems, process creation via `posix_spawnp` expects a list of arguments (argv). `from_arguments()` uses this directly, and `from_command_line()` safely parses a shell-style command line into arguments.

Always use `from_arguments()` or `from_command_line()` instead of calling `Process(...)` directly.

### `Process.run()`

Starts the process execution.

### `Process.wait() -> int`

Waits for the process to complete. Returns exit code of the process.

### `Process.kill()`

Terminates the process abruptly (`kill(pid, SIGKILL)` on POSIX, `TerminateProcess` on Windows).

I haven't implemented a method to terminate a process gracefully. Overly complex, requires supporting different user models (e.g., console-based apps, GUI-based apps, background services, etc.), especially on Windows.

## Platform Notes

- POSIX:
    - We assume the platform-dependent `sizeof(pid_t) <= sizeof(int64)`, `sizeof(posix_spawn_file_actions_t) <= 256`, `posix_spawnattr_t <= 512`. If this is not the case, please modify the source code of `proclaunch.posix`.

## License

MIT License. Do whatever you want - use this, modify this - but responsibly.
