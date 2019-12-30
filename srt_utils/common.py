""" TODO """

import pathlib

from srt_utils.exceptions import SrtUtilsException


def create_local_directory(dirpath: pathlib.Path):
    if dirpath.exists():
        return False

    # TODO: Debug and improve this in order to catch particular exceptions
    try:
        dirpath.mkdir(parents=True)
    except Exception as error:
        raise SrtUtilsException(
            f'Directory has not been created: {dirpath}. Exception '
            f'occured ({error.__class__.__name__}): {error}'
        )

    return True