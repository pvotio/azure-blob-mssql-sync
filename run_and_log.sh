#!/bin/sh
set -e
python main.py || true
echo "=== Contents of /tmp/odbc.log (if any) ==="
if [ -f /tmp/odbc.log ]; then cat /tmp/odbc.log; else echo "No /tmp/odbc.log found"; fi
echo "=== Contents of /tmp/odbcdriver.log (if any) ==="
if [ -f /tmp/odbcdriver.log ]; then cat /tmp/odbcdriver.log; else echo "No /tmp/odbcdriver.log found"; fi