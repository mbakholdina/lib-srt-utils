import logging
import pathlib
from abc import abstractmethod, ABC

import fabric
import paramiko
from patchwork.files import exists

from srt_utils.enums import Status
from srt_utils.exceptions import SrtUtilsException
import srt_utils.objects as objects
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


def create_local_directory(dirpath: pathlib.Path):
    logger.info(f'Creating a local directory for saving/copying object results: {dirpath}')
    if dirpath.exists():
        logger.info(f'Directory already exists, no need to create: {dirpath}')
        return
    dirpath.mkdir(parents=True, exist_ok=True)


def get_status(is_started: bool, proc: Process):
    """
    TODO
    """
    if not is_started:
        return Status.idle

    status, _ = proc.status

    if status == Status.idle:
        return Status.idle

    return Status.running


def before_collect_results_checks(
    is_started: bool,
    is_stopped: bool,
    collect_results_path: pathlib.Path,
    obj: objects.IObject,
    process: Process
):
    if not is_started:
        raise SrtUtilsException(
            f'Process has not been started yet: {obj}. '
            'Can not collect results'
        )

    if not is_stopped:
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
    @staticmethod
    @abstractmethod
    def _create_directory(dirpath: pathlib.Path):
        pass

    @classmethod
    @abstractmethod
    def from_config(cls, obj: objects.IObject, config: dict):
        # obj - object (app, hublet) to run
        # config - runner config
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def get_status(self):
        pass

    @abstractmethod
    def collect_results(self):
        pass


class LocalProcess(IObjectRunner):

    def __init__(
        self,
        obj: objects.IObject,
        collect_results_path: pathlib.Path=pathlib.Path('.')
    ):
        """
        TODO
        
        Attributes:
            obj:
                `objects.IObject` object to run.
            collect_results_path:
                `pathlib.Path` directory path where the results produced by 
                the object should be copied.
        """
        self.obj = obj
        self.collect_results_path = collect_results_path
        self.process = Process(self.obj.make_args())
        self.is_started = False
        self.is_stopped = False


    @staticmethod
    def _create_directory(dirpath: pathlib.Path):
        create_local_directory(dirpath)


    @classmethod
    def from_config(cls, obj: objects.IObject, config: dict={}):
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
        """ 
        Raises:
            SrtUtilsException
        """
        logger.info(f'Starting object on-premises: {self.obj}')

        if self.is_started:
            raise SrtUtilsException(
                f'Process has been started already: {self.obj}, {self.process}. '
                f'Start can not be done'
            )

        if self.obj.dirpath != None:
            self._create_directory(self.obj.dirpath)
        
        self.process.start()
        self.is_started = True


    def stop(self):
        """ 
        Raises:
            SrtUtilsException
        """
        logger.info(f'Stopping object on-premises: {self.obj}, {self.process}')

        if not self.is_started:
            raise SrtUtilsException(
                f'Process has not been started yet: {self.obj}. '
                f'Stop can not be done'
            )

        if self.is_stopped:
            return

        self.process.stop()
        self.is_stopped = True


    def get_status(self):
        return get_status(self.is_started, self.process)


    def collect_results(self):
        """
        Raises:
            SrtUtilsException
        """
        logger.info(f'Collecting object results: {self.obj}, {self.process}')

        before_collect_results_checks(
            self.is_started,
            self.is_stopped,
            self.collect_results_path,
            self.obj,
            self.process
        )

        # If an object has filepath defined, it means there should be 
        # an output file produced. However it does not mean that the file
        # was created successfully, that's why we check whether the filepath exists.
        if not self.obj.filepath.exists():
            stdout, stderr = self.process.collect_results()
            raise SrtUtilsException(
                'There was no output file produced by the object: '
                f'{self.obj}, nothing to collect. Process stdout: '
                f'{stdout}. Process stderr: {stderr}'
            )

        # Create 'local' folder to copy produced by the object file 
        # (inside self.collect_results_path directory)
        destination_dir = self.collect_results_path / 'local'
        create_local_directory(destination_dir)

        # The code below will raise a FileExistsError if destination already exists. 
        # Technically, this copies a file. To perform a move, simply delete source 
        # after the copy is done. Make sure no exception was raised though.

        # In case we have several tasks which is runned locally by 
        # LocalProcess runner and in case the tasks have the same names 
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


