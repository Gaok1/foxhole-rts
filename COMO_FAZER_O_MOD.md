# Como fazer o Foxhole RTS: rota, arquitetura, limitações e testes

Atualizado em 2026-10-06, com base no build Steam 25730371 (PE 1.64.6.1, `DefaultGame.ini` 1.67.10.1).

As decisões do usuário são três: modo solo contra IA, controle por esquadrão e o desenho normativo aprovado (ver "Regras do laboratório").

As evidências estão em `RECON_AMBIENTE.md`. Este documento é o "como fazer". As seções 1–8 vieram de análise estática (2026-10-06). A **seção 0** registra o que foi validado com o jogo rodando e **prevalece** quando houver conflito.

---

## 0. Validado em execução (2026-10-07) — receita que funciona

Rodando na cópia `D:\FoxholeLab\Foxhole` com UE4SS + `mod/FoxholeRTS` v0.3. Detalhes e logs em `MODLOG.md`.

| Etapa | Como | Armadilha encontrada |
|---|---|---|
| Lançar | `tools\lab.ps1 run` com o **Steam aberto e logado** + `steam_appid.txt` | Sem Steam aberto, `SteamAPI_Init` falha |
| Abrir sessão local | `GameplayStatics:OpenLevel(world, "/Game/Maps/HomeRegionW", true, "listen")` pelo mod | Shipping **ignora** o mapa da linha de comando |
| Não crashar | Hook em `SimPlayerController:ClientStartRespawnTimer`: na chamada aninhada, `Role` vai a AutonomousProxy | A RPC recursa no host (stack overflow) |
| Comandante (jogador) | `GameMode:RestartPlayerAtTransform(pc, transform)` em chão firme | `RestartPlayer` nasce sobre o vazio e morre na queda; **não precisa de stub de perfil** |
| Ver o mundo | `PlayerCameraManager:StopCameraFade()` + `SetManualCameraFade(0)` | O fade preto nunca é desfeito: tela preta com HUD visível |
| Câmera RTS | `CameraActor` como view target (pitch -60), pan pela borda/setas, zoom | A câmera do Foxhole fica dentro do personagem (zoom não inicializado) |
| Soldados | `SpawnActor(HeadlessPlayerController)` + `PlayerInput` + `bIsLocalPlayerController=true` + `RestartPlayerAtTransform` | `CreatePlayer` crasha (UI de opções por jogador); pawn de `AIController` é recolhido para (0,0,0) após ~20 s |
| Mover soldados | `AddMovementInput` a cada 33 ms, com `BrakingDecelerationWalking=0`, `GroundFriction=0`, `MaxAcceleration=20000`; `StopMovementImmediately` na chegada | Sem frenagem zero, pulsos espaçados mal saem do lugar |
| Ordem por clique | `GetHitResultUnderCursorByChannel(0, false, hit)` → `hit.ImpactPoint` | Parâmetros de saída do UE4SS: passar tabela vazia |
| Times | `PlayerState.TeamId` direto + `pawn.TeamId` + `OnRep_TeamIdNotify` + `BPSetTeamVisuals` (Colonials=0, Wardens=1) | `ServerJoinWar(0)` no HPC não mudou o PlayerState |
| Combate (v0.3) | `ApplyDamage` + efeitos do jogo (`RifleMF`, `BloodSplat`, `SimpleRifleImpact`, `RifleShot_Cue`) + visada por traço | Arma real ainda não: `ServerTakePickup` recursa no host (quebra-recursão evita o crash, item não entra) |
| Mensagens | `SimPlayerController:ClientAlertMessage(str, s)` | — |
| Recarregar o mod | reiniciar o jogo (`restart.sh`) | Ctrl+R do UE4SS travou o game thread |

Ferramentas: `um win shot --title '^War'` (captura GPU; a janela principal do processo é o console do UE4SS), `um win drive --title '^War'` (acrescentado ao toolkit nesta data), canal `D:\tools\foxhole-lab\cmd.lua` → `cmd.out` (`run.sh`).

