import logging
import pathlib
import time

import srt_utils.objects as objects
import srt_utils.object_runners as object_runners


logger = logging.getLogger(__name__)


class DirectoryExists(Exception):
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


    @staticmethod
    def _create_directory(dirpath: pathlib.Path, classname):
        """
        Raises:
            DirectoryExists
        """
        # but if this dir already exists from the previous run - stop the expirement and ask user to use the other nam
        # delete the directory is not good, cause the results of the previous run might be needed
        logger.info(f'[{classname}] Creating a directory for saving experiment results: {dirpath}')
        if dirpath.exists():
            logger.error(
                'Directory already exists, please use non-existing directory '
                'name and start the experiment again. Existing directory '
                'contents will not be changed.'
                )
            raise DirectoryExists(dirpath)

        dirpath.mkdir(parents=True)
        logger.info(f'[{classname}] Created successfully')


    @classmethod
    def from_config(cls, obj: objects.IObject, config: dict):
        return cls(obj, config)


    def start(self):
        """
        Raises:
            ValueError
            DirectoryExists
        """
        logger.info(f'[{self.__class__.__name__}] Starting experiment')

        if self.is_started:
            raise ValueError(
                f'Experiment has been started already. '
                f'Start can not be done.'
            )

        # Create directory for saving experiment results
        try:
            self._create_directory(self.collect_results_path, self.__class__.__name__)
        except DirectoryExists:
            raise

        # Start tasks
        print(self.tasks)

        # TODO: Catch exceptions, if something has not started, we should do clean up
        for task in self.tasks:
            logging.info(f'[{self.__class__.__name__}] Starting task: {task.name}, {task.obj.name}')
            task.obj_runner.start()
            task.obj_runner.get_status()
            sleep_after_start = task.sleep_after_start
            
            if sleep_after_start is not None:
                logger.info(f"[{self.__class__.__name__}] Sleeping {sleep_after_start} s after task start")
                time.sleep(sleep_after_start)

            logging.info(f'[{self.__class__.__name__}] Task - Started successfully')

        self.is_started = True

        logging.info(f'[{self.__class__.__name__}] Experiment - Started successfully')


    def stop(self):
        logger.info(f'[{self.__class__.__name__}] Stopping experiment')

        if not self.is_started:
            raise ValueError(
                f'Experiment has not been started yet. '
                f'Stop can not be done.'
            )

        # Stop the tasks in reverse order
        # TODO: Catch exceptions, clean up
        if self.ignore_stop_order:
            for task in self.tasks:
                sleep_after_stop = task.sleep_after_stop

                logging.info(f'[{self.__class__.__name__}] Stopping task: {task.name}')
                task.obj_runner.stop()

                if sleep_after_stop is not None:
                    logger.info(f"[{self.__class__.__name__}] Sleeping {sleep_after_stop}s ...")
                    time.sleep(sleep_after_stop)

                logging.info(f'[{self.__class__.__name__}] Task - Stopped successfully')

        # TODO: Implement stopping tasks according to the specified stop order
        
        logger.info(f'[{self.__class__.__name__}] Experiment - Stopped successfully')


    def get_status(self):
        pass


    def collect_results(self):
        logger.info(f'[{self.__class__.__name__}] Collecting experiment results')

        if not self.is_started:
            raise ValueError(f'Experiment has not been started yet')

        # if_stopped - and then collect results to prevent the situation when the
        # experiment is still running and we are trying to collect results before stopping it
        # the same might be valid for object runners

        # catch exceptions
        for task in self.tasks:
            task.obj_runner.collect_results()

        logger.info(f'[{self.__class__.__name__}] Collected successfully')


    def _clean_up(self):
        # In case of exception raised and catched - do clean up
        # Stop already started processes
        pass