class RemoteProcess(IObjectRunner):
    """ TODO """

    def __init__(
        self,
        obj: objects.IObject,
        username: str,
        host: str,
        collect_results_path: pathlib.Path=pathlib.Path('.')
    ):
        self.obj = obj
        self.username = username
        self.host = host
        self.collect_results_path = collect_results_path

        args = []
        args += SSH_COMMON_ARGS
        args += [f'{self.username}@{self.host}']
        obj_args = [f'"{arg}"'for arg in self.obj.make_args()]
        args += obj_args

        self.process = Process(args, True)

        self.is_started = False
        self.is_stopped = False


    @staticmethod
    def _create_directory(
        dirpath: str,
        username: str,
        host: str,
        classname: str
    ):
        """
        Create directory on a remote machine via SSH.

        Attributes:
            TODO

        Raises:
            SrtUtilsException
        """
        logger.info(
            f'[{classname}] Creating a directory for saving results remotely '
            f'via SSH. Username: {username}, host: {host}, dirpath: {dirpath}'
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
    def from_config(cls, obj: objects.IObject, config: dict):
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
        """ 
        Raises:
            SrtUtilsException
        """
        logger.info(f'Starting object remotely via SSH: {self.obj}')

        if self.is_started:
            raise SrtUtilsException(
                f'Process has been started already: {self.obj}, {self.process}. '
                f'Start can not be done'
            )

        if self.obj.dirpath != None:
            self._create_directory(
                self.obj.dirpath,
                self.username,
                self.host,
                self.__class__.__name__
            )

        self.process.start()
        self.is_started = True


    def stop(self):
        """ 
        Raises:
            SrtUtilsException
        """
        logger.info(f'Stopping object remotely via SSH: {self.obj}, {self.process}')

        if not self.is_started:
            raise SrtUtilsException(
                f'Process has not been started yet: {self.obj}. '
                f'Stop can not be done'
            )

        if self.is_stopped:
            return

        self.process.stop()
        self.is_stopped = True


    def get_status(self):
        return get_status(self.is_started, self.process)


    # TODO: The implementation is not finished
    def collect_results(self):
        """
        Raises:
            SrtUtilsException
        """
        logger.info(f'Collecting object results: {self.obj}, {self.process}')

        before_collect_results_checks(
            self.is_started,
            self.is_stopped,
            self.collect_results_path,
            self.obj,
            self.process
        )

        # TODO: Check this remotely via SSH
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
        create_local_directory(destination_dir)

        logger.info(f'Copying object results into: {destination_dir}')

        filename = self.obj.filepath.name
        source = self.obj.filepath
        destination = destination_dir / filename
        print(destination)

        with fabric.Connection(host=self.host, user=self.username) as c:
            # the folder tmp_5 should be there
            # result = c.get(self.obj.filepath, '/Users/msharabayko/projects/srt/lib-srt-utils/tmp_5/uhu.pcapng')
            # result = c.get(self.obj.filepath, 'tmp_5/olala.pcapng')

            # result = c.get(self.obj.filepath, f'{dirpath}/olala.pcapng')

            result = c.get(source, destination)
            print(result)

            # TODO: Implement
            # http://docs.fabfile.org/en/1.14/api/core/operations.html
            # http://docs.fabfile.org/en/2.3/api/transfer.html
            
            # if result.exited != 0:
            #     logger.debug(f'Directory has not been created: {dirpath}')
            #     raise DirectoryHasNotBeenCreated(f'Username: {username}, host: {host}, dirpath: {dirpath}')

        # TODO: Implement
        # exit code, stdout, stderr, files
        # download files via scp for SSHSubprocess

        # logger.info('Collected successfully')