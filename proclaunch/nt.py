# encoding: utf-8
from __future__ import absolute_import, print_function

import ctypes
import ctypes.wintypes
import msvcrt

from proclaunch import NAME_VALUE_PATTERN, ProcessState

# Load `user32`, `kernel32`
user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)


# `STARTUPINFOW` Definition
class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.wintypes.DWORD),
        ("lpReserved", ctypes.wintypes.LPWSTR),
        ("lpDesktop", ctypes.wintypes.LPWSTR),
        ("lpTitle", ctypes.wintypes.LPWSTR),
        ("dwX", ctypes.wintypes.DWORD),
        ("dwY", ctypes.wintypes.DWORD),
        ("dwXSize", ctypes.wintypes.DWORD),
        ("dwYSize", ctypes.wintypes.DWORD),
        ("dwXCountChars", ctypes.wintypes.DWORD),
        ("dwYCountChars", ctypes.wintypes.DWORD),
        ("dwFillAttribute", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("wShowWindow", ctypes.wintypes.WORD),
        ("cbReserved2", ctypes.wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.wintypes.BYTE)),
        ("hStdInput", ctypes.wintypes.HANDLE),
        ("hStdOutput", ctypes.wintypes.HANDLE),
        ("hStdError", ctypes.wintypes.HANDLE),
    ]


STARTF_USESTDHANDLES = 0x100


# `PROCESS_INFORMATION` Definition
class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", ctypes.wintypes.HANDLE),
        ("hThread", ctypes.wintypes.HANDLE),
        ("dwProcessId", ctypes.wintypes.DWORD),
        ("dwThreadId", ctypes.wintypes.DWORD),
    ]


# `GetCurrentProcess` Definition
GetCurrentProcess = kernel32.GetCurrentProcess
GetCurrentProcess.restype = ctypes.wintypes.HANDLE

# `DuplicateHandle` Definition
DuplicateHandle = kernel32.DuplicateHandle
DuplicateHandle.argtypes = [
    ctypes.wintypes.HANDLE,  # hSourceProcessHandle
    ctypes.wintypes.HANDLE,  # hSourceHandle
    ctypes.wintypes.HANDLE,  # hTargetProcessHandle
    ctypes.POINTER(ctypes.wintypes.HANDLE),  # lpTargetHandle
    ctypes.wintypes.DWORD,  # dwDesiredAccess
    ctypes.wintypes.BOOL,  # bInheritHandle
    ctypes.wintypes.DWORD  # dwOptions
]
DuplicateHandle.restype = ctypes.wintypes.BOOL

DUPLICATE_SAME_ACCESS = 0x00000002

# `GetEnvironmentStringsW` Definition
# Declared to return a `void *`, which will be converted into an `int`
GetEnvironmentStringsW = kernel32.GetEnvironmentStringsW
GetEnvironmentStringsW.restype = ctypes.c_void_p

# `FreeEnvironmentStringsW` Definition
# Declared to return a `void *`, which will be converted into an `int`
FreeEnvironmentStringsW = kernel32.FreeEnvironmentStringsW
FreeEnvironmentStringsW.argtypes = [ctypes.c_void_p]
FreeEnvironmentStringsW.restype = ctypes.wintypes.BOOL

# `CreateProcessW` Definition
CreateProcessW = kernel32.CreateProcessW
CreateProcessW.argtypes = [
    ctypes.wintypes.LPCWSTR,  # lpApplicationName
    ctypes.wintypes.LPWSTR,  # lpCommandLine
    ctypes.wintypes.LPVOID,  # lpProcessAttributes
    ctypes.wintypes.LPVOID,  # lpThreadAttributes
    ctypes.wintypes.BOOL,  # bInheritHandles
    ctypes.wintypes.DWORD,  # dwCreationFlags
    ctypes.wintypes.LPVOID,  # lpEnvironment
    ctypes.wintypes.LPCWSTR,  # lpCurrentDirectory
    ctypes.POINTER(STARTUPINFOW),  # lpStartupInfo
    ctypes.POINTER(PROCESS_INFORMATION)  # lpProcessInformation
]
CreateProcessW.restype = ctypes.wintypes.BOOL

# Must set the `CREATE_UNICODE_ENVIRONMENT` flag in `dwCreationFlags`
CREATE_UNICODE_ENVIRONMENT = 0x00000400

