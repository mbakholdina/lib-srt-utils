"""
Script designed for debugging pusposes: building configs, running
single experiments.
"""
import json
import logging
import os
import pprint
import time

import click

from srt_utils.exceptions import SrtUtilsException
from srt_utils.runners import SingleExperimentRunner


logger = logging.getLogger(__name__)


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


def create_experiment_config(config_path: str, resultsdir: str):
    if os.path.exists(config_path):
        logger.error(
            'Specified config path already exists, please restart '
            'the script with non-existing one'
        )
        return

    logger.info('Creating experiment config')

    LORUNNER_CONFIG = {}
    RERUNNER_USEAST_CONFIG = {
        'username': 'msharabayko',
        'host': '23.96.93.54',
    }
    RERUNNER_EUNORTH_CONFIG = {
        'username': 'msharabayko',
        'host': '40.69.89.21',
    }

    config = {}
    config['collect_results_path'] = resultsdir    # path to collect experiment results
    config['stop_after'] = 40                      # time to wait since the last task have been started and then stop the experiment
    config['ignore_stop_order'] = True             # stop the tasks in a specified order if True, otherwise the reverse order is used
    config['tasks'] = {}

    # Task 1 - Start tshark on a sender side
    TSHARK_SND_CONFIG = {
        'path': 'tshark',
        'interface': 'eth0',
        'port': '4200',
        'dirpath': '_results',
    }
    config['tasks']['1'] = create_task_config(
        'tshark', 
        TSHARK_SND_CONFIG, 
        'remote-runner', 
        RERUNNER_USEAST_CONFIG
    )

    # Task 2 - Start tshark on a receiver side
    TSHARK_RCV_CONFIG = {
        'path': 'tshark',
        'interface': 'eth0',
        'port': '4200',
        'dirpath': '_results',
    }
    config['tasks']['2'] = create_task_config(
        'tshark', 
        TSHARK_RCV_CONFIG, 
        'remote-runner', 
        RERUNNER_EUNORTH_CONFIG
    )

    # Task 3 - Start srt-xtransmit application (rcv)
    SRT_XTRANSMIT_RCV_CONFIG = {
        'type': 'rcv',
        'path': '/home/msharabayko/projects/srt/srt-xtransmit/_build/bin/srt-xtransmit',
        'port': '4200',
        'attrs_values': [
                ('transtype', 'live'),
                ('rcvbuf', '1000000000'),
                ('sndbuf', '1000000000'),
            ],
        'options_values': [
            ('--msgsize', '1316'),
        ],
        'statsdir': '_results',
        'statsfreq': '100'
    }
    config['tasks']['3']= create_task_config(
        'srt-xtransmit',
        SRT_XTRANSMIT_RCV_CONFIG,
        'remote-runner',
        RERUNNER_EUNORTH_CONFIG
    )

    # Task 4 - Start srt-xtransmit application (snd)
    SRT_XTRANSMIT_SND_CONFIG = {
        'type': 'snd',
        'path': '/home/msharabayko/projects/srt/srt-xtransmit/_build/bin/srt-xtransmit',
        'port': '4200',
        'host': '40.69.89.21',
        'attrs_values': [
            ('transtype', 'live'),
            ('rcvbuf', '1000000000'),
            ('sndbuf', '1000000000'),
        ],
        'options_values': [
            ('--msgsize', '1316'),
            ('--sendrate', '15Mbps'),
            ('--duration', '30'),
        ],
        'statsdir': '_results',
        'statsfreq': '100'
    }
    config['tasks']['4']= create_task_config(
        'srt-xtransmit',
        SRT_XTRANSMIT_SND_CONFIG,
        'remote-runner',
        RERUNNER_USEAST_CONFIG
    )

    # TODO: sort_dicts option - added in Python 3.8
    # pp = pprint.PrettyPrinter(indent=2, sort_dicts=False)
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(config)

    with open(config_path, "w") as write_file:
        json.dump(config, write_file, indent=4)

    return config


@click.command()
@click.argument(
    'config_path',
    type=click.Path()
)
@click.option(
    '--resultsdir',
    required=True,
    help =  'Directory path to store experiment results.'
)
def main(config_path, resultsdir):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)-15s [%(levelname)s] %(message)s',
    )

    config = create_experiment_config(config_path, resultsdir)

    try:
        exp_runner = SingleExperimentRunner.from_config(config)
        exp_runner.start()
        logger.info(f"Sleeping {config['stop_after']}s after experiment start")
        time.sleep(config['stop_after'])
        exp_runner.stop()
        exp_runner.collect_results()
    except SrtUtilsException as error:
        logger.error(f'Failed to run experiment. Reason: {error}', exc_info=True)
    finally:
        exp_runner.clean_up()


if __name__ == '__main__':
    main()