""" Unit tests for object_runners.py module """
import pytest

from srt_utils.objects import SrtXtransmit, Tshark
from srt_utils.object_runners import LocalRunner, RemoteRunner
from srt_utils.runners import SimpleFactory


SRT_XTRANSMIT_CONFIG = {
    'type': 'rcv',
    'path': '../srt-xtransmit/_build/bin/srt-xtransmit',
    'port': '4200',
}

TSHARK_CONFIG = {
    'path': 'tshark',
    'interface': 'en0',
    'port': 4200,
    'dirpath': '_results',
}

LOCAL_RUNNER_CONFIG = {}

REMOTE_RUNNER_CONFIG = {
    'username': 'msharabayko',
    'host': '137.116.228.51',
}

OBJECTS_CLASSES = [
    ('srt-xtransmit', SRT_XTRANSMIT_CONFIG, SrtXtransmit),
    ('tshark', TSHARK_CONFIG, Tshark),
]

OBJRUNNERS_CLASSES = [
    ('local-runner', LOCAL_RUNNER_CONFIG, LocalRunner),
    ('remote-runner', REMOTE_RUNNER_CONFIG, RemoteRunner),
]


@pytest.mark.parametrize('obj_type, obj_config, classname', OBJECTS_CLASSES)
def test_factory_creates_right_object(obj_type, obj_config, classname):
    factory = SimpleFactory()
    obj = factory.create_object(obj_type, obj_config)
    assert isinstance(obj, classname)


@pytest.mark.parametrize('runner_type, runner_config, classname', OBJRUNNERS_CLASSES)
def test_factory_creates_right_runner(runner_type, runner_config, classname):
    factory = SimpleFactory()
    obj = factory.create_object('tshark', TSHARK_CONFIG)
    runner = factory.create_runner(obj, runner_type, runner_config)
    assert isinstance(runner, classname)