---

## 1. Resumo em uma tela

| Pergunta | Resposta | Confiança |
|---|---|---|
| Existe rota oficial (offline, bots, SDK, servidor privado)? | Não | Alta (fontes oficiais) |
| O cliente consegue ser o servidor? | Provavelmente sim: código de servidor compilado (target *Game*), `UWorld::Listen`, fallback `IpNetDriver`, mapas com `DefaultGameMode = SimGameMode`. O `GameInstance` **pula o fluxo de menu quando a linha de comando traz `/Game/Maps/`** | Alta para "código presente", não testado em execução |
| O que pode impedir? | Um ponto só no caminho do host: o **carregamento de perfil em `PostLogin`** (pedido HTTP montado, mas só enviado em servidor dedicado). Auth (`FExternalWarService`), travel e `PreLogin` ficam fora desse caminho | Alta (decompilado e validado); falta medir em execução (T2) |
| VAC? | Sem EAC/BattlEye. Há VAC. Num cliente, o servidor Steam **só sobe** com `bInitServerOnClient`/`OSS.SteamInitServerOnClient`, ausentes na config. Se subisse, `bVACEnabled` (embutido = 1) daria modo seguro; `lab.ps1` grava `bVACEnabled=0` por garantia | Alta (decompilado) |
| Assets acessíveis? | PAK sem compressão, sem AES, sem `.sig`, sem IoStore | Alta (índice lido e verificado) |
| IA e navegação? | AIModule/Recast/Detour/Crowd compilados, mas o jogo não usa IA de soldado e os mapas não têm NavMesh | Alta |
| Soldados controláveis? | Sim, em princípio: o modo de teste de carga `-headless` já cria jogadores locais extras cujo controller move o `ASimCharacter` por código (`AddMovementInput`) | Alta para o mecanismo; não testado |
| Viável? | **Plausível.** Depende de: (1) o mapa abrir em `?listen` (T2), (2) um stub de perfil em C++/UE4SS (T6), (3) jogadores locais extras como soldados (T7) | — |

---

## 2. Rota escolhida: listen server local isolado + UE4SS

```
Steam (posse verificada normalmente)
  └─ Cópia de laboratório  D:\FoxholeLab\Foxhole   (nunca conecta em servidor oficial)
       ├─ War-Win64-Shipping.exe  /Game/Maps/HomeRegionW?listen  -log
       │     └─ ASimGameMode (autoridade local)
       │           ├─ PostLogin → UPlayerProfileManager → STUB DE PERFIL (C++, só nesta sessão)
       │           ├─ jogadores locais extras = soldados (SimPlayerController + ASimCharacter)
       │           └─ Steam game server: não sobe num cliente → sem VAC de servidor
       └─ UE4SS (proxy dll só na cópia)
             ├─ C++: stub de perfil (detour 0x1409a74f0), depois seleção/UI/pathfinding
             └─ Lua: criar soldados, ordens de esquadrão, IA adversária
```

### Por que essa rota
- Foxhole é **server-authoritative**. Só quem é servidor pode criar soldados e mover unidades de verdade. A sessão local `?listen` torna o próprio cliente o servidor, e aí as ordens RTS são legítimas dentro da simulação.
- A câmera do Foxhole já é isométrica e de cima. A "câmera RTS" é a parte mais barata do mod.
- UE4SS é a forma padrão de injetar lógica num UE4 sem editor nem código-fonte. O índice aberto do PAK permite ler os Blueprints para descobrir nomes de propriedades e funções.

### Rotas descartadas e por quê

