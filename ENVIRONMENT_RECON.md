# Investigação do ambiente de simulação

Data: 2026-10-06 | Steam build local: 25730371

## Resultado

Não foi encontrada uma rota pública, documentada e utilizável para executar o Foxhole instalado como uma simulação offline/controlada para o mod RTS. Isso é um resultado limitado da investigação, não uma prova de impossibilidade técnica.

## Evidências locais — somente leitura

Instalação: `D:\SteamLibrary\steamapps\common\Foxhole`.

Executáveis encontrados na listagem recursiva:

- `War.exe`
- `War\Binaries\Win64\War-Win64-Shipping.exe`
- `Engine\Binaries\Win64\CrashReportClient.exe`
- `Engine\Binaries\Win64\UnrealCEFSubProcess.exe`
- `Engine\Extras\Redist\en-us\UE4PrereqSetup_x64.exe`

Não foram encontrados arquivos soltos com extensões `.bat`, `.cmd`, `.ini`, `.uproject` ou `.uplugin` nessa listagem. Não foi identificado executável separado de servidor ou editor. Isso não demonstra que todo código de servidor esteja ausente do executável do cliente; essa hipótese não foi testada.

Na pasta específica `War\Content\Paks`, há um pacote: `War-WindowsNoEditor.pak`, com 25.681.549.397 bytes. A contagem de dois PAKs do scan inicial não deve ser interpretada como dois pacotes de gameplay: há pacotes auxiliares fora dessa pasta, inclusive do crash reporter e do navegador embutido.

O manifesto NonUFS identifica o executável Shipping e bibliotecas auxiliares. A ocorrência `vivoxsdk.dll` corresponde ao SDK de voz Vivox, não a um SDK de modding do Foxhole.

## Fontes primárias consultadas

### FAQ oficial

https://www.foxholegame.com/faq

Declara ausência de suporte oficial a mods, single-player e bots. Menciona mods visuais que não deem vantagem. Não fornece uma rota offline para simulação RTS.

### War API oficial

https://github.com/clapfoot/warapi

Documenta consultas GET de estado da guerra, relatórios e mapas. Não documenta comandos para criar unidades, mover personagens ou executar um servidor. Serve para consulta/visualização, não como interface de controle RTS.

### Foxhole Data Extractor — documentação do autor

https://github.com/C1ach0/fde

Ferramenta que lê PAKs locais com CUE4Parse e produz catálogos JSON e ícones. O termo “server-oriented” descreve a execução do extrator em servidor, não um servidor jogável de Foxhole. Não foi instalado nem executado.

### Tutorial de criação de mod — autor yurisuika

https://steamcommunity.com/sharedfiles/filedetails/?id=3207287574

O escopo declarado é modificar texturas via extração, edição e reempacotamento. Não demonstra controle da simulação. A página exibe avisos de remoção/incompatibilidade; não é receita validada para nosso build.

## O que não foi feito

- Nenhuma injeção, patch, extração de PAK ou instrumentação.
- Nenhum lançamento do jogo ou conexão a servidores.
- Nenhuma tentativa de ativar comandos não documentados ou contornar autenticação/proteção.
- Nenhum download de servidor/SDK vazado ou envio de mensagens a terceiros.

## Próximo passo que pode resolver o bloqueio

Obter informação específica da Siege Camp ou da comunidade de modding sobre um ambiente offline autorizado, SDK ou servidor de testes disponibilizado legitimamente. Pergunta sugerida, ainda NÃO enviada:

> Tenho Foxhole na Steam e gostaria de experimentar uma conversão RTS estritamente offline, sem interagir com servidores oficiais. Existe um ambiente de teste, SDK, servidor dedicado ou procedimento autorizado para executar uma cena local com controle da simulação? Mods de gameplay desse tipo são permitidos nesse ambiente?

Se aparecer uma ferramenta candidata, verificar origem, permissões e compatibilidade com o build antes de instalar. O projeto permanece um mod para Foxhole; nenhuma mudança para jogo independente foi feita.

---

# Rodada 2 — recon aprofundado (2026-10-06)

