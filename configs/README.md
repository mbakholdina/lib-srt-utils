# Experiment Config Demystified

*TODO:*

- *rename configs*
- *experiment timeline*
- *Document supported objects configs*
- *Document supported runners configs*

An experiment config is a `.json` file consisting of the following fields:

- collect_results_path:  The directory path where the results produced by the experiment should be copied,
- ignore_stop_order: True/False depending on whether the stop order specified in tasks' configs should be/should not be ignored when stopping the experiment,
- stop_after: The time, in seconds, after which the experiment should be stopped,
- tasks: The list of tasks to run within the experiments and their configs.

```
{
    "collect_results_path": "_experiment_results",
    "stop_after": 30,
    "ignore_stop_order": true,
    "tasks": {
        "1": {
            "obj_type": "tshark",
            "obj_config": {
                "path": "tshark",
                "interface": "en0",
                "port": "4200",
                "dirpath": "_results"
            },
            "runner_type": "local-runner",
            "runner_config": {},
            "sleep_after_start": null,
            "sleep_after_stop": null,
            "stop_order": null
        },
        "2": {
            "obj_type": "tshark",
            "obj_config": {
                "path": "tshark",
                "interface": "eth0",
                "port": "4200",
                "dirpath": "_results"
            },
            "runner_type": "remote-runner",
            "runner_config": {
                "username": "msharabayko",
                "host": "40.69.89.21"
            },
            "sleep_after_start": null,
            "sleep_after_stop": null,
            "stop_order": null
        },
        ...
    }
}
```

Task represents one step of a single experiment and contains both the information regarding the object to run and the way to run this object (object runner) as well as additional information like the sleep after start/stop time, stop order if defined, etc. The task config consists of the following fields:

- `obj_type`: The object to run, currently `tshark` and `srt-xtransmit` objects are supported,
- `obj_config`: The object config which helps to build the command line for subprocess,
- `runner_type`: The object runner to use, currently `local-runner` and `remote-runner` runners are supported, 
- `runner_config`: The object runner config which is empty `{}` for the `local-runner` and consists of `username` and `host` in case of `remote-runner`,
- `sleep_after_start`: The time to sleep after object start, in seconds (optional),
- `sleep_after_stop`: The time to sleep after object stop, in seconds (optional),
- `stop_order`: The order in which tasks should be stopped when stopping the experiment (optional). By default, the tasks are stopped in reversed order.

## Supported Objects

### tshark

```
"obj_type": "tshark",
"obj_config": {
		"path": "tshark",
		"interface": "en0",
		"port": "4200",
		"dirpath": "_results"
},
```

### srt-xtransmit

```
"obj_type": "srt-xtransmit",
            "obj_config": {
                "type": "snd",
                "path": "/home/msharabayko/projects/srt/srt-xtransmit/_build/bin/srt-xtransmit",
                "port": "4200",
                "host": "40.69.89.21",
                "attrs_values": [
                    [
                        "transtype",
                        "live"
                    ],
                    [
                        "rcvbuf",
                        "1000000000"
                    ],
                    [
                        "sndbuf",
                        "1000000000"
                    ]
                ],
                "options_values": [
                    [
                        "--msgsize",
                        "1316"
                    ],
                    [
                        "--sendrate",
                        "100Mbps"
                    ],
                    [
                        "--duration",
                        "30"
                    ]
                ],
                "statsdir": "_results",
                "statsfreq": "10"
            },
```



## Supported Object Runners

## Experiment Description

The usual experiment consists of the following tasks:
1. Start `tshark` locally or remotely via SSH on a sender side,
2. Start `tshark` locally or remotely via SSH on a receiver side,
3. Start `srt-xtransmit` test application (or another test application with SRT support), receiver, locally or remotely via SSH,
4. Start `srt-xtransmit` test application (or another test application with SRT support), sender, locally or remotely via SSH.

Adding/deleting tasks under the `tasks` field of the experiment config changes the logic of the experiment.

Once all the tasks have been started, the script sleeps for `stop_after` seconds specified in the config file to wait while the SRT sender finishes the transmission and then stop the experiment.

After stopping the tasks, the script collects the experiment artefacts (SRT `.csv` statistics, `tshark` `.pcapng` dumps) to the machine where the script is running.

Note:  `--duration` option of the `srt-xtransmit` application is used to control the time of data transmission. A particular value should be specified in the appropriate task config -> object config `obj_config` -> `options_values`. If the duration of data transmission is not set, sleep for `stop_after` seconds and stop the experiment. `srt-xtransmit` sender will be generating the data without any time limitation and then will be stopped by the script as well as the other tasks.

