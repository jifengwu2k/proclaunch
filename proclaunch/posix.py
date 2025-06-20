# encoding: utf-8
from __future__ import absolute_import, print_function

import ctypes

from split_command_line import split_command_line_posix

from proclaunch import NAME_VALUE_PATTERN, ProcessState

# Load libc of current process
libc = ctypes.CDLL(None, use_errno=True)

# `pid_t` Definition
# Conservative estimate
pid_t = ctypes.c_int64

# `posix_spawn_file_actions_t` Definition
# Conservative estimate
SIZEOF_POSIX_SPAWN_FILE_ACTIONS_T = 256


class posix_spawn_file_actions_t(ctypes.Structure):
    _fields_ = [('_opaque', ctypes.c_char * SIZEOF_POSIX_SPAWN_FILE_ACTIONS_T)]


# `posix_spawnattr_t` Definition
# Conservative estimate
SIZEOF_POSIX_SPAWNATTR_T = 512


class posix_spawnattr_t(ctypes.Structure):
    _fields_ = [('_opaque', ctypes.c_char * SIZEOF_POSIX_SPAWNATTR_T)]


# Standard file descriptors
STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2

# `posix_spawn_file_actions_init` Definition
posix_spawn_file_actions_init = libc.posix_spawn_file_actions_init
posix_spawn_file_actions_init.argtypes = [ctypes.POINTER(posix_spawn_file_actions_t)]
posix_spawn_file_actions_init.restype = ctypes.c_int

# `posix_spawn_file_actions_destroy` Definition
posix_spawn_file_actions_destroy = libc.posix_spawn_file_actions_destroy
posix_spawn_file_actions_destroy.argtypes = [ctypes.POINTER(posix_spawn_file_actions_t)]
posix_spawn_file_actions_destroy.restype = ctypes.c_int

# `posix_spawn_file_actions_adddup2` Definition
posix_spawn_file_actions_adddup2 = libc.posix_spawn_file_actions_adddup2
posix_spawn_file_actions_adddup2.argtypes = [
    ctypes.POINTER(posix_spawn_file_actions_t),
    ctypes.c_int,
    ctypes.c_int,
]
posix_spawn_file_actions_adddup2.restype = ctypes.c_int

# `posix_spawnp` Definition
posix_spawnp = libc.posix_spawnp
posix_spawnp.argtypes = [
    ctypes.POINTER(pid_t),  # pid_t *pid
    ctypes.c_char_p,  # const char *path
    ctypes.POINTER(posix_spawn_file_actions_t),  # const posix_spawn_file_actions_t *file_actions
    ctypes.POINTER(posix_spawnattr_t),  # const posix_spawnattr_t *attrp,
    ctypes.POINTER(ctypes.c_char_p),  # char *const argv[]
    ctypes.POINTER(ctypes.c_char_p),  # char *const envp[]
]
posix_spawnp.restype = ctypes.c_int

# `wait` Definition
wait = libc.wait
wait.argtypes = [ctypes.POINTER(ctypes.c_int)]
wait.restype = pid_t

# `waitpid` Definition
waitpid = libc.waitpid
waitpid.argtypes = [
    pid_t,
    ctypes.POINTER(ctypes.c_int),
    ctypes.c_int
]
waitpid.restype = pid_t


# `WIFEXITED`, `WEXITSTATUS`, `WIFSIGNALED`, `WTERMSIG` Definitions
def WIFEXITED(status):
    return (status & 0x7F) == 0


def WEXITSTATUS(status):
    return (status >> 8) & 0xFF


def WIFSIGNALED(status):
    return ((status & 0x7F) != 0) and ((status & 0x7F) != 0x7F)


def WTERMSIG(status):
    return status & 0x7F


# `strerror` Definition
strerror = libc.strerror
strerror.argtypes = [ctypes.c_int]
strerror.restype = ctypes.c_char_p

# `kill` Definition
kill_ = libc.kill
kill_.argtypes = [pid_t, ctypes.c_int]
kill_.restype = ctypes.c_int


# Read environment via `extern char **environ`
def get_env_dict():
    _environ = ctypes.POINTER(ctypes.c_char_p).in_dll(libc, "environ")

    _env_dict = {}

    i = 0
    while _environ[i]:
        _entry = _environ[i].decode('utf-8')

        match_or_none = NAME_VALUE_PATTERN.match(_entry)
        if match_or_none is not None:
            _name = match_or_none.group(1).upper()
            _value = match_or_none.group(2)
            _env_dict[_name] = _value

        i += 1

    return _env_dict


