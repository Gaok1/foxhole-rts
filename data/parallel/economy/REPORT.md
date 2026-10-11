# ECONOMIA — proposta isolada, 2026-10-09

Não integrada. `economy.lua` é módulo puro com três novas receitas e contabilidade; não altera main.lua, não acessa UE4SS/RPC/inventário, não cria material inicial gratuito. `test_economy.py` executa o Lua real e compara schema/custos/conteúdo/tempo com os dados extraídos: PASS.

## Receitas reais

| Produto próprio | CodeName nativo | Custo por caixa | Conteúdo | Tempo nativo |
|---|---|---|---|---|
| rifle | RifleW | Cloth 100 | 20 rifles | 70 s |
| grenade | GrenadeW | Cloth 100 + Explosive 40 | 20 granadas | 100 s |
| medical | Bandages | Cloth 80 | 50 bandagens | 40 s |

Fonte: `data/game_costs.txt`, linhas 74, 12, 66. ESTUDO_MECANICAS mapeia Cloth=bmat, Wood=rmat, Explosive=pó explosivo. FirstAidKit (Cloth60/10/35s) e TraumaKit (Cloth80/10/50s) são ferramentas distintas, não substituem bandagem consumível. BloodPlasma existe, mas reviver não está implementado. Não adicionar consumo de ferramenta por cada cura.

**Bloqueio explícito:** cadeia atual produz só bmat, não Explosive. Granadas ficam impossíveis até ECONOMIA/RE mapear produção própria de explosivo com custo/fluxo e infraestrutura explícitos. O módulo recusa start por falta de Explosive antes de debitar Cloth. Nunca cortar recurso da receita ou fingir que bmat paga tudo. Não chamar isso de cadeia completa integrada.

## Contrato de integração proposto

- `factory.materials`: nomes nativos, valores inteiros; reservar todos custos atomicamente em start. Uma job por fábrica; avanço recebe dt simulado, já ajustado por pausa/velocidade pelo chamador. Cancelamento explícito reembolsa uma única vez; destruição não deve chamar cancelamento automaticamente (perda é decisão registrada).
- `factory.boxes` e `truck.cargo.boxes`: caixas fechadas. `depot.stock`: unidades. Entrega somente no depósito aliado, uma única vez; destino perdido conserva carga para retorno à fábrica. Destruição retorna registro de perda, nunca caixa ao estoque.
- Estoques atuais ammo/shirts possuem contabilidade distinta; integração deve preservá-los e genericizar logi.nextKind/need/load/deliver/cyclePrio/HUD/snapshot. **Não apenas acrescentar recipes e esperar funções hardcoded funcionarem.** Schema de persistência precisa cobrir material reservado, caixas, unidades, carga/perdas e job.
- Rifles: usar 1 unidade no recrutamento de fuzileiro na frente, além de 1 camisa atual; reservar recurso antes de spawn e devolver se spawn falhar. Outros papéis não podem usar RifleW indiscriminadamente. Arma do mod permanece mesh próprio; não perseguir inventário real.
- Granada: transferência de unidades do depósito a `m.grenades`; em throwGrenade consumir 1 só quando ordem válida e strike/projétil for aceito. Hoje cooldown concede granadas infinitas. Fogo cancelado não consome; morte perde carga do soldado.
- Médico: abastecer `m.bandages`; medicTick gasta 1 por ciclo de tratamento efetivo de aliado ferido, nunca em alvo cheio/inválido/fora de alcance. Esse consumo por ciclo é **regra própria do mod**, não rastro provado da cura nativa; ritmo/gate de equilíbrio necessário. Não descontar uma bandagem por frame. Cura passiva de ponto/posto precisa política explícita de material, senão contorna escassez de médico.
- E.consume verifica todos custos antes de debitar; chamador só executa efeito após reserva e deve reverter se aplicação/spawn falhar. Módulo não realiza efeito UE nem afirma transação engine verificada.

## Testes / gates

