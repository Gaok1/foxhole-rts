# Foxhole RTS — instruções para agentes (Claude, Codex, Gemini, ...)

Mod UE4SS (Lua, UE 4.24) que transforma uma cópia de laboratório do Foxhole num RTS solo contra IA.
Código: `mod/FoxholeRTS/Scripts/main.lua` (v0.9). Controles e mecânicas: `mod/README.md`. Rumo: `ROADMAP.md`.
Tudo o que um agente precisa saber fica **neste repositório** (não em memória privada de agente): ao aprender algo
que vale para a próxima sessão, escreva aqui, no `MODLOG.md` ou no `ROADMAP.md`.

**Antes de trabalhar, leia em `MODLOG.md` a seção "Como retomar"** (meio do arquivo; procure por esse
título). Entradas novas do diário ficam no topo. Teste manual pendente do usuário: `TESTE_MANUAL.md`.
Dados extraídos do jogo: `ESTUDO_MECANICAS.md` e `dados/`.

## Regras do usuário
- Totalmente offline, com sistemas próprios do mod. Não perseguir RPC, inventário ou servidor do jogo.
- Manter a verificação de posse do Steam (Steam aberto e logado); nunca contornar DRM; nunca logar no Steam pelo usuário.
- Não remover o bloqueio de firewall do laboratório (o aviso "Falha ao baixar informações do servidor" no menu é
  efeito dele: Slate nativo, o mod não fecha; o autostart sai do menu em 2 s).
- O usuário negou acesso de computer-use à janela do jogo: não injete teclado nem mouse por nenhum meio.
  Testes com entrada real são dele; os seus vão pelo canal de comandos.
- Terminal do usuário: Windows PowerShell 5.1 (sem `&&`, sem caminhos `/d/`).
- Escreva docs e mensagens em português. Exceção: `README.md` da raiz e `PROGRESS.md` são a vitrine pública
  para a comunidade de Foxhole e ficam em inglês.
- O repositório é público (`github.com/Gaok1/foxhole-rts`, MIT): nada de tokens, caminhos pessoais
  (`C:\Users\...`) nem arquivos do jogo (binários, DLLs, paks, assets extraídos) nos commits.
- Instalações e downloads grandes vão para `D:\tools` (é onde há espaço).
- **Trabalhar em lotes:** várias features com teste offline, depois uma única sessão no laboratório (reiniciar o
  jogo custa minutos).
  **Reforço explícito do usuário (2026-10-11):** não abrir/reiniciar o laboratório a cada descoberta,
  sonda, helper ou pequena alteração. Avançar primeiro na pesquisa e implementação offline;
  acumular mudanças e preparar os cenários com critérios de aprovação. Só então publicar uma vez
  e executar os cenários sequencialmente na MESMA sessão do jogo, com cleanup entre eles.
  Novas ideias surgidas durante a validação entram no próximo lote; não iniciar outra run imediatamente.
  Exceção: crash ou pré-requisito concreto que impeça continuar o lote; registrar a causa antes de reiniciar.
- **Fechar o jogo quando o laboratório estiver ocioso:** terminado o teste/robô, ou ao passar ao trabalho só
  offline, encerrar apenas o PID da cópia em `D:\FoxholeLab\Foxhole`. Não deixar aberto "pronto para testar"
  por padrão. Manter aberto só enquanto houver validação ativa ou se o usuário pedir; não fechar Steam.
- **Direção (2026-10-09):** começar numa região pequena e só depois o mundo; a logística (recurso, refino,
  fábrica, transporte, abastecimento) é o centro, a guerra é "a pequena parte da engrenagem". O RTS precisa
  servir para olhar várias frentes (zoom alto, alertas, grupos).
- **Rastrear antes de reinventar** (`ROADMAP.md`): procure a chamada do próprio jogo e grave o fluxo real antes de
  recriar uma mecânica à mão.

