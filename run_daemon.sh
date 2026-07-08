#!/data/data/com.termux/files/usr/bin/bash

LOG=~/vasuki_processor.log

echo "Starting Vasuki Daemon..." > $LOG

while true; do
    python ~/vasuki/scripts/agent.py >> $LOG 2>&1
    python ~/vasuki/scripts/inspector.py >> $LOG 2>&1
    python ~/vasuki/scripts/labeler.py >> $LOG 2>&1

    echo "CYCLE COMPLETE - SLEEPING 10s" >> $LOG
    sleep 10
done
