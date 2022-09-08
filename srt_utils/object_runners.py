""" The module with IObjectRunner interface and its implementations. """
import logging
import pathlib
from abc import abstractmethod, ABC

import fabric
import paramiko
from patchwork.files import exists

from srt_utils.common import create_local_directory
from srt_utils.enums import Status
from srt_utils.exceptions import SrtUtilsException
from srt_utils.objects import IObject
from srt_utils.process import Process


logger = logging.getLogger(__name__)


SSH_CONNECTION_TIMEOUT = 10
# NOTE: It is important to add "-tt" option in order for subprocess to be
# able to pass SIGINT, SIGTERM signals to the command running remotely.
# Before "-t" option was used, experiments showed that "-t" option does not
# necessarily guarantee the allocation of pseudo-terminal which leads to
# SIGINT not being passed to the command launched on the remote machine.
# Replacing "-t" to "-tt" option which forces pseudo-tty allocation even 
# if SSH has no local tty solves the problem
# NOTE: It is important to add "-o BatchMode=yes" option 
# in order to disable any kind of promt
# NOTE: It is important to add # "-o ConnectTimeout={SSH_CONNECTION_TIMEOUT}"
# option in case when the server is down not to wait and be able to check 
# quickly that the process has not been started successfully
SSH_COMMON_ARGS = [
    'ssh', 
    '-tt',
    '-o', 'BatchMode=yes',
    '-o', f'ConnectTimeout={SSH_CONNECTION_TIMEOUT}',
]


def before_collect_results_checks(
    obj: IObject,
    process: Process,
    collect_results_path: pathlib.Path
):
    """
    Helper function which performs preliminary checks for `LocalRunner` and
    `RemoteRunner` classes before collecting object artifacts.
    """
    if not process.is_started:
        raise SrtUtilsException(
            f'Process has not been started yet: {obj}. '
            'Can not collect artifacts'
        )

    if not process.is_stopped:
        raise SrtUtilsException(
            f'Process has not been stopped yet: {obj}, {process}. '
            'Can not collect artifacts'
        )

    # It's expected that at this moment directory 
    # self.collect_results_path already exists, because it is created 
    # in SingleExperimentRunner class
    if not collect_results_path.exists():
        raise SrtUtilsException(
            'There was no directory for collecting experiment results created: '
            f'{collect_results_path}. Can not collect artifacts'
        )


class IObjectRunner(ABC):
    """
    Object Runner interface.

    Object here represents 1) a single application, e.g., tshark or any test
    application like srt-live-transmit, srt-xtransmit, etc.; or 2) a hublet,
    or 3) whatever we might need to run in future setups.
    
    Runner represents a way of running an object, e.g., locally or on a remote
    machine via SSH using Python library `subprocess`, etc.
    """

    @property
    @abstractmethod
    def status(self) -> Status:
        """
        Object runner status.

        Returns:
            `Status.idle`:
                If object runner has not been started yet,
                Or if object runner has been started successfully, but the 
                object is not running at the moment of getting status.
            `Status.running`:
                If object runner has been started successfully and the object 
                is still running at the moment of getting status.
        """
        pass


    @classmethod
    @abstractmethod
    def from_config(cls, obj: IObject, config: dict):
        """
        Create `IObjectRunner` instance from config.

        Attributes:
            obj:
                `IObject` object to run.
            config:
                Runner config.

        Config examples are provided in interface implementations.
        """
        pass


    @abstractmethod
    def start(self):
        """
        Start object.

        Raises:
            SrtUtilsException
        """
        pass


    @abstractmethod
    def stop(self):
        """
        Stop object.

        Raises:
            SrtUtilsException
        """
        pass


    @abstractmethod
    def collect_results(self):
        """
        Collect object results.

        Raises:
            SrtUtilsException
        """
        pass


