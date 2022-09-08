# lib-srt-utils

**`lib-srt-utils`** is a Python library containing supporting code for running SRT tests based on an experiment configuration. This is the next generation and improved version of the [srt-test-runner](https://github.com/mbakholdina/srt-test-runner) script written in a form of library.

**NOTE:**  [SRT](https://github.com/Haivision/srt) stands for Secure Reliable Transport and is an open source transport technology that optimizes streaming performance across unpredictable networks, such as the Internet.

The following is an example of a single experiment, consisting of a defined set of steps:

  1. Start [tshark](https://www.wireshark.org/docs/man-pages/tshark.html) on the SRT sender side.
  2. Start [tshark](https://www.wireshark.org/docs/man-pages/tshark.html) on the SRT receiver side.
  3. Start the SRT receiver.
  4. Start the SRT sender.
  5. Wait for the specified time to have SRT sender and receiver connected and SRT streaming finished.
  6. Collect the experiment artifacts (e.g., SRT `.csv` statistics, `tshark` `.pcapng` dumps) on the machine where the script is running.

Running the tasks is implemented both locally and remotely so that the following setup combinations are possible: local-local, local-remote and remote-remote . All the implemented configs as well as the detailed documentation can be found in the [configs](./configs) folder. [Here](./configs/rere_xtransmit_live_duration.json) is an example of the remote-remote config where [tshark](https://www.wireshark.org/docs/man-pages/tshark.html) and [srt-xtransmit](https://github.com/maxsharabayko/srt-xtransmit) applications are started consecutively on 2 remote machines (virtual machines in the cloud or regular machines). An SRT transmission is initiated, and once finished the experiment artifacts are collected on the machine where the script is running.

The `SingleExperimentRunner` class (see [srt_utils/runners.py](./srt_utils/runners.py) implements the logic of running a single experiment based on the experiment config. An example of the `SingleExperimentRunner` class usage can be found in the [scripts/run_experiment.py](./scripts/run_experiment.py) script designed to run a single experiment.

An implementation of the `TestRunner` class responsible for running a single test (a set of experiments executed in a consecutive order with different input parameters) is planned for the future. In the experiment example above, the same steps are performed several times, e.g., to test SRT live streaming mode with different values of bitrate. In this case, bitrate value is the particular input parameter that is changed from experiment to experiment during the test.

It is important to note that currently only [tshark](https://www.wireshark.org/docs/man-pages/tshark.html) and [srt-xtransmit](https://github.com/maxsharabayko/srt-xtransmit) applications are supported. [srt-live-transmit](https://github.com/Haivision/srt/blob/master/docs/srt-live-transmit.md) and other applications can be added by request.

## Getting Started

### Requirements

* python 3.6+
* [tshark](https://www.wireshark.org/docs/man-pages/tshark.html) — setting up `tshark` is described in [SRT CookBook](https://srtlab.github.io/srt-cookbook/how-to-articles/using-tshark-wireshark-to-analyse-srt-traffic.html) and [srt-test-runner documentation](https://github.com/mbakholdina/srt-test-runner)
* ssh-agent — setting up SSH keys and ssh-agent is described in SRT CookBook [here](https://srtlab.github.io/srt-cookbook/how-to-articles/how-to-work-with-ssh-keys.html)
* [srt-xtransmit](https://github.com/maxsharabayko/srt-xtransmit)

### Install the Library with pip

For development, it is recommended

* To use `venv` for virtual environments and `pip` for installing the library and any dependencies. This ensures the code and dependencies are isolated from the system Python installation.
* To install the library in “editable” mode by running from the same directory `pip install -e`. This lets changing the source code (both tests and library) and rerunning tests against library code at will. For regular installation, use `pip install`.


As soon as the library is installed, you can run modules directly:
```
venv/bin/python -m srt_utils.module --help
```

or use preinstalled executable scripts:
```
venv/bin/script --help
```

### Install the Library to Import in Another Project

Install with `pip` (a `venv` is recommended), using pip's VCS requirement specifier:
```
pip install 'git+https://github.com/mbakholdina/lib-srt-utils.git@v0.1.0#egg=srt_utils'
```

or simply put the following row in `requirements.txt`:
```
git+https://github.com/mbakholdina/lib-srt-utils.git@v0.1.0#egg=srt_utils
```

Remember to quote the full URL to avoid shell expansion in case of direct installation.

This installs the version corresponding to the git tag 'v0.1.0'. You can replace that with a branch name, a commit hash, or a git ref as necessary. See the [pip documentation](https://pip.pypa.io/en/stable/reference/pip_install/#vcs-support) for details.

As soon as the library is installed, you can import the whole library:
```
import srt_utils
```

or a particular module:
```
import srt_utils.module as module
```

### Running the Library

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

## Setting Up the Environment

As mentioned above, running the tasks is implemented both locally and remotely so that the following combinations are possible:

- Local-Local (LOC-LOC): the script is running on the local machine, `tshark` (single instance), SRT receiver and SRT sender are running on the same local machine,
- Local-Remote (LOC-REM): the script is running on the local machine, `tshark` and SRT receiver are running on the remote machine, another `tshark` and SRT sender are running on the local machine where the script is running,
- and Remote-Remote (REM-REM) setup: the script is running on a separate local machine, `tshark` and SRT receiver are running on the first remote machine, another `tshark` and SRT sender are running on the second remote machine.

### Supported OSs

- LOC-LOC: macOS / Ubuntu / CentOS
- LOC-REM: macOS &#8594; macOS / Ubuntu / CentOS
- REM-REM: macOS &#8594; (Ubuntu + Ubuntu) / (CentOS + CentOS)
- LOC-REM: CentOS / Ubuntu &#8594; macOS / Ubuntu / CentOS - should work, to be tested
- REM-REM: macOS &#8594; (macOS + macOS) - should work, to be tested
- REM-REM: CentOS / Ubuntu &#8594; (macOS + macOS) / (Ubuntu + Ubuntu) / (CentOS + CentOS) - should work, to be tested

|         |        | REM   | REM    | REM    |
|:-------:|:------:| -----:|:------:|:------:|
|         |        | macOS | Ubuntu | CentOS |
| **LOC** | macOS  | ✓     | ✓      | ✓      |
| **LOC** | Ubuntu | ?     | ?      | ?      |
| **LOC** | CentOS | ?     | ?      | ?      |

|            |        | REM-REM       | REM-REM         | REM-REM         |
|:----------:|:------:| -------------:|:---------------:|:---------------:|
|            |        | macOS + macOS | Ubuntu + Ubuntu | CentOS + CentOS |
| **Script** | macOS  | ?             | ✓               | ✓               |
| **Script** | Ubuntu | ?             | ?               | ?               |
| **Script** | CentOS | ?             | ?               | ?               |


**NOTE:** Any combinations with Windows are to be tested. There is currently no support for Windows implemented.



### Before Running the Script

1. Generate an SSH key on the machine where the script will be launched and copy it to the remote machines. This will allow the script to connect to the remote machines and run the tasks via SSH. See the instructions in [SRT CookBook](https://srtlab.github.io/srt-cookbook/how-to-articles/how-to-work-with-ssh-keys.html).

2. Install and set up `tshark` on both machines. The guidelines can be found [here](https://srtlab.github.io/srt-cookbook/how-to-articles/using-tshark-wireshark-to-analyse-srt-traffic.html).

3. Build [srt-xtransmit](https://github.com/maxsharabayko/srt-xtransmit) or any other test application required for running a particular experiment config on both machines.

4. On the local machine where the script is going to be executed, create a directory for the `lib-srt-utils` project and clone the source code in it:

   ```
   mkdir -p projects/srt/lib-srt-utils
   cd projects/srt
   git clone https://github.com/mbakholdina/lib-srt-utils.git lib-srt-utils
   ```

5. On the local machine, install `lib-srt-utils` library as per the [Install the Library with pip](#install-the-library-with-pip) section:

   ```
   cd lib-srt-utils
   python3 -m venv venv
   venv/bin/pip install -e .
   ```

6. Update the experiment config as required. A set of predefined configs and appropriate documentation can be found in the [configs](./configs/) folder.

7. On the local machine, start `ssh-agent` in the background and add your SSH private key generated at Step 1 to the `ssh-agent`. If you do not provide the key, the script will raise an exception `paramiko.ssh_exception.SSHException`.

8. Now you are ready to run the script.

## Scripts

All the implemented scripts can be found in the [scripts](./scripts/) folder.

### run_experiment.py

This script is designed to run a single experiment based on an experiment config. Example configs can be found in the [configs](./config) folder.

Example of execution:

```
venv/bin/python -m scripts.run_experiment --resultsdir _results configs/config.json
```

### rename_folders.py

This script helper is designed to move experiment results from subfolders to a root folder corresponding to a particular experiment. Run this command to get a full description, example of execution, and the list of options:

```
venv/bin/python -m scripts.rename_folders --help
```
