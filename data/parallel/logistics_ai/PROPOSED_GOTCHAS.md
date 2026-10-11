# Gotchas propostos (IA_LOGISTICA) para a nota `knowledge/games/foxhole/...`

O CLAUDE_IA_LOGISTICA não editou o universal-modder. Quem registra é o coordenador; `um kb check` local, sem PR
sem autorização do usuário.

1. **Contador de "carga" não é logística.** O comboio inimigo do mod somava +1 carga ao chegar, sem origem,
   e o save não guardava esse número (todo continue devolvia `cargo0`). Para a interdição ter efeito
   rastreável, o caminhão precisa levar caixas debitadas de um estoque que pode acabar, e a perda precisa
   entrar num razão (inicial + produzido = estoques + trânsito + consumido + perdido) que dê para conferir
   pelo canal.
2. **Prioridade entre fábrica e reconstrução de caminhão.** Se a fábrica inicia um job de 80 bmat sempre que
   pode, um caminhão de 100 bmat (TruckC/TruckW Cloth100) nunca volta sob consumo contínuo, porque o bmat
   nunca acumula 100. Quando a frota está zerada, reserve bmat para o caminhão. A simulação mostrou isso do
   lado inimigo; do lado do jogador (mesma ordem) ainda é hipótese.
3. **Comboio de uma caixa desperdiça caminhão.** Despachar assim que existe uma caixa faz cada emboscada custar
   um caminhão inteiro por pouca carga, e o produto mais barato monopoliza a fábrica. Exija uma carga mínima
   ou o pedido completo da frente.
4. **O save arredonda.** O `sv.ser` grava números não inteiros com 3 casas. Um razão validado no load com
   tolerância 1e-6 recusa saves legítimos. Valide com folga (0,05) e, ao restaurar, absorva a sobra nos termos
   de origem para o razão em memória fechar exato. Nunca transforme essa sobra em estoque.
5. **Atribuir a interdição exige contrafactual.** A carga perdida antes da onda N afeta várias ondas, não só a
   seguinte. Um contador "perdas desde a última onda" subestima o efeito; use um estoque fantasma que se gasta
   à medida que as ondas o teriam consumido.
6. **Teste do chunk inteiro com fronteiras trocadas.** No harness lupa, código acrescentado ao fim do mesmo
   chunk pode reatribuir `local function` de topo (`spawnEnemies`, `waveSpawnPoint`, `isLocalAuthority`), e
   as funções do mod enxergam isso como upvalue. Assim dá para trocar só a fronteira de engine e chamar o
   `waveTick`/`ai.tick`/`sv.load` reais, sem copiar a implementação nem editar o `main.lua`.
7. **Débito depois do spawn, não antes.** O spawn de soldado ou caminhão pode falhar parcialmente; ator com
   `IsValid` e `bActorIsBeingDestroyed` não conta. Decida a quantidade antes, debite só o que nasceu e use
   `combat.wave` inalterado para detectar a onda que nem abriu.
