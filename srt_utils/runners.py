import logging
import pathlib
import time

from srt_utils.common import create_local_directory
from srt_utils.enums import Status
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
        elif obj_type == 'srt-xtransmit':
            obj = objects.SrtXtransmit.from_config(obj_config)
        elif obj_type == 'netem':
            obj = objects.Netem.from_config(obj_config)
        else:
            print('No matching object found')

        return obj

    def create_runner(self, obj, runner_type: str, runner_config: dict) -> object_runners.IObjectRunner:
        runner = None

        if runner_type == 'local-runner':
            runner = object_runners.LocalRunner.from_config(obj, runner_config)
        elif runner_type == 'remote-runner':
            runner = object_runners.RemoteRunner.from_config(obj, runner_config)
        else:
            print('No matching runner found')

        return runner


### ITestRunner -> SingleExperimentRunner, TestRunner, CombinedTestRunner ###
# The methods will be similar to IRunner

class Task:

    def __init__(
        self,
        key: str,
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
            key:
                Task key.
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
        self.key = key
        self.obj = obj
        self.obj_runner = obj_runner
        self.sleep_after_start = config.get('sleep_after_start')
        self.sleep_after_stop = config.get('sleep_after_stop')
        self.stop_order = config.get('stop_order')


    def __str__(self):
        return f'task-{self.key}'


class SingleExperimentRunner:

    def __init__(
        self,
        collect_results_path: pathlib.Path,
        ignore_stop_order: bool,
        stop_after: int,
        tasks: dict
    ):
        """
        Class to run a single experiment.

        Attributes:
            collect_results_path:
                `pathlib.Path` directory path where the results produced by 
                the experiment should be copied.
            ignore_stop_order:
                True/False depending on whether the stop order specified in
                tasks' configs should be/should not be ignored when stopping
                the experiment.
            stop_after:
                The time in seconds after which experiment should be stopped.
            tasks:
                A `dict_items` object with the list of tasks to run within
                the experiments.
        """
        self.collect_results_path = collect_results_path
        self.ignore_stop_order = ignore_stop_order
        self.stop_after = stop_after

        self.tasks = []
        factory = SimpleFactory()

        for key, config in tasks:
            config['obj_config']['prefix'] = key
            config['runner_config']['collect_results_path'] = self.collect_results_path

            obj = factory.create_object(config['obj_type'], config['obj_config'])
            obj_runner = factory.create_runner(obj, config['runner_type'], config['runner_config'])

            self.tasks += [Task(key, obj, obj_runner, config)]

        self.is_started = False
        self.is_stopped = False

        # self.log = ContextualLoggerAdapter(LOGGER, {'context': type(self).__name__})


    @staticmethod
    def _create_directory(dirpath: pathlib.Path):
        """
        Create a local directory for saving experiment results.

        Raises:
            SrtUtilsException
        """
        logger.info(
            '[SingleExperimentRunner] Creating a local directory for saving '
            f'experiment results: {dirpath}'
        )

        created = create_local_directory(dirpath)

        if not created:
            raise SrtUtilsException(
                'Directory for saving experiment results already exists: '
                f'{dirpath}. Please use non-existing directory name and '
                'start the experiment again. Existing directory contents '
                'will not be deleted'
            )


    @classmethod
    def from_config(cls, config: dict):
        """
        Attributes:
            config:
                Single experiment config.

        Config Example:
        # TODO
        """
        return cls(
            pathlib.Path(config['collect_results_path']),
            config['ignore_stop_order'],
            config['stop_after'],
            config['tasks'].items()
        )


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
                'Experiment has been started already. Start can not be done'
            )

        self._create_directory(self.collect_results_path)

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
                'Experiment has not been started yet. Stop can not be done'
            )

        if self.is_stopped:
            logger.info('Experiment has been stopped already. Nothing to do')
            return

        logger.info(f'Stopping tasks in reversed order')

        # By default, stop the tasks in reverse order
        # TODO: Implement stopping tasks according to the specified stop order.
        # if self.ignore_stop_order:
        for task in reversed(self.tasks):
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
            raise SrtUtilsException('Not all the tasks have been stopped')

        self.is_stopped = True


    def collect_results(self):
        """
        Collect experiment results.

        Raises:
            SrtUtilsException
        """
        logger.info('Collecting experiment results')

        if not self.is_started:
            raise SrtUtilsException(
                'Experiment has not been started yet. Can not collect results'
            )

        # This is done to prevent the situation when the experiment is still 
        # running and we are trying to collect results before stopping it
        if not self.is_stopped:
            raise SrtUtilsException(
                'Experiment is still running. Can not collect results'
            )

        for task in self.tasks:
            logging.info(f'Collecting task results: {task}')
            # This try/except block is needed here in order to collect results
            # for as much tasks as we can in case of something has failed
            try:
                task.obj_runner.collect_results()
            except SrtUtilsException as error:
                logger.error(
                    f'Failed to collect task results: {task}. Reason: {error}'
                )
                continue


    def clean_up(self):
        """
        Perform cleaning up in case of something has gone wrong during 
        the experiment.

        Raises:
            SrtUtilsException
        """
        logger.info('Cleaning up after experiment')
        not_stopped_tasks = 0

        for task in self.tasks:
            if task.obj_runner.status == Status.running:
                logging.info(f'Stopping task: {task}')

                try:
                    task.obj_runner.stop()
                except SrtUtilsException as error:
                    logger.error(
                        f'Failed to stop task: {task}, retrying to stop '
                        f'again. Reason: {error}'
                    )
                    
                    try:
                        task.obj_runner.stop()
                    except SrtUtilsException as error:
                        logger.error(
                            f'Failed to stop task on the second try: {task}. '
                            f'Reason: {error}'
                        )
                        not_stopped_tasks += 1
                        continue

        if not_stopped_tasks != 0:
            raise SrtUtilsException(
                'Not all the tasks have been stopped during cleaning up'
            )

        self.is_stopped = True