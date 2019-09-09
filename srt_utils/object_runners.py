import logging
import pathlib
from abc import abstractmethod, ABC

import fabric
import paramiko

import srt_utils.objects as objects
import srt_utils.process as process


logger = logging.getLogger(__name__)


class IObjectRunner(ABC):
    @staticmethod
    @abstractmethod
    def _create_directory(dirpath: pathlib.Path):
        pass

    @classmethod
    @abstractmethod
    def from_config(cls, obj: objects.IObject, config: dict):
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

    def __init__(self, obj: objects.IObject):
        self.obj = obj
        self.runner = process.Process(self.obj.make_args())
        self.is_started = False


    @staticmethod
    def _create_directory(dirpath: pathlib.Path):
        logger.info(f'Creating a directory for saving results: {dirpath}')
        if dirpath.exists():
            logger.info('Directory already exists, no need to create')
            return
        dirpath.mkdir(parents=True)
        logger.info('Created successfully')


    @classmethod
    def from_config(cls, obj: objects.IObject, config: dict=None):
        return cls(obj)


    def start(self):
        """ 
        Raises:
            ValueError
            ProcessNotStarted
        """
        logger.info(f'Starting on-premises: {self.obj}')

        if self.is_started:
            raise ValueError(
                f'Process has been started already: {self.obj}. '
                f'Start can not be done'
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
            ProcessNotStopped
        """
        logger.info(f'Stopping on-premises: {self.obj}, {self.runner}')

        if not self.is_started:
            raise ValueError(
                f'Process has not been started yet: {self.obj}. '
                f'Stop can not be done'
            )

        try:
            self.runner.stop()
        except (ValueError, process.ProcessNotStopped):
            logger.error(f'Failed to stop: {self.obj}, {self.runner}', exc_info=True)
            raise
        
        logger.info(f'Stopped successfully: {self.obj}, {self.runner}')


    def get_status(self):
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

        logger.info('Collected successfully')


class RemoteProcess(IObjectRunner):
    """ TODO """

    def __init__(self, obj, username, host):
        self.obj = obj
        self.username = username
        self.host = host

        self.process = None
        self.is_started = False

    @staticmethod
    def _create_directory(dirpath: str, username: str, host: str):
        logger.info(f'Creating a directory for saving results: {dirpath}')

        try:
            # FIXME: By default Paramiko will attempt to connect to a running 
            # SSH agent (Unix style, e.g. a live SSH_AUTH_SOCK, or Pageant if 
            # one is on Windows). That's why promt for login-password is not 
            # disabled under condition that password is not configured via 
            # connect_kwargs.password
            with fabric.Connection(host=host, user=username) as c:
                # result = c.run(f'rm -rf {results_dir}')
                # if result.exited != 0:
                #     logger.info(f'Not created: {result}')
                #     return
                result = c.run(f'mkdir -p {dirpath}')
                # print(result.succeeded)
                # print(result.failed)
                # print(result.exited)
                # print(result)
                if result.exited != 0:
                    logger.debug(f'Directory has not been created: {dirpath}')
                    raise DirectoryHasNotBeenCreated(f'Username: {username}, host: {host}, dirpath: {dirpath}')
        except paramiko.ssh_exception.SSHException as error:
            logger.info(
                f'Exception occured ({error.__class__.__name__}): {error}. '
                'Check that the ssh-agent has been started.'
            )
            raise
        except TimeoutError as error:
            logger.info(
                f'Exception occured ({error.__class__.__name__}): {error}. '
                'Check that IP address of the remote machine is correct and the '
                'machine is not down.'
            )
            raise

        logger.info(f'Created successfully')

    @classmethod
    def from_config(cls, obj: objects.IObject, config: dict):
        # obj - object (app, hublet) to run
        # config - runner config
        """
        config = {
            'username': 'msharabayko',
            'host': '137.135.161.223',
        }
        """
        return cls(obj, config['username'], config['host'])

    def start(self):
        logger.info(f'Starting remotely via SSH: {self.obj}')

        if self.is_started:
            raise ValueError(f'Process has been started already: {self.obj}, {self.process}')

        if self.obj.dirpath != None:
            self._create_directory(self.obj.dirpath, self.username, self.host)

        args = []
        args += shared.SSH_COMMON_ARGS
        args += [f'{self.username}@{self.host}']
        obj_args = [f'"{arg}"'for arg in self.obj.make_args()]
        args += obj_args
        
        self.process = shared.create_process(args, True)
        self.is_started = True

        logger.info(f'Started successfully: {self.obj}, {self.process}')

    def stop(self):
        # TODO: use get_status method in order to check whether the process is running or not
        # instead of currently implemented logic in cleanup_process
        # TODO: change cleanup function to have only one input - process
        logger.info(f'Stopping remotely via SSH: {self.obj}, {self.process}')

        if not self.is_started:
            raise ValueError(f'Process has not been started yet: {self.obj}')

        shared.cleanup_process((self.obj, self.process))
        logger.info(f'Stopped successfully: {self.obj}, {self.process}')

    def get_status(self):
        # TODO: Adapt process_is_running()
        pass

    def collect_results(self):
        logger.info('Collecting results')
        
        if not self.is_started:
            raise ValueError(f'Process has not been started yet: {self.obj}')

        if self.obj.filepath is None:
            return

        with fabric.Connection(host=self.host, user=self.username) as c:
            result = c.get(self.obj.filepath)
            # TODO: Implement
            # http://docs.fabfile.org/en/1.14/api/core/operations.html
            # http://docs.fabfile.org/en/2.3/api/transfer.html
            
            # if result.exited != 0:
            #     logger.debug(f'Directory has not been created: {dirpath}')
            #     raise DirectoryHasNotBeenCreated(f'Username: {username}, host: {host}, dirpath: {dirpath}')

        # TODO: Implement
        # exit code, stdout, stderr, files
        # download files via scp for SSHSubprocess