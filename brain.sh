#!/data/data/com.termux/files/usr/bin/bash

echo "=== SCAN ==="
python ~/vasuki/scripts/index_files.py

echo "=== EDA ==="
python ~/vasuki/scripts/eda.py

echo "=== COMPLETE ==="
