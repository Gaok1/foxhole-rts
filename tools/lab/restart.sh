#!/bin/sh
# Publishes main.lua (syntax + globals check), closes the lab copy if open, relaunches it through lab.ps1
# and waits for the autostart to turn RTS mode on. Replaces UE4SS Ctrl+R, which froze the game thread.
# Usage: sh tools/lab/restart.sh [wait_s]
. "$(dirname "$0")/env.sh"
SRC=$REPO/mod/FoxholeRTS/Scripts/main.lua
BIN=$FOXHOLE_LAB/War/Binaries/Win64
DST=$BIN/ue4ss/Mods/FoxholeRTS/Scripts/main.lua
LOG=$BIN/ue4ss/UE4SS.log
PYTHONPATH=$PYLIBS python -c "
import sys
from lupa import LuaRuntime
r = LuaRuntime().eval('function(s) local f,e=load(s,\"main\",\"t\"); return f and \"OK\" or e end')(open(sys.argv[1], encoding='utf-8').read())
print('syntax:', r); sys.exit(0 if r == 'OK' else 1)
" "$SRC" || exit 1
python "$REPO/tools/check_globals.py" "$SRC" || exit 1
cp "$SRC" "$DST" || exit 1
mkdir -p "$LAB_CHANNEL" && rm -f "$LAB_CHANNEL/cmd.lua" "$LAB_CHANNEL/cmd.out"
winlab=$(cygpath -w "$FOXHOLE_LAB" 2>/dev/null || echo "$FOXHOLE_LAB")
# kill only the lab copy, by exact PID (never by name: that could hit the Steam install)
for pid in $(powershell -NoProfile -Command "Get-Process War-Win64-Shipping -ErrorAction SilentlyContinue | Where-Object { \$_.Path -like '$winlab\*' } | ForEach-Object { \$_.Id }"); do
  if [ -d "$UM_DIR" ]; then (cd "$UM_DIR" && python -m um win kill "$pid"); else taskkill //PID "$pid" //F; fi
  k=0
  while tasklist //FI "PID eq $pid" | grep -q "$pid" && [ $k -lt 30 ]; do sleep 1; k=$((k+1)); done
done
# the dead process can still hold the log; without deleting it the wait below would read the old log
k=0
while [ -f "$LOG" ] && [ $k -lt 30 ]; do rm -f "$LOG" 2>/dev/null; [ -f "$LOG" ] && sleep 1; k=$((k+1)); done
[ -f "$LOG" ] && { echo "could not delete $LOG"; exit 1; }
launch=$(powershell -NoProfile -ExecutionPolicy Bypass -File "$REPO/tools/lab.ps1" run -LabGame "$winlab" 2>&1) || { printf '%s\n' "$launch"; exit 1; }
printf '%s\n' "$launch" | grep -a "PID"
n=0
until grep -aq "modo RTS ligado\|autostart: mapa nao carregou" "$LOG" 2>/dev/null || [ $n -ge ${1:-240} ]; do sleep 2; n=$((n+2)); done
grep -a "FoxholeRTS" "$LOG" | tail -4
