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


def get_relative_paths(uri: str):
    """
    Depending on the ``uri`` type determine the corresponding relative
    URI path and relative parent path containing URI ones.
    Arguments:
        uri:
            An absolute URI path:
            /results/file.txt
            /file.txt
            or a relative URI path:
            ../results/file.txt
            ./results/file.txt
            results/file.txt
            ./file.txt
            file.txt
            to a file.
    Returns:
        A tuple of :class:`pathlib.Path` relative URI path and
        :class:`pathlib.Path` relative parent path containing URI ones.
    """
    # If URI starts with '/', i.e., it is absolute,
    # e.g., /file.txt
    if pathlib.Path(uri).is_absolute():
        uri_path = pathlib.Path(uri)
        parent_path = uri_path.parent
        relative_uri_path = uri_path.relative_to('/')
        relative_parent_path = parent_path.relative_to('/')
    # If URI does not start with '/', i.e., it is relative,
    # e.g., file.txt
    else:
        relative_uri_path = pathlib.Path(uri)
        relative_parent_path = relative_uri_path.parent

    return (
        relative_uri_path,
        relative_parent_path,
    )


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

    def __init__(self, interface: str, port: str, filepath: str):
        """
        An object for `tshark` application.

        Command example:
        tshark -i en0 -f "udp port 4200" -s 1500 -w _results/dump.pcapng

        Attributes:
            interface:
                Interface to listen and capture the traffic.
            port:
                Port to listen and capture the traffic.
            filepath:
                Filepath to store output .pcapng trace file.
        """
        super().__init__('tshark')
        self.interface = interface
        self.port = port
        # filepath must be relative
        self.filepath, self.dirpath = get_relative_paths(filepath)


    @classmethod
    def from_config(cls, config: dict):
        """ 
        Config Example:
            config = {
                'interface': 'en0',             # Interface to listen and capture the traffic
                'port': 4200,                   # Port to listen and capture the traffic
                'filepath': './dump.pcapng',    # Filepath to store output .pcapng trace file
            }
        """
        return cls(
            config['interface'],
            config['port'],
            config['filepath']
        )


    def make_args(self):
        """
        Command
        tshark -i en0 -f "udp port 4200" -s 1500 -w _results/dump.pcapng

        transforms to the following list of arguments 
        ['tshark', '-i', 'en0', '-f', 'udp port 4200', '-s', '1500', '-w', '_results/dump.pcapng']

        to run through `LocalRunner` based on Python `subprocess` module.
        """
        return [
            'tshark', 
            '-i', self.interface, 
            '-f', f'udp port {self.port}', 
            '-s', '1500', 
            '-w', str(self.filepath)
        ]


    def make_str(self):
        """
        Command
        ssh -t -o BatchMode=yes -o ConnectTimeout=10 msharabayko@137.116.228.51
        'tshark -i eth0 -f "udp port 4200" -s 1500 -w _results/dump.pcapng'

        transforms to the following list of arguments
        ['ssh', '-t', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'msharabayko@137.116.228.51',
        'tshark -i eth0 -f "udp port 4200" -s 1500 -w _results/dump.pcapng']

        when running through `RemoteRunner` based on Python `subprocess` module.

        Here we construct and return only the command string
        'tshark -i eth0 -f "udp port 4200" -s 1500 -w _results/dump.pcapng'

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
        statsfreq: typing.Optional[int]=None
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
        """
        super().__init__('srt-xtransmit')
        self.type = type
        self.path = path
        self.port = port
        self.host = host
        self.attrs_values = attrs_values
        self.options_values = options_values
        self.statsfreq = statsfreq

        if statsdir is not None:
            self.dirpath = pathlib.Path(statsdir)
            self.filepath = self.dirpath / f'{self.name}-stats-{self.type}.csv'


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
                'statsfreq': '100'                                          # Frequency of SRT statistics collection, in ms, optional
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
            config.get('statsfreq')
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