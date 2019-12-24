import logging
import pathlib
import time

from srt_utils.exceptions import SrtUtilsException
# from srt_utils.logutils import ContextualLoggerAdapter
import srt_utils.objects as objects
import srt_utils.object_runners as object_runners


# LOGGER = logging.getLogger(__name__)
logger = logging.getLogger(__name__)


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


### ITestRunner -> SingleExperimentRunner, TestRunner, CombinedTestRunner ###
# The methods will be similar to IRunner


class Task:

    def __init__(
        self,
        name: str,
        obj: objects.IObject,
        obj_runner: object_runners.IObjectRunner,
        config: dict
    ):
        """
        Class to store task details.

        Task represents one step of a single experiment and contains
        both the information regarding the object to run and the way to
        run this object (object runner) as well as additional information
        like the sleep after start/stop time, stop order if defined, etc.
        
        Task should be treated as a combination
        Attributes:
            name:
                Task name.
            obj:
                `objects.IObject` object to run.
            obj_runner:
                `object_runners.IObjectRunner` object runner.
            config:
                Task config.

        Config Example:
        config = { 
            'obj_config': {
                'filepath': '_results_local/dump1.pcapng',
                'interface': 'en0',
                'port': 4200
            },
            'obj_type': 'tshark',
            'runner_config': {},
            'runner_type': 'subprocess',
            'sleep_after_start': 3,             # optional
            'sleep_after_stop': 3,              # optional
            'stop_order': 1                     # optional
        }
        """
        print(config)
        self.name = name
        self.obj = obj
        self.obj_runner = obj_runner
        self.sleep_after_start = config.get('sleep_after_start')
        self.sleep_after_stop = config.get('sleep_after_stop')
        self.stop_order = config.get('stop_order')


    def __str__(self):
        return f'{self.name}'


class SingleExperimentRunner:

    def __init__(self, config: dict):
        """
        Class to run a single experiment.

        Attributes:
            config:
                Single experiment config.

        Config Example:
        # TODO
        """
        self.collect_results_path = pathlib.Path(config['collect_results_path'])
        self.ignore_stop_order = config['ignore_stop_order']
        self.stop_after = config['stop_after']

        self.tasks = []
        factory = SimpleFactory()

        for task_key, task_config in config['tasks'].items():
            name = 'task-' + task_key
            obj = factory.create_object(task_config['obj_type'], task_config['obj_config'])
            task_config['runner_config']['collect_results_path'] = self.collect_results_path
            obj_runner = factory.create_runner(obj, task_config['runner_type'], task_config['runner_config'])
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
        logger.info(
            f'[{classname}] Creating a local directory for saving experiment '
            f'results: {dirpath}'
        )

        if dirpath.exists():
            raise SrtUtilsException(
                'Directory for saving experiment results already exists: '
                f'{dirpath}. Please use non-existing directory name and '
                'start the experiment again. Existing directory contents '
                'will not be deleted'
            )

        dirpath.mkdir(parents=True)


    @classmethod
    def from_config(cls, config: dict):
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
            logging.info(f'Starting task: {task}')
            task.obj_runner.start()
            sleep_after_start = task.sleep_after_start
            if sleep_after_start is not None:
                logger.info(f'Sleeping {sleep_after_start}s after task start')
                time.sleep(sleep_after_start)

        self.is_started = True


    def stop(self):
        """
        Stop single experiment.

        Raises:
            SrtUtilsException
        """
        logger.info(f'Stopping single experiment')
        not_stopped_tasks = 0

        if not self.is_started:
            raise SrtUtilsException(
                'Experiment has not been started yet. '
                'Stop can not be done.'
            )

        if self.is_stopped:
            logger.info('Experiment has been stopped already. Nothing to do')
            return

        # TODO: Implement stopping tasks according to the specified stop order.
        # By default, stop the tasks in reverse order
        # if self.ignore_stop_order:

        for task in self.tasks:
            logging.info(f'Stopping task: {task}')

            # This try/except block is needed here in order to stop as much
            # tasks as we can in case of something has failed
            try:
                task.obj_runner.stop()
            except SrtUtilsException as error:
                logger.error(f'Failed to stop task: {task}. Reason: {error}')
                not_stopped_tasks += 1
                continue
            finally:
                sleep_after_stop = task.sleep_after_stop
                if sleep_after_stop is not None:
                    logger.info(f'Sleeping {sleep_after_stop}s after task stop')
                    time.sleep(sleep_after_stop)

        if not_stopped_tasks != 0:
            raise SrtUtilsException('Not all the tasks have been stopped.')

        self.is_stopped = True


    def get_status(self):
        pass


    def collect_results(self):
        """
        Collect experiment results.

        Raises:
            SrtUtilsException
        """
        logger.info('Collecting experiment results')

        if not self.is_started:
            raise SrtUtilsException(
                'Experiment has not been started yet. '
                'Can not collect results.'
            )

        # This is done to prevent the situation when the experiment is still 
        # running and we are trying to collect results before stopping it
        if not self.is_stopped:
            raise SrtUtilsException(
                'Experiment is still running. '
                'Can not collect results.'
            )

        for task in self.tasks:
            logging.info(f'Collecting task results: {task}')
            # This try/except block is needed here in order to collect results
            # for as much tasks as we can in case of something has failed
            try:
                task.obj_runner.collect_results()
            except SrtUtilsException as error:
                logger.error(f'Failed to collect task results: {task}. Reason: {error}')
                continue


    def clean_up(self):
        """
        Perform cleaning up in case of something has gone wrong during 
        the experiment.

        Raises:
            SrtUtilsException
        """
        logger.info('Cleaning up')
        not_stopped_tasks = 0

        for task in self.tasks:
            if task.obj_runner.get_status():
                logging.info(f'Stopping task: {task}')

                try:
                    task.obj_runner.stop()
                except SrtUtilsException as error:
                    logger.error(f'Failed to stop task: {task}, retrying to stop again. Reason: {error}')
                    
                    try:
                        task.obj_runner.stop()
                    except SrtUtilsException as error:
                        logger.error(f'Failed to stop task on the second try: {task}. Reason: {error}')
                        not_stopped_tasks += 1
                        continue

        if not_stopped_tasks != 0:
            raise SrtUtilsException('Not all the tasks have been stopped during cleaning up.')

        self.is_stopped = True