| Rota | Motivo |
|---|---|
| Mod no cliente conectado a servidor oficial | O servidor é a autoridade, então o cliente não comanda nada. Também viola o Code of Conduct e expõe a conta ao VAC |
| "Autenticar online e depois offline" | Um processo modificado conversaria com o backend oficial. É o maior risco de ban |
| Servidor dedicado (`-server`) | Não há string `-server` nem binário de servidor. O target dedicado não é distribuído |
| Emulador de servidor completo | Não existe; reimplementar o servidor é inviável |
| Pak mod de Blueprint com lógica nova | Exige cozinhar assets num UE 4.24 com o projeto `War`, que não temos. Só serve para trocas pontuais (fase tardia) |

### Planos B, se a rota principal cair
1. **Pak mod visual/UI:** tolerado pela comunidade, mas não dá RTS.
2. **Painel RTS-like sobre a War API:** só leitura, legítimo, mas não é jogo.
3. **Perguntar à Siege Camp:** há um rascunho em `RECON_AMBIENTE.md`.

---

## 3. Arquitetura do mod (camadas)

Cada camada só começa depois que a anterior passar no teste correspondente (seção 6).

### Camada 0: laboratório
- Cópia completa do jogo em `D:\FoxholeLab\Foxhole` (≈25,7 GB). A instalação da Steam continua intocada para jogar online.
- `steam_appid.txt` (conteúdo `505460`) ao lado do exe da cópia. É o mecanismo padrão da Steamworks para rodar o binário fora da pasta da Steam; a Steam continua exigindo login e posse do jogo.
- UE4SS (`dwmapi.dll` + pasta `ue4ss/`) **só** em `D:\FoxholeLab\Foxhole\War\Binaries\Win64`.
- Config do laboratório: `%LOCALAPPDATA%\War\Saved\Config\WindowsNoEditor\Engine.ini`. **Atenção:** essa pasta é compartilhada entre a cópia e a instalação da Steam. Todo ajuste precisa ser seguro também para o jogo online, ou ser aplicado/removido por um script de lançamento.
- Backup: `um backup create "%LOCALAPPDATA%\War" --name foxhole-config` antes de cada sessão modificada.

### Camada 1: sessão local
- URL: `/Game/Maps/HomeRegionW?listen` (48 MB, o menor mapa jogável, `SimGameMode`). Alternativas: `HomeRegionC`, `LykosIsleHex` (98 MB) e `DeadlandsHex`, o `ServerDefaultMap`, como controle.
- **O que o host local exige do backend** (decompilado e validado em 2026-10-06):

| Etapa | Função | Depende do backend? | Ação |
|---|---|---|---|
| Boot sem menu | `UWarGameInstance::StartGameInstance` 0x141150070 | Não: com `/Game/Maps/` na linha de comando, pula o `MainMenu` (vfunc `+0x378` = 0x141145270, carrega `/Game/Maps/MainMenu`) | Nenhuma |
| `PreLogin` | `ASimGameMode` 0x140b79540 | Só para clientes remotos | Nenhuma (host não passa) |
| `Login` | 0x140b6a7a0 | Não chama o WarService. Exige reserva (`?FactionId=0/1` + fila) **somente se** `WarTweakables.bCheckReservationsOnLogin` (`ServerSettings+0x5d9`) | Medir em T2. Se rejeitar, zerar a flag ou passar `?FactionId=` |
| **`PostLogin` → perfil** | `UPlayerProfileManager` 0x1409a74f0, callback 0x140b6f290 | **Sim, é o bloqueio real.** O pedido HTTP de perfil é montado, mas só é enviado (`ProcessRequest`, vfunc `0x88`) se `GetNetMode()==1` (dedicado). Em listen, o callback nunca roda e o personagem não é liberado. Se o mundo/HTTP for nulo, o callback roda com falha → "Unable to load Profile" (kick) | **Stub obrigatório:** detour em 0x1409a74f0 que invoca o callback com sucesso e um perfil local sem ban |
| `FExternalWarService` (auth) | `SendAuthMessage` 0x14092f2c0 / `OnAuthResponse` 0x140915aa0 | Criado em `UWarGameInstance::Init`, mas fora do caminho Login/PostLogin | Nenhuma; deve apenas falhar a conexão (aviso de UI) |
| TravelManager/reserva de travel | 0x140dd6850 | Só criado em servidor dedicado | Nenhuma |

