# PERSISTENCIA — pedido ao LABORATORIO (preparado, NÃO executado)

Responsável pela execução: agente LABORATORIO (Codex coordenador). O CLAUDE_PERSISTENCIA não abriu o jogo,
não usou o canal nem tocou `D:\FoxholeLab` ou saves reais. Tudo abaixo é roteiro.

## Pré-condições
- Steam aberto e logado; sem botloop; firewall do laboratório intacto (regras do `AGENTS.md`).
- Candidato integrado pelo coordenador (ordem em `REPORT.md`: ECONOMIA → [IA_LOGISTICA] → PERSISTENCIA),
  sintaxe + `check_globals.py` + `test_orders.py` + `data/parallel/persistence/test_*.py` PASS.
- Região: a mesma do lote 17 (CallumsCapeHex: campo ativo, ruínas de refinaria/fábrica, sem caminhões nativos).
- **Antes de tudo, copiar para fora** os arquivos existentes `War/Binaries/Win64/ue4ss/Mods/FoxholeRTS/save.txt*`
  da cópia de laboratório (são do laboratório, não do usuário) e registrar SHA256. `restart.sh` só copia o
  `main.lua`; o save sobrevive ao reinício (conferido lendo o script, não executando).
- Sonda somente leitura: copiar `data/parallel/persistence/lab/t_persist_state.lua` para `D:/tools/foxhole-lab/`.
  Chamadas que mudam estado vão pelo canal (`sv.save()`, `sv.load()`, `logi.deploy()`), nunca por teclado.

## Matriz

| # | Passo | Esperado | Evidência |
|---|---|---|---|
| L0 | Carga 1: `logi.deploy()` (Alt+L pelo canal), nova partida, deixar ondas e logística rodarem ≥ 90 s | 2 instalações + 3 TruckW; carteira 0/1100 com 5 registros `built` | sonda antes; captura |
| L1 | Com caminhão carregado em `toDep` e job em curso: `sv.save()` | `true`; `save.txt` começa com `return {`, ASCII, sem `function`/`load`; `.bak` só a partir do 2º save | sonda; SHA256 dos arquivos; tamanho; ms do `sv.save` (amostrador `os.clock`) |
| L2 | Ler o arquivo fora do jogo: `python -c` com `sv.decode` via lupa (ou a suíte) | decodifica e `sv.validate` aceita; `world` = caminho do CallumsCape; nenhum endereço/ator | saída do comando |
| L3 | **Reiniciar o jogo** (`restart.sh`), mesma região, sem Alt+L | ruínas visíveis de novo, nenhuma refinaria/fábrica/TruckW ativa (prova de que a infra não sobrevive sozinha) | sonda (atores) |
| L4 | `sv.load()` | `true`; 5 spawns (refinaria 2700, fábrica 2000, 3 TruckW 900, Team1); ruínas ocultas/sem colisão; carteira 0/1100 (sem débito novo); estoques, job, carga em trânsito, pontos/donos, soldados, fortificações iguais a L1 | sonda depois = sonda L1 (exceto posições de caminhões, que voltam ao estacionamento validado) |
| L5 | `sv.load()` de novo, mesma carga | nenhum spawn novo, mesma contagem de atores, estoques não dobram | sonda |
| L6 | Deixar rodar 60 s: o caminhão salvo em `toDep` replaneja e entrega uma vez; fábrica conclui a job sem debitar bmat de novo | entrega única; bmat só cai em job nova | log de entregas; sonda |
| L7 | Autosave (30 s) e `sv.save()`; conferir `.bak` = save anterior | rotação ok; `.tmp` ausente | listagem e SHA256 |
| L8 | Reiniciar; **antes** de continuar, `logi.deploy()` (Alt+L) e depois `sv.load()` | Alt+L cobra da carteira nova; `sv.load` reconhece implantação idêntica, não cria nada, carteira volta à do save (0/1100) | sonda |
| L9 | Recusas com sessão viva (nova partida rodando): (a) save de outra região (copiar save do HomeRegionW), (b) `save.txt` truncado à metade sem `.bak`, (c) `["v"]=3`, (d) ruína movida não é possível ao vivo — pular | `false`, mensagem "Continuar recusado (partida atual e save preservados)", soldados/estoques da sessão viva iguais, arquivos com o mesmo SHA256 | sonda antes/depois; SHA256 |
| L10 | Falha pós-preflight ao vivo é difícil de provocar sem hotpatch: **não** forçar. Só registrar se aparecer "INCOMPLETA … autosave suspenso" espontâneo | — | log |
| L11 | Vitória/derrota (ou `sv.clear()` pelo canal no fim) | `save.txt`, `.tmp`, `.bak`, `.corrupt` removidos | listagem |
| L12 | Fim: restaurar os arquivos de save copiados no início; encerrar só o PID da cópia | — | SHA256 igual ao inicial |

## Medições pedidas
- Tempo de `sv.save()` e `sv.load()` no game thread (offline: ~11 ms para 120 unidades em lupa; ao vivo é gate).
- `os.rename`/`os.remove`/`io.open("wb")`/`f:seek` no Lua do UE4SS no Windows: o código assume que `os.rename`
  **não** sobrescreve (MSVCRT) e remove o destino antes; registrar o retorno real.
- `World:GetFullName()` no hex (formato `World /Game/Maps/Master/<Hex>.<Hex>`) e após reinício (igual).
- Ruína/rotação idênticas entre cargas (a restauração exige ruína a ≤ 2 m e yaw ≤ 1° do salvo).

## Não validado por este roteiro
Rotas por estrada (driver da ESTRADAS ainda não integrado; caminhões continuam em reta), equilíbrio, cadeia
inimiga ao vivo (IA_LOGISTICA), queda do processo exatamente entre os dois renames (só offline), UI/teclado real.
