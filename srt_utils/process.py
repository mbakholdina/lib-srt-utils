import enum
import logging
import signal
import subprocess
import sys
import time

from srt_utils.enums import AutoName


logger = logging.getLogger(__name__)


SSH_CONNECTION_TIMEOUT = 10


@enum.unique
class ProcessStatus(AutoName):
    idle = enum.auto()
    running = enum.auto()


class ProcessNotStarted(Exception):
    pass

class ProcessNotTerminated(Exception):
    pass

class ProcessNotKilled(Exception):
    pass

class ProcessNotStopped(Exception):
    pass


class Process:
    """ TODO """

    def __init__(self, args, via_ssh: bool=False):
        self.args = args
        # TODO: change via_ssh to timeouts (for start, for stop - depending on object and 
        # whether it is started via ssh or locally)
        self.via_ssh = via_ssh

        self.process = None
        self.id = None
        self.is_started = False

    
    def __str__(self):
        return f'process id {self.id}'


    def start(self):
        """ 
        Raises:
            ValueError
            ProcessNotStarted
        """
        logger.debug(f'Starting process')
        if self.is_started:
            raise ValueError(
                f'Process has been started already: {self.id}. '
                f'Start can not be done'
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
        except OSError as e:
            raise ProcessNotStarted(f'{self.args}. Error: {e}')
    
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

        is_running, returncode = self.get_status()
        if not is_running:
            raise ProcessNotStarted(
                f'{self.args}, returncode: {returncode}, '
                f'stdout: {self.process.stdout.readlines()}, '
                f'stderr: {self.process.stderr.readlines()}'
            )
    
        self.id = self.process.pid
        logger.debug(f'Started successfully: {self.id}')


    def _terminate(self):
        logger.debug(f'Terminating process: {self.id}')

        if not self.is_started:
            raise ValueError(
                f'Process has not been started yet. '
                f'Terminate can not be done'
            )

        status, _ = self.get_status()
        if status == ProcessStatus.idle: 
            logger.debug(f'Process is idle, no need to terminate')
            return
        
        sig = signal.CTRL_C_EVENT if sys.platform == 'win32' else signal.SIGINT
        self.process.send_signal(sig)
        for i in range(3):
            time.sleep(1)
            status, _ = self.get_status()
            if status == ProcessStatus.idle: 
                logger.debug(f'Terminated successfully: {self.id}')
                return

        raise ProcessNotTerminated(f'{self.id}')


    def _kill(self):
        logger.debug(f'Killing process: {self.id}')

        if not self.is_started:
            raise ValueError(
                f'Process has not been started yet. '
                f'Kill can not be done'
            )

        status, _ = self.get_status()
        if status == ProcessStatus.idle: 
            logger.debug(f'Process is idle, no need to kill')
            return

        self.process.kill()
        time.sleep(1)

        status, _ = self.get_status()
        if status == ProcessStatus.running:
            raise ProcessNotKilled(f'{self.process.pid}')
            
        logger.debug(f'Killed successfully: {self.id}')


    def stop(self):
        """ 
        Raises:
            ValueError
            ProcessNotStopped
        """
        logger.debug(f'Stopping process: {self.id}')

        if not self.is_started:
            raise ValueError(
                f'Process has not been started yet. '
                f'Stop can not be done'
            )

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
        except ProcessNotTerminated:
            logger.error('Failed to terminate process', exc_info=True)

            # TODO: (For future) Experiment with this more. If stransmit will not 
            # stop after several terminations, there is a problem, and kill() will
            # hide this problem in this case.
            
            # TODO: (!) There is a problem with tsp, it's actually not killed
            # however process_is_running(process) becomes False

            try:
                self._kill()
            except ProcessNotKilled:
                logger.error('Failed to kill process', exc_info=True)
                raise ProcessNotStopped(f'{self.id}')

        logger.debug(f'Stopped successfully: {self.id}')


    def get_status(self):
        """ 
        Returns:
            A tuple of (result, returncode) where 
            - is_running is equal to True if the process is running and False if
            the process has terminated,
            - returncode is None if the process is running and the actual value 
            of returncode if the process has terminated.
        """
        if not self.is_started:
            raise ValueError(
                f'Process has not been started yet. '
                f'Can not get status'
            )

        returncode = self.process.poll()
        status = ProcessStatus.running if returncode is None else ProcessStatus.idle
        return (status, returncode)


    def collect_results(self):
        if not self.is_started:
            raise ValueError(
                f'Process has not been started yet. '
                f'Can not collect results.'
            )

        stdout = self.process.stdout.readlines()
        stderr = self.process.stderr.readlines()

        return stdout, stderr
