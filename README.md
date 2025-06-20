# `ctypes-unicode-proclaunch`

A minimal, robust, and Unicode-aware process launching library using ctypes.

- No:
    - Shell involvement: Arguments are not interpolated or globbed by any shell, ensuring "what you pass is what you
      get".
    - Python `subprocess` abstractions: No `Popen`/`communicate`/`universal_newlines`/encoding drama.
- Yes:
    - Native system call usage for maximum control and correctness.
        - `CreateProcessW` (NT)
        - `fork` and `execve` (POSIX)
    - Unicode on both Python 2 and 3.
    - Fully typed.

## Features

- Precise Process Spawning: Direct system call wrappers, not wrappers around wrappers.
- Escape-proof Argument Passing: Arguments are not interpreted or glob-expanded.
- Full Unicode Support: Give and receive Unicode paths/arguments everywhere.
- Explicit Environment: Can supply a Unicode environment dictionary. Does not mutate global environment variables.
- Handles Redirection: Pass open file descriptors for `stdin`, `stdout`, `stderr` just like with the C API.

## Installation

```bash
pip install ctypes-unicode-proclaunch
```

## Usage

### Process Launched

A Python script `print_argv.py`:

```python
# coding=utf-8
from __future__ import print_function
import sys

if __name__ == '__main__':
    for i, arg in enumerate(sys.argv):
        print('sys.argv[%d]=%s' % (i, arg))
```

### NT

```python
# coding=utf-8
from ctypes_unicode_proclaunch import launch, wait

# No `cmd.exe`'s handling of special characters:
process_handle_1 = launch([u'python', u'print_argv.py', u'%USERNAME%'])
wait(process_handle_1)
# sys.argv[0]=print_argv.py
# sys.argv[1]=%USERNAME%

process_handle_2 = launch([u'python', u'print_argv.py', u'Hello', u'&', u'python', u'print_argv.py', u'injected'])
wait(process_handle_2)
# sys.argv[0]=print_argv.py
# sys.argv[1]=Hello
# sys.argv[2]=&
# sys.argv[3]=python
# sys.argv[4]=print_argv.py
# sys.argv[5]=injected

process_handle_3 = launch([u'python', u'print_argv.py', u'*.txt'])
wait(process_handle_3)
# sys.argv[0]=print_argv.py
# sys.argv[1]=*.txt
```

### POSIX

```python
# coding=utf-8
from ctypes_unicode_proclaunch import launch, wait

pid_1 = launch([u'python', u'print_argv.py', u'$HOME'])
wait(pid_1)
# sys.argv[0]=print_argv.py
# sys.argv[1]=$HOME

pid_2 = launch([u'python', u'print_argv.py', u'"test"', u'>', u'$file'])
wait(pid_2)
# sys.argv[0]=print_argv.py
# sys.argv[1]="test"
# sys.argv[2]=>
# sys.argv[3]=$file

pid_3 = launch([u'python', u'print_argv.py', u'*.txt'])
wait(pid_3)
# sys.argv[0]=print_argv.py
# sys.argv[1]=*.txt
```

### Custom Environment and File Redirection

```python
# coding=utf-8
from ctypes_unicode_proclaunch import launch, wait
from read_unicode_environment_variables_dictionary import read_unicode_environment_variables_dictionary

# Doesn't modify `os.environ`
unicode_environment_variables_dictionary = read_unicode_environment_variables_dictionary()
unicode_environment_variables_dictionary[u'COVERAGE_FILE'] = u'test_coverage.sqlite3'

# We pass the file descriptors of the opened files for redirection.
# Just as in the Unix C API.
# The launched processes DO NOT respect the encodings you specified if you opened the files in text mode.
# This means that you should always open files in binary mode (`'rb'`, `'wb'`, etc.) to make that explicit.
with open('test_stdin.txt', 'rb') as f_0, open('test_stdout.txt', 'wb') as f_1, open('test_stderr.txt', 'wb') as f_2:
    pid_or_process_handle = launch(
        [u'python', u'-m', u'coverage', u'run', u'test.py'],
        environment=unicode_environment_variables_dictionary,
        stdin_file_descriptor=f_0.fileno(),
        stdout_file_descriptor=f_1.fileno(),
        stderr_file_descriptor=f_2.fileno()
    )
    wait(pid_or_process_handle)
```

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).