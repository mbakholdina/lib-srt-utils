#!/bin/zsh

# Set date - required
date=17.6.21

# Set transfer rate (Mbps), RTT (ms), packet loss (percentage) - required
transfer_rate=45
RTT=248
lossA=0
lossB=0

# Set number of repetitions per configuration
number_experiments=10

# Set config path - optional
# Note that config should correspond to the value of retransmit algo
# Everything should work if you do not change default names of configs

echo "Transfer Rate (Link Capacity): $transfer_rate Mbps"
echo "RTT: $RTT ms"
echo "Packet Loss: Endpoint A - $lossA%, Endpoint B - $lossB%"
echo "Number of experiments per configuration: $number_experiments"
echo ""

sleep 5

# Uncomment this if you would like to run a series of experiments
# Note that you might need to update the loop for sendrate or
# boundaries b1, b2 for latency range
step=$((RTT / 2))
b1=$step
b2=`expr $RTT \* 5`


for i in $(seq 1 $number_experiments)
  do
#  for sendrate in 5Mbps 8Mbps
#      do
    sendrate=10Mbps
        for ((latency=$b1; latency <= $b2; latency+=$step))
          do
          for algo in 0 1
            do
              resultsdir=_retransmit_algo_${date}_2mins/retransmit_algo_$algo
              config=../configs/retransmit_algo/retransmit_algo_$algo.json
              echo "Experiment $i, Sendrate: $sendrate, Latency: $latency ms, Algo: $algo"
              python run_experiment_with_config_change.py --resultsdir $resultsdir/_experiment${i}_cap${transfer_rate}_rtt${RTT}_lossA${lossA}B${lossB}_sendrate${sendrate}_latency$latency  --latency $latency --sendrate $sendrate $config
            done
          done
#      done
  done