# Lab paths. Defaults are the maintainer's machine; override them in your shell or in tools/lab/env.local.sh.
# FOXHOLE_LAB   isolated copy of the game (never your Steam install)
# LAB_CHANNEL   command channel folder; must match CFG.CMD_FILE / CFG.CMD_OUT in main.lua
# PYLIBS        folder with lupa installed (pip install --target "$PYLIBS" lupa)
# UM_DIR        optional universal-modder checkout, used to kill the game by exact PID
HERE=$(cd "$(dirname "$0")" && pwd)
[ -f "$HERE/env.local.sh" ] && . "$HERE/env.local.sh"
REPO=${FOXHOLE_RTS:-$(cd "$HERE/../.." && pwd)}
FOXHOLE_LAB=${FOXHOLE_LAB:-/d/FoxholeLab/Foxhole}
LAB_CHANNEL=${LAB_CHANNEL:-/d/tools/foxhole-lab}
PYLIBS=${PYLIBS:-D:/tools/pylibs}
UM_DIR=${UM_DIR:-/d/GitHub/universal-modder}
