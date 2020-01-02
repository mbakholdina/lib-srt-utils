""" For debugging purposes. Will be deleted later. """

import logging
import pprint
import time

import click

from srt_utils.exceptions import SrtUtilsException
from srt_utils.runners import SingleExperimentRunner


logger = logging.getLogger(__name__)


### Configs ###

def create_task_config(
    obj_type, 
    obj_config, 
    runner_type, 
    runner_config, 
    sleep_after_start: str=None, 
    sleep_after_stop: str=None,
    stop_order: int=None
):
    return {
        'obj_type': obj_type,
        'obj_config': obj_config,
        'runner_type': runner_type,
        'runner_config': runner_config,
        'sleep_after_start': sleep_after_start,
        'sleep_after_stop': sleep_after_stop,
        'stop_order': stop_order,
    }


def create_experiment_config(stop_after: int, collect_results_path: str, ignore_stop_order: bool=True):
    dirpath = '_results'
    sleep_after_start = 3
    sleep_after_stop = 1

    config = {}
    config['collect_results_path'] = collect_results_path     # path where to collect results
    config['stop_after'] = stop_after
    config['ignore_stop_order'] = ignore_stop_order

    config['tasks'] = {}
    tshark_config = {
        'interface': 'en0',
        'port': 4200,
        'filepath': f'{dirpath}_local/dump1.pcapng',
    }
    tshark_runner_config = {}
    config['tasks']['0'] = create_task_config(
        'tshark', 
        tshark_config, 
        'local-runner', 
        tshark_runner_config,
        sleep_after_start,
        sleep_after_stop
    )

    # tshark_config = {
    #     'interface': 'en0',
    #     'port': 4200,
    #     'filepath': f'{dirpath}_local/dump2.pcapng',
    # }
    # tshark_runner_config = {}
    # config['tasks']['1'] = create_task_config(
    #     'tshark', 
    #     tshark_config, 
    #     'local-runner', 
    #     tshark_runner_config,
    #     sleep_after_start
    # )

    tshark_config = {
        'interface': 'eth0',
        'port': 4200,
        'filepath': f'{dirpath}_remote/dump2.pcapng',
    }
    tshark_runner_config = {
        'username': 'msharabayko',
        'host': '137.116.228.51',
    }
    config['tasks']['1'] = create_task_config(
        'tshark', 
        tshark_config, 
        'remote-runner', 
        tshark_runner_config,
        None,
        sleep_after_stop
    )

    srt_test_msg_config = {
        'path': '/Users/msharabayko/projects/srt/srt-maxlovic/_build',
        'type': 'rcv',
        'host': '',
        'port': '4200',
        'attrs_values': [
            ('rcvbuf', '12058624'),
            ('congestion', 'live'),
            ('maxcon', '50'),
        ],
        'options_values': [
            ('-msgsize', '1456'),
            ('-reply', '0'),
            ('-printmsg', '0'),
        ],
        'collect_stats': True,
        'description': 'busy_waiting',
        'dirpath': '_results',
    } 
    srt_test_msg_runner_config = None
    # config['task3']= create_task_config('srt-test-messaging', srt_test_msg_config, 'local-runner', srt_test_msg_runner_config)

    srt_test_msg_config = {
        'path': 'projects/srt-maxlovic/_build',
        'type': 'rcv',
        'host': '',
        'port': '4200',
        'attrs_values': [
            ('rcvbuf', '12058624'),
            ('congestion', 'live'),
            ('maxcon', '50'),
        ],
        'options_values': [
            ('-msgsize', '1456'),
            ('-reply', '0'),
            ('-printmsg', '0'),
        ],
        'collect_stats': True,
        'description': 'busy_waiting',
        'dirpath': '_results',
    }
    srt_test_msg_runner_config = {
        'username': 'msharabayko',
        'host': '65.52.227.197',
    }
    # config['task4']= create_task_config('srt-test-messaging', srt_test_msg_config, 'remote-runner', srt_test_msg_runner_config)

    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(config)

    return config


@click.command()
@click.argument(
	'dirpath'
)
def main(dirpath):
    logging.basicConfig(
        level=logging.INFO,
        # format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        format='%(asctime)-15s [%(levelname)s] %(message)s',
    )

    # time to stream
    stop_after = 10
    # This will be changed to loading the config from file
    # and then adjusting it (srt parameters, etc.) knowing what kind of
    # experiment we are going to do. Or we will provide a cli to user with
    # the list of parameters we need to know (or it would be just a file with the list of params),
    # and then config file for the experiment will be built in a function and parameters will be adjusted
    config = create_experiment_config(stop_after, dirpath)

    try:
        exp_runner = SingleExperimentRunner.from_config(config)
        exp_runner.start()
        logger.info(f'Sleeping {stop_after}s after experiment start')
        time.sleep(stop_after)
        exp_runner.stop()
        exp_runner.collect_results()
    except SrtUtilsException as error:
        logger.error(f'Failed to run experiment. Reason: {error}', exc_info=True)
    finally:
        exp_runner.clean_up()


if __name__ == '__main__':
    main()