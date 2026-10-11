# Auditoria inicial do contorno — 2026-10-09

Leitura estática, não diagnóstico da causa nativa. Não há correção aplicada nem validação ao vivo nova.

## Evidência do código atual

- `destroyMarker` chama `anim.untrack` e `rts.clearOutline` antes de remover os demais marcadores.
- `clearOutline` destrói as cópias, apaga `outlineSources` e limpa `outlineParts`.
- `updateOutline` chama UFunctions em fontes e cópias armazenadas sem revalidar sua vida útil a cada uso.
  A fonte pode continuar `IsValid` até o GC; esse teste sozinho não prova segurança.
- `outlineDepth` conserva a lista de componentes até `clearOutline`; equipamentos substituídos enquanto
  a unidade permanece selecionada merecem reprodução específica.
- `setOutline` protege a criação com pcall, mas pcall não protege falhas nativas. Seu rollback não é
  evidência de segurança diante de GC/substituição de componente.
- O MID de preenchimento é ancorado via `AddOrUpdateBlendable` antes da configuração; os MIDs de cópias
  são associados aos componentes. Não atribuir as quedas a MID sem demonstrar perda dessas referências.
- O loop principal usa `LoopInGameThreadAfterFrames`; o erro de Registry do lote 17 exige separar
  callback persistente do mod e callbacks temporários das sondas. Não repetir hotpatch como prova limpa.

## Reprodução proposta para o dono do laboratório

1. Carga limpa; registrar hash, PID, mapa e início/fim de cada etapa em arquivo fora do repo.
2. Controle sem seleção; depois um soldado selecionado, sem callbacks de amostragem adicionais.
3. Alternar seleção e limpar/recriar soldados; registrar contagens de cópias e fontes por etapa.
4. Morte do selecionado pelo sistema próprio do mod: conferir remoção de referências antes da notificação
   de saúde, sem acessar AnimInstance/corpo depois da transição.
5. Testar componentes separadamente em variantes experimentais isoladas, preservando a fonte aprovada.
6. Testar coleta de memória somente com chamada refletida previamente confirmada e em etapa separada.
7. Só depois aumentar seleção e medir custo por quadro; estabilidade e aparência são gates distintos.

Critério: registrar qual transição falha e reproduzir com carga limpa antes de concluir causa ou corrigir.
Nenhuma ausência de crash num teste curto prova estabilidade prolongada.


## Auditoria complementar — agente estabilidade, 2026-10-09

### Defeito comprovado offline e proposta entregue

`updateOutline` (main.lua:3800) não testa pawn/clone em destruição nem validade da fonte antes de chamar
UFunctions. `test_lifetime.py` executa a função real extraída da fonte: os três casos continuam a acessar
componentes/atores na versão atual. A substituição `update_outline.before.lua` → `update_outline.after.lua`
limpa o conjunto antes de qualquer acesso em tais estados. Caso vivo preservado. Resultado: OK em 2026-10-09.
A proposta não altera main.lua. Gate ao vivo obrigatório antes de dizer que resolveu as quedas.

Limites: fonte ainda IsValid durante destruição não é capturada; componentes substituídos mas vivos também
não são detectados. `bActorIsBeingDestroyed` é propriedade do ator, não deve ser inventada no componente.
Não ler MasterPoseComponent/AnimClass. Esta defesa cobre estados observáveis, não demonstra segurança nativa.

### Callers e ordem de limpeza

- `setMarker` chama `setOutline`; `stratTick` repete por quadro para aliados/inimigos e limpa CustomDepth do olho.
- `reap`: `destroyMarker` → `clearOutline` → `anim.retire` → `OnRep_Health` → TTL do corpo. Ordem correta
  no caminho comum; `anim.retire` só tem esse caller. O teste existente de morte cobre a ordem.
- `resetCombat`/limpeza de sessão e remoção de inimigos: `destroyMarker` antes de `K2_DestroyActor`.
- `corpseTick` destrói corpos já retirados de listas e sem contorno; save/continue chama OnRep_Health para HP vivo.
- Médico, tendas e pontos notificam OnRep_Health com HP positivo. Não foi demonstrado que substituam malhas.
- `clearOutline` captura clones numa lista, destrói com pcall e zera fontes, depois limpa depth. Se destruição
  de clone falhar em Lua, referência é descartada mesmo assim; pode sobrar clone. Falha nativa não é contida.
