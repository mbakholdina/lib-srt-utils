#!/bin/zsh

# Set date - required
date=01.12.20

# Set transfer rate (Mbps), RTT (ms), packet loss (percentage) - required
transfer_rate=45
RTT=1000
lossA=0
lossB=0

# Set retransmit algo (0 or 1) - required
retransmit_algo=0

# Set directory path to store test results - optional
# Here is the recommended directory path. However you can change
# the first part of the path _retransmit_algo_${date}_2mins to
# something else. Please do not change the second part
# retransmit_algo_$retransmit_algo.
resultsdir=_response_time_${date}_2mins/retransmit_algo_$retransmit_algo

# Set config path - optional
# Note that config should correspond to the value of retransmit algo
# Everything should work if you do not change default names of configs
config=configs/response_time/response_time_with_tshark.json

echo "Transfer Rate (Link Capacity): $transfer_rate Mbps"
echo "RTT: $RTT ms"
echo "Packet Loss: Endpoint A - $lossA%, Endpoint B - $lossB%"
echo "Retransmit Algo: $retransmit_algo"
echo "Config: $config"
echo "Test results can be found here: $resultsdir"
echo ""

sleep 5

latency=`expr $RTT \* 4`
for sendrate in 500kbps 10Mbps
  do
    echo "Sendrate: $sendrate, Latency: $latency ms"
    venv/bin/python -m scripts.run_experiment_with_config_change --resultsdir $resultsdir/_cap${transfer_rate}_rtt${RTT}_lossA${lossA}B${lossB}_sendrate${sendrate}_latency$latency  --latency $latency --sendrate $sendrate $config
  done