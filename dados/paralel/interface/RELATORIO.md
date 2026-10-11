# INTERFACE — entrega offline, 2026-10-09

## Evidência existente / contrato

- `main.lua:4550–4684`: HUD Slate nativo não expõe TextBlocks; renderer do mod clona `CrosshairWidget_C`, usa `WidgetTree.RootWidget` (CanvasPanel), `StaticConstructObject(UMG.TextBlock)`, `AddChildToCanvas`, `SetAutoSize`, `SetPosition`, `SetText`, `SetVisibility` e `AddToViewport(50)`. Métodos já utilizados e registro de captura no código; nenhuma sessão nova certificada por esta task.
- `hudTick`: 0,25 s **tempo real**, inclusive pausa; remove widget quando RTS desliga. Troca de mapa ainda precisa gate específico: não confundir IsValid do widget antigo com dono/world atual.
- `logi.hudLine`: hoje concatena a logística numa linha extensa. Proposta `painel.patch` substitui só essa função, aproveitando TextBlock existente com linhas para produção, estoque físico/meta, caixas versus unidades e cada caminhão/carga/destino. Não cria actor, API UMG nova, tecla ou estoque.
- Uma tarefa de produção (`logi.job`), não fila arbitrária: debitada ao iniciar, caixa acrescentada ao completar. Não chamar isso de fila de pedidos do jogador.
- `fac.ammo`, `fac.shirts`, `tr.cargo` = **caixas**. `depot.ammo` = suprimento de munição; `depot.shirts` = camisas individuais; receita de camisa tem `units=10`. `logi.need` desconta trânsito; indicador do painel usa estoque físico e meta, não afirma escassez não atendida.
- `logi.depots()` cria/reusa depósitos dos pontos aliados via `depotOf`; proposta não introduz mutação adicional além da função já usada no HUD. Transporte destruído mostra carga perdida, não fictícia entrega pendente.

## Caixa de seleção: solução mínima, ainda NÃO implementada

`mouseTick` guarda **ponto de chão**, e `selectBox` testa retângulo XY no mundo com margem 50 cm. Desenhar retângulo entre posições de tela pode divergir em relevo/câmera. Rastrear antes de mudar semântica. Preferência: projetar quatro cantos do mesmo retângulo XY/margem sobre o chão e renderizar bordas não interativas no Canvas; se projeção não estiver disponível, definir/testar seleção em coordenadas de tela como alteração explícita de comportamento.

Sondas exigidas ao LABORATORIO (nenhuma executada pelo agente):
1. Inspecionar **somente UFunctions conhecidas/refletidas** do PlayerController/WidgetLayoutLibrary para projeção, conversão viewport/DPI e saída dos parâmetros. `GetMousePosition` já aparece no código, com saída na primeira tabela; projeção e escala NÃO estão comprovadas. Não chamar nomes presumidos no main.lua.
2. Descobrir classe e propriedades de UMG Image/Border e CanvasSlot: prova de construtor, tinta/transparência, posição/tamanho e hit-testing. Nenhuma chamada nova desses tipos neste patch.
3. Oráculo: usuário arrasta nos quatro sentidos; gravar pontos inicial/final de chão, coordenadas de tela, quatro cantos projetados e elenco selecionado; câmera estática/depois movida durante arrasto, zoom baixo/alto, terreno irregular e DPI/resolução diferentes.
4. A caixa deve surgir apenas após DRAG_MIN, sumir ao soltar/RTS desligar/mapa mudar, Shift somar sem bloquear direita/câmera, sem widget capturar mouse. Atualizar cada frame, não a cada 0,25 s.

## Foco e alertas

Reusar controles existentes Ctrl+L/Q/E/Espaço; o patch os explicita, não finge que linhas de texto são botões. Botões de foco de cada caminhão/instalação e alertas de estoque com deduplicação permanecem subtasks abertas: requerem contrato de ação/destino válido e gate de input. Não produzir alertas repetidos a cada refresh nem referências a atores destruídos.

## Gate de integração / visual / usuário

- Offline: `PYTHONPATH=D:/tools/pylibs python dados/paralel/interface/test_interface.py` PASS: produção, unidades, trânsito, destruição, metas, inatividade, não alteração de estoques.
- Integrador: aplicar `painel.patch` só após estabilidade; conferir fontes/âncoras e executar suíte existente. São zero novos locais de topo.
- Laboratório: painel em partida/logística ativa, pausa, logística desligada, mapa novo, depósito perdido, caminhão morto/recriado; registrar captura e dados do mesmo instante. Checar sobreposição, largura/altura nos vários zooms/resoluções, ajuda F5 e alertas nativos. Multilinha usa HUD atual, sem clipping/scroll provados. Se elenco exceder altura: ajustar layout antes de aprovar, não esconder estoques/veículos silenciosamente.
- Usuário: esquerda/Shift/direita/câmera/F5/Ctrl+L/Q/E/Espaço continuam funcionando. **Nenhuma entrada real foi testada aqui.** Caixa requer sondas anteriores, não está entregue.
- Status geral: proposta testada, NÃO feature integrada/concluída. main.lua não alterado; jogo/canal/processos não acessados.

## Universal-modder

Consultados reverse-engineering (oráculos/rastro real), mod-any-game e playbook Unreal. `um kb search foxhole` encontrou a nota existente; busca "foxhole widget" não retornou match. Coordenador deve registrar Gotcha na nota compartilhada (para evitar escrita simultânea): painel mistura caixas e unidades; retângulo XY do seletor não equivale automaticamente a retângulo de tela; chamadas UMG de projeção/DPI/borda ainda exigem sonda. Executar kb check no fim do lote.

## Revisão de preservação funcional

- Mantida linha de carga inimiga e aviso de comboio fora do assalto, iguais ao contrato anterior. Não afirma quantidade/posição que a fonte não fornece.
- Auditados todos os estados aliados: idle/res inicia coleta; idle/sup retorna ou aguarda fábrica (não afirmar que já chegou); toField, loading, toRef, toDep, dead. Destinos derivados de estado quando tr.dest não existe. nomes dos pontos vêm de pt.name -> dep.name; base usa "base".
- job.total sempre é produzido por factoryStep, mas snapshot/restore atuais NÃO persistem job nem total (restore chama start/reset). Proposta agora mostra apenas tempo restante quando total ausente, sem inventar duração reconstruída. Persistência incompleta é outra task, não corrigida pela UI.
- Testes adicionados: cada estado aliado, nomes de ponto, job.total ausente, carga inimiga, comboio e ocultação no assalto. PASS.