- `outlineDepth` reutiliza componentes até limpeza. Troca de equipamento enquanto selecionado pode deixar
  cópias/depth antigos: hipótese funcional a reproduzir, não causa atribuída dos crashes.
- `outlineFill`: MID referenciado por blendable do volume; MID do clone por material do componente.
  Cache Lua não garante raiz de GC, mas há ancoragem do engine no código. Não atribuir GC sem teste.
- Criação testa IsValid mas não bActorIsBeingDestroyed no retorno do spawn do clone; semelhante ao problema
  documentado dos caminhões. Requer sonda/falha simulada antes de ampliar o patch.

### Callbacks persistentes

Há um loop principal `LoopInGameThreadAfterFrames(1, ...)`, hook de animação por ABP, hooks de controller,
loop do canal `LoopInGameThreadWithDelay(1000, ...)` e callbacks ExecuteInGameThread das teclas.
Nenhum callback por clone é criado pelas funções de contorno. Portanto número de clones não demonstra
crescimento de referências de callbacks. `Lua::Registry::get_function_ref` permanece sem origem isolada.
Hotpatch/sonda com callback extra não é controle limpo para o loop principal.

## Matriz de sondas para o coordenador (sem executá-las aqui)

Todas em carga limpa, hash/PID/mapa/log inicial e final, sem botloop, sem hotpatch, sem input injetado.
Variantes temporárias por cópia de fonte preservada; somente dono do laboratório publica.

| Etapa | Variante / transição | Evidência mínima | Gate |
|---|---|---|---|
| A | Sem seleção, 10 min, sem novo callback | log de frame vivo/início-fim, crash/log | controle |
| B | 1 selecionado, 28 clones, 10 min | contagem peças/fontes, frame/prof, captura | reprodução base |
| C | Mesma B + patch proposto | mesmos tempos/estado | comparar, não concluir por ausência curta |
| D | 100 selecionar/desselecionar em máquina de estados do frame | clones criados/destruídos e nil após limpeza | zero referência residual |
| E | 20 morte/recriação pelo mod | limpeza antes OnRep_Health, sem acesso posterior | lifetime |
| F | 1 peça por execução: casaco, arma, cabeça, mãos, pernas, costas, capacete | 4 clones/peça e hash variante | isolar peça |
| G | Clone skinned sem MasterPose vs com MasterPose em execuções distintas | atores/tempo/stack | hipótese MasterPose, aparência só diagnóstico |
| H | Equipamento substituído enquanto selecionado | lista real antes/depois, fonte de clone atual | cache obsoleto |
| I | GC refletido somente após confirmar chamada nos dados do jogo | antes/depois e stack/log | hipótese GC |
| J | 1/3/10/25 selecionados, zoom alto, 60s por degrau | profile stratTick ms/quadro, 28*N atores, capture | custo |

Sondas de medição usam estado por quadro já existente, não dezenas de callbacks UE4SS temporários.
Não automatizar F/G/I até contrato refletido confirmado. Toda falha repete carga limpa no mesmo hash antes
de atribuir causa. Separar estabilidade, aparência, input real e desempenho.

### Gotcha sugerido para universal-modder (integração pelo coordenador)

Update de contorno chamava UFunctions mesmo com pawn/clone bActorIsBeingDestroyed ou fonte IsValid=false;
mock reproduz e preflight bloqueia. Isso NÃO explica crashes UE4SS do lote 17; fonte IsValid=true durante
retirada/troca ainda precisa rastro real. pcall protege erro Lua, não lifetime nativo.

Revisão do coordenador: guard aplicado também em outlineDepth para limpeza de pawn em destruição não tocar fontes. Teste passou usando clearOutline/outlineDepth REAIS extraídos, não stub de limpeza. Aplicar os dois blocos separados por linha vazia, não substituir documento inteiro.
