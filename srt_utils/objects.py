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
        # If running an object assumes having some artifacts produced, e.g.,
        # .pcapng trace file in case of tshark or .csv file with SRT
        # statistics in case of srt-live-transmit or srt-xtransmit, paths to
        # those files should be stored in self.artifacts.
        self.artifacts = []


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
        implementations.
        """
        pass


    @abstractmethod
    def make_str(self):
        """
        Make and return the string for command needs to be launched on a
        remote machine via `RemoteRunner` runner. The examples can be
        found in interface implementations.
        """
        pass


class Tshark(IObject):

    def __init__(
        self,
        path: str,
        interface: str,
        port: str,
        tracefile_path: str
    ):
        """
        Object for `tshark` application.

        Command example:
        tshark -i en0 -f "udp port 4200" -s 1500 -w _results/snd-tracefile.pcapng

        Attributes:
            path:
                Path to tshark application.
            interface:
                Interface to listen and capture the traffic.
            port:
                Port to listen and capture the traffic.
            tracefile_path:
                Filepath to store output .pcapng trace file.
        """
        super().__init__('tshark')
        self.path = path
        self.interface = interface
        self.port = port
        self.tracefile_path = tracefile_path
        self.artifacts += [pathlib.Path(tracefile_path)]

    @classmethod
    def from_config(cls, config: dict):
        """ 
        Config Example:
            config = {
                'path': 'tshark',                                 # Path to tshark application
                'interface': 'en0',                               # Interface to listen and capture the traffic
                'port': '4200',                                   # Port to listen and capture the traffic
                'tracefile_path': '_tmp/snd-tracefile.pcapng'     # Filepath to store output .pcapng trace file
            }
        """
        return cls(
            config['path'],
            config['interface'],
            config['port'],
            config['tracefile_path']
        )


    def make_args(self):
        """
        Command
        tshark -i en0 -f "udp port 4200" -s 1500 -w _tmp/snd-tracefile.pcapng

        transforms to the following list of arguments 
        ['tshark', '-i', 'en0', '-f', 'udp port 4200', '-s', '1500', '-w', '_tmp/snd-tracefile.pcapng']

        to run through `LocalRunner` based on Python `subprocess` module.
        """
        return [
            self.path, 
            '-i', self.interface, 
            '-f', f'udp port {self.port}', 
            '-s', '1500', 
            '-w', self.tracefile_path
        ]


    def make_str(self):
        """
        Command
        ssh -t -o BatchMode=yes -o ConnectTimeout=10 msharabayko@10.129.10.92
        'tshark -i en0 -f "udp port 4200" -s 1500 -w _tmp/snd-tracefile.pcapng'

        transforms to the following list of arguments
        ['ssh', '-t', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'msharabayko@10.129.10.92',
        'tshark -i en0 -f "udp port 4200" -s 1500 -w _tmp/snd-tracefile.pcapng']

        when running through `RemoteRunner` based on Python `subprocess` module.

        Here we construct and return only the command string
        'tshark -i en0 -f "udp port 4200" -s 1500 -w _tmp/snd-tracefile.pcapng'

        SSH related arguments are added on top of that in `RemoteRunner` class.
        """
        args = [f'"{arg}"' if ' ' in arg else arg for arg in self.make_args()]
        args_str = ' '.join(args)
        return args_str


class SrtXtransmit(IObject):

    def __init__(
        self,
        xtransmit_type: str,
        path: str,
        port: str,
        host: str='',
        attrs_values: typing.Optional[typing.List[typing.Tuple[str, str]]]=None,
        options_values: typing.Optional[typing.List[typing.Tuple[str, str]]]=None
    ):
        """
        An object for `srt-xtransmit` test application.
        Source code: https://github.com/maxsharabayko/srt-xtransmit.

        Command example:
        projects/srt-xtransmit/_build/bin/srt-xtransmit receive
        "srt://:4200?rcvbuf=1000000000&sndbuf=1000000000&latency=400"
        --msgsize 1316 --statsfile _results/srt-rcv-stats.csv --statsfreq 1s

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
                SRT URI attributes, optional. Format: [('attr1', 'value1'), ('attr2', 'value2'), ...],
                e.g. [('rcvbuf', '1000000000'), ('sndbuf', '1000000000'), ('latency', '400')].
            options_values:
                Application options, optional. Format: [('option1', 'value1'), ('option2', 'value2'), ...],
                e.g. [('--msgsize', '1316'), ('--statsfile', '_results/srt-rcv-stats.csv'), ('--statsfreq', '1s')].
        """
        super().__init__('srt-xtransmit')
        self.xtransmit_type = xtransmit_type
        self.path = path
        self.port = port
        self.host = host
        self.attrs_values = attrs_values
        self.options_values = options_values

        options = dict(self.options_values)

        if "--statsfile" in options.keys():
            self.artifacts.append(pathlib.Path(options['--statsfile']))

        if "--metricsfile" in options.keys():
            self.artifacts.append(pathlib.Path(options['--metricsfile']))


    @classmethod
    def from_config(cls, config: dict):
        """
        Config Example:
            config = {
                "type": "rcv",                                              # Type of the application as per `SrtApplicationType`
                "path": "projects/srt-xtransmit/_build/bin/srt-xtransmit",  # Path to srt-xtransmit application
                "port": "4200",                                             # Port to listen/call to
                "host": "",                                                 # Host to call to, optional
                "attrs_values": {                                           # SRT URI attributes, optional
                    "rcvbuf": "1000000000",
                    "sndbuf": "1000000000",
                    "latency": "400"
                },
                "options_values": {                                         # Application options, optional
                    "--msgsize": "1316",
                    "--statsfile": "_results/srt-rcv-stats.csv",
                    "--statsfreq": "1s"
                }
            }
        """
        return cls(
            config['type'],
            config['path'],
            config['port'],
            config.get('host', ''),
            list(config.get('attrs_values').items()),
            list(config.get('options_values').items())
        )


    def make_args(self):
        """
        Command
        projects/srt-xtransmit/_build/bin/srt-xtransmit receive 
        "srt://:4200?rcvbuf=1000000000&sndbuf=1000000000&latency=400"
        --msgsize 1316 --statsfile _results/srt-rcv-stats.csv --statsfreq 1s

        transforms to the following list of arguments 
        ['projects/srt-xtransmit/_build/bin/srt-xtransmit', 'receive',
        'srt://:4200?rcvbuf=1000000000&sndbuf=1000000000&latency=400',
        '--msgsize', '1316', '--statsfile', '_results/srt-rcv-stats.csv',
        '--statsfreq', '1s']

        to run through `LocalRunner` based on Python `subprocess` module.
        """
        args = []
        args += [f'{self.path}']

        if self.xtransmit_type == SrtApplicationType.sender.value:
            args += ['generate']

        if self.xtransmit_type == SrtApplicationType.receiver.value:
            args += ['receive']

        if self.attrs_values is not None:
            args += [f'srt://{self.host}:{self.port}?{get_query(self.attrs_values)}']
        else:
            args += [f'srt://{self.host}:{self.port}']

        for option, value in self.options_values:
            args += [option]
            if value:
                args += [value]

        return args


    def make_str(self):
        """
        Command
        ssh -tt -o BatchMode=yes -o ConnectTimeout=10 msharabayko@137.116.228.51
        'projects/srt-xtransmit/_build/bin/srt-xtransmit receive
        "srt://:4200?rcvbuf=1000000000&sndbuf=1000000000&latency=400"
        --msgsize 1316 --statsfile _results/srt-rcv-stats.csv --statsfreq 1s'

        transforms to the following list of arguments
        ['ssh', '-tt', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'msharabayko@137.116.228.51',
        'projects/srt-xtransmit/_build/bin/srt-xtransmit receive
        "srt://:4200?rcvbuf=1000000000&sndbuf=1000000000&latency=400"
        --msgsize 1316 --statsfile _results/srt-rcv-stats.csv --statsfreq 1s']

        when running through `RemoteRunner` based on Python `subprocess` module.

        Here we construct and return only the command string
        'projects/srt-xtransmit/_build/bin/srt-xtransmit receive
        "srt://:4200?rcvbuf=1000000000&sndbuf=1000000000&latency=400"
        --msgsize 1316 --statsfile _results/srt-rcv-stats.csv --statsfreq 1s'

        SSH related arguments are added on top of that in `RemoteRunner` class.
        """
        args = [f'"{arg}"' if arg.startswith('srt://') else arg for arg in self.make_args()]
        args_str = ' '.join(args)
        return args_str