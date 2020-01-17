import pytest

import srt_utils.objects as objects
from srt_utils.runners import SimpleFactory


# TSHARK_CONFIG = {
#     'interface': 'en0',
#     'port': 4200,
#     'filepath': './dump.pcapng',
# }

CONFIG_1 = {
    'type': 'rcv',
    'path': '../srt-xtransmit/_build/bin/srt-xtransmit',
    'port': '4200',
}
ARGS_1 = ['../srt-xtransmit/_build/bin/srt-xtransmit', 'receive', 'srt://:4200']

CONFIG_2 = {
    'type': 'rcv',
    'path': '../srt-xtransmit/_build/bin/srt-xtransmit',
    'port': '4200',
    'host': '',
}
ARGS_2 = ARGS_1

CONFIG_3 = {
    'type': 'rcv',
    'path': '../srt-xtransmit/_build/bin/srt-xtransmit',
    'port': '4200',
    'statsdir': '_results',
    'statsfreq': '100'
}
ARGS_3 = [
    '../srt-xtransmit/_build/bin/srt-xtransmit', 'receive', 'srt://:4200',
    '--statsfile', '_results/srt-xtransmit-stats-rcv.csv', '--statsfreq', '100'
]

CONFIG_4 = {
    'type': 'snd',
    'path': '../srt-xtransmit/_build/bin/srt-xtransmit',
    'port': '4200',
    'host': '127.0.0.1',
}
ARGS_4 = ['../srt-xtransmit/_build/bin/srt-xtransmit', 'generate', 'srt://127.0.0.1:4200']

CONFIG_5 = {
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
ARGS_5 = [
    '../srt-xtransmit/_build/bin/srt-xtransmit', 'generate',
    '"srt://127.0.0.1:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000"'
]

CONFIG_6 = {
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
ARGS_6 = [
    '../srt-xtransmit/_build/bin/srt-xtransmit', 'generate',
    'srt://127.0.0.1:4200', '--msgsize', '1316', '--sendrate', '15Mbps',
    '--duration', '10s'
]

# CONFIG_2 = {
#     'path': '/Users/msharabayko/projects/srt/srt-maxlovic/_build',
#     'type': 'rcv',
#     'host': '',
#     'port': '4200',
#     'attrs_values': [
#         ('rcvbuf', '12058624'),
#         ('congestion', 'live'),
#         ('maxcon', '50'),
#     ],
#     'options_values': [
#         ('-msgsize', '1456'),
#         ('-reply', '0'),
#         ('-printmsg', '0'),
#     ],
#     'collect_stats': True,
#     'description': 'busy_waiting',
#     'dirpath': '_results',
# }
# ARGS_2 = ['']



CONFIG_ARGS = [
    ('srt-xtransmit', CONFIG_1, ARGS_1),
    ('srt-xtransmit', CONFIG_2, ARGS_2),
    ('srt-xtransmit', CONFIG_3, ARGS_3),
    ('srt-xtransmit', CONFIG_4, ARGS_4),
    ('srt-xtransmit', CONFIG_5, ARGS_5),
    ('srt-xtransmit', CONFIG_6, ARGS_6),
]

@pytest.mark.parametrize('type, config, args', CONFIG_ARGS)
def test_make_args(type, config, args):
    factory = SimpleFactory()
    obj = factory.create_object(type, config)
    assert args == obj.make_args()