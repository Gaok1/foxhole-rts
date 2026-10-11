#!/bin/bash
# COLETA_MANUAL: reconstroi o candidato v3 e roda todas as suites; saida filtrada em SAIDA_TESTES.txt (so esta pasta).
#   cd /d/GitHub/foxhole-rts && bash dados/paralel/ia_logistica/acabamento/coleta_manual/rodar_tudo.sh
cd "$(dirname "$0")/../../../../.." || exit 1
export PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1
D=dados/paralel/ia_logistica/acabamento/coleta_manual
OUT=$D/SAIDA_TESTES.txt
rc=0
{
  echo "== COLETA_MANUAL: saida das suites (offline, lupa Lua 5.4 e 5.5; nao prova nada do jogo) =="
  echo "== build_coleta.py"
  python $D/build_coleta.py || rc=1
  echo "== tools/check_globals.py (sem saida = limpo)"
  python tools/check_globals.py $D/candidato_v3/main.lua; echo "rc=$?"
  for t in partida_manual coleta_nucleo travamento persistencia_coleta spawn_interface orders_v3; do
    echo; echo "== test_$t.py"
    python $D/test_$t.py 2>&1 | grep -v "carregado\|^$\|^\[FoxholeRTS\]"
    [ "${PIPESTATUS[0]}" -eq 0 ] || rc=1
  done
  echo; echo "== test_pilha_v3.py (22 etapas)"
  python $D/test_pilha_v3.py 2>&1 | grep -v "carregado\|^$\|^\[FoxholeRTS\]" | grep "^PASS\|^FAIL\|RESUMO\|^  \["
  [ "${PIPESTATUS[0]}" -eq 0 ] || rc=1
  echo; echo "== sensibilidade.py"
  python $D/sensibilidade.py 2>&1 | grep -v "carregado\|^$"
  echo; echo "== SHA256"
  cat $D/candidato_v3/SHA256.txt
  echo "rc_final=$rc"
} > "$OUT" 2>&1
tail -45 "$OUT"
exit $rc
