# Revisão final offline — somente inspeção, sem executar testes

Revisão na janela de controle A1 solicitada pelo coordenador. Nenhum teste CPU/gerador/script Lua executado. Nenhuma alteração main.lua, laboratório ou entregas CLAUDE.

- Fonte atual inspecionada ainda contém CFG.LOGI ammo/shirts, fac original, logi.need/hudLine/restore originais. A otimização de contorno não adicionou economia nem painel. Portanto patch econômico ainda é proposta independente, não código publicado; não reaplicar patch antigo de arquivo inteiro sobre fonte otimizada.
- build_patch.py faz substituições pontuais com âncoras assert únicas para edits, funções trocadas em limites de texto. Não toca contorno/callbacks; os testes anteriores em memória não certificam **esta** fonte nova até nova execução fora da janela controlada.
- Ordem futura: gerar economia contra fonte do integrador, aplicar economia; substituir hudLine pelo painel revisado; aplicar `reconciliation_extraHud.patch` conceitual sobre painel. Preservar função `extraHud` inserida pela economia. Não executar gerador econômico depois de já aplicar painel: âncora do return antigo deve falhar, não forçar patch.
- Reconciliação mínima entregue: painel chama extraHud somente se existir, uma vez; mantém a sua linha inimiga/convoy fora do assalto; extraHud adiciona stocks fábricas/depósitos/cargas rifles+bandagens. Estado returnCargo tem nome/destino legíveis. Munição/camisas ausentes no cargo genérico viram zero, sem format nil.
- Patch de reconciliação é unified diff de quatro linhas sobre painel.lua, com números conferidos por Select-String; não foi aplicado nem validado nesta janela. Regenerar painel.patch sobre fonte atual após reconciliação.
- UI continua sem validação de clipping/altura, layout e input; extraHud longo pode exceder largura. Não chamar isso de painel profissional aprovado. Pode reconverter extraHud para várias linhas após gate visual, sem ocultar produtos/cargas.
- Gate ESTRADAS continua: returnCargo não pode entregar nem devolver stock sem chegada física; driver em reta atual é insuficiente. Gate CLAUDE_PERSISTENCIA: IDs base0/factory-1/ponto índice são apenas legado local, não garantia regional. Nenhuma alteração em blocos CLAUDE.

Após término A1: repetir test_integration.py, test_existing.py e testar candidato painel+extraHud com mocks de estoque/carga/returnCargo/inimigo/assalto, antes de integração. Testes prévios PASS são de fonte anterior, não resultado desta janela.
