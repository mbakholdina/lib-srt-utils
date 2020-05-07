""" The module with IObject interface and its implementations. """
from abc import abstractmethod, ABC
import enum
import logging
import pathlib
import typing


logger = logging.getLogger(__name__)


@enum.unique
class SrtApplicationType(enum.Enum):
    """
    Defines the type of the test application supporting SRT protocol in a
    a particular experiment. Affects arguments generation and stats filename.
    """
    #:
    sender = "snd"
    #:
    receiver = "rcv"
    #:
    forwarder = "fwd"


def get_query(attrs_values: typing.List[typing.Tuple[str, str]]):
    """ Get query out of the list of attributes-values pairs. """
    query_elements = []
    for attr, value in attrs_values:
        query_elements.append(f'{attr}={value}')
    return f'{"&".join(query_elements)}'


class IObject(ABC):
    """
    Object interface.

    Object here represents 1) a single application, e.g., tshark or any test
    application like srt-live-transmit, srt-xtransmit, etc.; or 2) a hublet,
    or 3) whatever we might need to run in future setups.
    """

    def __init__(self, name: str):
        # Object name
        self.name = name
        # If running an object assumes having some output files produced,
        # e.g., .pcapng trace file produced by tshark or .csv file with
        # SRT statistics produced by srt-live-transmit, srt-xtransmit or
        # another test application, both `dirpath` and `filepath` specifying
        # where to store the object results should be present, otherwise it's None.
        self.dirpath = None
        self.filepath = None


    def __str__(self):
        return f'{self.name}'


    @classmethod
    @abstractmethod
    def from_config(cls, config: dict):
        """
        Create `IObject` instance from config.

        Attributes:
            config:
                Object config.

        Config examples are provided in interface implementations.
        """
        pass


    @abstractmethod
    def make_args(self):
        """
        Make and return the list of arguments to start the object via
        `LocalRunner` runner. The examples can be found in interface 
        implemenations.
        """
        pass


    @abstractmethod
    def make_str(self):
        """
        Make and return the string for command needs to be launched on a
        remote machine via `RemoteRunner` runner. The examples can be
        found in interface implemenations.
        """
        pass


class Tshark(IObject):

    def __init__(
        self,
        path: str,
        interface: str,
        port: str,
        dirpath: str,
        prefix: typing.Optional[str]=None
    ):
        """
        An object for `tshark` application.

        Command example:
        tshark -i en0 -f "udp port 4200" -s 1500 -w _results/tshark-trace-file.pcapng

        Attributes:
            path:
                Path to tshark application.
            interface:
                Interface to listen and capture the traffic.
            port:
                Port to listen and capture the traffic.
            dirpath:
                Dirpath to store output .pcapng trace file.
            prefix:
                Prefix to construct output filename.
        """
        super().__init__('tshark')
        self.path = path
        self.interface = interface
        self.port = port

        if prefix is not None:
            filename = f'{prefix}-{self.name}-tracefile'
        else:
            filename = f'{self.name}-tracefile'

        # TODO: For being able to implement unique names
        # self.pattern = filename + '-{:03d}.pcapng'
        filename += '.pcapng'

        self.dirpath = pathlib.Path(dirpath)
        self.filepath = self.dirpath / filename
        self.network_condition = False


    @classmethod
    def from_config(cls, config: dict):
        """ 
        Config Example:
            config = {
                'path': 'tshark',               # Path to tshark application
                'interface': 'en0',             # Interface to listen and capture the traffic
                'port': '4200',                 # Port to listen and capture the traffic
                'dirpath': '_results',          # Dirpath to store output .pcapng trace file
                'prefix': '1'                   # Prefix to construct output filename, optional
            }
        """
        return cls(
            config['path'],
            config['interface'],
            config['port'],
            config['dirpath'],
            config.get('prefix')
        )


    def make_args(self):
        """
        Command
        tshark -i en0 -f "udp port 4200" -s 1500 -w _results/tshark-trace-file.pcapng

        transforms to the following list of arguments 
        ['tshark', '-i', 'en0', '-f', 'udp port 4200', '-s', '1500', '-w', '_results/tshark-trace-file.pcapng']

        to run through `LocalRunner` based on Python `subprocess` module.
        """
        return [
            self.path, 
            '-i', self.interface, 
            '-f', f'udp port {self.port}', 
            '-s', '1500', 
            '-w', str(self.filepath)
        ]


    def make_str(self):
        """
        Command
        ssh -t -o BatchMode=yes -o ConnectTimeout=10 msharabayko@137.116.228.51
        'tshark -i en0 -f "udp port 4200" -s 1500 -w _results/tshark-trace-file.pcapng'

        transforms to the following list of arguments
        ['ssh', '-t', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'msharabayko@137.116.228.51',
        'tshark -i en0 -f "udp port 4200" -s 1500 -w _results/tshark-trace-file.pcapng']

        when running through `RemoteRunner` based on Python `subprocess` module.

        Here we construct and return only the command string
        'tshark -i en0 -f "udp port 4200" -s 1500 -w _results/tshark-trace-file.pcapng'

        SSH related arguments are added on top of that in `RemoteRunner` class.
        """
        args = [f'"{arg}"' if ' ' in arg else arg for arg in self.make_args()]
        args_str = ' '.join(args)
        return args_str