Quatro agentes em paralelo, todos somente leitura (nada executado, injetado, extraído ou alterado). Ferramentas: `python -m um scan`/`kb` do universal-modder, pefile/capstone para análise estática, WebSearch/WebFetch. Rascunhos e dumps ficaram fora do repositório (scratchpad da sessão).

## Resultado curto

1. **O cliente contém código de servidor.** O `War-Win64-Shipping.exe` é target *Game* (não *Client*): aceitação de login/join, `UWorld::Listen`, opção de URL `Listen`, ReplicationGraph do jogo e `ASimGameMode` estão compilados e referenciados. Listen server local é tecnicamente plausível; servidor dedicado (`-server`) provavelmente não.
2. **Bloqueio provável: backend externo.** O servidor do jogo depende de `FExternalWarService` (auth, perfis, reservas de travel, config da guerra). Uma simulação local deve quebrar nesses pontos. Não medido ainda — exige decompilação.
3. **Nenhuma rota pública:** sem offline, bots, servidor privado/dedicado distribuído, SDK, editor ou Workshop (fontes oficiais).
4. **Proteção:** sem EAC/BattlEye/EOS/packer. Há **VAC**, detecção própria de discrepância de tempo e `bAllowMods` nas configurações de servidor. Código de assinatura de PAK existe, mas não está ativo (sem `.sig`).
5. **PAK aberto:** índice não criptografado; mods de textura/UI em `War\Content\Paks` são prática corrente da comunidade (TrenchKit, Nexus, itch.io).

## Evidências locais (Sonnet — recon)

| Tema | Achado | Status |
|---|---|---|
| Anti-cheat | Nenhum arquivo/string de EAC, BattlEye, EOS, `start_protected_game`; Steam `gameprocess_log.txt` de jan/2026 mostra só `War.exe`, Shipping, CrashReportClient e CEF | Verificado |
| BEService no Windows | Pertence a Rainbow Six Siege (`%LOCALAPPDATA%\BattlEye\r6s`), não a Foxhole | Verificado |
| Manifesto Steam | Sem `LaunchOptions`; build 25730371, depot 505461 | Verificado |
| Config/logs/saves | Inexistentes: o jogo nunca rodou nesta instalação. Já rodou em jan/2026 numa instalação antiga em `G:\steam\...` (removida) | Verificado |
| PAK `War-WindowsNoEditor.pak` | Footer v8 (UE4.24), índice em 25.678.359.878 (3.189.298 bytes), SHA1 `b0693e21…8dba5b`, **índice não criptografado** (flag 0, GUID zero), sem `.sig`, sem IoStore | Verificado (só o footer foi lido) |
| Binários | Shipping 80 MB; plugins Vivox e Discord RPC; `steam_api64.dll` (Steamv151) | Verificado |

## Análise estática do executável (Opus)

PE: `Foxhole4.24.3: 87680`, ProductVersion 1.64.6.1, build embutido "Oct 5 2026". Sem packer, sem Authenticode, PDB ausente, strings e nomes de reflexão intactos (3049 classes nativas).

