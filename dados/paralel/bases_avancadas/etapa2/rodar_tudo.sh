#!/bin/bash
# BASES_AVANCADAS etapa 2: reconstroi o candidato v4 e roda todas as suites; saida filtrada em SAIDA_TESTES.txt (so esta pasta).
#   cd /d/GitHub/foxhole-rts && bash dados/paralel/bases_avancadas/etapa2/rodar_tudo.sh
cd "$(dirname "$0")/../../../.." || exit 1
export PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
D=dados/paralel/bases_avancadas/etapa2
V3=dados/paralel/ia_logistica/acabamento/coleta_manual/candidato_v3/main.lua
MAIN=mod/FoxholeRTS/Scripts/main.lua
OUT=$D/SAIDA_TESTES.txt
rc=0
FILT='carregado\|^$\|^\[FoxholeRTS\]'
{
  echo "== BASES_AVANCADAS etapa 2: saida das suites (offline, lupa Lua 5.4 e 5.5; nao prova nada do jogo) =="
  echo "== SHA256 antes (somente leitura): main.lua real e candidato_v3"
  sha256sum $MAIN $V3
  echo "== build_bases.py"
  python $D/build_bases.py || rc=1
  echo "== tools/check_globals.py (sem saida = limpo)"
  python tools/check_globals.py $D/candidato_v4/main.lua; echo "rc=$?"
  for t in construcao recrutamento perda trabalhadores persistencia_bases painel_teclas orders_v4 coleta_sobre_v4; do
    echo; echo "== test_$t.py"
    python $D/test_$t.py 2>&1 | grep -v "$FILT"
    [ "${PIPESTATUS[0]}" -eq 0 ] || rc=1
  done
  echo; echo "== test_pilha_v4.py (22 etapas)"
  python $D/test_pilha_v4.py 2>&1 | grep -v "$FILT" | grep "^PASS\|^FAIL\|RESUMO\|^  \["
  [ "${PIPESTATUS[0]}" -eq 0 ] || rc=1
  echo; echo "== sensibilidade_bases.py (mutantes: cada um tem de ser pego)"
  python $D/sensibilidade_bases.py 2>&1 | grep -v "$FILT"
  [ "${PIPESTATUS[0]}" -eq 0 ] || rc=1
  echo; echo "== SHA256 depois (devem ser iguais aos de antes) e candidato_v4"
  sha256sum $MAIN $V3
  cat $D/candidato_v4/SHA256.txt
  echo "rc_final=$rc"
} > "$OUT" 2>&1
tail -60 "$OUT"
exit $rc
