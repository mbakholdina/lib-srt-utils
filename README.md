# lib-srt-utils

A Python library containing supporting code for running [SRT](https://github.com/Haivision/srt) tests.

## Installation

Install with `pip` (a virtualenv is recommended), using pip's VCS requirement specifier. Remember to quote the full URL to avoid shell expansion:

`pip install 'git+https://github.com/mbakholdina/lib-srt-utils.git@v0.1#egg=srt_utils'`

This installs the version corresponding to the git tag 'v0.1'. You can replace that with a branch name, a commit hash, or a git ref as necessary. See the [pip documentation](https://pip.pypa.io/en/stable/reference/pip_install/#vcs-support) for details.

## Running the library

Running unit tests:
```
venv/bin/pytest --pyargs srt_utils
venv/bin/python -m pytest --pyargs srt_utils
```

Running modules, e.g. `script.py`:
```
venv/bin/python -m srt_utils.script
```

Starting SSH-agent:
```
eval "$(ssh-agent -s)"
ssh-add -K ~/.ssh/id_rsa
```

Building `srt-xtransmit` test application on MacOS:
```
mkdir _build
cd _build
export OPENSSL_ROOT_DIR=$(brew --prefix openssl)
export OPENSSL_LIB_DIR=$(brew --prefix openssl)"/lib"
export OPENSSL_INCLUDE_DIR=$(brew --prefix openssl)"/include"
cmake ../ -DENABLE_CXX17=OFF
cmake --build ./
```