class SrtXtransmit(IObject):

    def __init__(
        self,
        type: str,
        path: str,
        port: str,
        host: str='',
        attrs_values: typing.Optional[typing.List[typing.Tuple[str, str]]]=None,
        options_values: typing.Optional[typing.List[typing.Tuple[str, str]]]=None,
        statsdir: typing.Optional[str]=None,
        statsfreq: typing.Optional[str]=None,
        prefix: typing.Optional[str]=None
    ):
        """
        An object for `srt-xtransmit` test application.
        Source code: https://github.com/maxsharabayko/srt-xtransmit.

        Command example:
        projects/srt-xtransmit/_build/bin/srt-xtransmit receive 
        "srt://:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000"
        --msgsize 1316 --statsfile _results/srt-xtransmit-stats-rcv.csv --statsfreq 100

        Attributes:
            type:
                Type of the application as per `SrtApplicationType`.
            path:
                Path to srt-xtransmit application.
            port:
                Port to listen/call to.
            host:
                Host to call to, optional.
            attrs_values:
                SRT URI attributes, optional. Format: [('attr', 'value'), ...], e.g.
                [('transtype', 'live'), ('rcvbuf', '1000000000'), ('sndbuf', '1000000000')].
            options_values:
                Application options, optional. Format: [('option', 'value'), ...], e.g.
                [('--msgsize', '1316')].
            statsdir:
                Dirpath to collect SRT statistics, optional. If not specified,
                statistics will not be collected.
            statsfreq:
                Frequency of SRT statistics collection, in ms, optional.
            prefix:
                Prefix to construct output filename.
        """
        super().__init__('srt-xtransmit')
        self.type = type
        self.path = path
        self.port = port
        self.host = host
        self.attrs_values = attrs_values
        self.options_values = options_values
        self.statsfreq = statsfreq
        self.network_condition = False

        if statsdir is not None:

            if prefix is not None:
                filename = f'{prefix}-{self.name}-stats-{self.type}'
            else:
                filename = f'{self.name}-stats-{self.type}'

            # TODO: For being able to implement unique names
            # self.pattern = filename + '-{:03d}.csv'
            filename += '.csv'

            self.dirpath = pathlib.Path(statsdir)
            self.filepath = self.dirpath / filename


    @classmethod
    def from_config(cls, config: dict):
        """
        Config Example:
            config = {
                'type': 'rcv',                                              # Type of the application as per `SrtApplicationType`
                'path': 'projects/srt-xtransmit/_build/bin/srt-xtransmit',  # Path to srt-xtransmit application
                'port': '4200',                                             # Port to listen/call to
                'host': '',                                                 # Host to call to, optional
                'attrs_values': [                                           # SRT URI attributes, optional
                        ('transtype', 'live'),
                        ('rcvbuf', '1000000000'),
                        ('sndbuf', '1000000000'),
                    ],
                'options_values': [                                         # Application options, optional
                    ('--msgsize', '1316'),
                ],
                'statsdir': '_results',                                     # Dirpath to collect SRT statistics, optional. If not specified, statistics will not be collected
                'statsfreq': '100',                                         # Frequency of SRT statistics collection, in ms, optional
                'prefix': '1-rcv1'                                          # Prefix to construct output filename, optional
            }

        Suggested additional fields:
        'mode' to reflect whether it is listener, caller, or rendezvous mode
        and be able to perform additional config validations.
        """
        return cls(
            config['type'],
            config['path'],
            config['port'],
            config.get('host', ''),
            config.get('attrs_values'),
            config.get('options_values'),
            config.get('statsdir'),
            config.get('statsfreq'),
            config.get('prefix')
        )


    def make_args(self):
        """
        Command
        projects/srt-xtransmit/_build/bin/srt-xtransmit receive 
        "srt://:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000"
        --msgsize 1316 --statsfile _results/srt-xtransmit-stats-rcv.csv --statsfreq 100

        transforms to the following list of arguments 
        ['projects/srt-xtransmit/_build/bin/srt-xtransmit', 'receive',
        'srt://:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000',
        '--msgsize', '1316', '--statsfile', '_results/srt-xtransmit-stats-rcv.csv',
        '--statsfreq', '100']

        to run through `LocalRunner` based on Python `subprocess` module.
        """
        args = []
        args += [f'{self.path}']

        if self.type == SrtApplicationType.sender.value:
            args += ['generate']

        if self.type == SrtApplicationType.receiver.value:
            args += ['receive']

        if self.attrs_values is not None:
            args += [f'srt://{self.host}:{self.port}?{get_query(self.attrs_values)}']
        else:
            args += [f'srt://{self.host}:{self.port}']

        if self.options_values is not None:
            for option, value in self.options_values:
                args += [option, value]

        if self.dirpath:
            args += ['--statsfile', str(self.filepath)]

            if self.statsfreq:
                args += ['--statsfreq', self.statsfreq]

        return args


    def make_str(self):
        """
        Command
        ssh -t -o BatchMode=yes -o ConnectTimeout=10 msharabayko@137.116.228.51
        'projects/srt-xtransmit/_build/bin/srt-xtransmit receive
        "srt://:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000"
        --msgsize 1316 --statsfile _results/srt-xtransmit-stats-rcv.csv --statsfreq 100'

        transforms to the following list of arguments
        ['ssh', '-tt', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'msharabayko@137.116.228.51',
        'projects/srt-xtransmit/_build/bin/srt-xtransmit receive
        "srt://:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000"
        --msgsize 1316 --statsfile _results/srt-xtransmit-stats-rcv.csv --statsfreq 100']

        when running through `RemoteRunner` based on Python `subprocess` module.

        Here we construct and return only the command string
        'projects/srt-xtransmit/_build/bin/srt-xtransmit receive
        "srt://:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000"
        --msgsize 1316 --statsfile _results/srt-xtransmit-stats-rcv.csv --statsfreq 100'

        SSH related arguments are added on top of that in `RemoteRunner` class.
        """
        args = [f'"{arg}"' if arg.startswith('srt://') else arg for arg in self.make_args()]
        args_str = ' '.join(args)
        return args_str


class Netem(IObject):

    def __init__(
            self,
            interface: str,
            rules: typing.List[str]
            # interface,
            # rules,
    ):

        super().__init__('netem')
        self.filepath = None
        self.interface = interface
        self.rules = rules
        self.network_condition = True

    @classmethod
    def from_config(cls, config: dict):

        return cls(
            config['interface'],
            config['rules']
        )

    def make_args(self):

        args = ['sudo', 'tc', 'qdisc', 'add', 'dev', self.interface, 'root', 'netem']

        print(args)
        for rule in self.rules:
            args += rule.split(' ')
        print(args)
        return args

    def make_str(self):
        args = self.make_args()
        args_str = ' '.join(args)
        return args_str
