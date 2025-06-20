# `proclaunch`

> **We launch real OS processes. No shell. No abstraction. No guessing.**

This project provides a minimal interface over C for launching OS processes in Python 2 and 3 and across NT and POSIX, without:

- Invoking a shell
- Relying on Python's overly abstract `subprocess` module.

It uses native system calls via `ctypes` and `msvcrt`:

- `CreateProcessW` etc. on NT
- `posix_spawnp` etc. on POSIX

Wrapped in:

- `proclaunch.nt.Process` for NT
- `proclaunch.posix.Process` on POSIX.

## Usage Example

### Process Launched

A Python script `print_argv.py`:

```python
from __future__ import print_function
import sys

if __name__ == '__main__':
    for i, arg in enumerate(sys.argv):
        print('sys.argv[%d]=%s' % (i, arg))
```

### NT

```python
from proclaunch.nt import Process

# No `cmd.exe`'s handling of special characters:
p1 = Process.from_command_line(u'python print_argv.py %USERNAME%'); p1.run(); p1.wait()
# sys.argv[0]=print_argv.py
# sys.argv[1]=%USERNAME%

p2 = Process.from_command_line(u'python print_argv.py Hello & python print_argv.py injected'); p2.run(); p2.wait()
# sys.argv[0]=print_argv.py
# sys.argv[1]=Hello
# sys.argv[2]=&
# sys.argv[3]=python
# sys.argv[4]=print_argv.py
# sys.argv[5]=injected

p3 = Process.from_command_line(u'python print_argv.py *.txt'); p3.run(); p3.wait()
# sys.argv[0]=print_argv.py
# sys.argv[1]=*.txt

# But there's still MSVCRT's GetCommandLine at work (note the raw strings below):
p4 = Process.from_command_line(r'python print_argv.py "\"\\\""'); p4.run(); p4.wait()
# sys.argv[0]=print_argv.py
# sys.argv[1]="\"

p5 = Process.from_command_line(r'python print_argv.py "\\\\\"\""'); p5.run(); p5.wait()
# sys.argv[0]=print_argv.py
# sys.argv[1]=\\""

p6 = Process.from_command_line(r'python print_argv.py "\"abc\" & \"def\""'); p6.run(); p6.wait()
# sys.argv[0]=print_argv.py
# sys.argv[1]="abc" & "def"

# Note that `cmd.exe` WOULD handle the `&` outside of parentheses below (we wouldn't)
p7 = Process.from_command_line(r'python print_argv.py "\"a&\"b\"c\"d\"\""'); p7.run(); p7.wait()
# sys.argv[0]=print_argv.py
# sys.argv[1]="a&"b"c"d""
```

### POSIX

```python
from proclaunch.posix import Process

p1 = Process.from_command_line(r'python print_argv.py $HOME'); p1.run(); p1.wait()
# sys.argv[0]=print_argv.py
# sys.argv[1]=$HOME

p2 = Process.from_command_line(r'python print_argv.py \$HOME'); p2.run(); p2.wait()
# sys.argv[0]=print_argv.py
# sys.argv[1]=$HOME

p3 = Process.from_command_line(r'python print_argv.py "\$HOME"'); p3.run(); p3.wait()
# sys.argv[0]=print_argv.py
# sys.argv[1]=$HOME

p4 = Process.from_command_line(r'python print_argv.py "$HOME"'); p4.run(); p4.wait()
# sys.argv[0]=print_argv.py
# sys.argv[1]=$HOME

p5 = Process.from_command_line(r'python print_argv.py "\"test\"" > $file'); p5.run(); p5.wait()
# sys.argv[0]=print_argv.py
# sys.argv[1]="test"
# sys.argv[2]=>
# sys.argv[3]=$file

p6 = Process.from_command_line(r'python print_argv.py *.txt'); p6.run(); p6.wait()
# sys.argv[0]=print_argv.py
# sys.argv[1]=*.txt
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

- On NT, process creation via `CreateProcessW` expects a single command line string, not a list of arguments. `from_command_line()` uses this directly, and `from_arguments()` converts the argument list into a properly quoted command line.
- On POSIX, process creation via `posix_spawnp` expects a list of arguments (argv). `from_arguments()` uses this directly, and `from_command_line()` safely parses a shell-style command line into arguments.

Always use `from_arguments()` or `from_command_line()` instead of calling `Process(...)` directly.

### `Process.run()`

Starts the process execution.

### `Process.wait() -> int`

Waits for the process to complete. Returns exit code of the process.

### `Process.kill()`

Terminates the process abruptly (`TerminateProcess` on NT, `kill(pid, SIGKILL)` on POSIX).

I haven't implemented a method to terminate a process gracefully. Overly complex, requires supporting different user models (e.g., console-based apps, GUI-based apps, background services, etc.), especially on NT.

## Platform Notes

- POSIX:
    - We assume the platform-dependent `sizeof(pid_t) <= sizeof(int64)`, `sizeof(posix_spawn_file_actions_t) <= 256`, `posix_spawnattr_t <= 512`. If this is not the case, please modify the source code of `proclaunch.posix`.

## License

MIT License. Do whatever you want - use this, modify this - but responsibly.