class Process:
    @classmethod
    def from_arguments(cls, arguments, env_dict=None, stdin_fd=None, stdout_fd=None, stderr_fd=None):
        return cls(arguments, env_dict, stdin_fd, stdout_fd, stderr_fd)

    @classmethod
    def from_command_line(cls, command_line, env_dict=None, stdin_fd=None, stdout_fd=None, stderr_fd=None):
        arguments = list(split_command_line_posix(command_line))
        return cls(arguments, env_dict, stdin_fd, stdout_fd, stderr_fd)

    def __init__(self, arguments, env_dict=None, stdin_fd=None, stdout_fd=None, stderr_fd=None):
        self._last_process_state = ProcessState.NOT_INITIALIZED
        self._path = None
        self._argv = None
        self._envp = None
        self._p_file_actions = None
        self._pid = None

        # Initialize `self._path`, `self._argv`
        encoded_arguments = [argument.encode('utf-8') for argument in arguments]
        encoded_arguments.append(None)

        if len(encoded_arguments) <= 1:
            raise ValueError('Empty command line')

        self._path = ctypes.c_char_p(encoded_arguments[0])

        self._argv = (ctypes.c_char_p * len(encoded_arguments))(*encoded_arguments)

        # Initialize `self._envp`
        if env_dict is not None:
            environment_entries = []
            for name, value in env_dict.items():
                environment_entry = (u'%s=%s' % (name, value)).encode('utf-8')
                environment_entries.append(environment_entry)
            environment_entries.append(None)

            self._envp = (ctypes.c_char_p * len(environment_entries))(*environment_entries)

        # Initialize `self._p_file_actions`
        if stdin_fd is not None or stdout_fd is not None or stderr_fd is not None:
            self._p_file_actions = ctypes.pointer(posix_spawn_file_actions_t())

            if posix_spawn_file_actions_init(self._p_file_actions) != 0:
                posix_spawn_file_actions_destroy(self._p_file_actions)

                errno = ctypes.get_errno()
                raise OSError(errno, "posix_spawn_file_actions_init failed: %s" % strerror(errno).decode('utf-8'))

            if stdin_fd is not None:
                # Redirect stdin -> stdin_fd
                if posix_spawn_file_actions_adddup2(self._p_file_actions, stdin_fd, STDIN_FILENO) != 0:
                    posix_spawn_file_actions_destroy(self._p_file_actions)

                    errno = ctypes.get_errno()
                    raise OSError(errno, "posix_spawn_file_actions_adddup2 (stdin) failed: %s" % strerror(errno).decode(
                        'utf-8'))

            if stdout_fd is not None:
                # Redirect stdout -> stdout_fd
                if posix_spawn_file_actions_adddup2(self._p_file_actions, stdout_fd, STDOUT_FILENO) != 0:
                    posix_spawn_file_actions_destroy(self._p_file_actions)

                    errno = ctypes.get_errno()
                    raise OSError(errno,
                                  "posix_spawn_file_actions_adddup2 (stdout) failed: %s" % strerror(errno).decode(
                                      'utf-8'))

            if stderr_fd is not None:
                # Redirect stderr -> stderr_fd
                if posix_spawn_file_actions_adddup2(self._p_file_actions, stderr_fd, STDERR_FILENO) != 0:
                    posix_spawn_file_actions_destroy(self._p_file_actions)

                    errno = ctypes.get_errno()
                    raise OSError(errno,
                                  "posix_spawn_file_actions_adddup2 (stderr) failed: %s" % strerror(errno).decode(
                                      'utf-8'))

        # Initialize `self._last_process_state`
        self._last_process_state = ProcessState.INITIALIZED

    def run(self):
        if self._last_process_state != ProcessState.INITIALIZED:
            raise RuntimeError('Cannot run process. Process is not initialized, already running, or terminated.')

        # Call `posix_spawnp`
        self._pid = pid_t()

        ret = posix_spawnp(
            ctypes.byref(self._pid),
            self._path,
            self._p_file_actions,
            None,
            self._argv,
            self._envp,
        )

        if ret != 0:
            self._pid = None

            errno = ctypes.get_errno()
            raise OSError(errno, "posix_spawnp failed: %s" % strerror(errno).decode('utf-8'))

        self._last_process_state = ProcessState.RUNNING

    def wait(self):
        if self._last_process_state != ProcessState.RUNNING:
            raise RuntimeError('Cannot wait for the process to complete. Process is not running.')

        # Call waitpid
        status = ctypes.c_int()
        if waitpid(self._pid, ctypes.byref(status), 0) == -1:
            # Return an error and leave the state unchanged
            errno = ctypes.get_errno()
            raise OSError(errno, "waitpid failed: %s" % strerror(errno).decode('utf-8'))

        # Process terminated, update state
        self._last_process_state = ProcessState.TERMINATED

        # Clean up file actions if they were set
        if self._p_file_actions is not None:
            posix_spawn_file_actions_destroy(self._p_file_actions)

        # Decode exit status
        if WIFEXITED(status.value):
            return WEXITSTATUS(status.value)  # Return exit code
        elif WIFSIGNALED(status.value):
            raise OSError('Child killed by signal: %d' % WTERMSIG(status.value))
        else:
            raise OSError("Child terminated abnormally")

    def kill(self):
        if self._last_process_state != ProcessState.RUNNING:
            raise RuntimeError('Cannot kill process. Process is not running.')

        # Send SIGKILL signal to terminate the process
        if kill_(self._pid, 9) != 0:
            # Return an error and leave the state unchanged
            errno = ctypes.get_errno()
            raise OSError(errno, "kill failed: %s" % strerror(errno).decode('utf-8'))

        # Call waitpid to prevent process from becoming zombie
        status = ctypes.c_int()
        if waitpid(self._pid, ctypes.byref(status), 0) == -1:
            # Return an error and leave the state unchanged
            errno = ctypes.get_errno()
            raise OSError(errno, "waitpid failed: %s" % strerror(errno).decode('utf-8'))

        # Process terminated, update state
        self._last_process_state = ProcessState.TERMINATED

        # Clean up file actions if they were set
        if self._p_file_actions is not None:
            posix_spawn_file_actions_destroy(self._p_file_actions)