| Evidência | Força |
|---|---|
| Target *Game* (nome `War-Win64-Shipping`, não `WarClient`) → WITH_SERVER_CODE | Forte (inferência por convenção UBT) |
| `UWorld::NotifyControlMessage` lado servidor (VA 0x1429de920): "Login request…", "PreLogin failure", "Join succeeded" | Forte |
| `UWorld::Listen` (VA 0x1429dc8e0), "IpNetDriver listening on port %i"; `UEngine::LoadMap` testa `Listen` | Forte |
| `UWarReplicationGraph` e nós próprios (Rail/Air vehicle, GridSpatialization2D) — lógica só de servidor | Forte |
| `ASimGameMode`, `AWarGameMode`, `AWarGameSession`, `UPlayerProfileManager`, `UWarSaveGame` | Forte |
| `UServerSettings`: `NextWarMapOverride`, `WarTweakables`, `IsCommunityServer`, `bAllowMods`, `bFriendlyFire`… | Forte |
| `EWarServerType::Skirmish/WorldConquest/Event/Training/HomeRegion*` | Média |
| `"?listen"` montado por código do jogo (VA 0x141150223, provável `UWarGameInstance`) — finalidade não identificada | Média |
| `-server` como string isolada: ausente | Inferência: dedicado indisponível |
| Backend: `FExternalWarService::SendAuthMessage/OnAuthResponse/MapDataResponse/OnNextWarConfigMessage`, `FailureWarServiceUnavailable`; config remota em `s3.amazonaws.com/foxhole-updates/config/client_config*.json` | Forte (dependência) |
| IA/navegação: AIModule, BehaviorTree, EQS, Recast/Detour, Crowd compilados; o jogo usa IA só em torretas (`UAITurretComponent`…) | Engine forte / uso pelo jogo fraco |
| Console/cheats: `UConsole`, `UCheatManager` compilados; ativação no Shipping improvável; cheats próprios são requests de admin de regimento/squad | Classes fortes / console ativo desconhecido |
| `Mods/` na tabela de FPaths = `ProjectModsDir` padrão do UE, não loader do Foxhole | Inferência |
| VAC: "VAC ban detected - kicking…", `ETimeDiscrepancyType::AntiCheat` | Forte |
| UE4SS: FNamePool/GUObjectArray localizáveis → compatibilidade técnica provável, não testada | Inferência |

## Pesquisa pública (Sonnet — web)

- **Servidores:** shards são centrais (Live1, Live2, Dev Branch via Steam Betas). Nenhum servidor privado/dedicado distribuído, nenhum emulador. Fontes: https://foxhole.wiki.gg/wiki/Shard, https://foxhole.wiki.gg/wiki/Development_Branch. Confiança média-alta (ausência de evidência; Discord/devblogs não lidos).
- **Offline/bots:** inexistentes — FAQ oficial. "Modbox para Foxhole" em buscas é spam de SEO; descartado.
- **Anti-cheat e política:** "VAC integration and other behind the scenes tools" — https://www.foxholegame.com/moderation-faq. Code of Conduct (Siege Camp, 2020): proíbe modificar o cliente para obter vantagem injusta. Nenhum caso documentado de ban por mod visual.
- **Comunidade:** pak mods de textura/UI ativos; TrenchKit (MIT, https://github.com/Tapawingo/TrenchKit) gerencia ordem por prefixo. Nada de UE4SS, gameplay mods, bots ou emuladores.
- **Ferramentas oficiais:** só War API (consulta) e Dev Branch. Sem SDK/editor/Workshop.

## Base de conhecimento do toolkit (Haiku)

Nenhuma nota prévia de Foxhole. Regra do toolkit (`skills/mod-any-game/references/safety.md`): parar se online-only sem servidor do usuário ou com anti-cheat ativo, a menos que exista modo offline que o desative. Rota aceita para jogos server-authoritative: servidor próprio + cliente original. Exemplos: AzerothCore, Project Zomboid dedicated.

## Leitura conjunta

- O executável contém a autoridade da simulação. É a única pista concreta de uma "simulação sob nosso controle" com o binário oficial.
- Duas incógnitas decidem a viabilidade:
  1. **Técnica:** o caminho `?listen` e o `ASimGameMode` funcionam sem o `FExternalWarService`? Isso se mede com decompilação, e o Ghidra está sendo preparado.
  2. **Normativa:** substituir ou simular o serviço de auth/backend da Siege Camp, mesmo offline, pode ser contornar uma verificação de propriedade/autenticação. Isso é vedado pelas regras do toolkit e precisa de decisão explícita antes de qualquer passo.
- VAC: qualquer injeção (UE4SS, proxy DLL) só seria aceitável numa cópia isolada que nunca conecte a servidores oficiais. Mesmo assim, há risco de conta, a avaliar.

## Pendências

- [ ] Decompilar no Ghidra a função que monta `?listen` (VA ~0x141150070–0x141150380) e o fluxo `ASimGameMode` ↔ `FExternalWarService`. Medir o que é bloqueante sem backend.
- [ ] Verificar no índice do PAK se os mapas têm NavMesh (`RecastNavMesh`) gerado. Ler só o índice, sem extrair.
- [ ] Decidir com o usuário a rota normativa antes de qualquer execução modificada.