Offline PASS: parsing fail-closed de receita, explosivo ausente sem débito parcial, fábrica ocupada, produção só no prazo/uma vez, cancelamento/reembolso único, carga/capacidade, destino inimigo, retorno, morte/perda, consumo atômico, custos zero inválidos, dt inválido e conservação. Usa zero dependências novas (lupa já utilizado no repo).

Pendente: patch de integração completo; testes dos efeitos reais spawn/throwGrenade/medicTick, conservação com múltiplos soldados, restauração no save e UI; gate laboratório cadeia sem estoque inicial fictício, corte de transporte -> escassez -> retomada, carga destruída, produção e efeito de combate. Gate visual/input/equilíbrio não foi executado. Nenhuma tecla nova proposta.

Universal-modder consultado no começo (nota Foxhole/oráculos/Unreal); registrar Gotcha pelo coordenador: GrenadeW exige Explosive além de Cloth; Bandages consumível não equivale a FirstAidKit; nova receita não funciona só editando CFG.LOGI porque transporte/depósito/prioridade/save estão hardcoded ammo/shirts. Sem escrita concorrente na nota compartilhada.

## Integração completa proposta — segunda entrega

`build_patch.py` transforma **fonte atual** em memória (âncoras únicas, fail-closed); gera `economy_integrated.patch`. Não aplica ao main.lua. `functions.lua` e `save.lua` alimentam o gerador, não são um segundo runtime/estoque. `economy.lua` anterior é protótipo de referência, **não deve ser carregado junto** com integração: nenhuma duplicação de contabilidade.

### Fluxos efetivos do candidato

- CFG.LOGI inclui quatro produtos ammo/shirts/rifle/medical. Fuzil e bandagem seguem exatamente receita auditada; granada não tem receita/produção/prioridade porque falta Explosive. Produção utiliza fac/job/bmat existentes; fábrica desconta custo ao iniciar e só produz caixa ao concluir.
- nextKind, needs, pickDest, carga/capacidade, entrega e retorno genericizados. Conteúdo é caixa em fac/cargo; é unidade de produto em depot. Munição preserva seu contrato antigo de caixa de suprimento/reloads, sem fingir que 40 RifleAmmo nativos equivalem a tiros usados pelo mod. Demandas rifle4 e bandages20 são metas **próprias do mod**, não custos do jogo.
- Necessidade dos novos produtos usa ceil(falta/unidades), sem -0,5 legado: demandar 20 bandagens com caixa50 exige 1 caixa, não zero. ammo/shirts preservam regra anterior.
- Shift+L inclui fuzis/bandagens; sem tecla nova. HUD mantém texto antigo/inimigo e acrescenta stocks/cargo novos. Isso precisa reconciliar `extraHud` com patch INTERFACE multilinha; não substituir o painel por versão anterior inadvertidamente.
- Recrutamento manual de **rifle** exige 1 fuzil+1 camisa; outros papéis continuam consumindo camisa apenas (não usam RifleW indevidamente). Spawn fracassado não debita nada; sucesso debita no game thread síncrono. Mensagem fallback original "sem camisas" também deve ser ajustada pelo integrador quando a falta for fuzil.
- Médico aliado, com logística ativa, só trata ferido ao alcance se existe depósito aliado com bandagem dentro de POINT_RADIUS do médico. Débito de 1 após aumento efetivo de Health, respeito ao cooldown. Cura inimiga e partidas sem logística preservam behavior anterior. Não há item userdata/inventário nem bolso invisível duplicando bandagens.
- **Política explicitamente limitada:** cura passiva de pontos/postos ainda gratuita, diferente de médico ativo; spawn de composição inicial/recompensa/F6 grátis não passa por recruit e não consome fuzil. Assim esta entrega não afirma "todo reforço e toda cura dependem de estoque". Ampliar isso exige alterar política de start/ondas/medevac e equilíbrio, não truncar silenciosamente o tutorial/partida.
- Captura inimiga zera todos produtos do depósito; caminhão destruído perde cargo de todos produtos sem retorno/entrega fictícia.

