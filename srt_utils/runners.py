import logging
import pathlib
import time

from srt_utils.exceptions import SrtUtilsException
import srt_utils.objects as objects
import srt_utils.object_runners as object_runners
import srt_utils.process as process
from srt_utils.logutils import ContextualLoggerAdapter


# LOGGER = logging.getLogger(__name__)
logger = logging.getLogger(__name__)


class RunnersException(Exception):
    pass


### Simple Factory ###

class SimpleFactory:

    def create_object(self, obj_type: str, obj_config: dict) -> objects.IObject:
        obj = None

        if obj_type == 'tshark':
            obj = objects.Tshark.from_config(obj_config)
        elif obj_type == 'srt-test-messaging':
            obj = objects.SrtTestMessaging.from_config(obj_config)
        else:
            print('No matching object found')

        return obj

    def create_runner(self, obj, runner_type: str, runner_config: dict) -> object_runners.IObjectRunner:
        runner = None

        if runner_type == 'subprocess':
            runner = object_runners.LocalProcess.from_config(obj, runner_config)
        elif runner_type == 'ssh-subprocess':
            runner = object_runners.RemoteProcess.from_config(obj, runner_config)
        else:
            print('No matching runner found')

        return runner


# TODO: Use attrs here
class Task:

    def __init__(self, name: str, obj: objects.IObject, obj_runner: object_runners.IObjectRunner, config: dict):
        # TODO: Check config for validity
        self.name = name
        self.obj = obj
        self.obj_runner = obj_runner
        self.sleep_after_start = config['sleep_after_start']
        self.sleep_after_stop = config['sleep_after_stop']
        self.stop_order = config['stop_order']


### ITestRunner -> SingleExperimentRunner, TestRunner, CombinedTestRunner ###
# The methods will be similar to IRunner

class SingleExperimentRunner:

    def __init__(self, config: dict):
        self.factory = SimpleFactory()
        # TODO: Check config for validaty - use some json tools: 
        # tasks should have unique keys, there should be at least one task defined,
        # etc. Raise exception in case of problems.
        self.config = config

        # TODO: Add attributes from config
        self.collect_results_path = pathlib.Path(self.config['collect_results_path'])
        self.ignore_stop_order = self.config['ignore_stop_order']

        # TODO: Create a class for task: obj, obj_runner, sleep_after_stop, stop_order
        self.tasks = []

        for task_key, task_config in self.config['tasks'].items():
            print(task_key)
            name = 'task-' + task_key
            obj = self.factory.create_object(task_config['obj_type'], task_config['obj_config'])
            runner_config = task_config['runner_config']
            runner_config['collect_results_path'] = self.collect_results_path
            # change task_config as well
            print(runner_config)
            obj_runner = self.factory.create_runner(obj, task_config['runner_type'], runner_config)
            self.tasks += [Task(name, obj, obj_runner, task_config)]

        self.is_started = False
        self.is_stopped = False

        # self.log = ContextualLoggerAdapter(LOGGER, {'context': type(self).__name__})


    @staticmethod
    def _create_directory(dirpath: pathlib.Path, classname: str):
        """
        Create a local directory for saving experiment results.

        Raises:
            SrtUtilsException
        """
        logger.info(f'[{classname}] Creating a local directory for saving experiment results: {dirpath}')

        if dirpath.exists():
            logger.error(
                f'[{classname}] Directory for saving experiment results '
                f'already exists: {dirpath}. Please use non-existing '
                'directory name and start the experiment again. Existing '
                'directory contents will not be deleted.'
                )
            raise SrtUtilsException(
                f'Directory for saving experiment results already exists: {dirpath}.'
            )

        dirpath.mkdir(parents=True)
        # logger.info(f'[{classname}] Created successfully')


    @classmethod
    def from_config(cls, config: dict):
        # TODO: Config example
        return cls(config)


    def start(self):
        """
        Start single experiment.

        Raises:
            SrtUtilsException
        """
        # self.log.info('Starting experiment')
        logger.info('Starting single experiment')

        if self.is_started:
            raise SrtUtilsException(
                'Experiment has been started already. '
                'Start can not be done.'
            )

        self._create_directory(self.collect_results_path, type(self).__name__)

        for task in self.tasks:
            logging.info(f'Starting task: {task.name}')
            task.obj_runner.start()
            sleep_after_start = task.sleep_after_start
            if sleep_after_start is not None:
                logger.info(f'Sleeping {sleep_after_start}s after task start')
                time.sleep(sleep_after_start)

        self.is_started = True


    def stop(self):
        """
        Raises:
            RunnersException
        """
        logger.info(f'[{self.__class__.__name__}] Stopping experiment')

        if not self.is_started:
            raise RunnersException(
                f'Experiment has not been started yet. '
                f'Stop can not be done.'
            )

        # TODO: Stop the tasks in reverse order
        # as of now comment - if self.ignore_stop_order:
        if self.ignore_stop_order:
            for task in self.tasks:
                logging.info(f'[{self.__class__.__name__}] Stopping task: {task.name}')

                # in case of fail - try to stop the other tasks
                try:
                    task.obj_runner.stop()
                except object_runners.ObjectRunnersException:
                    logger.error(f'Failed to stop task: {task.name}', exc_info=True)
                    # TODO: continue

                sleep_after_stop = task.sleep_after_stop
                if sleep_after_stop is not None:
                    logger.info(f"[{self.__class__.__name__}] Sleeping {sleep_after_stop}s ...")
                    time.sleep(sleep_after_stop)

                # logging.info(f'[{self.__class__.__name__}] Task - Stopped successfully')

        # TODO: Implement stopping tasks according to the specified stop order

        # TODO: clean up, and if clean up does not help - exception

        # TODO: if at least one task is not stop, is stopped = False ???
        self.is_stopped = True
        
        # logger.info(f'[{self.__class__.__name__}] Experiment - Stopped successfully')


    def get_status(self):
        pass


    def collect_results(self):
        """
        Raises:
            RunnersException
        """
        logger.info(f'[{type(self).__name__}] Collecting experiment results')

        if not self.is_started:
            raise RunnersException(
                'Experiment has not been started yet. '
                'Can not collect results.'
            )

        # This is done to prevent the situation when the experiment is still 
        # running and we are trying to collect results before stopping it
        if not self.is_stopped:
            raise RunnersException(
                'Experiment has not been stopped yet. '
                'Can not collect results.'
            )

        # We should try to collect the results for all the tasks
        for task in self.tasks:
            try:
                task.obj_runner.collect_results()
            except object_runners.ObjectRunnersException:
                logger.error(
                    f'Failed to collect task results: {task.name}',
                    exc_info=True
                )
                # TODO: continue

        # logger.info(f'[{self.__class__.__name__}] Collected successfully')


    def clean_up(self):
        # In case of exception raised and catched - do clean up
        # Stop already started 
        
        # TODO: Here I should stop for several times + log if retry
        logger.info('Clean up')

        if not self.is_started:
            logger.info(
                'Experiment has not been started yet. '
                'Nothing to clean up.'
            )
            return

        for task in self.tasks:

            if task.obj_runner.get_status():
                # Catch exceptions, the same logic as in stop function
                logging.info(f'Stopping task: {task.name}')
                task.obj_runner.stop()
