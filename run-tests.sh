#!/bin/zsh
#if [ $# -eq 0 ]
#then
#    TAKE=1
#else
#    TAKE=$1
#fi

for sendrate in 5 10 20 50
  do
    for ((latency=20; latency <= 160; latency+=10))
      do
        venv/bin/python -m scripts.experiment_runner --resultsdir _send_buffer_19.06.20_rtt40_loss0_2mins/_rtt40_loss0_sendrate${sendrate}_latency$latency  --latency $latency --sendrate ${sendrate}Mbps configs/send_buffer/rere-flip-flop.json
      done
  done

