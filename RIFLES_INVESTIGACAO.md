# Rifles reais — evidências e próximo diagnóstico

2026-10-07. **Ainda não implementados.** Análise estática da cópia local, sem
execução do jogo nesta rodada. Endereços abaixo são VAs do build investigado;
não são API estável. Decompilações permanecem fora deste repositório.

## Caminho confirmado no material local

1. Thunk refletido `ServerTakePickup` em `0x14122a630`: valida pelo slot
   `+0xc18` e despacha a implementação pelo slot `+0xc20`.
2. Slot `+0xc20` aponta para `0x140b0bb00`: verifica objeto e chama slot `+0x9d0`.
3. Slot `+0x9d0` aponta para `0x140b10e50`: lê `ItemInstance`, verifica estado
   de atividade, outra condição via controller e capacidade dos holders; no ramo
   de sucesso chama `0x141225a20`, que despacha uma UFunction por ProcessEvent.
4. Portanto, neste caminho a flag `bIsLocalPlayerController` não aparece como
   condição direta no wrapper ou no corpo examinado. Isso é consistente com a
   tentativa t_pk3 ter falhado; não prova ausência de uso em funções chamadas.
5. O teste de atividade usa byte em `+0x12e0`, identificado no dump de reflexão
   como `CharacterActivityStateInternal`; valor diferente de zero retorna antes
   do caminho de pickup. Não alterar esse estado às cegas: primeiro observar.

Fontes locais: `D:\tools\foxhole-lab\re-agent\d11\14122a630.c`,
`re-agent\d5\140b0bb00.c`, `decomp12\140b10e50.c`,
`re-agent\d1\141225a20.c`, `re-agent\props_SimCharacter.txt`, todos sob
`D:\tools\foxhole-lab`.

## Armadilha encontrada na ferramenta de RE

O helper local `re-agent/pe.py:vtable_of` segue a primeira chamada do construtor
e procura uma tabela no construtor base. Retornou `0x143528bf8` tanto para
SimCharacter quanto PlayerCharacter, mas o construtor PlayerCharacter
`0x141201dc0` escreve depois **`0x143751bf8`** em `[rbx]`.

Confirmado lendo as instruções e os ponteiros do PE com pefile/capstone, sem
abrir processo. Nos dois slots relevantes (`+0x9d0`, `+0xc20`) os destinos são
iguais nas duas tabelas, portanto essa diferença **não explica** o pickup vazio.
Não generalizar a igualdade para outros métodos nem para a vtable do Blueprint
em execução. O helper ainda não foi corrigido: conferir a escrita final manualmente.

Outra cautela: pseudocódigo de funções dos holders mostra parâmetros aparentemente
não usados. Antes de concluir que o holder é ignorado, conferir assembly/protótipo;
Ghidra pode perder argumentos com convenções internas/otimizações.

### Atualização: argumento do holder confirmado no assembly

Em `0x140a5c3e0`, RCX (primeiro argumento, o holder) não é sobrescrito antes do
`call 0x140a622d0` em `0x140a5c43f`. RDX passa a apontar para o resultado local
e R8 para a cópia do item. Portanto o holder **é repassado**: o pseudocódigo que
mostrava `local_68` como primeiro argumento estava incorreto nesse ponto.
O retorno compara a quantidade resultante com zero; ainda não prova aquisição.
Confirmado por leitura estática com o helper pefile/capstone, não por execução.

Próxima informação necessária: estado real dos holders/atividade do soldado.
Não acrescentar outro quebrador de RPC nem zerar atividade sem essa medição.

## Próximo teste: medir antes de mudar

`D:\GitHub\foxhole-rts\tools\probe_inventory.lua` observa cada soldado: classe,
HP, atividade, controller, PlayerState, flag local, holders e arrays de itens.
Não chama RPC de pickup, não cria itens e não muda estado.

Depois de confirmar isolamento e abrir a cópia com canal local habilitado:

1. Criar um soldado com F6 e aguardar estabilizar.
2. Publicar o diagnóstico no canal por cópia temporária e rename, para evitar
   leitura de um arquivo parcialmente escrito:

   ```powershell
   # Execute apenas quando nao houver outro comando pendente no canal.
   $lab = 'D:\tools\foxhole-lab'
   if (Test-Path "$lab\cmd.lua") { throw 'Comando anterior pendente' }
   Copy-Item D:\GitHub\foxhole-rts\tools\probe_inventory.lua "$lab\probe.pending"
   Move-Item -LiteralPath "$lab\probe.pending" -Destination "$lab\cmd.lua"
   ```

3. Ler `cmd.out` apenas após nova gravação e término com a linha `FIM` deste probe.
   Saída antiga não conta como sucesso. Um único operador deve usar o canal.
4. Se atividade não for zero ou objetos necessários estiverem ausentes, investigar
   essa pré-condição antes de tentar mais flags/hooks de RPC.
5. Após qualquer futura tentativa de aquisição, medir **inventário e equipamento**,
   não só retorno sem exceção ou desaparecimento do pickup.

Sintaxe do probe verificada offline; execução e resultados em jogo ainda pendentes.
