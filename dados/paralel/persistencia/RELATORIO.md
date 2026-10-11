# PERSISTENCIA — salvar infraestrutura e logística regional com segurança (CLAUDE_PERSISTENCIA, 2026-10-09)

Entrega offline, não integrada. `main.lua` real intacto (SHA256 `33d6c7e5…e679` antes e depois). Sem jogo,
laboratório, canal, botloop ou saves reais. Consultado o universal-modder no início (`um kb search` save /
persistence / serialization / atomic write / foxhole); gotchas propostos em `GOTCHAS_PROPOSTOS.md`.

## 1. Auditoria do save/continue atual (`mod/FoxholeRTS/Scripts/main.lua`)

| # | Onde | Problema |
|---|---|---|
| A1 | `sv.parse` 4397-4403 | `load(txt, "save", "t", {})`: ambiente vazio, mas executa o arquivo (laço infinito/memória) e aceita qualquer expressão que dê tabela com `v == 1`. |
| A2 | `sv.save` 4445-4452 | `io.open(..., "w")` direto no único arquivo: queda/disco cheio no meio trunca o save; retorno de `write` ignorado; sem backup. |
| A3 | `sv.ser` 4379-4395 | NaN/inf viram `0` e userdata/função vira `nil` em silêncio (perda de dado sem erro). |
| A4 | `sv.load` 4514-4530, `sv.restore` 4465-4512 | Só confere o nome curto do mapa. `sv.restore` chama `clearSquad` (4466) antes de qualquer checagem de mundo; se `addPoint` (2227-2233) recusar um ponto, os índices andam e os depósitos `pts[i]` (3095) e postos inimigos (4499) caem no ponto errado. `pcall(logi.restore)` ignora falha (4522). |
| A5 | `logi.restore` 3089-3097 | `logi.start()` (2673) recria estoque de cenário (bmat 240, munição/camisas iniciais) e só depois atribui; sem validação de números. |
| A6 | `logi.snapshot` 3081-3087 | Sem job (bmat já debitado some), sem caminhões/carga em trânsito, sem estado de reconstrução. (Corrigido pelo schema v2 da ECONOMIA.) |
| A7 | `logi.deployWallet` 2523-2527, `logi.deploy` 2614-2662 | Carteira chaveada por `GetFullName..GetAddress` (muda a cada carga) e nunca salva; o deploy não registra o que pagou. Após reiniciar, ruínas voltam, carteira renasce com 1100: continuar exige Alt+L de novo e paga outra vez. **Infraestrutura e orçamento não persistem.** |
| A8 | `logi.start` 2681 | Comboio inimigo volta a `cargo0` a cada continue (carga inimiga recriada). |
| A9 | `sv.tick` 4533-4550 | Autosave depois de continue incompleto sobrescreve o save bom com a partida degradada. |
| A10 | `sv.clear` 4462 | Só remove o arquivo principal. |

Já persistia (v1, por coordenada): pontos/donos/progresso/trincheira/arame inimigo, barreiras, trincheiras,
postos, arames, soldados dos dois lados, placar, mão de obra, dificuldade, modo.

## 2. Schema v2 (reconciliado com ECONOMIA e IA_LOGISTICA)

Mesmo texto `return {...}` do v1; **lido por `sv.decode`** (parser de literais, sem `load`). Top-level `v = 2`:

