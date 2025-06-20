# coding: utf-8
# Copyright (c) 2025 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
import ctypes
from itertools import chain

from escape_nt_command_line_argument import escape_nt_command_line_argument
from find_unicode_executable import find_unicode_executable
from posix_or_nt import posix_or_nt
from read_unicode_environment_variables_dictionary import read_unicode_environment_variables_dictionary
from send_recv_json import recv_json, send_json
from typing import Any, Iterable, Mapping, Optional, Sequence, Text, Tuple

# STDIN_FILENO, STDOUT_FILENO, STDERR_FILENO
STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2

if posix_or_nt() == 'nt':
    import ctypes.wintypes
    import msvcrt

    # Load `user32`, `kernel32`
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)


    # `STARTUPINFOW` Definition
    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ('cb', ctypes.wintypes.DWORD),
            ('lpReserved', ctypes.wintypes.LPWSTR),
            ('lpDesktop', ctypes.wintypes.LPWSTR),
            ('lpTitle', ctypes.wintypes.LPWSTR),
            ('dwX', ctypes.wintypes.DWORD),
            ('dwY', ctypes.wintypes.DWORD),
            ('dwXSize', ctypes.wintypes.DWORD),
            ('dwYSize', ctypes.wintypes.DWORD),
            ('dwXCountChars', ctypes.wintypes.DWORD),
            ('dwYCountChars', ctypes.wintypes.DWORD),
            ('dwFillAttribute', ctypes.wintypes.DWORD),
            ('dwFlags', ctypes.wintypes.DWORD),
            ('wShowWindow', ctypes.wintypes.WORD),
            ('cbReserved2', ctypes.wintypes.WORD),
            ('lpReserved2', ctypes.POINTER(ctypes.wintypes.BYTE)),
            ('hStdInput', ctypes.wintypes.HANDLE),
            ('hStdOutput', ctypes.wintypes.HANDLE),
            ('hStdError', ctypes.wintypes.HANDLE),
        ]


    STARTF_USESTDHANDLES = 0x100


    # `PROCESS_INFORMATION` Definition
    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ('hProcess', ctypes.wintypes.HANDLE),
            ('hThread', ctypes.wintypes.HANDLE),
            ('dwProcessId', ctypes.wintypes.DWORD),
            ('dwThreadId', ctypes.wintypes.DWORD),
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


    def join_arguments_to_nt_command_line(arguments):
        # type: (Iterable[Text]) -> Text
        return u' '.join(map(escape_nt_command_line_argument, arguments))


    def make_environment_block(environment):
        # type: (Mapping[Text, Text]) -> Text
        return u'\0'.join(
            chain(
                (u'%s=%s' % (name, value) for name, value in environment.items()),
                (u'\0',)
            )
        )


    def duplicate_file_handle_of_file_descriptor(file_descriptor):
        # type: (int) -> ctypes.wintypes.HANDLE
        file_handle = msvcrt.get_osfhandle(file_descriptor)
        inheritable = ctypes.wintypes.HANDLE()

        if not DuplicateHandle(
                GetCurrentProcess(),
                file_handle,
                GetCurrentProcess(),
                ctypes.byref(inheritable),
                0,
                True,
                DUPLICATE_SAME_ACCESS
        ):
            raise ctypes.WinError(ctypes.get_last_error())

        return inheritable


    def launch(
            arguments,
            environment=None,
            stdin_file_descriptor=None,
            stdout_file_descriptor=None,
            stderr_file_descriptor=None
    ):
        # type: (Sequence[Text], Optional[Mapping[Text, Text]], Optional[int], Optional[int], Optional[int]) -> ctypes.wintypes.HANDLE
        if len(arguments) == 0:
            raise ValueError('Empty command line')

        command_line = join_arguments_to_nt_command_line(arguments)

        use_redirection = stdin_file_descriptor is not None or stdout_file_descriptor is not None or stderr_file_descriptor is not None

        lp_application_name = None
        lp_command_line = ctypes.create_unicode_buffer(command_line)

        if environment is not None:
            lp_environment = ctypes.create_unicode_buffer(make_environment_block(environment))
        else:
            lp_environment = None

        dw_creation_flags = CREATE_UNICODE_ENVIRONMENT

        startup_info_w = STARTUPINFOW()
        startup_info_w.cb = ctypes.sizeof(STARTUPINFOW)

        if use_redirection:
            h_std_input = duplicate_file_handle_of_file_descriptor(
                stdin_file_descriptor if stdin_file_descriptor is not None else STDIN_FILENO)
            h_std_output = duplicate_file_handle_of_file_descriptor(
                stdout_file_descriptor if stdout_file_descriptor is not None else STDOUT_FILENO)
            h_std_error = duplicate_file_handle_of_file_descriptor(
                stderr_file_descriptor if stderr_file_descriptor is not None else STDERR_FILENO)

            startup_info_w.dwFlags |= STARTF_USESTDHANDLES
            startup_info_w.hStdInput = h_std_input
            startup_info_w.hStdOutput = h_std_output
            startup_info_w.hStdError = h_std_error

            handles_of_file_descriptors_to_close = [h_std_input, h_std_output, h_std_error]
        else:
            handles_of_file_descriptors_to_close = []

        process_information = PROCESS_INFORMATION()

        if not CreateProcessW(
                lp_application_name,
                lp_command_line,
                None,
                None,
                True,
                dw_creation_flags,
                lp_environment,
                None,
                ctypes.byref(startup_info_w),
                ctypes.byref(process_information)
        ):
            # Clean up handles on failure
            for handle in handles_of_file_descriptors_to_close:
                CloseHandle(handle)

            raise ctypes.WinError(ctypes.get_last_error())

        for handle in handles_of_file_descriptors_to_close:
            CloseHandle(handle)
        CloseHandle(process_information.hThread)

        return process_information.hProcess


    def wait(process_handle):
        # type: (ctypes.wintypes.HANDLE) -> int
        if WaitForSingleObject(process_handle, INFINITE) != WAIT_OBJECT_0:
            raise ctypes.WinError(ctypes.get_last_error())

        exit_code = ctypes.wintypes.DWORD()
        if not GetExitCodeProcess(process_handle, ctypes.byref(exit_code)):
            raise ctypes.WinError(ctypes.get_last_error())

        CloseHandle(process_handle)

        return exit_code.value


    def kill(process_handle):
        # type: (ctypes.wintypes.HANDLE) -> None
        exit_code = ctypes.wintypes.DWORD()
        if not GetExitCodeProcess(process_handle, ctypes.byref(exit_code)):
            raise ctypes.WinError(ctypes.get_last_error())

        if exit_code.value == STILL_ACTIVE:
            if not TerminateProcess(process_handle, 1):
                raise ctypes.WinError(ctypes.get_last_error())

        wait(process_handle)


