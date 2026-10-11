#!/bin/bash
# COLETA_MANUAL: reconstroi o candidato v3 e roda todas as suites; saida filtrada em TEST_OUTPUT.txt (so esta pasta).
#   cd /d/GitHub/foxhole-rts && bash data/parallel/logistics_ai/finishing/manual_collection/run_all.sh
cd "$(dirname "$0")/../../../../.." || exit 1
export PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1
D=data/parallel/logistics_ai/finishing/manual_collection
OUT=$D/TEST_OUTPUT.txt
rc=0
{
  echo "== COLETA_MANUAL: saida das suites (offline, lupa Lua 5.4 e 5.5; nao prova nada do jogo) =="
  echo "== build_collection.py"
  python $D/build_collection.py || rc=1
  echo "== tools/check_globals.py (sem saida = limpo)"
  python tools/check_globals.py $D/candidate_v3/main.lua; echo "rc=$?"
  for t in partida_manual coleta_nucleo travamento persistencia_coleta spawn_interface orders_v3; do
    echo; echo "== test_$t.py"
    python $D/test_$t.py 2>&1 | grep -v "carregado\|^$\|^\[FoxholeRTS\]"
    [ "${PIPESTATUS[0]}" -eq 0 ] || rc=1
  done
  echo; echo "== test_stack_v3.py (22 etapas)"
  python $D/test_stack_v3.py 2>&1 | grep -v "carregado\|^$\|^\[FoxholeRTS\]" | grep "^PASS\|^FAIL\|RESUMO\|^  \["
  [ "${PIPESTATUS[0]}" -eq 0 ] || rc=1
  echo; echo "== sensitivity.py"
  python $D/sensitivity.py 2>&1 | grep -v "carregado\|^$"
  echo; echo "== SHA256"
  cat $D/candidate_v3/SHA256.txt
  echo "rc_final=$rc"
} > "$OUT" 2>&1
tail -45 "$OUT"
exit $rc
