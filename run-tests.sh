#!/bin/zsh
#if [ $# -eq 0 ]
#then
#    TAKE=1
#else
#    TAKE=$1
#fi

for sendrate in 1 5 7 10 20 30 50
  do
    for ((latency=10; latency <= 80; latency+=5))
      do
        # echo $latency
        venv/bin/python -m scripts.experiment_runner --resultsdir _send_buffer_12.06.20_rtt20_loss0/_rtt20_loss0_sendrate${sendrate}_latency$latency  --latency $latency --sendrate $sendrate configs/send_buffer/rere-flip-flop.json
        #venv/bin/python compute-loss.py _nak/_loss4_latency_$latency/msharabayko@10.129.10.165/1-srt-xtransmit-stats-rcv.csv _nak/_loss4_latency_$latency/local/2-srt-xtransmit-stats-snd.csv >> results_loss4.txt
      done
  done
