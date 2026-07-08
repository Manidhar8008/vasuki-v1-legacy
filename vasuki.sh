#!/data/data/com.termux/files/usr/bin/bash

echo "=== VASUKI SYSTEM START ==="

PGDATA=~/pgdata

# 1. Check Postgres
pg_isready -h 127.0.0.1 -p 5432

if [ $? -ne 0 ]; then
    echo "Postgres not running. Starting..."
    pg_ctl -D $PGDATA start
    sleep 2
fi

# 2. Fix role issue silently (safe check)
psql -U u0_a348 -d vasuki -c "\q" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "Trying fallback login..."
fi

# 3. Start agent
echo "Starting AI Agent..."
python ~/vasuki/agent_core.py