| Campo | Dono | Conteúdo |
|---|---|---|
| `v, map, diff, wave, kills, losses, elapsed, mp, aimp, shots, hits, nextIn, mode, points, squad, enemies, walls, trenches, tents, wires` | v1 (inalterado) | idem v1 |
| `world` | PERSISTENCIA (novo) | caminho do mundo sem prefixo de classe (`/Game/Maps/Master/CallumsCapeHex.CallumsCapeHex`); comparação sem caixa |
| `logi` | **ECONOMIA** (`version=2`, `dados/paralel/economia/save.lua`) | sem alteração; validado pela `logi.validateSave` dela, contra os pontos **do save** (proxy), não os vivos |
| `infra` | PERSISTENCIA (novo, `version=1`) | `budget, bmat, spent` (carteira de implantação) + `built[]` = registros pagos `{kind="site", code="Refinery"/"Factory", x,y,z,yaw}` e `{kind="truck", x,y,z,yaw}` |
| `elogi` | **IA_LOGISTICA** (`v=1`, `logi.eSnapshot`) | aceito só se o módulo dela estiver integrado e `logi.eValid` aprovar; sem o módulo, recusa ("campo desconhecido: elogi") |
| `enemy` | PERSISTENCIA (`version=1`, reservado) | `cargo, convoys, cut` do comboio abstrato do main atual; **não é gravado** quando a IA_LOGISTICA está integrada (ela é a dona do estado inimigo via `elogi`) |

Regras: nenhum ator, userdata, função ou endereço (`sv.pure` + decodificação do próprio texto antes de gravar);
campo desconhecido no topo, em `infra`, nos registros e em `enemy` = recusa (sem descarte silencioso);
`bmat + spent == budget` e `spent == Σ custo(built)` (400/400/100 de `CFG.DEPLOY`); instalação única por código.
Rotas da ESTRADAS **não** são salvas (epoch inclui a sessão): caminhão replaneja (`route/routeDest/pathJob=nil`,
já feito pela ECONOMIA). Destino do caminhão e depósitos ficam por índice de ponto (contrato da ECONOMIA), com
identidade estabilizada: preflight garante que todos os pontos voltam e `sv.verify` confere índice→coordenada.

**Versões/migração.** `v=1` (legado, com ou sem `elogi` de uma build com IA): aceito; sem `infra`, a carteira
não é tocada (comportamento atual); `logi` sem `version` = legado da ECONOMIA. `v>2`, `infra.version>1`,
`enemy.version>1`: recusa com "versão futura" e arquivo preservado. Para mudar o schema: subir a versão do bloco
dono e acrescentar a migração em `sv.validate`/carregamento.

## 3. Revalidação antes de restaurar (`sv.preflight`, sem mutação)

1. Arquivo: primeiro válido entre `save.txt`, `.tmp`, `.bak` (`sv.read`); nada é apagado na leitura.
2. Schema completo (`sv.validate`), incl. ECONOMIA e IA_LOGISTICA pelos validadores deles.
3. Mundo: `world` igual ao caminho atual (v1: nome curto).
4. Superfície: cada ponto salvo com `surfaceZ` e sem sobreposição (senão `addPoint` recusaria); chão (`groundZ`)
   para barreiras, trincheiras e postos.
5. Infraestrutura (`sv.infraPlan`): carteira da carga atual lida **sem criar** (`logi.walletId`).
   - Mesma carga com implantação idêntica (sites por código ≤ 2 m, mesma contagem de caminhões): nada a fazer.
   - Carga com implantação diferente: recusa.
   - Carga nova: cada instalação paga precisa de ativo (não refaz, não reembolsa) ou ruína da classe certa a
     ≤ `PERSIST.tol` (200 cm) e yaw ≤ 1°; campo de sucata ativo (nunca inventado); caminhões faltantes só até o
     número pago, em vagas Landscape validadas (`logi.parking`); classes carregadas.
6. Logística: com plano vazio, `logi.ready()` precisa achar a cadeia ativa.

Só então: `logi.applyPlan` (rollback próprio: destrói spawns parciais, restaura ocultação/colisão da ruína, não
mexe na carteira) → carteira := a do save (sem débito novo) → `clearSquad`/`sv.restore` → `sv.verify` →
`logi.restore` (ECONOMIA, substitui, não soma) só se os pontos conferem → `logi.eRestore(d.elogi)` (IA) ou
`enemy`. `logi.deploy` foi dividido em `logi.applyPlan` (sem carteira) + `logi.deploy` (debita e registra
`wallet.built`); comportamento do Alt+L inalterado (suíte `test_orders` PASS).

