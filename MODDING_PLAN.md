# Foxhole RTS — reconhecimento inicial

> Atualização 2026-10-07: o planejamento abaixo preserva hipóteses históricas.
> O estado executado está no MODLOG: v0.3 validada anteriormente; v0.3.1 adiciona
> parada por grupo (H), com testes offline aprovados e teste no jogo pendente.
> Uso e avaliação do toolkit: UNIVERSAL_MODDER_NOTES.md. Rifles reais pendentes.
> Atualização 2026-10-07 (noite): decisão de ficar totalmente offline com modelo próprio.
> v0.4 validada no jogo: parada H corrigida, classes com armas na mão, recrutamento e economia.
> Rifles via inventário/RPC saíram do caminho crítico.

Data: 2026-10-06. Status: investigação; nenhuma rota RTS demonstrada.

Atualização (rodada 2): o executável do cliente contém código de servidor (listen server via `?listen`, `ASimGameMode`, ReplicationGraph). O bloqueio provável é a dependência do backend `FExternalWarService`. Não há rota pública (offline, servidor privado, SDK). Detalhes em `ENVIRONMENT_RECON.md` (seção Rodada 2). Próximo passo: medir essa dependência por decompilação no Ghidra, sem executar o jogo.

## Instalação verificada

- Caminho: `D:\SteamLibrary\steamapps\common\Foxhole`.
- Loja: Steam; App ID `505460`; build instalado `25730371`, conforme manifesto local.
- Engine detectada pelo scanner: Unreal, assinatura `UE4+Release-4.24`. Não determina todas as customizações da engine.
- Projeto: `War`; executável principal: `War\Binaries\Win64\War-Win64-Shipping.exe`.
- Scanner encontrou dois arquivos PAK, sem IoStore, e nenhum loader instalado.
- Sem EAC/BattlEye/EOS/packer (verificado em arquivos, strings e histórico de processos). Há VAC, detecção própria de discrepância de tempo e `bAllowMods` no servidor: tratar o cliente online como protegido.
- PAK principal com índice não criptografado, sem `.sig`, sem IoStore.
- Config/logs/saves inexistentes: o jogo nunca rodou nesta instalação. Só serão criados após o primeiro lançamento.

## Rota e limitações

A FAQ oficial não oferece suporte a mods de gameplay nem single-player com bots. Menciona somente mods visuais sem vantagem competitiva: https://www.foxholegame.com/faq.

O scanner sugere UE4SS/PAK por reconhecer Unreal. Essa sugestão é genérica, NÃO é compatibilidade confirmada com Foxhole e NÃO será aplicada ao cliente online.

Histórico: a rota inicial era reconhecimento somente leitura. Ela foi substituída pela rota abaixo, com o desenho normativo aprovado em 2026-10-06. O UE4SS vai **somente** na cópia de laboratório, nunca no cliente online.

## Rota escolhida: listen server local isolado (viabilidade técnica pendente)

"Listen server local isolado": usar o código de servidor já presente no cliente para hospedar uma sessão local, sem conectar aos servidores oficiais. A camada RTS (câmera, seleção, ordens) entra depois, via UE4SS/Lua ou pak.

Condições, todas ainda não satisfeitas:
1. **Técnica:** `?listen` e `ASimGameMode` funcionam sem `FExternalWarService`, ou com dependência contornável sem falsificar autenticação. A medição é por decompilação.
2. **Normativa (aprovada pelo usuário em 2026-10-06):**
   - Manter intacta a verificação de posse do Steam (`steam_api64`, sem tocar em DRM nem em tickets).
   - A sessão modificada nunca contata serviços da Siege Camp. As chamadas do `FExternalWarService` recebem respostas locais apenas dentro da sessão local.
   - O servidor local roda sem VAC (modo inseguro, a confirmar).
   - O mod fica inativo fora do modo RTS local.
   - Rejeitado: "autenticar online e depois ficar offline", porque expõe um cliente modificado ao backend oficial (risco de VAC/ban).
3. **Isolamento:** cópia de laboratório que nunca conecta a servidores oficiais (VAC). Backup e autorização antes de instalar loader.

Alternativas, se a rota cair:
- (a) mod só visual/UI via pak, tolerado mas sem simulação;
- (b) painel RTS-like sobre a War API, só leitura;
- (c) perguntar à Siege Camp (rascunho em `ENVIRONMENT_RECON.md`).

## Próximas verificações

O documento operacional agora é `HOW_TO_MAKE_THE_MOD.md`: arquitetura, limitações e protocolo de testes T0–T9. Resumo do estado:

1. **Feito (estático):**
   - boot direto no mapa por linha de comando;
   - sem servidor Steam/VAC num cliente;
   - único bloqueio do host é o perfil em `PostLogin`;
   - soldados = jogadores locais extras, molde `-headless`;
   - mapas sem NavMesh.
2. **A executar com o usuário:** T0–T3 (lançamentos do cliente e da cópia, `?listen`, conferência de VAC no log).
3. **Depois:** UE4SS na cópia (T4–T5), stub de perfil em C++ (T6), primeiro soldado (T7), navegação (T8), marco do esquadrão (T9).

## Verificação realizada

- Rodada 2: recon local, análise estática PE/strings/xrefs, pesquisa web e varredura da KB, todos somente leitura. Ghidra 12.1.2 + GhidraMCP 5.14.2 instalados em `D:\tools`; projeto `D:\tools\ghidra-projects\Foxhole`, fora do repo.

- `python -m um scan "Foxhole" --json` — inspeção estática, 43 arquivos indexados, sem truncamento informado.
- Leitura do manifesto Steam e listagem superficial de executáveis.
- Busca da base local por Foxhole sem resultados; notas Unreal encontradas não comprovam suporte a este jogo.
- Nenhum jogo aberto, processo instrumentado, arquivo de instalação alterado ou pacote extraído.