- **Como fazer o stub:**
  - 0x1409a74f0 é função nativa, não UFunction. O `RegisterHook` do Lua não alcança; é preciso um **mod C++ do UE4SS** com detour por assinatura (AOB).
  - O formato do perfil esperado pelo callback 0x140b6f290 ainda precisa ser mapeado. Próxima tarefa de RE: decompilar 0x140b6f290 e `OnBanAndProfileLoadComplete` 0x1409bc580 para montar o perfil mínimo.
- **Proibido pela regra 2:** fazer o pedido sair para a Siege Camp, ou falsificar a resposta deles na rede. O stub vive só dentro do processo.
- Switches de linha de comando que existem (FParse): `adminall`, `adminnone`, `noqueue`, `RepDriverDisable`, `headless`, `headlessclients=`, `supportsheadless`, `maxsplitscreensperconnection=`, `forceloadsavefromdisk`, `BeaconPort=`, `nosteam`. **Não existem** `-offline`, `-nowarservice` nem `-skipauth`.
- **VAC (resolvido por config, falta confirmar em execução):**
  - Cadeia: `FOnlineSubsystemSteam::Init` 0x140562ce0 → `InitSteamworksServer` 0x1405f8980 → 0x1405f78e0 → `SteamInternal_GameServer_Init`. Num cliente, **o servidor Steam só sobe se** a cvar `OSS.SteamInitServerOnClient` ≠ 0 **ou** `[OnlineSubsystemSteam] bInitServerOnClient=True`. Nenhuma das duas existe na config do jogo, então num `?listen` padrão **não há servidor Steam nem VAC de servidor**.
  - Se subisse: `GConfig [OnlineSubsystemSteam] bVACEnabled` → `eServerMode = 2 + bVACEnabled`.
  - O `BaseEngine.ini` embutido tem `bVACEnabled=1`, e o `DefaultEngine.ini` do War não sobrescreve. Então `tools/lab.ps1` grava `bVACEnabled=0` em `%LOCALAPPDATA%\War\Saved\Config\WindowsNoEditor\Engine.ini` antes de cada `run`.
  - Isso é inofensivo online, onde o cliente nunca é servidor.
- **Entrar direto no mapa:** `FUN_141150070` (GameInstance) só chama o fluxo padrão de menu (vfunc `+0x378`) se a linha de comando **não** tiver `/Game/Maps/`. Com `/Game/Maps/HomeRegionW?listen`, o engine abre o mapa direto (Browse padrão do `UGameInstance::StartGameInstance`).
- **Host local não passa por `PreLogin`:** o jogador local de um listen server entra via `SpawnPlayActor` → `GameMode::Login`, e não pelo handshake de rede (`NotifyControlMessage`). O risco de auth fica em `Login`/`PostLogin`/perfil (`UPlayerProfileManager`).

### Camada 2: soldados controláveis
- Classe base nativa: `ASimCharacter` (Blueprint `/Game/Blueprints/Character/Character`).
- **Descartado: `AOfflineCharacter`** (o "personagem offline" deixado ao deslogar). É `AActor`, não Pawn: só malhas e `MulticastApplyFatalHit`, sem movimento nem Possess. Além disso, fica desligado nos HomeRegion (0x140b53be0). Serve só de figurante ou alvo.
- **Rota principal: soldados = jogadores locais extras no host.** O jogo já faz isso no modo de teste de carga `-headless`:
  - `UWarGameInstance::OnStart` (0x141147150) cria `-headlessclients=N` jogadores locais (`UHeadlessLocalPlayer`).
  - Cada um recebe um `AHeadlessPlayerController : ASimPlayerController`, cujo `PlayerTick` (0x140a2deb0, validado) pega o pawn `ASimCharacter` e chama `AddMovementInput` (vfunc `0x720`). É um bot de movimento nativo.
  - Cada jogador local passa pelo fluxo normal: Login → `SimPlayerController` + `PlayerState` + `ASimCharacter`. Assim, inventário, animação e vida funcionam como para um humano.
  - No mod: `GameplayStatics:CreatePlayer(world, id, true)` via UE4SS, ou o próprio `-headless -headlessclients=N` (avaliar o efeito no jogador 0). Depois o mod controla o movimento (`AddMovementInput`) em vez do padrão aleatório.
  - Requisitos: o stub de perfil (camada 1) vale para cada jogador local; e sem splitscreen (`[/Script/EngineSettings.GameMapsSettings] bUseSplitscreen=False` no Engine.ini do laboratório).
