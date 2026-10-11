#!/bin/sh
# Regression bot: plays until the match ends (or 25 min). Log in $LAB_CHANNEL/botrun.log.
# Do not use run.sh by hand while it runs: the answers get mixed.
. "$(dirname "$0")/env.sh"
L=$LAB_CHANNEL/botrun.log; : > "$L"
sh "$HERE/run.sh" "$HERE/${BOT0:-t_bot0.lua}" 20 >> "$L"
for i in $(seq 1 150); do
  sleep 10
  r=$(sh "$HERE/run.sh" "$HERE/t_bot.lua" 20 | tail -1); echo "$i $r" >> "$L"
  case "$r" in *"auto	false"*) break;; esac
done
