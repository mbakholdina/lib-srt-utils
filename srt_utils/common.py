""" TODO """

import pathlib


def create_local_directory(dirpath: pathlib.Path):
    if dirpath.exists():
        return False

    dirpath.mkdir(parents=True)
    return True