# `WaitForSingleObject` Definition
WaitForSingleObject = kernel32.WaitForSingleObject
WaitForSingleObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD]
WaitForSingleObject.restype = ctypes.wintypes.DWORD

INFINITE = -1  # Wait indefinitely
WAIT_OBJECT_0 = 0  # Wait successful

# `GetExitCodeProcess` Definition
GetExitCodeProcess = kernel32.GetExitCodeProcess
GetExitCodeProcess.argtypes = [
    ctypes.wintypes.HANDLE,  # hProcess
    ctypes.POINTER(ctypes.wintypes.DWORD)  # lpExitCode
]
GetExitCodeProcess.restype = ctypes.wintypes.BOOL

STILL_ACTIVE = 259

# `CloseHandle` Definition
CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
CloseHandle.restype = ctypes.wintypes.BOOL

# `GenerateConsoleCtrlEvent` Definition
GenerateConsoleCtrlEvent = kernel32.GenerateConsoleCtrlEvent
GenerateConsoleCtrlEvent.argtypes = [
    ctypes.wintypes.DWORD,  # dwCtrlEvent
    ctypes.wintypes.DWORD  # dwProcessGroupId
]
GenerateConsoleCtrlEvent.restype = ctypes.wintypes.BOOL

# Create the callback function type
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

# `EnumWindows` Definition
EnumWindows = user32.EnumWindows
EnumWindows.argtypes = [WNDENUMPROC, ctypes.wintypes.LPARAM]
EnumWindows.restype = ctypes.wintypes.BOOL

# `GetWindowThreadProcessId` Definition
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowThreadProcessId.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.DWORD)]
GetWindowThreadProcessId.restype = ctypes.wintypes.DWORD

# `GetParent` Definition
GetParent = user32.GetParent
GetParent.argtypes = [ctypes.wintypes.HWND]
GetParent.restype = ctypes.wintypes.HWND

# `PostMessageW` Definition
PostMessageW = user32.PostMessageW
PostMessageW.argtypes = (
    ctypes.wintypes.HWND,  # hWnd
    ctypes.wintypes.UINT,  # Msg
    ctypes.wintypes.WPARAM,  # wParam
    ctypes.wintypes.LPARAM  # lParam
)
PostMessageW.restype = ctypes.wintypes.BOOL

# `TerminateProcess` Definition
TerminateProcess = kernel32.TerminateProcess
TerminateProcess.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.UINT]
TerminateProcess.restype = ctypes.wintypes.BOOL


def get_env_dict():
    _env_block_addr = GetEnvironmentStringsW()

    if not _env_block_addr:
        raise ctypes.WinError(ctypes.get_last_error())

    _env_dict = {}

    _cur_addr = _env_block_addr

    while True:
        # Convert address to LPWSTR (`wchar_t *`)
        _lpwstr = ctypes.cast(_cur_addr, ctypes.c_wchar_p)

        # Get Unicode string
        _entry = _lpwstr.value

        if not _entry:
            break

        _match_or_none = NAME_VALUE_PATTERN.match(_entry)
        if _match_or_none is not None:
            _name = _match_or_none.group(1).upper()
            _value = _match_or_none.group(2)
            _env_dict[_name] = _value

        # Move address forward, +1 for the trailing L'\0'`
        _cur_addr += ctypes.sizeof(ctypes.c_wchar) * (len(_entry) + 1)

    FreeEnvironmentStringsW(_env_block_addr)

    return _env_dict


def escape_double_quotes_and_backslashes_nt(chars):
    """
    Escapes double quotes and backslashes in a string for use in Windows NT command-line arguments.

    This function yields a properly escaped version of the input characters such that:
    - Double quotes (") are escaped by a preceding backslash.
    - Backslashes (\) are doubled when they precede a double quote or the end of the argument.
    - The escaped string is enclosed in double quotes.

    Args:
        chars (Iterable[str]): An iterable of characters representing the argument to be escaped.

    Yields:
        str: Characters of the escaped argument, properly quoted and escaped.
    """
    yield u'"'

    backslashes = []

    for char in chars:
        if char == u'\\':
            backslashes.append(char)
        elif char == u'"':
            # Output double the buffered backslashes
            for bs in backslashes:
                yield bs
            for bs in backslashes:
                yield bs
            backslashes = []

            yield u'\\'
            yield u'"'
        else:
            for bs in backslashes:
                yield bs
            backslashes = []

            yield char

    # Finalize: double remaining backslashes and close quote
    for bs in backslashes:
        yield bs
    for bs in backslashes:
        yield bs

    yield u'"'


