# BASES_AVANCADAS — decisões D1–D7 (2026-10-09)

O usuário delegou as decisões de design ao Claude orquestrador ("faça o que for melhor pro game").
Referência: `SPEC.md` §"Decisões abertas" e ROADMAP.md fase 3 ("de onde vêm os soldados").

- **D1 — Shift+J (não J duplo).** Hoje `J` adiciona ponto de controle (`addPoint`); dar a ele um segundo sentido
  por toque duplo confunde e pode criar ponto sem querer. Ctrl+0..9 já está todo ocupado. Shift+J fica ao lado do
  `J` (bases moram sobre pontos) e a especificação o conferiu como livre. Primeiro Shift+J mostra custo e local;
  o segundo em 4 s confirma. Exige atualizar `MANUAL_TEST.md` e o teste de teclas de `tools/test_orders.py`
  (na integração; na etapa 2, numa cópia).
- **D2 — Aceita.** No ramo logístico, ponto sem base deixa de ser local de reforço; `CFG.SPAWN.pointSpawn`
  devolve o comportamento antigo. É o que dá sentido à base avançada e ao corte de abastecimento.
- **D3 — Aceita.** Paga com `logi.bmat` da fábrica, debitado só após spawn validado; sem bmat, pedido pendente
  com reserva (a fábrica para de gastar até juntar), respeitando a reserva de caminhões já existente.
  Prioridade quando há caminhão destruído: caminhão primeiro (a renda vem antes da expansão).
- **D4 — Aceita.** v1 só sobre pontos de controle próprios.
- **D5 — Aceita.** Inimigo não constrói bases na v1; a frente inimiga continua o estoque agregado da logistics_ai v2.
- **D6 — Aceita.** Assalto inalterado (sem bases, mão de obra abstrata).
- **D7 — Aceita como provisória.** 15 = slots de caixa até a sonda A3/B1 provar outra coisa; tudo em `CFG.FWD`.

**Risco do início (fuzis = 0 na base):** é a rampa desejada (estilo Age of Empires: trabalhadores primeiro,
produção depois), mas sem nenhum reforço nos primeiros minutos a primeira onda pode ser decisiva. Decisão:
`CFG.SPAWN.startRifles = 10` na base principal na partida com logística (proposta; calibrar no laboratório
junto com a cadência real das ondas). O esquadrão inicial do cenário continua como hoje.

**Laboratório:** as sondas A1–A4 são só leitura; o ensaio B1 (criar/destruir `BPForwardBase1_C`) é trabalho normal
do agente LABORATORIO na cópia de laboratório e entra no roteiro do lote, depois do gate de estabilidade.
Plano B se a classe não nascer íntegra: malha do próprio mod, sem mudar o design.