## Fluxo
- **universal-modder (`D:/GitHub/universal-modder`) no começo e no fim** (o usuário cobrou isso duas vezes):
  antes de uma mecânica nova ou de um problema de engine, `um kb search <tema>` e as skills `reverse-engineering`
  ("record real traces"), `mod-any-game` (`references/engines/unreal.md`) e a técnica de oráculos. No fim da
  sessão, acrescentar os aprendizados como Gotchas na nota `knowledge/games/foxhole/...` e rodar `um kb check`
  (local; PR só com OK do usuário). Rodar com `UM_HOME=D:/tools/um-home python -m um ...`.
- Publicar e reiniciar o jogo: `bash D:/tools/foxhole-lab/restart.sh` (checa sintaxe e locais, copia, espera o RTS).
  Não use o Ctrl+R do UE4SS (travou o jogo).
- Testes offline: `PYTHONPATH=D:/tools/pylibs python tools/test_orders.py`.
- Comandos ao vivo: `sh D:/tools/foxhole-lab/run.sh <arquivo.lua>`; a saída vem só de `out(...)`. Os scripts
  `t_*.lua` e o robô `botloop.sh` ficam em `D:/tools/foxhole-lab/`, fora deste repositório. Não usar o canal
  com o robô rodando (as respostas se misturam).
- Robô de regressão: `sh D:/tools/foxhole-lab/botloop.sh` em segundo plano. O que ele faz e não faz: `MODLOG.md`.
- Captura: `cd D:/GitHub/universal-modder && UM_HOME=D:/tools/um-home python -m um win shot --title '^War' --scale 0.5 <png>`.
- Depois de cada mudança: validar ao vivo, registrar no topo do `MODLOG.md`, atualizar `mod/README.md`
  e, se houver tecla nova, `TESTE_MANUAL.md` e o teste de teclas em `tools/test_orders.py`.
- Quando um item do roteiro mudar de estado (`[ ]` → `[~]` → `[x]`, só `[x]` com validação ao vivo), atualizar
  `PROGRESS.md` e rodar `python tools/progress.py`, que recalcula as barras do `README.md`.

