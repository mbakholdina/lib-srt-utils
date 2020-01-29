# Title

# Config files summary


| Config                             | Description                                                  | Commands |
| ---------------------------------- | ------------------------------------------------------------ | -------- |
| lore_xtransmit_live.json           | Local-remote setup, `srt-xtransmit` application is used for transmission, live mode |          |
| lore_xtransmit_live_duration       | Local-remote setup, `set-xtransmit` application is used for transmission, live mode, `--duration` option of `srt-xtransmit` is used to control the time of data transmission |          |
| TODO: lolo_xtransmit_live_duration |                                                              |          |
| rere_xtransmit_live_duration       | Remote-remote setup, `set-xtransmit` application is used for transmission, live mode, `--duration` option of `srt-xtransmit` is used to control the time of data transmission |          |
| TODO: lore_xtransmit_file_duration |                                                              |          |
| TODO: rere_xtransmit_file_duration |                                                              |          |
|                                    |                                                              |          |

## Experiment Description and Test Setup

TODO: Add information regarding local and remote runner here as well

The experiment consists of the following tasks:
1. Start `tshark` locally on a sender side.
2. Start `tshark` remotely via SSH on a receiver side.
3. Start `srt-xtransmit` test application, receiver, remotely via SSH.
4. Start `srt-xtransmit` test application, sender, locally.

Then the script sleeps for `stop_after` seconds specified in config file to wait while sender finishes the transmission and then stop the experiment. `--duration` option of `srt-xtransmit` is used to control the time of data transmission. A particular value should be specified in the appropriate task config -> obj_config -> options_values. If the duration of data transmission is not set, sleep for `stop_after` seconds and stop the experiment. `srt-xtransmit` sender will be generating the data without any time limitation and then stopped by the script as well as the other tasks.

Then the script collects the experiment results produced by the tasks: ...

Note: regarding stop_after and duration

Experiment timeline

How to read the config and how to change the config


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