"""
Description : Python easy shell utilities
Author      : david.ohana@ibm.com
License     : Apache v2
"""

import atexit
import logging
import os
import shlex
import signal
import subprocess
import sys
import time

logger = logging.getLogger(__name__)


class ColorCodes:
    """16 colors ANSI color palette that works with most terminals and terminals emulators."""

    def __init__(self):
        pass

    default = "\x1b[39m"

    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    magenta = "\x1b[35m"
    cyan = "\x1b[36m"
    white = "\x1B[37m"

    bold_black = "\x1b[30;1m"
    bold_red = "\x1b[31;1m"
    bold_green = "\x1b[32;1m"
    bold_yellow = "\x1b[33;1m"
    bold_blue = "\x1b[34;1m"
    bold_magenta = "\x1b[35;1m"
    bold_cyan = "\x1b[36;1m"
    bold_white = "\x1B[37;1m"

    dark_gray = "\x1b[90m"
    light_red = "\x1b[91m"
    light_green = "\x1b[92m"
    light_yellow = "\x1b[93m"
    light_blue = "\x1b[94m"
    light_magenta = "\x1b[95m"
    light_cyan = "\x1b[96m"
    light_white = "\x1B[97m"

    reset = "\x1b[0m"


class ColorizedArgsFormatter(logging.Formatter):
    """
    Log formatter that prints each verbosity level in each own color
    """

    def __init__(self, fmt):
        super(ColorizedArgsFormatter, self).__init__(fmt)
        self.level_to_formatter = {}

        def add_color_format(level, color, _format):
            formatter = logging.Formatter(color + _format + ColorCodes.reset)
            self.level_to_formatter[level] = formatter

        add_color_format(logging.DEBUG, ColorCodes.dark_gray, fmt)
        add_color_format(logging.INFO, ColorCodes.green, fmt)
        add_color_format(logging.WARNING, ColorCodes.yellow, fmt)
        add_color_format(logging.ERROR, ColorCodes.red, fmt)
        add_color_format(logging.CRITICAL, ColorCodes.bold_red, fmt)

    def format(self, record):
        formatter = self.level_to_formatter.get(record.levelno)
        formatted = formatter.format(record)
        return formatted