## 4. Tratamento de erro

- Recusa antes da mutação (arquivo ausente/corrompido/truncado/grande/versão futura, outro mundo, superfície,
  ruína ausente/movida/girada, campo ausente, sem vaga, caminhões não pagos, implantação divergente, falha de
  spawn): `false`, aviso "Continuar recusado (partida atual e save preservados)", sessão e arquivos idênticos.
- Falha depois do preflight (soldado/ponto/fortificação que não volta): partida continua marcada INCOMPLETA,
  logística só volta se os pontos conferem (senão `logi.reset`, sem estoque fictício), **autosave suspenso**
  para essa partida (`sv.degraded.start == combat.startT`); Ctrl+F6 tenta de novo sem recobrar/duplicar
  infraestrutura; Shift+F6 (nova partida) libera o autosave.
- Gravação: temporário relido e conferido → anterior para `.bak` (ou `.corrupt` se inválido) → temporário vira
  save (Windows não renomeia por cima: remove o destino antes); falha devolve o anterior. `sv.save` recusa
  NaN/userdata/schema inválido e mantém o arquivo antigo. Vitória/derrota apaga `save.txt`, `.tmp`, `.bak`, `.corrupt`.

## 5. Testado (offline, lupa) e resultado

```bash
# raiz do repositório (Git Bash)
PYTHONPATH=D:/tools/pylibs python dados/paralel/persistencia/build_patch.py
PYTHONPATH=D:/tools/pylibs python dados/paralel/persistencia/test_persistencia.py
PYTHONPATH=D:/tools/pylibs python dados/paralel/persistencia/test_regressao.py
```

- `test_persistencia.py`: **36/36 PASS** = 9 cenários × Lua 5.4 (UE4SS) e 5.5 × 2 pilhas
  (main+ECONOMIA+PERSISTENCIA e main+ECONOMIA+IA_LOGISTICA+PERSISTENCIA). Cada carga do jogo é um runtime novo
  com o chunk candidato inteiro; só io/os, atores/spawn/traces e spawn de soldado/ponto/fortificação são falsos.
  Cenários: parser (sem `load`, sem userdata, 21 entradas maliciosas/corrompidas recusadas, limites); schema e
  versões futuras/migração v1; **ida e volta** em carga nova (5 spawns, carteira 0/1100 sem débito, razão
  completo idêntico, entrega única no depósito certo, regravação sem ator/endereço); **restauração repetida**
  (3×, sem duplicar atores nem estoques; mesma carga; Alt+L antes de continuar); **recusas** preservando sessão
  e arquivo (mundo errado, caixa diferente aceita, ruína movida/girada, campo ausente, telhado, ponto sem
  superfície, parede sem chão, implantação divergente, versão futura, truncado, estoque negativo, ausente,
  `elogi` inválido/sem módulo, caminhões não pagos; com caminhões nativos sem reembolso); **rollback** de spawn
  parcial; **falha pós-preflight** (autosave suspenso, sem estoque fictício, nova tentativa sem duplicar);
  **gravação atômica** (abrir/escrever/renomear falhando, queda entre renames recuperada do `.tmp`, corrompido
  vai para `.corrupt` sem perder `.bak`, NaN não grava); **legado v1**.
- `test_regressao.py`: PASS em `tools/test_orders.py` (pilha sem IA e com IA, com o bloco de comboio trocado
  pelo da IA como ela faz), `economia/test_integracao.py`, `ia_logistica/test_ia_logistica.py` (sobre a pilha
  com persistência) e `tools/check_globals.py` nos dois candidatos (≤ 180 locais de topo; nenhum local novo).
- Testes de mutação manuais (não versionados): remover suspensão do autosave, idempotência da infra, conferência
  da ruína, escrita atômica, conferência de mundo ou restauração da carteira faz a suíte falhar. A guarda
  `pointsOk` antes de `logi.restore` é redundante hoje (a `validateSave` da ECONOMIA também recusa), mantida
  como defesa.
