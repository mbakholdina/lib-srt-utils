#!/bin/bash
#if [ $# -eq 0 ]
#then
#    TAKE=1
#else
#    TAKE=$1
#fi
LOSSRATE=0

for latency in {25..250..5}
  do
    FLDR=_stats_nak/_loss${LOSSRATE}_latency_${latency}
    venv/bin/python -m scripts.experiment_runner --resultsdir $FLDR configs/lore_xtransmit_periodic_nak.json --latency $latency
    #venv/bin/python compute-loss.py ${FLDR}/msharabayko@10.129.10.165/1-srt-xtransmit-stats-rcv.csv ${FLDR}/local/2-srt-xtransmit-stats-snd.csv >> ./periodic_nak_loss${LOSSRATE}_R7Mbps.txt

    FLDR=_stats_nak_tango/_loss${LOSSRATE}_latency_${latency}
    venv/bin/python -m scripts.experiment_runner --resultsdir $FLDR configs/lore_xtransmit_periodic_nak_tango.json --latency $latency
    #venv/bin/python compute-loss.py ${FLDR}/msharabayko@10.129.10.165/1-srt-xtransmit-stats-rcv.csv ${FLDR}/local/2-srt-xtransmit-stats-snd.csv >> ./tango_nak_loss${LOSSRATE}_R7Mbps.txt

    FLDR=_stats_no_nak/_loss${LOSSRATE}_latency_${latency}
    venv/bin/python -m scripts.experiment_runner --resultsdir $FLDR configs/lore_xtransmit_no_nak.json --latency $latency
    #venv/bin/python compute-loss.py ${FLDR}/msharabayko@10.129.10.165/1-srt-xtransmit-stats-rcv.csv ${FLDR}/local/2-srt-xtransmit-stats-snd.csv >> ./no_nak_loss${LOSSRATE}_R7Mbps.txt
  done
