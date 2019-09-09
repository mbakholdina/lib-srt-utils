import srt_utils.objects as objects
import srt_utils.object_runners as object_runners


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

class SingleExperimentRunner:

    def __init__(self, factory: SimpleFactory, config: dict):
        self.factory = factory
        self.config = config

        # TODO: Add attributes from config

        # TODO: Create a class for task: obj, obj_runner, sleep_after_stop, stop_order
        self.tasks = []
        self.is_started = False

    # TODO: create_directory

    def start(self):
        logger.info('[SingleExperimentRunner] Starting experiment')

        if self.is_started:
            raise ValueError(f'Experiment has been started already')

        for task, task_config in self.config['tasks'].items():
            obj = self.factory.create_object(task_config['obj_type'], task_config['obj_config'])
            obj_runner = self.factory.create_runner(obj, task_config['runner_type'], task_config['runner_config'])
            obj_runner.start()
            obj_runner.get_status()
            self.tasks += [(obj, obj_runner, task_config['sleep_after_stop'], task_config['stop_order'])]
            if task_config['sleep_after_start'] is not None:
                logger.info(f"[SingleExperimentRunner] Sleeping {task_config['sleep_after_start']} s")
                time.sleep(task_config['sleep_after_start'])

        self.is_started = True
            
    def stop(self):
        logger.info('[SingleExperimentRunner] Stopping experiment')

        if not self.is_started:
            raise ValueError(f'Experiment has not been started yet')

        # TODO: Stop the tasks in reverse order
        if self.config['ignore_stop_order']:
            for _, obj_runner, sleep_after_stop, _ in self.tasks:
                obj_runner.stop()
                if sleep_after_stop is not None:
                    logger.info(f"[SingleExperimentRunner] Sleeping {sleep_after_stop}s ...")
                    time.sleep(sleep_after_stop)

        # TODO: Implement stopping tasks according to the specified stop order

    def get_status(self):
        pass

    def collect_results(self):
        logger.info('[SingleExperimentRunner] Collecting experiment results')

        if not self.is_started:
            raise ValueError(f'Experiment has not been started yet')

        for _, obj_runner, _, _ in self.tasks:
            obj_runner.collect_results()

    def _clean_up(self):
        # In case of exception raised and catched - do clean up
        # Stop already started processes
        pass