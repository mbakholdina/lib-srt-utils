#!/bin/bash
#if [ $# -eq 0 ]
#then
#    TAKE=1
#else
#    TAKE=$1
#fi

#for latency in {25..250..5}
for latency in {170..250..5}
  do
    venv/bin/python -m scripts.experiment_runner --resultsdir _nak_2/_loss4_latency_$latency configs/lore_xtransmit_periodic_nak.json --latency $latency
    #venv/bin/python compute-loss.py _nak/_loss4_latency_$latency/msharabayko@10.129.10.165/1-srt-xtransmit-stats-rcv.csv _nak/_loss4_latency_$latency/local/2-srt-xtransmit-stats-snd.csv >> results_loss4.txt
  done
