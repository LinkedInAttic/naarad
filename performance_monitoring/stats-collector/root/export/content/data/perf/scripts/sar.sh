#!/bin/bash

set -x 

PATH=$PATH:/sbin:/usr/sbin:/usr/local/sbin
NOW=`date +%s`
TODAY=`date +%Y-%m-%d`
COUNT=450
INTERVAL=2
export PATH

t=`date +"%Y-%m-%d"`
export RESULT="/export/content/data/perf/sar-results-$t"

mkdir -p $RESULT

#####################
# EVERY 2 SECONDS
#####################
echo $t >> $RESULT/top.out &
top -b -M -n $COUNT -d $INTERVAL | grep -A 40 '^top' >> $RESULT/top.out &
sar -B $INTERVAL $COUNT >> $RESULT/sar.paging.out &
sar -d -p $INTERVAL $COUNT >> $RESULT/sar.device.out &
sar -R $INTERVAL $COUNT >> $RESULT/sar.memory.out &
sar -r $INTERVAL $COUNT >> $RESULT/sar.memutil.out &
sar -u ALL $INTERVAL $COUNT >> $RESULT/sar.cpuusage.out &
sar -n DEV $INTERVAL $COUNT >> $RESULT/sar.network.out &
sar -W $INTERVAL $COUNT >> $RESULT/sar.swapping.out &
sar -m $INTERVAL $COUNT >> $RESULT/sar.cpuhz.out &
sar -n EDEV $INTERVAL $COUNT >> $RESULT/sar.edev.out &
sar -n TCP $INTERVAL $COUNT >> $RESULT/sar.tcp.out &
sar -n ETCP $INTERVAL $COUNT >> $RESULT/sar.etcp.out &
sar -n SOCK $INTERVAL $COUNT >> $RESULT/sar.sock.out &

#sar -n NFS $INTERVAL $COUNT >> $RESULT/sar.nfs.out &

#####################
# EVERY 2 SECONDS (for now)
#####################
COUNT1=$COUNT
INTERVAL1=$INTERVAL
for ((i=1; i<= $COUNT1; i++)); do cat /proc/meminfo | sed "s/^/$(date +%Y-%m-%d\ %H:%M:%S.%05N)\t/" >> $RESULT/proc.meminfo.out; sleep $INTERVAL1 ; done &
for ((i=1; i<= $COUNT1; i++)); do cat /proc/vmstat | sed "s/^/$(date +%Y-%m-%d\ %H:%M:%S.%05N)\t/" >> $RESULT/proc.vmstat.out; sleep $INTERVAL1 ; done &
for ((i=1; i<= $COUNT1; i++)); do cat /proc/zoneinfo | sed "s/^/$(date +%Y-%m-%d\ %H:%M:%S.%05N)\t/" >> $RESULT/proc.zoneinfo.out; sleep $INTERVAL1 ; done &