def init_logging(min_level=logging.DEBUG):
    """
    Initializing logging to stdout with different color per verbosity level
    :param min_level:
        Min level to print
    :return:
        Root logger
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(min_level)
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(ColorizedArgsFormatter("%(message)s"))
    root_logger.addHandler(console_handler)
    return root_logger


def print_color(text, color):
    """Prints text to stdout with ANSI color"""
    print(color + text + ColorCodes.reset)


def is_env_option_set(key, env=os.environ, default=False):
    """Convert an environment key/val into a boolean"""
    env_val = env.get(key) or ""
    env_val = env_val.lower()
    if env_val in ["1", "on", "true", "yes", "y", "t"]:
        return True
    if env_val in ["0", "off", "false", "no", "n", "f"]:
        return False
    return default


class ShellResult:
    def __init__(self):
        self.returncode = None
        self.stdout = None
        self.stderr = None


child_process_ids = set()


def sh(cmd,
       echo_cmd=True,
       echo_cmd_args=False,
       exit_on_fail=True,
       exit_on_timeout=False,
       capture_out=False,
       capture_err=False,
       output_remove_trailing_newlines=True,
       timeout_sec=0,
       timeout_exitcode=88,
       poll_wait_sec=0.1,
       shell=False,
       shell_single_command=True,
       env=None,
       log_process_id=True
       ):
    """
    Executes a command in a child process.

    :param str cmd:
        The command to execute as a single string
    :param bool echo_cmd:
        Print command before executing (imitating shell set -x (xtrace) argument)
    :param bool echo_cmd_args:
        Print command as arguments before executing (only when not in shell mode)
    :param bool exit_on_fail:
        When enabled, script will terminate with exit code of the command when exit code != 0
    :param bool exit_on_timeout:
        When enabled, script will terminate with exit code specified in timeout_exitcode if command execurion
        was not finished in the specified timeout value.
    :param bool capture_out:
        When enabled, command stdout is returned instead of being printed.
    :param bool capture_err:
        When enabled, command stderr is returned instead of being printed.
    :param bool output_remove_trailing_newlines:
        When enabled, captured command output will be cleared from trailing line separators.
        This is typically desired because most of shell commands output ends with linebreak and we don't want it when
        processing the result
    :param int timeout_sec:
        max time to wait until a command execution is complete (child process exits).
        0 means no timeout.
    :param int timeout_exitcode:
        The exit code that the script will end with when timeout occurred and exit_on_timeout is enabled.
    :param int poll_wait_sec:
        Time to wait between polls to check whether command execution already finished. Relevant only for calls
        with timeout enabled.
    :param bool shell:
        Use the shell as the program to execute. This allows using features like pipes in commands, but is
        considered a security risk due to the possibility of shell injection vulnerabilities. Use it only
        if you trust the source of input for the command.
    :param bool shell_single_command:
        In shell mode, treat multiple lines as a single command by adding backslash at
        the end of each line. when disabled, each line will be treated as separate shell command. Note that when
        not in shell mode, single-command is always enabled.
    :param env: test
        A mapping that defines the environment variables for the child process.
        Will use the script environment when not specified.
    :param log_process_id:
        When enabled, ID of child process will be logged at debug level when created and terminated.
    :return:
        ShellResult instance with command exit code and captured output (if enabled)
    """

    cmd = cmd.strip()
    if shell and shell_single_command:
        cmd = cmd.replace("\n", " \\\n")

    if echo_cmd:
        logger.info("+ " + cmd)

    if not shell:
        cmd = shlex.split(cmd)
        if echo_cmd_args:
            logger.info("+ " + str(cmd))

    std_out_param = subprocess.PIPE if capture_out else None
    std_err_param = subprocess.PIPE if capture_err else None

    p = subprocess.Popen(cmd,
                         stdout=std_out_param,
                         stderr=std_err_param,
                         shell=shell,
                         universal_newlines=False,
                         env=env)

    if log_process_id:
        logger.debug("process ID {} created".format(p.pid))

    # register the process ID so that we can terminate it on exit hook
    # if the parent process terminates while still waiting for child process to complete
    # note: child will not be terminated if parent (this) process is killed
    child_process_ids.add(p.pid)

    res = ShellResult()

    timed_out = False
    if timeout_sec == 0:
        p.wait()
    else:
        start_time = time.time()
        while True:
            if p.poll() is not None:
                break
            if 0 < timeout_sec <= time.time() - start_time:
                logger.debug("shell call timeout ({} sec)".format(timeout_sec))
                timed_out = True
                os.kill(p.pid, signal.SIGHUP)
                os.kill(p.pid, signal.SIGTERM)
                break
            time.sleep(poll_wait_sec)

    if log_process_id:
        logger.debug("process ID {} terminated".format(p.pid))

    # child process already terminated, no need to kill it at exit
    child_process_ids.remove(p.pid)

    if p.stdout:
        res.stdout = p.stdout.read().decode()
    if p.stderr:
        res.stderr = p.stderr.read().decode()
    if p.returncode:
        res.returncode = p.returncode

    if output_remove_trailing_newlines:
        if res.stdout:
            res.stdout = res.stdout.rstrip(os.linesep)
        if res.stderr:
            res.stderr = res.stderr.rstrip(os.linesep)

    if exit_on_timeout and timed_out:
        logger.error("shell call timed-out - stopping execution")
        exit(timeout_exitcode)

    if not timed_out and exit_on_fail and p.returncode != 0:
        logger.error("shell call failed with code {} - stopping execution".format(p.returncode))
        exit(p.returncode)

    return res


def input_compatible(prompt=None):
    """
    Get input from stdin, compatible with both python 2.7 and Python 3+
    """
    try:
        input_func = raw_input
    except NameError:
        input_func = input
    # noinspection PyUnboundLocalVariable
    return input_func(prompt)


def yes_or_no(question, yes="y", no="n"):
    """Gets y/n input"""
    prompt = '{} ({}/{}): '.format(question, yes, no)
    answer = input_compatible(prompt)
    print(answer)

    reply = str(answer).lower().strip()
    if reply == yes:
        return True
    if reply == no:
        return False
    else:
        return yes_or_no(question)


# noinspection PyUnresolvedReferences
def kill_child_processes():
    """
    Kills all child processes that were created with sh() and did were not terminated yet.
    """
    for pid in child_process_ids:
        logger.warn("at_exit: killing pid {}".format(pid))
        try:
            os.kill(pid, signal.SIGHUP)
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            # child process may already been terminated,so ignore it
            # note that ProcessLookupError is Python v3.5+ only but
            # Python 2.7 interpreter should just ignore it.
            pass


atexit.register(kill_child_processes)
