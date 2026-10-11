#!/bin/sh
# Sends a Lua script to the mod's command channel and waits for the answer (only out(...) is returned).
# Usage: sh tools/lab/run.sh <file.lua> [timeout_s]. Needs Mods/FoxholeRTS/autostart.txt in the lab copy.
. "$(dirname "$0")/env.sh"
src=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
cd "$LAB_CHANNEL" || exit 1
rm -f cmd.out
cp "$src" cmd.tmp && mv cmd.tmp cmd.lua
t=${2:-30}
i=0
while [ ! -f cmd.out ] && [ $i -lt $t ]; do sleep 1; i=$((i+1)); done
if [ -f cmd.out ]; then cat cmd.out; else echo "(no answer in ${t}s)"; fi