- **Rota B:** `AAIController` + `Possess` direto num `ASimCharacter`. Os casts em `ASimCharacter` parecem condicionais, mas a dependência de `ASimPlayerController`/`PlayerState` não foi provada nem descartada.
- **Navegação:** os mapas não têm `RecastNavMesh`. Há `NavigationSystemConfig` com `bEnableNavigationSystem`/`bAutoSpawnMissingNavData` serializados, o que indica que estão desligados. Opções, em ordem:
  1. Ligar o NavigationSystem e criar um `RecastNavMesh` dinâmico em runtime, só em volta da área da batalha (Recast está compilado). Custa CPU; limitar com um `NavMeshBoundsVolume` pequeno.
  2. Fallback: pathfinding próprio em grade (A* sobre heightfield/traces), com `AddMovementInput` a cada tick. Funciona sem NavMesh.
- Dados de unidades e armas: DataTables `BPItemDynamicData`, `BPWeaponDynamicData`, `DTDamageProfiles`, `DTArmourProfiles` (leitura via FModel/CUE4Parse, sem extrair para o repo).

### Camada 3: controle por esquadrão (jogador)
- **Esquadrão:** um líder e N membros (jogadores locais extras) em formação relativa, com offset por slot. A ordem vai ao esquadrão; os membros seguem o líder.
- **Entrada:**
  - fase 1: teclas e console UE4SS (Lua `RegisterKeyBind`) + clique para destino (raycast do cursor);
  - fase 2: seleção por retângulo e painel de esquadrões (C++ mod com overlay ImGui do UE4SS).
- **Câmera:** usar a câmera do `ASimPlayerController` (já top-down), com zoom maior e desacoplada do personagem do jogador. Opção: um pawn espectador.
- **Ordens mínimas:** mover, atacar-mover, segurar posição, recuar.

### Camada 4: IA adversária
- Duas camadas, ambas em Lua/C++, sem BehaviorTree. O jogo não tem BT, e não temos editor para criar.
  - **Comandante:** máquina de estados sobre objetivos (capturar ponto, defender, reforçar).
  - **Esquadrão:** reage a contato (ataque, cobertura, recuo por moral/vida).
- O disparo de armas tem de passar pelas funções de servidor do personagem ou da arma. As "Server RPCs" do jogo precisam ser mapeadas no dump do UE4SS.

### Camada 5: conteúdo e escopo
1. Prova: 1 esquadrão se move por clique.
2. Dois esquadrões de infantaria contra a IA num `HomeRegion`.
3. Um tanque/veículo (`ASimVehicle`) e um objetivo.
4. Produção, logística e construção, só se as camadas anteriores estiverem estáveis.

---

## 4. Limitações conhecidas

