import logging
import signal
import subprocess
import sys
import time
import typing

from srt_utils.enums import AutoName, Status
from srt_utils.exceptions import SrtUtilsException


logger = logging.getLogger(__name__)


SSH_CONNECTION_TIMEOUT = 10


class Process:

    def __init__(self, args: typing.List[str], via_ssh: bool=False):
        """
        Helper class to work with Python `subprocess` module.

        Attributes:
            args:
                The arguments used to launch the process.
            via_ssh:
                True/False depending on whether the arguments `args` contain
                SSH related ones.
        """
        self.args = args
        # TODO: change via_ssh to timeouts (for start, for stop - depending on object and 
        # whether it is started via ssh or locally)
        self.via_ssh = via_ssh
        self.process = None
        self.id = None
        self.is_started = False
        self.is_stopped = False


    def __str__(self):
        return f'process id {self.id}'


    @property
    def status(self):
        """
        Get process status.

        Returns:
            A tuple of status and returncode depending on process status.

        Possible combinations:
            (Status.idle, None):
                If the process has not been started yet,
            (Status.running, None):
                If the process has been started successfully and still running
                at the moment of getting status,
            (Status.idle, some returncode):
                If the process has been started successfully, but is not
                running at the moment of getting status.
        """
        if self.process == None:
            return (Status.idle, None)

        if not self.is_started:
            return (Status.idle, None)

        returncode = self.process.poll()
        status = Status.running if returncode is None else Status.idle
        return (status, returncode)


    def start(self):
        """
        Start process.

        Raises:
            SrtUtilsException
        """
        logger.debug(f'Starting process')

        if self.is_started:
            raise SrtUtilsException(
                f'Process has been started already: {self.id}. '
                'Start can not be done'
            )

        try:
            if sys.platform == 'win32':
                self.process = subprocess.Popen(
                    self.args, 
                    stdin =subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=False,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    bufsize=1
                )
            else:
                self.process = subprocess.Popen(
                    self.args, 
                    stdin =subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    #universal_newlines=False,
                    bufsize=1
                )
                self.is_started = True
        except OSError as error:
            raise SrtUtilsException(
                f'Process has not been started: {self.args}. {error}'
            )
    
        # TODO: Adjust timers
        # Check that the process has started successfully and has not terminated
        # because of an error
        if self.via_ssh:
            time.sleep(SSH_CONNECTION_TIMEOUT + 1)
        else:
            # FIXME: Find a better solution, I changed the time from 1 to 5 s,
            # cause it was not enough in case of errors with srt-test-messaging
            # app, e.g. when starting the caller first and there is no listener yet
            # NOTE: A good thing to consider - what would be in case the child process
            # finfishes its work earlier than the time specified (5s). It is
            # important to consider especially in case of fsrt and small files
            # transmission.
            time.sleep(5)

        status, returncode = self.status
        if status == Status.idle and 'netem' not in self.args:
            raise SrtUtilsException(
                f'Process has not been started: {self.args}, returncode: '
                f'{returncode}, stdout: {self.process.stdout.readlines()}, '
                f'stderr: {self.process.stderr.readlines()}'
            )

        self.id = self.process.pid


    def _terminate(self):
        """
        Terminate process.

        Raises:
            SrtUtilsException
        """
        logger.debug(f'Terminating process: {self.id}')

        if not self.is_started:
            raise SrtUtilsException(
                'Process has not been started yet. Terminate can not be done'
            )

        if self.is_stopped:
            return

        status, _ = self.status
        if status == Status.idle:
            return

        logger.debug('Sending SIGINT/CTRL_C_EVENT signal')
        sig = signal.CTRL_C_EVENT if sys.platform == 'win32' else signal.SIGINT
        self.process.send_signal(sig)
        for i in range(3):
            time.sleep(1)
            status, _ = self.status
            if status == Status.idle:
                return

        raise SrtUtilsException(f'Process has not been terminated: {self.id}')


    def _kill(self):
        """
        Kill process.

        Raises:
            SrtUtilsException
        """
        logger.debug(f'Killing process: {self.id}')

        if not self.is_started:
            raise SrtUtilsException(
                'Process has not been started yet. Kill can not be done'
            )

        if self.is_stopped:
            return

        status, _ = self.status
        if status == Status.idle: 
            return

        self.process.kill()
        time.sleep(1)

        status, _ = self.status
        if status == Status.running:
            raise SrtUtilsException(f'Process has not been killed: {self.id}')


    def stop(self):
        """
        Stop process.

        Raises:
            SrtUtilsException
        """
        logger.debug(f'Stopping process: {self.id}')

        if not self.is_started:
            raise SrtUtilsException(
                'Process has not been started yet. Stop can not be done'
            )

        if self.is_stopped:
            return

        # NOTE: There is a problem with terminating processes which use SSH 
        # to run a command on a remote server. The problem is in SSH not 
        # forwarding a signal (e.g., SIGINT, SIGTERM). As a result, SSH session 
        # itself terminates and process.poll() returns None, however 
        # an application started from a command continues to work on a remote server.
        # The solution is to use -t option in order to allocate a pseudo-terminal. 
        # See https://stackoverflow.com/questions/48419781/work-around-ssh-does-not-forward-signal
        # for details. FIXME: Maybe it is reasonable to add additional check in
        # clean-up actions that the process is not running on a remote server
        # ps -A | grep [process_name]

        # FIXME: However, there is a problem with wrong interpretation of carriage 
        # (\r\n) from pseudo-terminal in this case. Check stdout, it is full of b'\r\n'.

        # FIXME: Signals may not work on Windows properly. Might be useful
        # https://stefan.sofa-rockers.org/2013/08/15/handling-sub-process-hierarchies-python-linux-os-x/

        try:
            self._terminate()
        except SrtUtilsException:
            logger.error(f'Failed to terminate process: {self.id}')

            # TODO: (For future) Experiment with this more. If stransmit will not 
            # stop after several terminations, there is a problem, and kill() will
            # hide this problem in this case.
            
            # TODO: (!) There is a problem with tsp, it's actually not killed
            # however process_is_running(process) becomes False

            try:
                self._kill()
            except SrtUtilsException:
                logger.error(f'Failed to kill process: {self.id}')
                raise SrtUtilsException(
                    f'Process has not been stopped: {self.id}'
                )

        self.is_stopped = True


    def collect_results(self):
        """
        Collect process results: stderr, stdout.

        Raises:
            SrtUtilsException
        """
        if not self.is_started:
            raise SrtUtilsException(
                f'Process has not been started yet. '
                f'Can not collect results'
            )

        stdout = self.process.stdout.readlines()
        stderr = self.process.stderr.readlines()

        return stdout, stderr