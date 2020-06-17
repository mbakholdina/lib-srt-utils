#!/bin/zsh
#if [ $# -eq 0 ]
#then
#    TAKE=1
#else
#    TAKE=$1
#fi


for ((latency=10; latency <= 80; latency+=5))
  do
    # echo $latency
    venv/bin/python -m scripts.experiment_runner --resultsdir _send_buffer_16.06.20_rtt20_loss0_2mins/_rtt20_loss0_sendrate10_latency$latency  --latency $latency configs/send_buffer/rere-flip-flop.json
    #venv/bin/python compute-loss.py _nak/_loss4_latency_$latency/msharabayko@10.129.10.165/1-srt-xtransmit-stats-rcv.csv _nak/_loss4_latency_$latency/local/2-srt-xtransmit-stats-snd.csv >> results_loss4.txt
  done