class LocalRunner(IObjectRunner):

    def __init__(
        self,
        obj: IObject,
        collect_results_path: pathlib.Path=pathlib.Path('.')
    ):
        """
        Runner used to run the object locally using Python
        `subprocess` library.

        Attributes:
            obj:
                `IObject` object to run.
            collect_results_path:
                `pathlib.Path` directory path where the results produced by 
                the object should be copied once the object finishes its work.
        """
        self.obj = obj
        self.collect_results_path = collect_results_path
        self.args = self.obj.make_args()
        self.process = Process(self.args)


    @property
    def status(self):
        status, _ = self.process.status
        return status


    @staticmethod
    def _create_directory(dirpath: pathlib.Path):
        """
        Create local directory for saving object results before 
        starting the object.

        Attributes:
            dirpath:
                `pathlib.Path` directory path.
        """
        logger.info(
            '[LocalRunner] Creating local directory for saving object '
            f'artifacts: {dirpath}'
        )

        _ = create_local_directory(dirpath)


    @classmethod
    def from_config(cls, obj: IObject, config: dict={}):
        """
        Config Example:
            config = {
                'collect_results_path': '_results_exp'      # optional
            }
        """
        if 'collect_results_path' in config:
            return cls(obj, pathlib.Path(config['collect_results_path']))

        return cls(obj)


    def start(self):
        logger.info(f'Starting object on-premises: {self.obj}')
        logger.info(f'Arguments for LocalRunner: {self.obj.make_args()}')

        for filepath in self.obj.artifacts:
            self._create_directory(filepath.parent)

        self.process.start()


    def stop(self):
        logger.info(f'Stopping object on-premises: {self.obj}, {self.process}')
        self.process.stop()


    def collect_results(self):
        """
        Before collecting object artifacts, this function creates a local 
        directory `local` inside self.collect_results_path directory
        where the results produced by the object are copied.
        """
        logger.info(f'Collecting object artifacts: {self.obj}, {self.process}')

        before_collect_results_checks(
            self.obj,
            self.process,
            self.collect_results_path
        )

        if self.obj.artifacts is []:
            logger.info('There were no artifacts expected, nothing to collect')
            return

        # Create 'local' folder to copy produced by the object file 
        # (inside self.collect_results_path directory)
        destination_dir = self.collect_results_path / 'local'
        logger.info(
            'Creating local directory for saving object artifacts: '
            f'{destination_dir}'
        )
        _ = create_local_directory(destination_dir)

        # The code below will raise a FileExistsError if destination already exists. 
        # Technically, this copies a file. To perform a move, simply delete source 
        # after the copy is done. Make sure no exception was raised though.

        # In case we have several tasks which are run locally by 
        # LocalRunner runner and in case the tasks have the same names 
        # for the output files, the result might be overwritten. 
        # That's why we do not delete destination file before, instead
        # we catch FileExistsError exception. That's why it is necessary 
        # to make sure that the file names for different tasks are unique.

        for filepath in self.obj.artifacts:
            logger.info(f'Saving file: {filepath} into: {destination_dir}')

            # Check if the file exists on a local machine
            if not filepath.exists():
                stdout, stderr = self.process.collect_results()
                logger.warning(
                    f'File {filepath} was not created by the object: '
                    f'{self.obj}, nothing to collect. Process stdout: '
                    f'{stdout}. Process stderr: {stderr}'
                )
                continue

            destination = destination_dir / filepath.name

            try:
                with destination.open(mode='xb') as fid:
                    fid.write(filepath.read_bytes())
            except FileExistsError:
                logger.error(
                    'The destination file already exists, there might be a '
                    f'file created by another object: {destination}. File '
                    f'with object results was not copied: {filepath}'
                )

        # TODO: (?) Delete source file, might be an option, but not necessary at the start