else:
    libc = ctypes.CDLL(None, use_errno=True)


    # WIFEXITED, WEXITSTATUS, WIFSIGNALED, WTERMSIG
    def WIFEXITED(status):
        # type: (int) -> bool
        return (status & 0x7F) == 0


    def WEXITSTATUS(status):
        # type: (int) -> int
        return (status >> 8) & 0xFF


    def WIFSIGNALED(status):
        # type: (int) -> bool
        return ((status & 0x7F) != 0) and ((status & 0x7F) != 0x7F)


    def WTERMSIG(status):
        # type: (int) -> int
        return status & 0x7F


    # pid_t
    pid_t = ctypes.c_int

    # close
    close = libc.close
    close.argtypes = [ctypes.c_int]
    close.restype = ctypes.c_int

    # dup2
    dup2 = libc.dup2
    dup2.argtypes = [ctypes.c_int, ctypes.c_int]
    dup2.restype = ctypes.c_int

    # _exit
    _exit = libc._exit
    _exit.argtypes = [ctypes.c_int]

    # fork
    fork = libc.fork
    fork.restype = pid_t

    # execve
    execve = libc.execve
    execve.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_char_p)]
    execve.restype = ctypes.c_int

    # kill
    kill_ = libc.kill
    kill_.argtypes = [pid_t, ctypes.c_int]
    kill_.restype = ctypes.c_int

    # pipe
    pipe = libc.pipe
    pipe.argtypes = [ctypes.POINTER(ctypes.c_int)]
    pipe.restype = ctypes.c_int

    # read
    read = libc.read
    read.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
    read.restype = ctypes.c_size_t

    # strerror
    strerror = libc.strerror
    strerror.argtypes = [ctypes.c_int]
    strerror.restype = ctypes.c_char_p

    # waitpid
    waitpid = libc.waitpid
    waitpid.argtypes = [
        pid_t,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int
    ]
    waitpid.restype = pid_t

    # write
    write = libc.write
    write.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
    write.restype = ctypes.c_size_t


    def create_pipe():
        # type: () -> Tuple[int, int]
        fds = (ctypes.c_int * 2)()  # Array of 2 integers

        # Create the pipe
        result = pipe(fds)
        if result < 0:
            error_number = ctypes.get_errno()
            raise OSError(error_number, 'pipe failed: %s' % strerror(error_number).decode('utf-8'))

        return fds[0], fds[1]


    def utf_8_c_char_p_array_from_unicode_strings(unicode_strings):
        encoded_unicode_strings = []
        encoded_unicode_strings.extend(unicode_string.encode('utf-8') for unicode_string in unicode_strings)
        encoded_unicode_strings.append(None)

        return (ctypes.c_char_p * len(encoded_unicode_strings))(*encoded_unicode_strings)


    def serialize_to_os_error_json(errno, strerror):
        # type: (int, str) -> Any
        return {"errno": errno, "strerror": strerror}


    def deserialize_from_os_error_json(os_error_json):
        # type: (Any) -> OSError
        return OSError(os_error_json['errno'], os_error_json['strerror'])


    def send_to_pipe(write_fd, data):
        # type: (int, bytes) -> int
        return write(write_fd, data, len(data))


    def recv_from_pipe(read_fd, size):
        # type: (int, int) -> bytes
        string_buffer = ctypes.create_string_buffer(size)
        bytes_read = read(read_fd, string_buffer, size)
        return string_buffer.raw[:bytes_read]


    def launch(
            arguments,
            environment=None,
            stdin_file_descriptor=None,
            stdout_file_descriptor=None,
            stderr_file_descriptor=None
    ):
        # type: (Sequence[Text], Optional[Mapping[Text, Text]], Optional[int], Optional[int], Optional[int]) -> int
        if len(arguments) == 0:
            raise ValueError('Empty command line')

        executable = arguments[0]
        path = next(find_unicode_executable(executable), None)
        if path is None:
            raise ValueError('Cannot find executable %s' % executable)

        remaining_arguments = arguments[1:]

        if environment is None:
            environment = read_unicode_environment_variables_dictionary()

        utf_8_c_char_p_path = ctypes.c_char_p(path.encode('utf-8'))
        utf_8_c_char_p_array_argv = utf_8_c_char_p_array_from_unicode_strings(
            chain([path], remaining_arguments)
        )
        utf_8_c_char_p_array_envp = utf_8_c_char_p_array_from_unicode_strings(
            u'%s=%s' % (name, value)
            for name, value in environment.items()
        )

        read_fd, write_fd = create_pipe()

        pid = fork()

        if pid < 0:
            # fork failed, parent process
            error_number = ctypes.get_errno()
            raise OSError(error_number, 'fork failed: %s' % strerror(error_number).decode('utf-8'))

        if pid == 0:
            # fork succeeded, child process

            # Close read_fd
            close(read_fd)

            # Handle redirection
            for redirected_fd, original_fd in zip(
                    [stdin_file_descriptor, stdout_file_descriptor, stderr_file_descriptor],
                    [STDIN_FILENO, STDOUT_FILENO, STDERR_FILENO]):
                if redirected_fd is not None and redirected_fd != original_fd:
                    if dup2(redirected_fd, original_fd) < 0:
                        error_number = ctypes.get_errno()
                        error_string = 'dup2 failed: %s' % strerror(error_number).decode('utf-8')
                        send_json(
                            lambda data: send_to_pipe(write_fd, data),
                            serialize_to_os_error_json(error_number, error_string)
                        )

                        _exit(1)
                    elif redirected_fd not in [STDIN_FILENO, STDOUT_FILENO, STDERR_FILENO]:
                        close(redirected_fd)

            # Replace with new process
            execve(utf_8_c_char_p_path, utf_8_c_char_p_array_argv, utf_8_c_char_p_array_envp)

            # execvp fails
            error_number = ctypes.get_errno()
            error_string = 'execve failed: %s' % strerror(error_number).decode('utf-8')
            send_json(
                lambda data: send_to_pipe(write_fd, data),
                serialize_to_os_error_json(error_number, error_string)
            )

            _exit(1)

        # fork succeeded, parent process

        # Close write_fd
        close(write_fd)

        # Attempt to recv an OSError JSON
        try:
            os_error_json = recv_json(lambda size: recv_from_pipe(read_fd, size))
            raise deserialize_from_os_error_json(os_error_json)
        except EOFError:
            pass

        return pid


    def wait(pid):
        # type: (int) -> int
        # Call waitpid
        status = ctypes.c_int()
        if waitpid(pid, ctypes.byref(status), 0) < 0:
            # Return an error and leave the state unchanged
            error_number = ctypes.get_errno()
            error_string = 'waitpid failed: %s' % strerror(error_number).decode('utf-8')
            raise OSError(error_number, error_string)

        # Decode exit status
        if WIFEXITED(status.value):
            return WEXITSTATUS(status.value)  # Return exit code
        elif WIFSIGNALED(status.value):
            raise OSError('Child killed by signal: %d' % WTERMSIG(status.value))
        else:
            raise OSError('Child terminated abnormally')


    def kill(pid):
        # type: (int) -> None
        # Send SIGKILL signal to terminate the process
        if kill_(pid, 9) != 0:
            error_number = ctypes.get_errno()
            error_string = 'kill failed: %s' % strerror(error_number).decode('utf-8')
            raise OSError(error_number, error_string)

        # Call waitpid to prevent process from becoming zombie
        status = ctypes.c_int()
        if waitpid(pid, ctypes.byref(status), 0) == -1:
            error_number = ctypes.get_errno()
            error_string = 'waitpid failed: %s' % strerror(error_number).decode('utf-8')
            raise OSError(error_number, error_string)
