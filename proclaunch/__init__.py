# coding: utf-8
import re

# To remove environment variables like `u'=::=::\\'`
NAME_VALUE_PATTERN = re.compile(u'^([^\\s=]+)=(.*)$')


class ProcessState:
    NOT_INITIALIZED = 0
    INITIALIZED = 1
    RUNNING = 2
    TERMINATED = 3