class RemoteRunner(IObjectRunner):

    def __init__(
        self,
        obj: IObject,
        username: str,
        host: str,
        collect_results_path: pathlib.Path=pathlib.Path('.')
    ):
        """
        Runner used to run the object remotely via SSH using Python
        `subprocess` library.

        Attributes:
            obj:
                `IObject` object to run.
            username:
                Username on the remote machine to connect through.
            host:
                IP address of the remote machine to connect.
            collect_results_path:
                `pathlib.Path` directory path where the results produced by 
                the object should be copied once the object finishes its work.
        """
        self.obj = obj
        self.username = username
        self.host = host
        self.collect_results_path = collect_results_path
        
        self.args = []
        self.args += SSH_COMMON_ARGS
        self.args += [f'{self.username}@{self.host}']
        self.args += [self.obj.make_str()]

        self.process = Process(self.args, True)


    @property
    def status(self):
        status, _ = self.process.status
        return status


    @staticmethod
    def _create_directory(
        dirpath: str,
        username: str,
        host: str
    ):
        """
        Create directory on a remote machine via SSH for saving object 
        results before starting the object.

        Attributes:
            dirpath:
                `pathlib.Path` directory path.
            username:
                Username on the remote machine to connect through.
            host:
                IP address of the remote machine to connect.

        Raises:
            SrtUtilsException
        """
        logger.info(
            '[RemoteRunner] Creating directory for saving object artifacts '
            f'remotely via SSH. Username: {username}, host: {host}, '
            f'dirpath: {dirpath}'
        )

        try:
            # FIXME: By default Paramiko will attempt to connect to a running 
            # SSH agent (Unix style, e.g. a live SSH_AUTH_SOCK, or Pageant if 
            # one is on Windows). That's why promt for login-password is not 
            # disabled under condition that password is not configured via 
            # connect_kwargs.password
            with fabric.Connection(host=host, user=username) as c:
                result = c.run(f'mkdir -p {dirpath}')
        except paramiko.ssh_exception.SSHException as error:
            raise SrtUtilsException(
                f'Directory was not created: {dirpath}. Exception '
                f'occurred ({error.__class__.__name__}): {error}. Check that '
                'ssh-agent has been started before running the script'
            )
        except TimeoutError as error:
            raise SrtUtilsException(
                f'Directory was not created: {dirpath}. Exception '
                f'occurred ({error.__class__.__name__}): {error}. Check that '
                'IP address of the remote machine is correct and the '
                'machine is not down'
            )

        if result.exited != 0:
            raise SrtUtilsException(f'Directory was not created: {dirpath}')


    @classmethod
    def from_config(cls, obj: IObject, config: dict):
        """
        Config Example:
            config = {
                'username': 'msharabayko',
                'host': '10.129.10.91',
                'collect_results_path': '_results_exp'      # optional
            }
        """
        if 'collect_results_path' in config:
            return cls(
                obj,
                config['username'],
                config['host'],
                pathlib.Path(config['collect_results_path'])
            )

        return cls(obj, config['username'], config['host'])


    def start(self):
        logger.info(f'Starting object remotely via SSH: {self.obj}')
        logger.info(f'Arguments for RemoteRunner: {self.args}')

        for filepath in self.obj.artifacts:
            self._create_directory(
                filepath.parent,
                self.username,
                self.host
            )

        self.process.start()


    def stop(self):
        logger.info(f'Stopping object remotely via SSH: {self.obj}, {self.process}')
        self.process.stop()


    def collect_results(self):
        """
        Before collecting object artifacts, this function creates a local 
        directory `username@host` inside self.collect_results_path directory
        where the results produced by the object are copied.
        """
        logger.info(f'Collecting object artifacts: {self.obj}, {self.process}')

        before_collect_results_checks(
            self.obj,
            self.process,
            self.collect_results_path
        )

        if self.obj.artifacts is []:
            logger.info('There were no artifacts expected, nothing to collect')
            return

        # Create 'username@host' folder to copy produced by the object files
        # (inside self.collect_results_path directory)
        destination_dir = self.collect_results_path / f'{self.username}@{self.host}'
        logger.info(
            'Creating local directory for saving object artifacts: '
            f'{destination_dir}'
        )
        _ = create_local_directory(destination_dir)

        logger.info(f'Saving object artifacts into: {destination_dir}')

        for filepath in self.obj.artifacts:
            logger.info(f'Saving file: {filepath}')

            # Check if the file exists on a remote machine
            with fabric.Connection(host=self.host, user=self.username) as c:
                if not exists(c, filepath):
                    stdout, stderr = self.process.collect_results()
                    logger.warning(
                        f'File {filepath} was not created by the object: '
                        f'{self.obj}, nothing to collect. Process stdout: '
                        f'{stdout}. Process stderr: {stderr}'
                    )
                    continue

            # Check if there is no file with the same name on the local machine
            destination = destination_dir / filepath.name

            if destination.exists():
                logger.warning(
                    'A file with the same name already exists. This might be a '
                    f'file created by another object: {destination}. File '
                    f'with object results was not copied: {filepath}'
                )
                continue

            # TODO: Implement copying files using rsync
            try:
                # http://docs.fabfile.org/en/2.3/api/transfer.html
                with fabric.Connection(host=self.host, user=self.username) as c:
                    _ = c.get(filepath, destination)
            except OSError as error:
                logger.error(
                    f'File {filepath} was not saved. '
                    f'Exception occurred ({error.__class__.__name__}): {error}. '
                )
            except Exception as error:
                logger.error('Most probably paramiko exception')
                logger.error(
                    f'File {filepath} was not saved. '
                    f'Exception occurred ({error.__class__.__name__}): {error}. '
                )