from abc import abstractmethod, ABC
import enum
import logging
import pathlib


logger = logging.getLogger(__name__)


@enum.unique
class SrtApplicationType(enum.Enum):
    """
    Defines the type of the application supporting SRT protocol in a
    a particular experiment. Affects arguments generation and stats
    filename.
    """
    #:
    sender = "snd"
    #:
    receiver = "rcv"
    #:
    forwarder = "fwd"


def get_query(attrs_values):
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


class DirectoryHasNotBeenCreated(Exception):
    pass


### IObject (application, hublet, etc.) ###
# ? IObjectConfig

class IObject(ABC):

    def __init__(self, name: str):
        self.name = name
        # If running an object assumes having some output files produced,
        # e.g. dump or stats files, dirpath/filepath to store the results should be
        # specified, otherwise it's None.
        self.dirpath = None
        self.filepath = None

    def __str__(self):
        return f'{self.name}'

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict):
        pass

    @abstractmethod
    def make_args(self):
        pass


class Tshark(IObject):

    def __init__(self, interface: str, port: str, filepath: str):
        super().__init__('tshark')
        self.interface = interface
        self.port = port
        # filepath must be relative
        self.filepath, self.dirpath = get_relative_paths(filepath)
        # TODO: Make a validator, the line below works if only file exists
        # assert self.filepath.is_file()

    @classmethod
    def from_config(cls, config: dict):
        # config - object config (parameters needed to form the args for cmd)
        """ 
        Config Example:
            config = {
                'interface': 'en0',
                'port': 4200,
                'filepath': './dump.pcapng',
            }
        """
        return cls(
            config['interface'],
            config['port'],
            config['filepath']
        )

    def make_args(self):
        return [
            'tshark', 
            '-i', self.interface, 
            '-f', f'udp port {self.port}', 
            '-s', '1500', 
            '-w', self.filepath
        ]


class SrtTestMessaging(IObject):

    def __init__(
        self,
        type,
        path,
        host,
        port,
        attrs_values,
        options_values,
        collect_stats,
        description,
        dirpath
    ):
        """
        Types:
        number,
        path_to_srt: str,
        host: str,
        port: str,
        attrs_values: typing.Optional[typing.List[typing.Tuple[str, str]]]=None,
        options_values: typing.Optional[typing.List[typing.Tuple[str, str]]]=None,
        description: str=None,
        collect_stats: bool=False,
        dirpath: pathlib.Path=None
        """
        self.name = 'srt-test-messaging'
        self.type = type
        self.path = path
        self.host = host
        self.port = port
        self.attrs_values = attrs_values
        self.options_values = options_values
        self.collect_stats = collect_stats
        self.description = description
        self.dirpath = dirpath
        # TODO: Determine
        self.filepath = None

    @classmethod
    def from_config(cls, config: dict):
        """
        config = {
            'path': '/Users/msharabayko/projects/srt/srt-maxlovic/_build',
            'type': 'snd',
            'host': '137.135.161.223',
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
        attrs_values:
            A list of SRT options (SRT URI attributes) in a format
            [('rcvbuf', '12058624'), ('smoother', 'live'), ('maxcon', '50')].
        options_values:
            A list of srt-test-messaging application options in a format
            [('-msgsize', '1456'), ('-reply', '0'), ('-printmsg', '0')].
        """
        return cls(
            config['type'],
            config['path'],
            config['host'],
            config['port'],
            config['attrs_values'],
            config['options_values'],
            config['collect_stats'],
            config['description'],
            config['dirpath']
        )

    def make_args(self):
        # TODO: Add receiver support
        args = []
        args += [f'{self.path}/{self.name}']

        if self.attrs_values is not None:
            # FIXME: But here there is a problem with "" because sender has been
            # started locally, not via SSH
            if self.type == SrtApplicationType.sender.value:
                args += [f'srt://{self.host}:{self.port}?{get_query(self.attrs_values)}']
            # FIXME: Deleted additonal quotes, needs to be tested with receiver running locally
            if self.type == SrtApplicationType.receiver.value:
                args += [f'srt://{self.host}:{self.port}?{get_query(self.attrs_values)}']
        else:
            args += [f'srt://{self.host}:{self.port}']

        if self.type == SrtApplicationType.sender.value:
            args += ['']

        if self.options_values is not None:
            for option, value in self.options_values:
                args += [option, value]

        if self.collect_stats:
            # stats_file = self.dirpath / f'{self.description}-stats-{self.type}.csv'
            stats_file = self.dirpath + '/' + f'{self.description}-stats-{self.type}.csv'
            args += [
                '-statsfreq', '1',
                '-statsfile', stats_file,
            ]
        
        return args