## Ambiente
- Cópia de laboratório: `D:\FoxholeLab\Foxhole` (UE4SS em `War/Binaries/Win64/ue4ss`, log `UE4SS.log`).
  Precisa do Steam aberto e logado + `steam_appid.txt`. Config/logs do jogo: `%LOCALAPPDATA%\Foxhole\Saved\`
  (não "War"); crashes em `Saved\Crashes`.
- O primeiro carregamento fica ~3 min em tela preta "Not responding": está carregando, não travou.
- Shipping ignora o mapa da linha de comando; o mod abre `HomeRegionW?listen` com `OpenLevel` (autostart).
- Ghidra 12.1.2 em `D:\tools\ghidra\ghidra_12.1.2_PUBLIC` (JDK 21); ponte GhidraMCP em
  `D:\tools\ghidra-mcp-v5.14.2`, servidor em `127.0.0.1:8089` (GUI com o plugin ou
  `com.xebyte.headless.GhidraMCPHeadlessServer`); projeto `D:\tools\ghidra-projects\Foxhole`, pré-script
  `D:\tools\ghidra-scripts\FoxPre.java`. Agentes não editam `~/.claude.json`: passe ao usuário comandos `claude mcp`.

## Armadilhas
- Custos: receitas usam `ProductionResource.ItemCodeName`; estruturas/veículos usam
  `ResourceAmounts` com `CodeNameSmallQuantity.CodeName`. Não engolir erro de schema como custo zero.
  Exportador/teste em `tools/export_costs.lua` e `tools/test_costs.py`.
- Spawn de caminhão pode retornar IsValid já em destruição; trace de chão pode acertar telhado.
  Conferir `bActorIsBeingDestroyed`, posição/saúde e superfície/folga, não só retorno/bounds totais.
- Lua tem limite de 200 locais por chunk: `main.lua` está em 178. Constantes em `CFG`, estados em `S`,
  funções novas em tabelas (`rts`, `fort`, `sv`, `logi`, `anim`, `ai`).
- Repositório git desde 2026-10-11 (`main` em github.com/Gaok1/foxhole-rts); o histórico anterior não existe.
  `.gitattributes` guarda os bytes como estão (`* -text`): não converter CRLF/LF dos patches `_lf` e candidatos.
- Hook de animação (`anim.onUpdate`, em `BlueprintUpdateAnimation` do `ABP_Male_C`, roda depois do nativo) só
  escreve no AnimInstance vivo. Todo caminho que destrói um soldado chama `anim.untrack` (endereço reaproveitado →
  escrita em pawn morto → crash nativo que pcall não pega). Mesma regra para qualquer cache por endereço.
- O canal de comandos só enxerga o que está na tabela `env` de `runCommandFile`; local nova precisa entrar lá.
- `tools/check_globals.py` é insensível a escopo: um `local x` interno antes do `local x` de topo esconde usos
  do de topo como global nil. Ele avisa esses casos; não use nome de tabela de topo (`ai`, `sv`, `fort`, `rts`,
  `anim`, `S`, `logi`) como variável local.
- Movimento: o mod zera atrito e frenagem, então a escala de `AddMovementInput` só limita a aceleração; para
  desacelerar escreva `CharacterMovement.Velocity` (`fort.capSpeed`). Meça movimento com um amostrador
  `LoopInGameThreadWithDelay(100)` gravando em `_G`, não com idas e vindas pelo canal (~1,8 s cada).
- UE4SS: ler `MasterPoseComponent`/`AnimClass` de um SkeletalMeshComponent derrubou o UE4SS; componentes não
  refletidos se acham por nome com `K2_GetComponentsByClass` (`v:get()`). Funções UFunction não podem ser chamadas
  de dentro de corrotina Lua: fatie trabalho longo em máquina de estados por quadro. `UEHelpers.GetWorld()` /
  `GetPlayerController()` fazem `FindAllOf` a cada chamada (lento): o mod guarda em cache por quadro.
  `K2_DestroyActor` não destrói `HeadlessPlayerController` (o mod reaproveita). `IsValid()` continua true em ator
  destruído até o GC. Saída de parâmetros vai na primeira tabela (`GetMousePosition(a, b)` → `a.LocationX/Y`).
- Visão: o jogo esconde personagens e veículos que o **pawn** do comandante não vê; o mod transforma o comandante
  num "olho" invisível levado ao soldado mais perto do foco da câmera. Mudar a posição do componente de LOS não
  adianta. Bordas de neve bloqueiam a visão.
- **Imagem não prova ausência:** estruturas também podem ficar invisíveis conforme o ângulo/oclusão da câmera.
  Conferir atores/classes/variantes e estado carregado; distinguir ruína de instalação ativa. Uma contagem zero
  numa classe não prova que a instalação não exista no mapa nem no estado de uma guerra do servidor.
- Traços em HomeRegionW: canal Visibility (0) atravessa veículos; Camera (1) bate em caminhões e prédios e não em
  `BPNoBuild_C` (o A* usa esse); traço por tipo de objeto acerta os volumes `BPNoBuild_C` (ignore).
- Animação: `CharacterStance` 0 em pé / 1 agachado / 3 correndo (+ `bStanceIsCrouched`); `ActivityState` 3 atirando,
  6 arremessando, 20 primeiros socorros; arma no soquete `S_GenericGun`; mira ao ombro com `bIsInScopeMode` +
  `canEnterStandScoping`.
- Achar assets: `FindAllOf("StaticMesh"/"SoundCue"/"Material")` + filtro de nome, `GetBounds()` para tamanho,
  depois uma "vitrine" lado a lado + captura para escolher.
- Câmera do RTS olha para +X: topo da tela = X maior, direita = Y maior.