- **Updates quebram o mod.** Cada patch muda offsets, assinaturas do UE4SS e possivelmente Blueprints. Mitigação: a cópia de laboratório congela a versão; manter uma tabela "build suportado".
- **Risco de conta.** A proteção vem de uma regra rígida: nunca abrir a cópia modificada conectando a servidor oficial, e nunca colocar o UE4SS na instalação da Steam. Mesmo assim, o VAC é da Valve e não há garantia formal. Usar por conta e risco.
- **Pasta de config compartilhada** (`%LOCALAPPDATA%\War`) entre cópia e instalação oficial (ver camada 0).
- **Sem editor/SDK:** nada de Blueprints novos cozidos, só lógica injetada e reaproveitamento de assets existentes.
- **Soldados nunca foram feitos para IA.** Animação, inventário e vida podem depender de `PlayerState`/perfil. Isso pode exigir stubs extras.
- **Sem NavMesh:** pathfinding é trabalho nosso (ver camada 2).
- **Performance:** hexes carregam 100–280 MB e proxies; o listen server roda tudo num processo só.
- **Política:** o Code of Conduct proíbe modificar o cliente "para vantagem injusta". O uso local e offline não dá vantagem a ninguém, mas não há permissão explícita da Siege Camp.
- **Distribuição:** o mod distribui só nossos scripts e DLLs. Nunca arquivos do jogo, assets extraídos ou decompilação.

---

## 5. Regras do laboratório (aprovadas em 2026-10-06)

1. A posse do jogo continua verificada pela Steam; não tocar em DRM nem em tickets.
2. A sessão modificada nunca contata serviços da Siege Camp. Os stubs respondem só dentro da sessão local.
3. O servidor local roda sem VAC.
4. O mod fica inativo fora do modo RTS local, e o UE4SS fica só na cópia de laboratório.
5. Backup antes de cada sessão modificada; registrar tudo no `MODLOG.md`.

---

## 6. Protocolo de testes (para rodar com o usuário presente)

Cada teste tem um critério objetivo de sucesso e a evidência a guardar (trecho de log em `MODLOG.md` e captura via `um win shot`). Comandos a partir de `D:\GitHub\universal-modder`.

| # | Teste | Como | Sucesso | Se falhar |
|---|---|---|---|---|
| T0 | Lançamento original | `python -m um win launch --steam 505460 -- -log` e ir até o menu; fechar | `%LOCALAPPDATA%\War\Saved\Logs\War.log` existe. Anotar hosts, auth, NetDriver, carregamento de perfil | Registrar o erro; sem T0 nada segue |
| T1 | Cópia de laboratório | `steam_appid.txt` = `505460` em `D:\FoxholeLab\Foxhole\War\Binaries\Win64`; lançar o exe da cópia com `-log` | Abre o menu a partir da cópia (log aponta o caminho da cópia) | Se a Steam relançar a instalação oficial, usar o exe com `-log` via `um win launch "<exe>"` e investigar `RestartAppIfNecessary` |
| T2 | Listen sem mod | Cópia, sem UE4SS, **com a internet do processo bloqueada** (regra de firewall de saída para o exe da cópia): `War-Win64-Shipping.exe /Game/Maps/HomeRegionW?listen -log` | O log mostra `LoadMap` do HomeRegionW, `SimGameMode` e o driver ouvindo (`SteamSocketsNetDriver` ou `IpNetDriver`). **Esperado:** host parado esperando perfil, ou "Unable to load Profile" | Se quebrar antes do PostLogin (Login/reserva), anotar a mensagem: define a flag de reserva da camada 1 |
| T3 | VAC local | Log de T2 (com `-LogCmds="LogOnline Verbose"`) | **Ausência** de "Initializing Steam Game Server" e de "Steam Dedicated Server API initialized" | Se aparecer, `bInitServerOnClient`/`OSS.SteamInitServerOnClient` foi ligado em algum lugar: parar e investigar antes de seguir |
| T4 | UE4SS | Copiar o UE4SS (experimental-latest) só para a cópia; lançar no menu | `UE4SS.log` sem erro de AOB; Live View lista `ASimCharacter`, `ASimGameMode` | Configurar override de versão 4.24 / AOBs customizados |
| T5 | Dump | UE4SS: dump de objetos e headers (CXX header dump) | SDK com `ASimCharacter`, `ASimPlayerController`, `FExternalWarService`, funções `Server*` | — |
| T6 | Stub de perfil | Mod C++ do UE4SS: detour em `UPlayerProfileManager` 0x1409a74f0 → callback 0x140b6f290 com sucesso e perfil local. Se `Login` rejeitar: `bCheckReservationsOnLogin` (`ServerSettings+0x5d9`) = 0 | Sessão `?listen` com o personagem do host em campo | Voltar ao Ghidra: estrutura do perfil em 0x140b6f290 / 0x1409bc580 |
| T7 | Primeiro soldado | Lua: `GameplayStatics:CreatePlayer(world, 1, true)` (ou `-headless -headlessclients=2` na cópia) + `AddMovementInput` por 10 m | O segundo personagem anda sozinho (captura + log) | Rota B: `SpawnAIFromClass` + `AAIController` |
| T8 | Navegação | Gerar NavMesh dinâmico na área, ou ligar o pathfinding próprio | `MoveToLocation` contornando um obstáculo | Fallback A* |
| T9 | **Marco** | Selecionar o esquadrão (tecla) e clicar no destino | **Todos os membros se movem até o ponto** | — |

