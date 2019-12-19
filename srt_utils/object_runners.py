import logging
import pathlib
from abc import abstractmethod, ABC

import fabric
import paramiko

import srt_utils.objects as objects
import srt_utils.process as process


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
    logger.info(f'Creating a local directory for saving object results: {dirpath}')
    if dirpath.exists():
        logger.info(f'Directory already exists, no need to create: {dirpath}')
        return
    dirpath.mkdir(parents=True)
    # logger.info('Created successfully')


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
    """ TODO """

    def __init__(self, obj: objects.IObject, collect_results_path: pathlib.Path=pathlib.Path('.')):
        # dirpath (on machine where we run the script) where to collect results
        self.obj = obj
        self.collect_results_path = collect_results_path
        self.runner = process.Process(self.obj.make_args())
        self.is_started = False


    @staticmethod
    def _create_directory(dirpath: pathlib.Path):
        create_local_directory(dirpath)
        # logger.info(f'Creating a directory for saving results: {dirpath}')
        # if dirpath.exists():
        #     logger.info('Directory already exists, no need to create')
        #     return
        # dirpath.mkdir(parents=True)
        # logger.info('Created successfully')


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
            ValueError
            process.ProcessNotStarted
        """
        logger.info(f'Starting object on-premises: {self.obj}')

        if self.is_started:
            raise ValueError(
                f'Process has been started already: {self.obj}. '
                f'Start can not be done.'
            )

        if self.obj.dirpath != None:
            self._create_directory(self.obj.dirpath)
        
        try:
            self.runner.start()
        except (ValueError, process.ProcessNotStarted):
            logger.error(f'Failed to start: {self.obj}', exc_info=True)
            raise

        self.is_started = True

        logger.info(f'Started successfully: {self.obj}, {self.runner}')


    def stop(self):
        """ 
        Raises:
            ValueError
            process.ProcessNotStopped
        """
        logger.info(f'Stopping object on-premises: {self.obj}, {self.runner}')

        if not self.is_started:
            raise ValueError(
                f'Process has not been started yet: {self.obj}. '
                f'Stop can not be done.'
            )

        try:
            self.runner.stop()
        except (ValueError, process.ProcessNotStopped):
            logger.error(f'Failed to stop: {self.obj}, {self.runner}', exc_info=True)
            raise
        
        logger.info(f'Stopped successfully: {self.obj}, {self.runner}')


    def get_status(self):
        """ 
        Raises:
            ValueError
        """
        logger.info(f'Getting status: {self.obj}, {self.runner}')

        if not self.is_started:
            raise ValueError(
                f'Process has not been started yet: {self.obj}. '
                f'Can not get status.'
            )

        status, _ = self.runner.get_status()
        return status


    def collect_results(self):
        logger.info(f'Collecting results: {self.obj}, {self.runner}')
        
        if not self.is_started:
            raise ValueError(
                f'Process has not been started yet: {self.obj}. '
                'Can not collect results.'
            )

        stdout, stderr = self.runner.collect_results()
        # TODO: Implement writing stderr, stdout in files (logs folder)
        print(f'stdout: {stdout}')
        print(f'stderr: {stderr}')

        if not self.collect_results_path.exists():
            print('There was no directory for collecting results created, error')
            # exception
            # it's expected that this directory is already there and created from SingleExpRunner
            return

        # If an object has filepath defined, it means there should an output file
        # however it does not mean that the file was created successfully
        # that's why we check whether the filepath exists
        if self.obj.filepath == None:
            print('There was no output file expected, nothing to collect')
            logger.info('Collected successfully')
            return

        if not self.obj.filepath.exists():
            print('There was no output file created, error')
            # it means that the object has not produce the file, probably because of some error
            # in this case stdout, stderr of the process will be useful
            # exception
            return

        # Create runner folder to copy the results - local - inside the self.collect_results_path dir
        filename = self.obj.filepath.name
        source = self.obj.filepath
        destination_dir = self.collect_results_path / 'local'
        destination = destination_dir / filename
        print(f'destination: {destination}')

        create_local_directory(destination_dir)

        # The code above will raise a FileExistsError if destination already exists. 
        # Technically, this copies a file. To perform a move, simply delete source 
        # after the copy is done (see below). Make sure no exception was raised though.

        # In case we have several tasks which is runned locally and in case the tasks have the same name,
        # the result might be overwritten. That's why we do not delite destination file before,
        # we catch FileExistsError in this case. That's why it is necessary to make unique file names
        # for different tasks
        try:
            with destination.open(mode='xb') as fid:
                fid.write(source.read_bytes())
        except FileExistsError:
            print('The destination file already exists, there might be a file collected by the other task/obj')
            print(f'File was not copied: {self.obj.filepath}')
            # raise exception ?

        # Delete source file (?), might be an option, but not necessary as a start

        logger.info('Collected successfully')


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

        self.runner = process.Process(args, True)
        self.is_started = False


    @staticmethod
    def _create_directory(dirpath: str, username: str, host: str, classname: str):
        """
        Raises:
            DirectoryHasNotBeenCreated
            paramiko.ssh_exception.SSHException
            TimeoutError
        """
        print(type(classname))
        logger.info(
            f'[{classname}] Creating a directory for saving '
            f'results remotely via SSH: {dirpath}'
        )

        try:
            # FIXME: By default Paramiko will attempt to connect to a running 
            # SSH agent (Unix style, e.g. a live SSH_AUTH_SOCK, or Pageant if 
            # one is on Windows). That's why promt for login-password is not 
            # disabled under condition that password is not configured via 
            # connect_kwargs.password
            with fabric.Connection(host=host, user=username) as c:
                # result = c.run(f'rm -rf {dirpath}')
                # if result.exited != 0:
                #     logger.info(f'Not deleted: {result}')
                #     return
                result = c.run(f'mkdir -p {dirpath}')
                if result.exited != 0:
                    logger.error(
                        f'[{classname}] Directory has not been '
                        f'created: {dirpath}'
                    )
                    raise DirectoryHasNotBeenCreated(
                        f'[{classname}] Username: {username}, '
                        f'host: {host}, dirpath: {dirpath}'
                    )
        except paramiko.ssh_exception.SSHException as error:
            logger.info(
                f'[{classname}] Exception occured ({error.__class__.__name__}): {error}. '
                'Check that the ssh-agent has been started.'
            )
            raise
        except TimeoutError as error:
            logger.info(
                f'[{classname}] Exception occured ({error.__class__.__name__}): {error}. '
                'Check that IP address of the remote machine is correct and the '
                'machine is not down.'
            )
            raise

        logger.info(f'[{classname}] Created successfully')


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
            ValueError
            process.ProcessNotStarted
        """
        logger.info(f'Starting object remotely via SSH: {self.obj}')

        if self.is_started:
            raise ValueError(
                f'Process has been started already: {self.obj}. '
                f'Start can not be done.'
            )

        if self.obj.dirpath != None:
            self._create_directory(
                self.obj.dirpath,
                self.username,
                self.host,
                self.__class__.__name__
            )

        try:
            self.runner.start()
        except (ValueError, process.ProcessNotStarted):
            logger.error(f'Failed to start: {self.obj}', exc_info=True)
            raise
        
        self.is_started = True

        logger.info(f'Started successfully: {self.obj}, {self.runner}')


    def stop(self):
        """ 
        Raises:
            ValueError
            process.ProcessNotStopped
        """
        logger.info(f'Stopping object remotely via SSH: {self.obj}, {self.runner}')

        if not self.is_started:
            raise ValueError(
                f'Process has not been started yet: {self.obj}. '
                f'Stop can not be done.'
            )

        try:
            self.runner.stop()
        except (ValueError, process.ProcessNotStopped):
            logger.error(f'Failed to stop: {self.obj}, {self.runner}', exc_info=True)
            raise
        
        logger.info(f'Stopped successfully: {self.obj}, {self.runner}')


    def get_status(self):
        """ 
        Raises:
            ValueError
        """
        logger.info(f'Getting status: {self.obj}, {self.runner}')

        if not self.is_started:
            raise ValueError(
                f'Process has not been started yet: {self.obj}. '
                f'Can not get status'
            )

        status, _ = self.runner.get_status()
        return status


    def collect_results(self):
        logger.info(f'Collecting results: {self.obj}, {self.runner}')
        
        if not self.is_started:
            raise ValueError(
                f'Process has not been started yet: {self.obj}. '
                f'Can not collect results.'
            )

        stdout, stderr = self.runner.collect_results()
        # TODO: Implement writing stderr, stdout in files (logs folder)
        print(f'stdout: {stdout}')
        print(f'stderr: {stderr}')

        # ? or dirpath is None - there can be multiple files
        if self.obj.filepath is None:
            return

        print(self.obj.dirpath)
        print(self.obj.filepath)

        # TODO: All the checks as above



        # Create directory on the local machine
        # TODO: redundant code
        dirpath = pathlib.Path(f'{self.username}@{self.host}')
        print(dirpath)
        logger.info(f'Creating a directory for loading the results: {dirpath}')
        if dirpath.exists():
            logger.info('Directory already exists, no need to create')
            # return
        else:
            dirpath.mkdir(parents=True)
            logger.info('Created successfully')

        with fabric.Connection(host=self.host, user=self.username) as c:
            # the folder tmp_5 should be there
            # result = c.get(self.obj.filepath, '/Users/msharabayko/projects/srt/lib-srt-utils/tmp_5/uhu.pcapng')
            # result = c.get(self.obj.filepath, 'tmp_5/olala.pcapng')
            result = c.get(self.obj.filepath, f'{dirpath}/olala.pcapng')
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

        logger.info('Collected successfully')