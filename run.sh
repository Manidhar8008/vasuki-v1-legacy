#!/data/data/com.termux/files/usr/bin/bash

echo "Starting Vasuki System..."

pg_ctl -D ~/pgdata start

python ~/vasuki/agent_core.py
