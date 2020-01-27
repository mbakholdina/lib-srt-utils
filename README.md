# lib-srt-utils

A Python library containing supporting code for running [SRT](https://github.com/Haivision/srt) tests.

# Getting Started

## Requirements

* python 3.6+
* tshark, setting up tshark is described [here](https://github.com/mbakholdina/srt-test-runner) <!-- Add link to CookBook -->
* ssh-agent
* `srt-xtransmit` test application

<!-- Few words about setting up tshark, ssh-agent and test applications -->

## Install the library with pip

For development, it is recommended 
* To use `venv` for virtual environments and `pip` for installing the library and any dependencies. This ensures the code and dependencies are isolated from the system Python installation,
* To install the library in “editable” mode by running from the same directory `pip install -e .`. This lets changing the source code (both tests and library) and rerunning tests against library code at will. For regular installation, use `pip install .`.

<!-- Revise this -->
As soon as the library is installed, you can run modules directly
```
venv/bin/python -m srt_utils.script --help
```

or use preinstalled executable scripts
```
venv/bin/script --help
```

## Install the library to import in another project

<!-- Revise this -->

Install with pip (a venv is recommended), using pip's VCS requirement specifier
```
pip install 'git+https://github.com/mbakholdina/lib-srt-utils.git@v0.1#egg=srt_utils'
```

or simply put the following row in `requirements.txt`
```
git+https://github.com/mbakholdina/lib-srt-utils.git@v0.1#egg=srt_utils
```

Remember to quote the full URL to avoid shell expansion in case of direct installation.

This installs the version corresponding to the git tag 'v0.1'. You can replace that with a branch name, a commit hash, or a git ref as necessary. See the [pip documentation](https://pip.pypa.io/en/stable/reference/pip_install/#vcs-support) for details.

As soon as the library is installed, you can import the whole library
```
import srt_utils
```

or a particular module
```
import srt_utils.module as module
```

## Running the library

<!-- Revise and delete this section afterwards -->

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


# Setting up the environment

<!-- Use cases -->
<!-- Target OS -->

Local-Remote use case

1. Generate SSH key on the local machine (the machine where the script will be launched) and copy it to the remote one for script to connect to remote machine and run the tasks on it via SSH.

<!-- ! Link to how to article -->

2. Install and set up `tshark` on both machines.

<!-- ! Link to how to article -->

3. Build [srt-xtransmit](https://github.com/maxsharabayko/srt-xtransmit) or any other test application required for running a particular experiment config on both machines.

<!-- Link to srt-xtransmit -->
<!-- Link to the section with experiment config -->

4. On the local machine, create the directory for the `lib-srt-utils` project and clone the source code in here:
```
mkdir -p projects/srt/lib-srt-utils
cd projects/srt
git clone https://github.com/mbakholdina/lib-srt-utils.git lib-srt-utils
```

5. On the local machine, install `lib-srt-utils` library as per "Install the library with pip" section:
```
cd lib-srt-utils
python3 -m venv venv
venv/bin/pip install -e .
```

<!-- Running the script -->

6. Update the experiment config ...

7. Start ssh-agent in the background and add your SSH private key generated at Step 1 to the ssh-agent. Without doing this, scripts will raise an exception `paramiko.ssh_exception.SSHException`.

<!-- ! Link to how to article -->

8. Run the script ... The results can be found here