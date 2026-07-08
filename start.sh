#!/data/data/com.termux/files/usr/bin/bash

echo "STARTING VASUKI DAEMONS..."

nohup python ~/vasuki/scripts/queue_daemon.py > ~/vasuki_queue.log 2>&1 &
echo "Queue daemon started"

nohup python ~/vasuki/scripts/processor_daemon.py > ~/vasuki_processor.log 2>&1 &
echo "Processor daemon started"

echo "ALL SYSTEMS RUNNING"
