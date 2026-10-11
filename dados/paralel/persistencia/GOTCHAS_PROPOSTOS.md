# Gotchas propostos (para a nota `knowledge/games/foxhole/...` do universal-modder; o coordenador registra)

Consultado no início: `um kb search` para save, persistence, serialization, "atomic write", foxhole (nota Foxhole,
gotchas 33–38; nota Minecraft com escrita atômica via temp + move). Nada foi escrito no universal-modder.

1. **Save como `return {...}` + `load` não é leitura segura.** Ambiente vazio impede `os`/`io`, mas não um laço
   infinito nem uma string gigante; e aceita qualquer coisa que avalie para tabela. Um parser de literais
   (tabelas `[k]=v`, números, strings `%q`, booleanos) com limites de bytes/profundidade/itens resolve sem
   dependência. `sv.ser` também escrevia NaN/inf como `0` e userdata como `nil` em silêncio: validar o que vai
   ser gravado e decodificar o próprio texto antes de trocar o arquivo.
2. **Windows: `os.rename` não sobrescreve.** O MSVCRT falha se o destino existe. Escrita atômica: temporário
   conferido por releitura → anterior vira `.bak` (ou `.corrupt`, se inválido) → temporário vira o save; falha
   devolve o anterior. Na leitura, ordem save → `.tmp` (queda entre os renames) → `.bak`. Comportamento real no
   Lua do UE4SS ainda é gate de laboratório.
3. **Infraestrutura implantada não sobrevive ao reinício e a carteira por endereço do mundo renasce cheia.**
   `S.deploy` era chaveado por `GetFullName..GetAddress` (muda a cada carga) e não ia para o save: continuar
   pedia Alt+L de novo e pagava outra vez com 1100 novos. Persistir o que foi **pago** (código, XYZ, yaw da
   ruína) e a carteira; na carga nova, refazer só sobre ruína correspondente (≤ 2 m, ≤ 1°), sem cobrar de novo,
   caminhões só até o número pago. Nunca persistir o endereço; ele só identifica a carga atual.
4. **Índice de ponto como identidade quebra se um ponto não volta.** O save guarda depósitos e postos por
   índice; `addPoint` pode recusar (sem superfície, sobreposição, limite). Conferir superfície/sobreposição
   antes de limpar a partida e, depois, comparar índice→coordenada; diferença = logística não restaurada (sem
   estoque inicial fictício no lugar) e autosave suspenso para não sobrescrever o save bom.
5. **Preflight antes de `clearSquad`.** O continue antigo destruía a partida atual e só depois descobria
   problemas. Ordem segura: ler/validar → mundo/superfície/ruínas/carteira/logística → refazer infra (com
   rollback próprio) → limpar e restaurar → verificar contagens.
6. **`logi.start` cria estoque de cenário.** Restaurar chamando start e depois atribuindo campos deixa estoque
   fictício se algo falha no meio; e o comboio inimigo voltava a `cargo0`. Validar tudo antes; em falha,
   `logi.reset` em vez de deixar o estoque inicial.
7. **Rotas não se salvam.** O grafo de ESTRADAS tem epoch com a sessão; rota antiga é inválida por construção.
   Salvar só estado/carga/destino por identificador e replanejar (`route/routeDest/pathJob = nil`).
