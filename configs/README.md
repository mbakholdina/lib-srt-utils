# Experiment Config Demystified

An experiment config is a `.json` file consisting of the following fields:

- `collect_results_path`:  The directory path where the results produced by the experiment should be copied,
- `ignore_stop_order`: True/False depending on whether the stop order specified in tasks' configs should be/should not be ignored when stopping the experiment,
- `stop_after`: The time, in seconds, after which the experiment should be stopped,
- `tasks`: The list of tasks to run within the experiment and their configs.

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

The task represents one step of a single experiment and contains both the information regarding the object to run and the way to run this object (object runner) as well as additional information like the sleep after start/stop time, stop order if defined, etc. The task config consists of the following fields:

- `obj_type`: The object to run, currently `tshark`, `srt-xtransmit` and `netem` objects are supported,
- `obj_config`: The object config which helps to build the command line for subprocess,
- `runner_type`: The object runner to use, currently `local-runner` and `remote-runner` runners are supported, 
- `runner_config`: The object runner config which is empty `{}` for the `local-runner` and consists of `username` and `host` in case of `remote-runner`,
- `sleep_after_start`: The time to sleep after object start, in seconds (optional),
- `sleep_after_stop`: The time to sleep after object stop, in seconds (optional),
- `stop_order`: The order in which tasks should be stopped when stopping the experiment (optional). By default, the tasks are stopped in reversed order.

## Supported Objects and Their Configs

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

`path`: Path to tshark application.

`interface`: Interface to listen and capture the traffic.

`port`: Port to listen and capture the traffic.

`dirpath`: Dirpath to store output .pcapng trace file.

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

`type`: Type of the application as per `SrtApplicationType`. Currently `snd`, `rcv` types are supported.

`path`: Path to `srt-xtransmit` application.

`port`: Port to listen/call to.

`host`: Host to call to, optional.

`attrs_values`: SRT URI attributes, optional. Format: `[('attr', 'value'), ...]`.

`options_values`: Application options, optional. Format: `[('option', 'value'), ...]`.

`statsdir`: Dirpath to collect SRT statistics, optional. If not specified, statistics will not be collected.

`statsfreq`: Frequency of SRT statistics collection, in ms, optional.

### tc-netem

```
{
  "obj_type": "netem",
  "obj_config": {
    "interface": "en0",
    "rules": [
      "delay 100ms",
      "loss 10"
    ]
}
```
`interface`: interface where network conditions will be applied.
`rules`: list of rules that will apply to the previous interface. For more information, visit [tc-netem docs](http://man7.org/linux/man-pages/man8/tc-netem.8.html)


## Supported Object Runners and Their Configs

### local-runner

The config is empty in case `local-runner` usage:

```
"runner_type": "local-runner",
"runner_config": {},
```

### remote-runner

```
"runner_type": "remote-runner",
"runner_config": {
    "username": "msharabayko",
    "host": "40.69.89.21"
},
```

`username`: Username on the remote machine to connect througth.

`host`: IP address of the remote machine to connect.

## Experiment Description

The usual experiment consists of the following tasks:
1. Start `tshark` locally or remotely via SSH on a sender side,
2. Start `tshark` locally or remotely via SSH on a receiver side,
3. Start `srt-xtransmit` test application (or another test application with SRT support), receiver, locally or remotely via SSH,
4. Start `srt-xtransmit` test application (or another test application with SRT support), sender, locally or remotely via SSH.

Adding/deleting tasks under the `tasks` field of the experiment config changes the logic of the experiment.

Once all the tasks have been started, the script sleeps for `stop_after` seconds specified in the config file to wait while the SRT sender finishes the transmission and then stop the experiment.

After stopping the tasks, the script collects the experiment artefacts (SRT `.csv` statistics, `tshark` `.pcapng` dumps) to the machine where the script is running.

Note:  `--duration` option of the `srt-xtransmit` application is used to control the time of data transmission. A particular value should be specified in the appropriate task config &#8594; object config `obj_config` &#8594; `options_values`. If the duration of data transmission is not set, sleep for `stop_after` seconds and stop the experiment. `srt-xtransmit` sender will be generating the data without any time limitation and then will be stopped by the script as well as the other tasks.

## Config Files Summary


| Config                                                       | Description                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| lolo_xtransmit_live_duration                                 | Local-local setup, `srt-xtransmit` application is used for transmission, live mode, `--duration` option of `srt-xtransmit` is used to control the time of data transmission. **Not implemented.** |
| [lore_xtransmit_live](#lore_xtransmit_live)                  | Local-remote setup, `srt-xtransmit` application is used for transmission, live mode. |
| [lore_xtransmit_live_duration](#lore_xtransmit_live_duration) | Local-remote setup, `srt-xtransmit` application is used for transmission, live mode, `--duration` option of `srt-xtransmit` is used to control the time of data transmission. |
| [rere_xtransmit_live_duration](#rere_xtransmit_live_duration) | Remote-remote setup, `set-xtransmit` application is used for transmission, live mode, `--duration` option of `srt-xtransmit` is used to control the time of data transmission. |
| [lore_xtransmit_live_network_conditions](#lore_xtransmit_live_network_conditions) | Loca-remote setup, `set-xtransmit` application is used for transmission, live mode, `--duration` option of `srt-xtransmit` is used to control the time of data transmission. `tc-netem` is used to apply network conditions |
| TODO: lore_xtransmit_file_duration                           |                                                              |
| TODO: rere_xtransmit_file_duration                           |                                                              |

### Commands to reproduce the experiment

#### lore_xtransmit_live

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

#### lore_xtransmit_live_duration

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

#### rere_xtransmit_live_duration

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

#### lore_xtransmit_live_network_conditions

```
# Task 1
ssh -tt -o BatchMode=yes -o ConnectTimeout=10 msharabayko@23.96.93.54 'tshark -i eth0 -f "udp port 4200" -s 1500 -w _results/tshark-trace-file.pcapng'

# Task 2
ssh -tt -o BatchMode=yes -o ConnectTimeout=10 msharabayko@40.69.89.21 'tshark -i eth0 -f "udp port 4200" -s 1500 -w _results/tshark-trace-file.pcapng'

# Task 3
sudo tc qdisc add dev en0  root  netem  delay 100ms

# Task 4
ssh -tt -o BatchMode=yes -o ConnectTimeout=10 msharabayko@40.69.89.21 '/home/msharabayko/projects/srt/srt-xtransmit/_build/bin/srt-xtransmit receive "srt://:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000" --msgsize 1316 --statsfile _results/srt-xtransmit-stats-rcv.csv --statsfreq 100'

# Task 5
ssh -tt -o BatchMode=yes -o ConnectTimeout=10 msharabayko@23.96.93.54 '/home/msharabayko/projects/srt/srt-xtransmit/_build/bin/srt-xtransmit generate "srt://40.69.89.21:4200?transtype=live&rcvbuf=1000000000&sndbuf=1000000000" --msgsize 1316 --sendrate 15Mbps --duration 30 --statsfile _results/srt-xtransmit-stats-snd.csv --statsfreq 100'
```