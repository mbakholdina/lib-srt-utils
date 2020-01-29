""" Unit tests for objects.py module """
import pytest

from srt_utils.runners import SimpleFactory


CONFIG_0 = {
    'type': 'rcv',
    'path': '../srt-xtransmit/_build/bin/srt-xtransmit',
    'port': '4200',
}
ARGS_0 = ['../srt-xtransmit/_build/bin/srt-xtransmit', 'receive', 'srt://:4200']
ARGSSTR_0 = '../srt-xtransmit/_build/bin/srt-xtransmit receive "srt://:4200"'


CONFIG_1 = {
    'type': 'rcv',
    'path': '../srt-xtransmit/_build/bin/srt-xtransmit',
    'port': '4200',
    'host': '',
}
ARGS_1 = ARGS_0
ARGSSTR_1 = ARGSSTR_0


CONFIG_2 = {
    'type': 'rcv',
    'path': '../srt-xtransmit/_build/bin/srt-xtransmit',
    'port': '4200',
    'statsdir': '_results',
    'statsfreq': '100'
}
ARGS_2 = [
    '../srt-xtransmit/_build/bin/srt-xtransmit', 'receive', 'srt://:4200',
    '--statsfile', '_results/srt-xtransmit-stats-rcv.csv', '--statsfreq', '100'
]
ARGSSTR_2 = '../srt-xtransmit/_build/bin/srt-xtransmit receive "srt://:4200" ' \
    '--statsfile _results/srt-xtransmit-stats-rcv.csv --statsfreq 100'


CONFIG_3 = {
    'type': 'snd',
    'path': '../srt-xtransmit/_build/bin/srt-xtransmit',
    'port': '4200',
    'host': '127.0.0.1',
}
ARGS_3 = ['../srt-xtransmit/_build/bin/srt-xtransmit', 'generate', 'srt://127.0.0.1:4200']
ARGSSTR_3 = '../srt-xtransmit/_build/bin/srt-xtransmit generate "srt://127.0.0.1:4200"'


CONFIG_4 = {
    'type': 'snd',
    'path': '../srt-xtransmit/_build/bin/srt-xtransmit',
    'port': '4200',
    'host': '127.0.0.1',
    'attrs_values': [
        ('transtype', 'live'),
        ('rcvbuf', '1000000000'),
        ('sndbuf', '1000000000'),
    ],
}
ARGS_4 = [
    '../srt-xtransmit/_build/bin/srt-xtransmit', 'generate',
    'srt://127.0.0.1:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000'
]
ARGSSTR_4 = '../srt-xtransmit/_build/bin/srt-xtransmit generate ' \
    '"srt://127.0.0.1:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000"'


CONFIG_5 = {
    'type': 'snd',
    'path': '../srt-xtransmit/_build/bin/srt-xtransmit',
    'port': '4200',
    'host': '127.0.0.1',
    'options_values': [
        ('--msgsize', '1316'),
        ('--sendrate', '15Mbps'),
        ('--duration', '10s'),
    ],
}
ARGS_5 = [
    '../srt-xtransmit/_build/bin/srt-xtransmit', 'generate',
    'srt://127.0.0.1:4200', '--msgsize', '1316', '--sendrate', '15Mbps',
    '--duration', '10s'
]
ARGSSTR_5 = '../srt-xtransmit/_build/bin/srt-xtransmit generate ' \
    '"srt://127.0.0.1:4200" --msgsize 1316 --sendrate 15Mbps --duration 10s'


CONFIG_6 = {
    'path': 'tshark',
    'interface': 'en0',
    'port': '4200',
    'dirpath': '_results',
}
ARGS_6 = ['tshark', '-i', 'en0', '-f', 'udp port 4200', '-s', '1500', '-w', '_results/tshark-trace-file.pcapng']
ARGSSTR_6 = 'tshark -i en0 -f "udp port 4200" -s 1500 -w _results/tshark-trace-file.pcapng'


CONFIG_ARGS = [
    ('srt-xtransmit', CONFIG_0, ARGS_0),
    ('srt-xtransmit', CONFIG_1, ARGS_1),
    ('srt-xtransmit', CONFIG_2, ARGS_2),
    ('srt-xtransmit', CONFIG_3, ARGS_3),
    ('srt-xtransmit', CONFIG_4, ARGS_4),
    ('srt-xtransmit', CONFIG_5, ARGS_5),
    ('tshark', CONFIG_6, ARGS_6),
]


CONFIG_ARGSSTRS = [
    ('srt-xtransmit', CONFIG_0, ARGSSTR_0),
    ('srt-xtransmit', CONFIG_1, ARGSSTR_1),
    ('srt-xtransmit', CONFIG_2, ARGSSTR_2),
    ('srt-xtransmit', CONFIG_3, ARGSSTR_3),
    ('srt-xtransmit', CONFIG_4, ARGSSTR_4),
    ('srt-xtransmit', CONFIG_5, ARGSSTR_5),
    ('tshark', CONFIG_6, ARGSSTR_6),
]


@pytest.mark.parametrize('type, config, args', CONFIG_ARGS)
def test_make_args(type, config, args):
    factory = SimpleFactory()
    obj = factory.create_object(type, config)
    assert args == obj.make_args()


@pytest.mark.parametrize('type, config, args_str', CONFIG_ARGSSTRS)
def test_make_str(type, config, args_str):
    factory = SimpleFactory()
    obj = factory.create_object(type, config)
    assert args_str == obj.make_str()