# Morte nativa de veículo — 2026-10-11

Investigação OFFLINE, sem canal/jogo, RPC, HP write, edição main.lua ou chamadas por
offset. Observação do usuário: caminhão explodiu e deixou algo; objeto não identificado.

## Fluxo comprovado estaticamente

1. `SimVehicle` DamageableActor interface0x140d81a00 debita Health real. Ao chegar
   a zero chama virtual+0xd60, que na vtable nativa0x1436290f8 aponta0x140d970b0.
2. Esse lifecycle já é chamado automaticamente pela aplicação de dano autoritativa:
   trata flags do DamageType, collision/effects, ocupantes/componentes e finaliza
   em helper0x140d6a8c0. Não chamar callback de morte manualmente nem duplicá-lo.
3. Final0x140d973b7 carrega constante float **15.0** de0x1433eb978 e a passa ao
   helper0x140d6a8c0. Helper chama virtual+0x378 em0x140d6a9cb, apontando
   Actor0x1422e85e0. O wrapper refletido Engine.Actor.SetLifeSpan0x1429faac0
   também chama virtual+0x378: nome comprovado, não palpite pelo timer.
4. SetLifeSpan escreve InitialLifeSpan e registra timer no caminho de autoridade.
   Logo ator continuar IsValid/nonbeingDestroyed imediatamente apósHP0 é compatível
   com **casco transitório e TTL nativo15s**; não prova callback faltante.

## OnRep_Health

SimVehicle.OnRep_Health wrapper0x1412499a0 despacha virtual+0xe88→0x140d83470,
que atualiza estado e efeitos condicionados por modo/contexto; chama helper0x140d9a270.
Isso é notificação local refletida, não o aplicador de dano ou gatilho obrigatório
da morte autoritativa. O caminho de TakeDamage já invocou morte acima.
Não transportar automaticamente workaround de OnRep do personagem para o caminhão.

## Evidência e limites

Oracle PID12456 comprovou Health900→873→840→0, sem HP artificial, usando tipos
nativos. Usuário confirmou explosão/drop. Cleanup removeu ator logo após; **TTL15s
não foi observado ao vivo**, só identificado estaticamente. Drop desconhecido: não
presumir inventário/carga/perda contábil; não perseguir sistema de inventário nativo.

Gate posterior opcional, no lote adequado: ator exclusivo, morte pelo dano real,
observar GetLifeSpan, Health, classe/posição/Hidden e destructionflag por>15s SEM
cleanup antecipado; nunca escrever lifespan/Health nem chamar OnRep/morte manual.
Tratar Health0 como morto para cache/lógica mesmo que IsValid aindatrue.

Disassembly externo protegido: `D:/tools/foxhole-lab/vehicle-death-native-static.txt`.
Nada integrado ao mod ou anunciado como rifle/impacto completo nesta investigação.