def escape_argument_for_command_line_nt(argument):
    """
    Escapes a string argument for safe inclusion in a Windows NT command-line call.

    This wraps the argument in double quotes and ensures that internal quotes and
    backslashes are properly escaped according to Windows command-line parsing rules.

    Args:
        argument (str): The argument string to escape.

    Returns:
        str: A properly escaped and quoted command-line argument.
    """
    return u''.join(escape_double_quotes_and_backslashes_nt(argument))


def join_arguments_to_command_line_nt(arguments):
    """
    Escapes and joins a list of string arguments into a single command-line string
    suitable for Windows NT command execution.

    Args:
        arguments (Iterable[str]): A sequence of argument strings.

    Returns:
        str: A single command-line string with each argument safely escaped and joined by spaces.
    """
    return u' '.join(map(escape_argument_for_command_line_nt, arguments))


class Process:
    @classmethod
    def from_arguments(cls, arguments, env_dict=None, stdin_fd=None, stdout_fd=None, stderr_fd=None):
        command_line = join_arguments_to_command_line_nt(arguments)
        return cls(command_line, env_dict, stdin_fd, stdout_fd, stderr_fd)

    @classmethod
    def from_command_line(cls, command_line, env_dict=None, stdin_fd=None, stdout_fd=None, stderr_fd=None):
        return cls(command_line, env_dict, stdin_fd, stdout_fd, stderr_fd)

    def __init__(self, command_line, env_dict=None, stdin_fd=None, stdout_fd=None, stderr_fd=None):
        self._last_process_state = ProcessState.NOT_INITIALIZED
        self._lp_command_line = None
        self._lp_environment = None
        self._new_stdin_handle = None
        self._new_stdout_handle = None
        self._new_stderr_handle = None
        self._lp_startup_info = None
        self._process_information = None

        # Initialize `self._lp_command_line`
        if not command_line:
            raise ValueError('Empty command line')

        self._lp_command_line = ctypes.wintypes.LPWSTR(command_line)

        # Initialize `self._lp_environment`
        if env_dict is not None:
            environment_entries = []
            for name, value in env_dict.items():
                entry = u'%s=%s' % (name, value)
                if NAME_VALUE_PATTERN.match(entry) is None:
                    raise ValueError('Invalid environment variable name/value `%s`' % entry)

                environment_entries.append(entry)
            environment_entries.append(u'\0')

            self._lp_environment = ctypes.wintypes.LPWSTR(u'\0'.join(environment_entries))

        # Initialize `self._new_stdin_handle`, etc.
        self._use_redirection = stdin_fd is not None or stdout_fd is not None or stderr_fd is not None

        if self._use_redirection:
            stdin_handle = ctypes.wintypes.HANDLE(msvcrt.get_osfhandle(stdin_fd or 0))
            # Duplicate handle to make it inheritable
            self._new_stdin_handle = ctypes.wintypes.HANDLE()
            if not DuplicateHandle(
                    GetCurrentProcess(),
                    stdin_handle,
                    GetCurrentProcess(),
                    ctypes.byref(self._new_stdin_handle),
                    0,
                    True,
                    DUPLICATE_SAME_ACCESS
            ):
                raise ctypes.WinError(ctypes.get_last_error())

            stdout_handle = ctypes.wintypes.HANDLE(msvcrt.get_osfhandle(stdout_fd or 1))
            self._new_stdout_handle = ctypes.wintypes.HANDLE()
            if not DuplicateHandle(
                    GetCurrentProcess(),
                    stdout_handle,
                    GetCurrentProcess(),
                    ctypes.byref(self._new_stdout_handle),
                    0,
                    True,
                    DUPLICATE_SAME_ACCESS
            ):
                raise ctypes.WinError(ctypes.get_last_error())

            stderr_handle = ctypes.wintypes.HANDLE(msvcrt.get_osfhandle(stderr_fd or 2))

            self._new_stderr_handle = ctypes.wintypes.HANDLE()
            if not DuplicateHandle(
                    GetCurrentProcess(),
                    stderr_handle,
                    GetCurrentProcess(),
                    ctypes.byref(self._new_stderr_handle),
                    0,
                    True,
                    DUPLICATE_SAME_ACCESS
            ):
                raise ctypes.WinError(ctypes.get_last_error())

        self._startup_info = STARTUPINFOW()
        self._startup_info.cb = ctypes.sizeof(self._startup_info)
        if self._use_redirection:
            self._startup_info.hStdInput = self._new_stdin_handle
            self._startup_info.hStdOutput = self._new_stdout_handle
            self._startup_info.hStdError = self._new_stderr_handle

            self._startup_info.dwFlags |= STARTF_USESTDHANDLES

        # Initialize `self._process_information`
        self._process_information = PROCESS_INFORMATION()

        # Initialize `self._last_process_state`
        self._last_process_state = ProcessState.INITIALIZED

    def run(self):
        if self._last_process_state != ProcessState.INITIALIZED:
            raise RuntimeError('Cannot run process. Process is not initialized, already running, or terminated.')

        # Call `CreateProcessW`
        success = CreateProcessW(
            None,
            self._lp_command_line,
            None,
            None,
            True,
            CREATE_UNICODE_ENVIRONMENT,
            self._lp_environment,
            None,
            ctypes.byref(self._startup_info),
            ctypes.byref(self._process_information),
        )

        if not success:
            raise ctypes.WinError(ctypes.get_last_error())

        self._last_process_state = ProcessState.RUNNING

    def wait(self):
        if self._last_process_state != ProcessState.RUNNING:
            raise RuntimeError('Cannot wait for the process to complete. Process is not running.')

        # Wait for process to finish
        if WaitForSingleObject(self._process_information.hProcess, INFINITE) != WAIT_OBJECT_0:
            raise ctypes.WinError(ctypes.get_last_error())

        # Get exit code
        exit_code = ctypes.wintypes.DWORD()
        if not GetExitCodeProcess(
                self._process_information.hProcess,
                ctypes.byref(exit_code)
        ):
            raise ctypes.WinError(ctypes.get_last_error())

        self._last_process_state = ProcessState.TERMINATED

        # Close handles safely
        if self._use_redirection:
            if self._new_stdin_handle:
                CloseHandle(self._new_stdin_handle)
            if self._new_stdout_handle:
                CloseHandle(self._new_stdout_handle)
            if self._new_stderr_handle:
                CloseHandle(self._new_stderr_handle)

        if self._process_information.hThread:
            CloseHandle(self._process_information.hThread)
        if self._process_information.hProcess:
            CloseHandle(self._process_information.hProcess)

        return exit_code.value

    def kill(self):
        if self._last_process_state != ProcessState.RUNNING:
            raise RuntimeError('Cannot kill process. Process is not running.')

        # Windows doesn't allow killing a non-existent (exited) or unauthorized process.
        exit_code = ctypes.wintypes.DWORD()
        if not GetExitCodeProcess(
                self._process_information.hProcess,
                ctypes.byref(exit_code)
        ):
            raise ctypes.WinError(ctypes.get_last_error())

        if exit_code == STILL_ACTIVE:
            # Call TerminateProcess with the process handle and exit code
            if not TerminateProcess(self._process_information.hProcess, 1):
                raise ctypes.WinError(ctypes.get_last_error())
        else:
            # Process has already exited; no need to terminate
            # Call WaitForSingleObject instead
            if WaitForSingleObject(self._process_information.hProcess, INFINITE) != WAIT_OBJECT_0:
                raise ctypes.WinError(ctypes.get_last_error())

        self._last_process_state = ProcessState.TERMINATED

        # Close handles safely
        if self._use_redirection:
            if self._new_stdin_handle:
                CloseHandle(self._new_stdin_handle)
            if self._new_stdout_handle:
                CloseHandle(self._new_stdout_handle)
            if self._new_stderr_handle:
                CloseHandle(self._new_stderr_handle)

        if self._process_information.hThread:
            CloseHandle(self._process_information.hThread)
        if self._process_information.hProcess:
            CloseHandle(self._process_information.hProcess)
