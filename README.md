# lib-srt-utils

A Python library containing supporting code for running SRT tests based on the experiment config. [SRT](https://github.com/Haivision/srt) stands for Secure Reliable Transport and is an open source transport technology that optimizes streaming performance across unpredictable networks, such as the Internet. This is the next generation and improved version of [srt-test-runner](https://github.com/mbakholdina/srt-test-runner) script written in a form of library.

An example of a single experiment, consisting of a defined set of steps, is the following:

- Start `tshark` on the SRT sender side,

- Start `tshark` on the SRT receiver side,

- Start the SRT receiver,

- Start the SRT sender,

- Wait for the specified time to have SRT sender and receiver connected and SRT streaming finished,

- Collect the experiment artefacts (SRT `.csv` statistics, `tshark` `.pcapng` dumps) to the machine where the script is running.

Running the tasks is implemented both locally and remotely so that the following combinations are possible: local-local, local-remote and remote-remote setup. All the implemented configs as well as the detailed documentation can be found in [configs](https://github.com/mbakholdina/lib-srt-utils/tree/master/configs) folder. [Here](https://github.com/mbakholdina/lib-srt-utils/blob/master/configs/rere_xtransmit_live_duration.json) is an example of the remote-remote config where `tshark` and `srt-xtransmit` applications are started consequtively on 2 remote machines (virtual machines in the cloud or regular machines), the SRT transmission is happening and once finished the experiment artefacts are collected to the machine where the script is running.

The `SingleExperimentRunner` class, see [srt_utils/runners.py](https://github.com/mbakholdina/lib-srt-utils/blob/master/srt_utils/runners.py), implements the logic of running a single experiment based on the experiment config. An example of the `SingleExperimentRunner` class usage can be found in [scripts/experiment_runner.py](https://github.com/mbakholdina/lib-srt-utils/blob/master/scripts/experiment_runner.py) script designed to run a single experiment.

An implementation of the `TestRunner` class responsible for running a single test (a set of experiments executed in a consecutive order with the different input parameters) is planned for future. The same experiment example as above, however, the same steps are performed several times, e.g., to test SRT live streaming mode with different values of bitrate. In this case, bitrate value is that particular input parameter that is changed from experiment to experiment during the test.

Important to note, that currently only `tshark` and [srt-xtransmit](https://github.com/maxsharabayko/srt-xtransmit) test application are supported. [srt-live-transmit](https://github.com/Haivision/srt/blob/master/docs/srt-live-transmit.md) and other applications can be added by request.

# Getting Started

## Requirements

* python 3.6+
* tshark, setting up tshark is described in [SRT Cookbook](https://srtlab.github.io/srt-cookbook/apps/wireshark/) and [srt-test-runner documentation](https://github.com/mbakholdina/srt-test-runner)
* ssh-agent, setting up SSH keys and ssh-agent is described in [SRT Cookbook](https://srtlab.github.io/srt-cookbook/how-to-articles/how-to-work-with-ssh-keys/)
* [srt-xtransmit](https://github.com/maxsharabayko/srt-xtransmit) test application

## Install the library with pip

For development, it is recommended 
* To use `venv` for virtual environments and `pip` for installing the library and any dependencies. This ensures the code and dependencies are isolated from the system Python installation,
* To install the library in “editable” mode by running from the same directory `pip install -e .`. This lets changing the source code (both tests and library) and rerunning tests against library code at will. For regular installation, use `pip install .`.


As soon as the library is installed, you can run modules directly

```
venv/bin/python -m srt_utils.module --help
```

or use preinstalled executable scripts
```
venv/bin/script --help
```

## Install the library to import in another project

Install with `pip` (a `venv` is recommended), using pip's VCS requirement specifier
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

Running unit tests:
```
venv/bin/pytest --pyargs srt_utils
venv/bin/python -m pytest --pyargs srt_utils
```

Running modules, e.g. `module.py`:
```
venv/bin/python -m srt_utils.module
```

Starting SSH-agent:
```
eval "$(ssh-agent -s)"
ssh-add -K ~/.ssh/id_rsa
```

# Setting Up the Environment

As mentioned above, running the tasks is implemented both locally and remotely so that the following combinations are possible: 

- local-local: the script is running on the local machine, `thark` (single instance), SRT receiver and SRT sender are running on the same local machine,
- local-remote: the script is running on the local machine, `thark` and SRT receiver are running on the remote machine, another `tshark` and SRT sender are running on the local machine where the script is running, 
- and remote-remote setup: the script is running on a separate local machine, `thark` and SRT receiver are running on the first remote machine, another `tshark` and SRT sender are running on the second remote machine.

## Supported OSs

- MacOS / Ubuntu / CentOS (local-local)

- MacOS &#8594; MacOS / Ubuntu / CentOS (local-remote)
- MacOS &#8594; Ubuntu + Ubuntu / CentOS + CentOS (remote-remote) 
- CentOS / Ubuntu &#8594; MacOS / Ubuntu / CentOS (local-remote) - to be tested
- MacOS &#8594; MacOS + MacOS (remote-remote) - to be tested
- CentOS / Ubuntu &#8594; MacOS + MacOS / Ubuntu + Ubuntu / CentOS + CentOS (remote-remote) - to be tested 
- Any combinations with Windows - to be tested, there is no support for Windows implemented.

## Steps to Do before Running the Script

1. Generate SSH key on the machine where the script will be launched and copy it to the remote machines for the script to connect to them and run the tasks via SSH. See the instructions in [SRT Cookbook](https://srtlab.github.io/srt-cookbook/how-to-articles/how-to-work-with-ssh-keys/).

2. Install and set up `tshark` on both machines. The guidelines can be found [here](https://srtlab.github.io/srt-cookbook/apps/wireshark/).

3. Build [srt-xtransmit](https://github.com/maxsharabayko/srt-xtransmit) or any other test application required for running a particular experiment config on both machines.

4. On the local machine where the script is going to be executed, create the directory for the `lib-srt-utils` project and clone the source code in it:

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
6. Update the experiment config as required. A set of predifend configs and appropriate documentaion can be found in `configs` folder.

7. On the local machine, start `ssh-agent` in the background and add your SSH private key generated at Step 1 to the `ssh-agent`. Without doing this, the script will raise an exception `paramiko.ssh_exception.SSHException`.

8. Now you are ready to run the script.

# Executable Scripts

All the implemented scripts can be found in `scripts` folder. Please use [scripts/experiment_runner.py](https://github.com/mbakholdina/lib-srt-utils/blob/master/scripts/experiment_runner.py) script to run a single experiment based on the experiment config.