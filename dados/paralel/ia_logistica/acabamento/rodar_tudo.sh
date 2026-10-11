#!/bin/bash
# Roda todos os testes do acabamento e grava SAIDA_TESTES.txt (so esta pasta; nada em D:\FoxholeLab, nada no main.lua).
#   cd /d/GitHub/foxhole-rts && bash dados/paralel/ia_logistica/acabamento/rodar_tudo.sh
# A varredura em grade (sweep_echain.py --grid, ~25 min) fica fora: seu resultado esta em GRADE_RESULTADOS.txt.
cd "$(dirname "$0")/../../../.." || exit 1
export PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
A=dados/paralel/ia_logistica/acabamento
OUT=$A/SAIDA_TESTES.txt
: > "$OUT"
fail=0
run() {  # run <titulo> <comando...>
    local titulo="$1"; shift
    echo "\$ $titulo" >> "$OUT"
    "$@" 2>&1 | grep -v '^\[FoxholeRTS\]' | grep -v '^$' | cut -c1-230 >> "$OUT"
    local rc=${PIPESTATUS[0]}
    echo "rc=$rc" >> "$OUT"; echo >> "$OUT"
    [ "$rc" -eq 0 ] || fail=1
}
run "python $A/build_patch_v2.py (IA v2: patches + candidato, main.lua intacto)" python $A/build_patch_v2.py
run "python $A/build_persistencia_v2.py (pilha completa em $A/main_final_v2.lua)" python $A/build_persistencia_v2.py
run "python tools/check_globals.py $A/main_candidato_v2.lua" python tools/check_globals.py $A/main_candidato_v2.lua
run "python tools/check_globals.py $A/main_final_v2.lua" python tools/check_globals.py $A/main_final_v2.lua
run "python $A/test_bmat_caminhao.py   (item 2)" python $A/test_bmat_caminhao.py
run "python $A/test_elogi.py   (item 3)" python $A/test_elogi.py
run "python $A/test_persistencia_v2.py   (item 3: test_persistencia contra a variante)" python $A/test_persistencia_v2.py
run "python $A/test_ia_logistica_v2.py   (itens 1/3: test_ia_logistica contra a variante)" python $A/test_ia_logistica_v2.py
run "python $A/test_regressao_v2.py   (test_orders + economia/test_integracao + ia + globals na pilha completa)" python $A/test_regressao_v2.py
run "python $A/sweep_echain.py   (item 1: tabela antes/depois; saida tambem em TABELA_CALIBRACAO.txt)" python $A/sweep_echain.py
run "python $A/sweep_echain.py --sens   (item 1: sensibilidade; SENSIBILIDADE.txt)" python $A/sweep_echain.py --sens
run "python $A/sweep_echain.py --cad   (item 1: controle em cadencias rapidas; CADENCIAS.txt)" python $A/sweep_echain.py --cad
# controle: os testes ORIGINAIS (inalterados) seguem passando contra os modulos originais
run "python dados/paralel/ia_logistica/test_ia_logistica.py   (original, controle)" python dados/paralel/ia_logistica/test_ia_logistica.py
run "python dados/paralel/persistencia/test_persistencia.py   (original, controle)" python dados/paralel/persistencia/test_persistencia.py
python $A/sweep_echain.py 2>&1 | grep -v '^\[FoxholeRTS\]' | grep -v '^$' > $A/TABELA_CALIBRACAO.txt
python $A/sweep_echain.py --sens 2>&1 | grep -v '^\[FoxholeRTS\]' | grep -v '^$' > $A/SENSIBILIDADE.txt
python $A/sweep_echain.py --cad 2>&1 | grep -v '^\[FoxholeRTS\]' | grep -v '^$' > $A/CADENCIAS.txt
if [ "$fail" -eq 0 ]; then echo "TUDO PASS" >> "$OUT"; else echo "HA FALHAS" >> "$OUT"; fi
tail -1 "$OUT"
exit $fail