# Config files summary


| Config                             | Description                                                  | Commands |
| ---------------------------------- | ------------------------------------------------------------ | -------- |
| lore_xtransmit_live.json           | Local-remote setup, `srt-xtransmit` application is used for transmission, live mode |          |
| lore_xtransmit_live_duration       | Local-remote setup, `srt-xtransmit` application is used for transmission, live mode, `--duration` option of `srt-xtransmit` is used to control the time of data transmission |          |
| TODO: lolo_xtransmit_live_duration |                                                              |          |
| rere_xtransmit_live_duration       | Remote-remote setup, `set-xtransmit` application is used for transmission, live mode, `--duration` option of `srt-xtransmit` is used to control the time of data transmission |          |
| TODO: lore_xtransmit_file_duration |                                                              |          |
| TODO: rere_xtransmit_file_duration |                                                              |          |
|                                    |                                                              |          |

## 

# Commands to reproduce the experiment

## lore_xtransmit_live.json

```
# Task 1
tshark -i en0 -f "udp port 4200" -s 1500 -w _results/tshark-trace-file.pcapng

# Task 2
ssh -tt -o BatchMode=yes -o ConnectTimeout=10 msharabayko@40.69.89.21 'tshark -i eth0 -f "udp port 4200" -s 1500 -w _results/tshark-trace-file.pcapng'

# Task 3
ssh -tt -o BatchMode=yes -o ConnectTimeout=10 msharabayko@40.69.89.21 '/home/msharabayko/projects/srt/srt-xtransmit/_build/bin/srt-xtransmit receive "srt://:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000" --msgsize 1316 --statsfile _results/srt-xtransmit-stats-rcv.csv --statsfreq 100

# Task 4
../srt-xtransmit/_build/bin/srt-xtransmit generate "srt://40.69.89.21:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000" --msgsize 1316 --sendrate 15Mbps --statsfile _results/srt-xtransmit-stats-snd.csv --statsfreq 100
```

## lore_xtransmit_live_duration

```
# Task 1
tshark -i en0 -f "udp port 4200" -s 1500 -w _results/tshark-trace-file.pcapng

# Task 2
ssh -tt -o BatchMode=yes -o ConnectTimeout=10 msharabayko@40.69.89.21 'tshark -i eth0 -f "udp port 4200" -s 1500 -w _results/tshark-trace-file.pcapng'

# Task 3
ssh -tt -o BatchMode=yes -o ConnectTimeout=10 msharabayko@40.69.89.21 '/home/msharabayko/projects/srt/srt-xtransmit/_build/bin/srt-xtransmit receive "srt://:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000" --msgsize 1316 --statsfile _results/srt-xtransmit-stats-rcv.csv --statsfreq 100

# Task 4
../srt-xtransmit/_build/bin/srt-xtransmit generate "srt://40.69.89.21:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000" --msgsize 1316 --sendrate 15Mbps --duration 30 --statsfile _results/srt-xtransmit-stats-snd.csv --statsfreq 100
```

## rere_xtransmit_live_duration

```
# Task 1
ssh -tt -o BatchMode=yes -o ConnectTimeout=10 msharabayko@23.96.93.54 'tshark -i eth0 -f "udp port 4200" -s 1500 -w _results/tshark-trace-file.pcapng'

# Task 2
ssh -tt -o BatchMode=yes -o ConnectTimeout=10 msharabayko@40.69.89.21 'tshark -i eth0 -f "udp port 4200" -s 1500 -w _results/tshark-trace-file.pcapng'

# Task 3
ssh -tt -o BatchMode=yes -o ConnectTimeout=10 msharabayko@40.69.89.21 '/home/msharabayko/projects/srt/srt-xtransmit/_build/bin/srt-xtransmit receive "srt://:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000" --msgsize 1316 --statsfile _results/srt-xtransmit-stats-rcv.csv --statsfreq 100'

# Task 4
ssh -tt -o BatchMode=yes -o ConnectTimeout=10 msharabayko@23.96.93.54 '/home/msharabayko/projects/srt/srt-xtransmit/_build/bin/srt-xtransmit generate "srt://40.69.89.21:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000" --msgsize 1316 --sendrate 15Mbps --duration 30 --statsfile _results/srt-xtransmit-stats-snd.csv --statsfreq 100'
```