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
# NOTE: It is important to add "-t" option in order for SSH 
# to transfer SIGINT, SIGTERM signals to the command
# NOTE: It is important to add "-o BatchMode=yes" option 
# in order to disable any kind of promt
# NOTE: It is important to add # "-o ConnectTimeout={SSH_CONNECTION_TIMEOUT}"
# option in case when the server is down not to wait and be able to check 
# quickly that the process has not been started successfully
SSH_COMMON_ARGS = [
    'ssh', 
    '-t',
    '-o', 'BatchMode=yes',
    '-o', f'ConnectTimeout={SSH_CONNECTION_TIMEOUT}',
]


def before_collect_results_checks(
    obj: IObject,
    process: Process,
    collect_results_path: pathlib.Path
):
    """
    Helper function which performs prelimenary checks for `LocalRunner` and
    `RemoteRunner` classes before collecting object results.
    """
    if not process.is_started:
        raise SrtUtilsException(
            f'Process has not been started yet: {obj}. '
            'Can not collect results'
        )

    if not process.is_stopped:
        raise SrtUtilsException(
            f'Process has not been stopped yet: {obj}, {process}. '
            'Can not collect results'
        )

    # It's expected that at this moment directory 
    # self.collect_results_path already exists, because it is created 
    # in SingleExperimentRunner class
    if not collect_results_path.exists():
        raise SrtUtilsException(
            'There was no directory for collecting results created: '
            f'{collect_results_path}. Can not collect results'
        )

    # If an object has filepath equal to None, it means there should be
    # no output file produced
    if obj.filepath == None:
        logger.info('There was no output file expected, nothing to collect')
        return


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

        Config examples are provided in interface implementation.
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
        self.process = Process(self.obj.make_args())


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
            '[LocalRunner] Creating a local directory for saving '
            f'object results: {dirpath}'
        )

        created = create_local_directory(dirpath)

        if not created:
            logger.info(
                '[LocalRunner] Directory already exists, no need to '
                f'create: {dirpath}'
            )


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

        if self.obj.dirpath != None:
            self._create_directory(self.obj.dirpath)

        self.process.start()


    def stop(self):
        logger.info(f'Stopping object on-premises: {self.obj}, {self.process}')
        self.process.stop()


    def collect_results(self):
        """
        Before collecting object results, this function creates a local 
        directory `local` inside self.collect_results_path directory
        where the results produced by the object are copied.
        """
        logger.info(f'Collecting object results: {self.obj}, {self.process}')

        before_collect_results_checks(
            self.obj,
            self.process,
            self.collect_results_path
        )

        # If an object has filepath defined, it means there should be 
        # an output file produced. However it does not mean that the file
        # was created successfully, that's why we check whether the filepath exists.
        if not self.obj.filepath.exists():
            print(self.process.status)
            stdout, stderr = self.process.collect_results()
            raise SrtUtilsException(
                'There was no output file produced by the object: '
                f'{self.obj}, nothing to collect. Process stdout: '
                f'{stdout}. Process stderr: {stderr}'
            )

        # Create 'local' folder to copy produced by the object file 
        # (inside self.collect_results_path directory)
        destination_dir = self.collect_results_path / 'local'
        logger.info(
            'Creating a local directory for copying object '
            f'results: {destination_dir}'
        )
        created = create_local_directory(destination_dir)
        if not created:
            logger.info(
                'Directory already exists, no need to create: '
                f'{destination_dir}'
            )

        # The code below will raise a FileExistsError if destination already exists. 
        # Technically, this copies a file. To perform a move, simply delete source 
        # after the copy is done. Make sure no exception was raised though.

        # In case we have several tasks which is runned locally by 
        # LocalRunner runner and in case the tasks have the same names 
        # for the output files, the result might be overwritten. 
        # That's why we do not delete destination file before, instead
        # we catch FileExistsError exception. That's why it is necessary 
        # to make sure that the file names for different tasks are unique.
        logger.info(f'Copying object results into: {destination_dir}')

        filename = self.obj.filepath.name
        source = self.obj.filepath
        destination = destination_dir / filename

        try:
            with destination.open(mode='xb') as fid:
                fid.write(source.read_bytes())
        except FileExistsError:
            raise SrtUtilsException(
                'The destination file already exists, there might be a '
                f'file created by the other object: {destination}. File '
                f'with object results was not copied: {self.obj.filepath}'
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
                Username on the remote machine to connect througth.
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

        args = []
        args += SSH_COMMON_ARGS
        args += [f'{self.username}@{self.host}']
        obj_args = [f'"{arg}"' if ' ' in arg else f'{arg}' for arg in self.obj.make_args()]
        args += obj_args
        print(args)

        self.process = Process(args, True)


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
                Username on the remote machine to connect througth.
            host:
                IP address of the remote machine to connect.

        Raises:
            SrtUtilsException
        """
        logger.info(
            '[RemoteRunner] Creating a directory for saving object results '
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
                f'Directory has not been created: {dirpath}. Exception '
                f'occured ({error.__class__.__name__}): {error}. Check that '
                'ssh-agent has been started before running the script'
            )
        except TimeoutError as error:
            raise SrtUtilsException(
                f'Directory has not been created: {dirpath}. Exception '
                f'occured ({error.__class__.__name__}): {error}. Check that '
                'IP address of the remote machine is correct and the '
                'machine is not down'
            )

        if result.exited != 0:
            raise SrtUtilsException(f'Directory has not been created: {dirpath}')


    @classmethod
    def from_config(cls, obj: IObject, config: dict):
        """
        Config Example:
            config = {
                'username': 'msharabayko',
                'host': '137.135.161.223',
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

        if self.obj.dirpath != None:
            self._create_directory(
                self.obj.dirpath,
                self.username,
                self.host
            )

        self.process.start()


    def stop(self):
        logger.info(f'Stopping object remotely via SSH: {self.obj}, {self.process}')
        self.process.stop()


    def collect_results(self):
        """
        Before collecting object results, this function creates a local 
        directory `username@host` inside self.collect_results_path directory
        where the results produced by the object are copied.
        """
        logger.info(f'Collecting object results: {self.obj}, {self.process}')

        before_collect_results_checks(
            self.obj,
            self.process,
            self.collect_results_path
        )

        # If an object has filepath defined, it means there should be 
        # an output file produced. However it does not mean that the file
        # was created successfully, that's why we check whether the filepath exists.
        with fabric.Connection(host=self.host, user=self.username) as c:
            if not exists(c, self.obj.filepath):
                stdout, stderr = self.process.collect_results()
                raise SrtUtilsException(
                    'There was no output file produced by the object: '
                    f'{self.obj}, nothing to collect. Process stdout: '
                    f'{stdout}. Process stderr: {stderr}'
                )

        # Create 'username@host' folder to copy produced by the object file 
        # (inside self.collect_results_path directory)
        destination_dir = self.collect_results_path / f'{self.username}@{self.host}'
        logger.info(
            'Creating a local directory for copying object '
            f'results: {destination_dir}'
        )
        created = create_local_directory(destination_dir)
        if not created:
            logger.info(
                'Directory already exists, no need to create: '
                f'{destination_dir}'
            )

        logger.info(f'Copying object results into: {destination_dir}')
        filename = self.obj.filepath.name
        source = self.obj.filepath
        destination = destination_dir / filename

        if destination.exists():
            raise SrtUtilsException(
                'The destination file already exists, there might be a '
                f'file created by the other object: {destination}. File '
                f'with object results was not copied: {self.obj.filepath}'
            )

        # TODO: Implement copying files using rsync
        try:
            # http://docs.fabfile.org/en/2.3/api/transfer.html
            with fabric.Connection(host=self.host, user=self.username) as c:
                result = c.get(source, destination)
        except OSError as error:
            raise SrtUtilsException(
                f'Object results have not been collected: {self.obj.filepath}'
                f'. Exception occured ({error.__class__.__name__}): {error}. '
            )
        except Exception as error:
            logger.info('Most probably paramiko exception')
            raise SrtUtilsException(
                f'Object results have not been collected: {self.obj.filepath}'
                f'. Exception occured ({error.__class__.__name__}): {error}. '
            )