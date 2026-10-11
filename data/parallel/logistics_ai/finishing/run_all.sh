#!/bin/bash
# Roda todos os testes do acabamento e grava TEST_OUTPUT.txt (so esta pasta; nada em D:\FoxholeLab, nada no main.lua).
#   cd /d/GitHub/foxhole-rts && bash data/parallel/logistics_ai/finishing/run_all.sh
# A varredura em grade (sweep_echain.py --grid, ~25 min) fica fora: seu resultado esta em RESULTS_GRID.txt.
cd "$(dirname "$0")/../../../.." || exit 1
export PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
A=data/parallel/logistics_ai/finishing
OUT=$A/TEST_OUTPUT.txt
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
run "python $A/build_persistence_v2.py (pilha completa em $A/main_final_v2.lua)" python $A/build_persistence_v2.py
run "python tools/check_globals.py $A/main_candidate_v2.lua" python tools/check_globals.py $A/main_candidate_v2.lua
run "python tools/check_globals.py $A/main_final_v2.lua" python tools/check_globals.py $A/main_final_v2.lua
run "python $A/test_truck_bmat.py   (item 2)" python $A/test_truck_bmat.py
run "python $A/test_elogi.py   (item 3)" python $A/test_elogi.py
run "python $A/test_persistence_v2.py   (item 3: test_persistencia contra a variante)" python $A/test_persistence_v2.py
run "python $A/test_logistics_ai_v2.py   (itens 1/3: test_ia_logistica contra a variante)" python $A/test_logistics_ai_v2.py
run "python $A/test_regression_v2.py   (test_orders + economy/test_integracao + ia + globals na pilha completa)" python $A/test_regression_v2.py
run "python $A/sweep_echain.py   (item 1: tabela antes/depois; saida tambem em CALIBRATION_TABLE.txt)" python $A/sweep_echain.py
run "python $A/sweep_echain.py --sens   (item 1: sensibilidade; SENSITIVITY.txt)" python $A/sweep_echain.py --sens
run "python $A/sweep_echain.py --cad   (item 1: controle em cadencias rapidas; CADENCES.txt)" python $A/sweep_echain.py --cad
# controle: os testes ORIGINAIS (inalterados) seguem passando contra os modulos originais
run "python data/parallel/logistics_ai/test_logistics_ai.py   (original, controle)" python data/parallel/logistics_ai/test_logistics_ai.py
run "python data/parallel/persistence/test_persistence.py   (original, controle)" python data/parallel/persistence/test_persistence.py
python $A/sweep_echain.py 2>&1 | grep -v '^\[FoxholeRTS\]' | grep -v '^$' > $A/CALIBRATION_TABLE.txt
python $A/sweep_echain.py --sens 2>&1 | grep -v '^\[FoxholeRTS\]' | grep -v '^$' > $A/SENSITIVITY.txt
python $A/sweep_echain.py --cad 2>&1 | grep -v '^\[FoxholeRTS\]' | grep -v '^$' > $A/CADENCES.txt
if [ "$fail" -eq 0 ]; then echo "TUDO PASS" >> "$OUT"; else echo "HA FALHAS" >> "$OUT"; fi
tail -1 "$OUT"
exit $fail