- Custo medido offline: `sv.save` com 120+ unidades ≈ 11 ms; ler+validar ≈ 6 ms (lupa; ao vivo é gate).

## 6. NÃO testado (gates ao vivo — ver `ROTEIRO_LABORATORIO.md`)

`io.open("rb"/"wb")`, `f:seek`, `os.rename`/`os.remove` no Lua do UE4SS/Windows; spawn real refazendo a
infraestrutura numa carga nova do hex e ruína/yaw idênticos entre cargas; `GetFullName` do mundo; carga em
trânsito retomada com o driver real; custo no game thread; IA_LOGISTICA ao vivo; queda real entre renames.
Transporte continua em reta até a ESTRADAS integrar o driver. **A task não está concluída** sem a matriz do
laboratório.

## 7. Ordem de aplicação

1. ESTABILIDADE (já no main) → 2. **ECONOMIA** → 3. **IA_LOGISTICA** (opcional) → 4. **PERSISTENCIA**.
- Sem IA: `persistencia.patch` (diff sobre main+ECONOMIA). Com IA: `persistencia_sobre_ia.patch` (diff sobre
  main+ECONOMIA+IA). A PERSISTENCIA substitui a linha de `sv.load` em que a IA ancora, por isso vem depois dela;
  o `build_on` reconhece as duas variantes. `persistencia_completo.patch` = main atual → final (referência).
- Recomendado aplicar pelo script (`build_patch.build` / `build_with_ia`, âncoras únicas, fail-closed). Os
  `.patch` são LF; o `main.lua` é CRLF (candidatos em `candidato/` saem CRLF).
- INTERFACE: as âncoras da PERSISTENCIA não tocam o HUD; o conflito ECONOMIA × INTERFACE (`table.concat(deps,
  " | "), foe)`) é anterior e não depende desta entrega.
- Sem tecla nova (Ctrl+F6/Shift+F6 inalterados): `TESTE_MANUAL.md` e teste de teclas não mudam. README precisa
  descrever: save v2 com infraestrutura/carteira, recusas e autosave suspenso em continuação incompleta.
- Canal: `sv`/`logi` já estão no `env`; as funções novas (`sv.preflight`, `sv.infraPlan`, `sv.decode`,
  `sv.validate`, `logi.applyPlan`) ficam acessíveis sem mudar `runCommandFile`.

## 8. Riscos

- Mudança de layout do hex/servidor (ruína em outro lugar) torna o save irrecuperável por desenho (recusa, não
  inventa). Tolerância 2 m / 1° é hipótese a confirmar ao vivo.
- Continuação incompleta suspende o autosave até Ctrl+F6 bem-sucedido ou partida nova: protege o save, mas o
  progresso dessa partida não é gravado (avisado na tela).
- Instalação já ativa nativamente numa carga nova é reutilizada sem reembolso (conservador).
- Fallback para `.bak`/`.tmp` carrega um save até 30 s mais antigo (avisado como "[lido de save.bak]").
- `sv.parse` virou só decodificador (contrato usado pelos testes da suíte e da IA); validação do save inteiro é
  `sv.parseSave`.
- Python pode ter usado o `__pycache__` já existente em `economia/` ao importar o build dela; o build agora
  desliga a escrita de bytecode.

## Arquivos

`persistencia.lua` (módulo `sv`/`CFG.PERSIST`), `implantacao.before.lua`/`implantacao.after.lua` (divisão do
deploy), `build_patch.py`, `persistencia.patch`, `persistencia_sobre_ia.patch`, `persistencia_completo.patch`,
`candidato/main.lua`, `candidato/main_com_ia.lua`, `harness_test.lua`, `test_persistencia.py`,
`test_regressao.py`, `lab/t_persist_estado.lua` (sonda só leitura, não executada), `ROTEIRO_LABORATORIO.md`,
`GOTCHAS_PROPOSTOS.md`.
