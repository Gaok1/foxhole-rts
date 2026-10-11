# NOTAS_PROGRESSO (etapa 2 BASES_AVANCADAS) - para retomar se a sessao cair
Estado (2026-10-10): leitura/projeto concluidos; escrevendo bases_cfg.lua, bases_funcs.lua, build_bases.py.
Plano: build_bases.py le coleta_manual/candidato_v3/main.lua (so leitura) -> candidato_v4/main.lua + bases.patch + SHA256.txt.
Depois: harness_bases.py, test_*.py, test_pilha_v4.py (copia adaptada de test_pilha_v3), test_orders_v4.py (+Shift+J), RELATORIO.md, rodar_tudo.sh, SAIDA_TESTES.txt.
CUIDADO: nao rodar test_pilha_v3.py original (grava saida_testes_v3.txt na pasta da coleta; ja rodou 1x por engano, mesmo tamanho).
Feito: (atualize abaixo)
- bases_cfg.lua e bases_funcs.lua escritos (funcoes fwd*, spawnSite/Commit novos, recruit logistico). Falta: build_bases.py (ancoras), depois testes.
- build_bases.py escrito e roda (v4 gerado, compila). Falta: harness_bases.py + testes + pilha v4 + RELATORIO.
- harness_bases.py e test_construcao.py escritos (depurando)
- test_construcao.py PASS (depurado). Proximos: test_recrutamento, test_perda (corte/destruicao/captura/derrota), test_trabalhadores, test_persistencia_bases, test_painel_teclas, test_pilha_v4, test_orders_v4, coleta sobre v4, RELATORIO
- test_recrutamento.py PASS
- test_perda.py escrito (depurando)
- test_perda.py PASS (fwdAudit ajustado p/ dead). Falta: test_trabalhadores, test_persistencia_bases, test_painel_teclas, pilha_v4 etc.
- test_trabalhadores PASS; test_persistencia_bases escrito (depurando)
- test_persistencia_bases PASS. Falta: test_painel_teclas, test_orders_v4 (copia), test_pilha_v4, coleta sobre v4, RELATORIO, rodar_tudo, SAIDA
- test_orders_v4.py e test_coleta_sobre_v4.py PASS. Falta: test_painel_teclas, test_pilha_v4, RELATORIO, rodar_tudo, SAIDA
- test_painel_teclas PASS (9/9). Falta: test_pilha_v4 (copia de test_pilha_v3 -> candidato_v4, log proprio), RELATORIO, rodar_tudo, SAIDA
- test_pilha_v4.py PASS 22/22 (spawnCapable passou a honrar pointSpawn=true; adaptacoes V4 em 05/08/09). Falta: rodar_tudo.sh, SAIDA_TESTES.txt, RELATORIO.md, SubagentHandback
- sensibilidade_bases.py 17/17 mutantes pegos; testes extras em construcao/perda. Falta: rodar_tudo.sh (rodar), RELATORIO.md, SubagentHandback
- CONCLUIDO: rodar_tudo.sh rc=0, SAIDA_TESTES.txt gerado, RELATORIO.md escrito. SHA v4 025e3b80...aaab0. So falta o SubagentHandback.