### Save/restore necessário à contabilidade

Schema de logi.version=2; aceita legado sem version (novos estoques zero). Snapshot inclui fac/base/pontos novos, job já debitada e tempo restante/total, estado/HP/carga/depósito de destino/sucata/espera/reconstrução dos caminhões. Tabelas copiadas, sem alias/userdata/endereço.

Pré-validação completa de números/receita/prioridade/estado/capacidade/destino acontece **antes** de ready/start/reset. Dados negativos, cargo inválida ou versão desconhecida preservam estado corrente. Preflight de mundo indisponível idem. Restore substitui dados, não soma; repetir restore não duplica caixas. Destino perdido mantém caixa fechada no caminhão em returnCargo; fábrica só recebe após chegada confirmada pelo driver. job retomada não debita bmat novamente. Infraestrutura NÃO é reconstruída/persistida aqui; caminhões usam estacionamento de start, não XY/trajeto antigo. IDs de destino são índices dos pontos, como save atual; mudança de mapa/pontos precisa schema regional da task PERSISTENCIA.

**Limite transacional importante:** testes provam pré-validação e recusa de preflight, não rollback de exceção nativa após start/reset. ready/start carregam/checavam mundo no contrato existente; erro nativo/interrupção em spawn engine continua gate. Não apresentar validação Lua como transação engine.

### Reproduzir sem aplicar

Desde raiz do repositório:

```powershell
$env:PYTHONPATH='D:/tools/pylibs'
python data/parallel/economy/build_patch.py
python data/parallel/economy/test_integration.py
python data/parallel/economy/test_existing.py
```

Todos PASS nesta entrega. Test_integracao executa **todo chunk candidato** main.lua e substitui apenas limites engine (drive/spawn/ready/start) por spies; chama funções reais de produção, truckStep, recruit, medicTick, hit, snapshot/validateSave/restore. Regressão inteira test_orders executada contra candidato em memória também PASS.

Gates restantes: aplicação sequencial + reconciliação painel; globals/sintaxe; teste ao vivo receita -> produção -> transporte -> rifle recrutado/bandagem tratada sem estoques artificiais; contraste escassez/corte/retomada; save em meio a produção e cargo; falha engine pós-preflight; captura/novo mapa; legibilidade e equilíbrio. Atualizar README/TESTE_MANUAL para prioridade fuzis/bandagens e suprimento ativo médico/recrutamento. Task continua [ . ].

## Correção obrigatória de retorno físico (revisão do coordenador)

A devolução instantânea anterior foi removida do candidato, tanto em truckStep quanto restore. Contrato é o mesmo de `data/parallel/roads/RETURN_PATCH.lua`:

- destino perdido -> `tr.state="returnCargo"`, `tr.dest=logi.factory`, carga continua no caminhão; invalida route/routeDest/pathJob;
- estado returnCargo chama driver à fábrica; retorno false (sem rota/bloqueio/ainda andando) mantém tudo sem crédito;
- somente retorno true (chegada **fisicamente confirmada**) credita caixas na fac e limpa cargo/dest/state; nada em restore move crédito;
- snapshot/validateSave/restore preservam returnCargo/cargo. `dest=-1` é sentinela **serializada para fábrica**, não endereço. Base=0, pontos=índice legado >0. Não é garantia regional/IDs estáveis; reconciliação com CLAUDE_PERSISTENCIA obrigatória.

Testes atualizados: perda de destino no tick sem crédito; driver false mantém carga/fac0; chegada true devolve uma vez; save com destino perdido restaura returnCargo/fac0; salvar/restaurar durante retorno continua com carga; só chegada posterior retorna. Suite integração e test_orders candidato PASS.

**Gate impossível de contornar:** driver atual do main ainda anda em reta. Não aplicar este patch como transporte seguro sem integrar driver ESTRADAS com rota/sweep/chegada; testes apenas substituem o driver por false/true controlados. Não usar timeout ou falta de rota como chegada. Nenhum código/bloco CLAUDE foi modificado.