---

## 7. Estado atual das ferramentas

| Ferramenta | Onde | Estado |
|---|---|---|
| Ghidra 12.1.2 + GhidraMCP 5.14.2 | `D:\tools\ghidra`, `D:\tools\ghidra-mcp-v5.14.2` | Auto-análise concluída (57 min). Decompilação por string: `D:\tools\ghidra-scripts\DecompStrRefs.java` (saída em `D:\tools\foxhole-lab\decomp*`) |
| Índice do PAK | `D:\tools\foxhole-lab\pak-index.tsv`, `pak-config-excerpts.txt` | Pronto (25.898 entradas) |
| Cópia de laboratório | `D:\FoxholeLab\Foxhole` | Pronta (97 arquivos, 26.035.003.749 bytes, idêntica à Steam), com `steam_appid.txt` |
| Script do laboratório | `tools/lab.ps1` | `check`/`prepare` executados. `vac-off` testado em pasta temporária (4 casos). `run`/`ue4ss-*` aguardam o usuário |
| Mod (esqueleto) | `mod/FoxholeRTS/Scripts/main.lua` | Escrito, **não executado** (F5 status, F6 esquadrão, F7 mover, F8 limpar) |
| UE4SS | — | Pendente: o download foi bloqueado pelo modo automático; precisa ser liberado pelo usuário |
| Lançar o jogo | `um win launch` | Bloqueado pelo modo automático sem o usuário presente |

## 8. Perguntas ao binário: respondidas e abertas

Respondidas (decompilação validada; funções em `D:\tools\foxhole-lab\decomp*`):
1. **`?listen` no código:** é o boot do servidor dedicado oficial (só em `NM_DedicatedServer` e `ServerType` WorldConquest/HomeRegion), que acrescenta `?listen` ao mapa do save. Não é modo de treino offline. O modo dedicado é inalcançável neste exe: o ramo `IsRunningDedicatedServer` foi compilado fora e `GIsClient=1`. Ganho prático: a linha de comando com `/Game/Maps/...` pula o menu.
2. **VAC:** sem servidor Steam num cliente, a menos que `bInitServerOnClient`/`OSS.SteamInitServerOnClient` esteja ligado; ver camada 1.
3. **Backend:** o único bloqueio no caminho do host é o perfil em `PostLogin`; ver a tabela da camada 1.
4. **Controle:** o jogo move um `ASimCharacter` por código via `AHeadlessPlayerController`. Soldados = jogadores locais extras.

Abertas:
- Estrutura do perfil esperado por 0x140b6f290 / 0x1409bc580, para o stub do T6.
- Valor padrão de `WarTweakables.bCheckReservationsOnLogin` numa sessão sem backend.
- Se `-headless` muda o jogador 0, já que `LocalPlayerClass` vira `UHeadlessLocalPlayer`.
- Se `ASimCharacter` funciona com `AAIController` puro (rota B).
