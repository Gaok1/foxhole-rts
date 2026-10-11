# Roteiro do Foxhole RTS

## Estado atual — depois do batch integrado de 11/10

**Estamos na fase 3: MVP logístico em uma região pequena, ainda não aprovado.**
**Lote logístico 2:** ajustes publicados, mas validação interrompida por crash
(PID4696/158s desde início). Último autosave60s tinha bmat40/sucata0; relatório
final perdido. Causa completa pendente; não aprovar cadeia/medevac/contratação.
Contrato vivo do caminhão confirmou RWDVehicleMovementComponent, raiz/updated
VehicleCollision(Box), ignoreNonRoot=true e colisão true→false ao ligar logística.
Não prova estrada/suporte. Sem segundo restart; diagnóstico segue offline.
Diagnóstico estreitou o crash para lista de PlayerState.UniqueId no fluxo local
de participantes/voz. IDs vazios de bots são hipótese; desligar voz não protege
todo o loop. Falta corrigir o contrato de NPC/controlador sem quebrar movimento
ou fabricar identidade; não há correção aprovada ainda.
Oracle CPU executou produtor/bridge/controlador/helper reais com fixtures: voz
false ou PlayerSaveGame ausente ainda permitem acumular nulos; objeto não nulo
posterior reproduz read0 no RVA do crash. Não prova quem os produz no jogo.
bRunPhysicsWithNoController também não substitui localidade de NPC possuído:
gate nativo e oracle CPU mostram que Controller presente pula essa flag.
Não desapossar NPC nem publicar esse atalho; posse/GC/movimento ainda necessários.
Sonda read-only de localidade/PlayerState/roster de tropas e pool preparada para
o próximo lote integrado; teste offline PASS, ainda não executada no Unreal.
Init nativo de HeadlessLocalPlayer rastreado parcialmente; constructor sozinho
não completa o contrato. Sem executor local refletido comprovado, não usar
conexão/login/RPC ou criação cega de LocalPlayer como correção.
As entradas históricas abaixo não substituem os resultados atuais:

- **Implementado:** implantação de refinaria/fábrica, coleta manual, refino/produção,
  caminhões, depósitos, recrutamento por estoque, bases avançadas, economia inimiga,
  ordens/grupos/alertas e save. Transporte continua reto/sem colisão, não por estrada.
- **Granadas integradas e testadas:** Warden/Colonial usam classes/data nativos;
  Owner/Instigator, fuse4, dano, reset em voo, classes simultâneas, contexto emprestado/
  trocado e GC em voo passaram no lote. Friendlyfire foi observado (soldado100→1).
  Não comprovada morte nativa do soldado/lançador nem estabilidade geral prolongada.
- **Falha de colisão comprovada:** Warden no caminhão collision-on900→788;
  collision-off900→900. A frota ainda desliga colisão, portanto explosivos não são
  integração funcional de interdição logística. Fuzil local continua pendente;
  DPS fictício de caminhão foi removido, não restaurá-lo para maquiar esse buraco.
- **Cadeia fresca falhou:** 353s/35amostras no hex: sucata entregue0/perdida110,02,
  bmat40 sem crescimento, caminhão de recurso não produzido. Combate/reabastecimento
  e cadeia inimiga ocorreram (4entregas/15camisas consumidas), conservação PASS;
  derrota na onda3. Logs registram perdas por morte e "ordem do jogador"; causa
  completa ainda não isolada. O ciclo antigo com120entregues não aprova esta partida.
- **Gate de morte/perda do caminhão também falhou:** dezesseis granadas Colonial
  deixaram o ator850HP; sem morte/carga perdida, não creditar cleanup como prova.

### Próximo lote, em ordem
**Candidato offline — save de comboios:** eSnapshot observa morte nativa antes
de converter carga em pendente; sv.collect captura a carteira após recompensas
dessas observações. Regressão FAIL antes/PASS depois, bateria15testes PASS.
Ainda sem publicação/validação viva; não resolve persistência de ferimentos.
Ambos os snapshots recusam HP desconhecido; save preserva arquivo anterior sem
perda inventada. Falta também persistir carga manual dos coletores (unitData não
guarda m.col): reatar ao trabalhador e replanejar entrega física, nunca creditar
refinaria só por carregar o save.
**Ajustes publicados, sem aprovação viva:** isolado no log que medevac automático descartava carga como
"ordem do jogador". Correção conserva carga durante evacuação e retoma a rota após
cura; morte/ordens explícitas continuam contabilizando perda. Dez testes offline
PASS; publicados no lote interrompido, não aprova a cadeia fresca.
Reposição automática também aguarda saída sem inimigo dentro do raio de perigo
já usado pela coleta; não gasta camisa na recusa. Sem aprovação viva, não prova
da causa de todas as mortes. Gate de reconstrução agora recusa registro ausente
em vez de tratar silêncio como sucesso. Treze testes offline PASS.

1. Isolar por que a coleta fresca não entrega e perde carga/consome camisas; corrigir
   sem dinheiro extra, entrega fictícia ou retirar combate para esconder a falha.
2. Tornar caminhões acessíveis a impactos nativos sem destruir transporte; estrada,
   obstáculos/água/pontes continuam parte do requisito, não simples ajuste visual.
3. Completar executor local de fuzil/impacto e morte/perda logística nativas;
   morteiro ainda próprio é dívida. Não alterar proteções/debug para forçar resultado.
   Pesquisa offline ampliou callers de trace e descartou confusão com consultas
   aéreas/mount e callbacks de apresentação; ainda sem executor de rifle comprovado.
4. Repetir ciclo integrado com critérios de coleta/refino/produção/transporte/
   consumo/corte/expansão. Mais UI, refinamento e mundo só depois do núcleo funcionar.

Evidências: `data/trace_native_batch_integrated.txt` e
`data/trace_batch_mvp_integrated.txt`; verificadores estritos retornam1 pelos gates
não aprovados. Uma publicação/run, sem crash observado; laboratório encerrado e
Steam preservado. Fonte publicada SHA256 ACB6ADFD3AE05828AB50C3D26CC3970673B09184E8FCD4BBCB3D010042CEFA64.

## Direção vigente — MVP primeiro (10/10)

**Candidato offline 11/10 — HP logístico nativo:** `logi.syncHealth` observa o
Health do ator antes de transportar/entregar; HP0/perda de ator encerra a viagem
e contabiliza carga perdida uma vez, sem esconder/destruir antecipadamente o casco.
DPS abstrato de emboscadas e dano próprio de morteiro contra veículos removidos.
Não entregue como combate completo: fuzil local, colisão das granadas com caminhões
e persistência de ferimentos pendentes. Nove scripts de teste offline PASS;
sem publicação. Gates vivos acumulados em `NATIVE_BATCH.md`, uma única sessão futura.

**Correção explícita do usuário:** MVP pouco refinado NÃO autoriza reinventar dano,
tiros e veículos já existentes no jogo. Prioridade antes de calibrar emboscadas:
rastrear disparo/projétil/impacto/dano nativo de veículo, provar execução local e
reutilizar o fluxo. IA/ordens/economy próprias continuam; sistemas de engine do
jogo não devem ser substituídos por DPS abstrato sem demonstrar a impossibilidade.
Ramo atual logi.hit/logi.blast/convoyTick é dívida de implementação, não direção aceita.

**Autorização 11/10:** reutilizar configuração nativa local do cliente, mantendo tudo
offline. `ServerSettings` deriva de `SaveGame`; constructor nativo preenche os
tweakables. Primeiro gate: `tools/probe_native_settings.lua` compara uma instância
própria com os defaults rastreados, sem associá-la ao GameInstance nem aplicar dano.
Sonda executada com defaults/binding confirmados; Steam aberto/logado pelo usuário.
Não criar rede/RPC, alterar CDO, desligar proteção ou inventar fórmulas.

**Gate vivo 11/10:** defaults e binding PASS; ApplyDamage45Explosive em caminhão
exclusivo deu retorno31.5/HP900→869 com settings recém-criada/associada imediatamente,
contra0/900 sem settings. Restore e cleanup PASS. Dano genérico comprovado; falta
integração/lifetime ancorado, morte e disparo nativo. Rastro `data/trace_damage_settings_fresh.txt`.
Oracle posterior (`data/trace_damage_native_repeated.txt`) comprovou Light/Heavy/Explosive
e HP até0 sem crash, com restore/cleanup. Wreck/destruição completa e rifle ainda não provados;
ator de teste foi removido manualmente só no cleanup, não creditar isso como morte nativa.
Usuário confirmou visualmente explosão e algo dropado nesse teste; registrar como
reação visual nativa observada, com identidade/conteúdo do drop ainda desconhecidos.
Lifecycle estático: Health0 aciona morte nativa e SetLifeSpan15s; casco ainda válido
imediatamente é esperado. Não chamar OnRep/morte manual para antecipar o timer.
**Explosivo local comprovado:** SpawnActor BPGrenadeW e timer nativo20s causaram
Health900→780 no caminhão sem ApplyDamage manual nem inventário/RPC. Restore/cleanup
PASS. Integração de lançamento/fuse real/atribuição ainda pendente; não é prova de rifle.

**Evidência nova:** ciclo de403s em CallumsCape com ondas/estoques reais do mod:
120sucata entregue/perda0, reconstrução de caminhão, produção/entrega na base,
reabastecimento em combate,4entregas inimigas/13camisas consumidas e derrota na onda4
com apenas3trabalhadores vivos. Conservação conferida em36amostras.
`tools/check_mvp_trace.py` verifica `data/trace_mvp_cycle.txt`.
Corte de comboio, expansão/base avançada em combate e vitória ainda não provados nesse ciclo.

Usuário pediu provar o conceito, aceitando implementação grossa e pouco refinada.
Priorizar cadeia jogável na região pequena: recurso -> refino -> fábrica -> transporte ->
abastecimento -> combate/expansão. Não gastar o próximo lote polindo chegada/animação.
Transporte atravessando estruturas permanece limitação funcional do protótipo, não prova de
acesso físico por estrada. Crashes e visibilidade que impedem jogar não viram mero cosmético.

### Refinamentos adiados, não bloqueiam o MVP
- [ ] Trabalhadores chegarem a um acesso/ponto de entrega e depois esperarem em local seguro,
  em vez de parar no trilho por entrar no raio de entrega de 15 m.
  Sondas: data/trace_access_refinery.txt e data/trace_area_use_refinery.txt;
  UseAreaBox/TransferLocation nativos encontrados, sem integração nem interação nativa.
- [ ] Marcha/medevac dos soldados já presos em saves antigos; não confundir unidade sem ordem
  com falha de rota, nem usar sucesso da coleta para declarar navegação geral resolvida.

Esta direção substitui as prioridades históricas abaixo: entrega regional funcional/MVP
antes de refinamento do estacionamento dos trabalhadores.

**Visual (10/10):** linha horizontal durante movimento desapareceu no teste do usuário com VSync1.
Publicado VSync no RTS/restauração na saída e olho no foco da câmera (inclusive pausa); caminhão longe
do esquadrão reapareceu. Corrigida origem de nova partida para base independente do olho.
Visibilidade geral e soldados presos continuam abertos: próxima prioridade é marcha/medevac dos
trabalhadores com base correta, sem extrapolar a entrega120 de um percurso para navegação geral.

**Atualização mais recente (10/10):** coleta fina entregou120/perda0 sem auxílio. Reconstrução transacional
publicada: ator900HP na fábrica e débito único100 validados; nova partida comprou/reaproveitou o ator
após coleta/refino sem créditos. Bateria29/29 PASS. Próximo: caminhões pela estrada real; transporte
atual reto/sem colisão não aprova cadeia regional. Detalhes no topo do MODLOG.md.

**Prioridade atual (10/10):** o usuário pediu continuar desenvolvimento e adiar crashes/efeito amarelo.
Lote logístico v4.1 integrado à fonte: 29/29 testes offline passaram. Validação Unreal ainda pendente;
não chamar de estável nem bloquear novas features pelo antigo gate manual. Estradas continuam pendentes.

**Validação de 10/10:** base nativa construída, recruta em base abastecida e save v2 restaurado após reinício
e na mesma carga em HomeRegionW. Estoque 9 camisas/19 fuzis preservado; testes com créditos de laboratório,
não equilíbrio nem transporte real. Infraestrutura/carteira no hex e rede de estradas ainda precisam validação.

**Lote seguinte de 10/10:** implantação de 1000 e restauração de infraestrutura/carteira passaram em CallumsCape,
inclusive repetição sem duplicar. Coleta manual NÃO passou: 120 sucata recolhida, retorno bloqueado por
IndustrialWall03Snow31, zero entregue. Próximo trabalho é navegação dos trabalhadores em volta do muro.
Rede da região exportada (405 controles/431 segmentos), mas superfície/envelope/acessos continuam pendentes.

**Navegação da coleta:** fallback cego removido só desse ramo e recusa/frenagem validadas no jogo.
Ainda falta encontrar a passagem real ao redor do muro e completar entrega sem auxílio do usuário.
Rastro: data/trace_path_collection.txt. Limite de inclinação do planner difere do nativo, mas ampliar limites sozinho não resolveu.

Direção do usuário (2026-10-09): o mundo do Foxhole é enorme, então começamos numa **região pequena**,
melhoramos até ficar bom, e só depois vamos para o mundo todo. No Foxhole **a guerra é a parte pequena da
engrenagem**: o que move tudo é a logística (recursos, refino, fábrica, transporte, abastecimento da frente),
com veículos, navios e aviões. O RTS precisa ter isso como centro, não só o combate de esquadrão.

## Fase 1 — Frente pequena (agora: HomeRegionW)
Combate de esquadrão, pontos, ondas, assalto, fortificação, tempo, câmera e ferramentas de várias frentes
(lotes 1–11). Falta: os testes com entrada real do usuário (`MANUAL_TEST.md`).

## Fase 2 — Estudo das mecânicas do jogo (pelos dados do próprio jogo)
**Primeira leitura feita (2026-10-09): `MECHANICS_STUDY.md`.** HomeRegionW tem campos, refinarias,
fábrica e caminhões para prototipar a cadeia, mas é a ilha de treinamento/embarque dos Wardens,
não uma região da guerra. O laboratório não substitui a validação num mapa `Maps/Master/*Hex`.
Ler em tempo de execução (UE4SS) o que o Foxhole já define, para que os números do mod venham do jogo:
- **Itens e custos:** classes de item, o que cada caixa contém, custo em material (bmat, emat, rmat, combustível).
- **Produção:** refinaria, fábrica, fábrica de munição, oficina de veículos, estaleiro: receitas e tempos.
- **Recursos:** campos de sucata, componentes, enxofre, petróleo, carvão; o que o mapa de teste tem.
- **Veículos:** caminhões (capacidade, velocidade, combustível), blindados, tanques, artilharia.
- **Navios e aviões:** quais existem na versão do cliente (a tela "Foxhole Airborne" indica aviões), papel de cada um.
- **Estruturas:** base avançada, depósito, porto, casamata, bunker, trincheira: custo, vida, função.
- **Mapas:** quais regiões estão no cliente e qual é um bom "pedaço" do mundo para a fase 3.

## Princípio: rastrear antes de reinventar (pedido do usuário, 2026-10-09)
O mod chama peças do jogo uma a uma e às vezes esquece uma (ex.: soldado morto que continua "correndo" no lugar).
Antes de implementar ou consertar uma mecânica:
0. **Consultar o universal-modder:** skill `reverse-engineering` (seção "Make it an oracle": gravar traços reais
   e comparar com o que o mod faz) e `um kb search`.
1. **Procurar a chamada de alto nível** que o jogo já usa (morrer, atirar, recarregar, curar, construir) e
   preferir ela a montar os efeitos à mão. Ferramentas: lista de UFunctions da classe (`ForEachFunction`),
   Ghidra para o código nativo (projeto já montado, `ghidra-setup`).
2. **Rastrear o fluxo real uma vez:** ligar hooks do UE4SS nas UFunctions das classes envolvidas (personagem,
   controlador, arma, AnimInstance) e gravar a ordem das chamadas e os valores que mudam quando a ação acontece
   de verdade (o usuário faz a ação com o personagem dele, ou o jogo faz sozinho, como a morte).
3. **Montar o contrato:** a lista do que o fluxo real muda (variáveis de animação, velocidade, flags replicadas,
   efeitos, sons). Se o mod precisa reinventar (porque o caminho do jogo exige servidor ou inventário, que
   ficaram fora do modo offline), ele cumpre esse contrato item por item.
4. **Testar o contrato:** um teste ao vivo lê esses mesmos valores depois da ação do mod e compara com o rastro.
Limite: o jogo não tem IA de soldado; nossos soldados são "jogadores" sem teclado, então a parte de decidir sempre
será do mod. O que dá para ganhar de graça é o que vem depois da decisão (animação, morte, efeitos).

**Primeiro contrato validado (lote 14): morte.** `ApplyDamage` no host zerava HP sem acionar o ragdoll;
`OnRep_Health` faz a transição visual nativa. O mod agora para o movimento, devolve os valores originais e
retira o cache de animação antes dessa chamada. Rastro antes/depois: `data/trace_death.txt`.

## Interface e retorno visual (pedidos do usuário, 2026-10-09)
Vale em qualquer fase; entra quando a mecânica correspondente estiver firme.
- **Visibilidade RTS (pedido de 10/10):** resolver soldados, caminhões e estruturas ficando invisíveis.
  **Reforço de 11/10 — pendente:** usuário ainda observa coisas sumindo pela distância.
  Incluir reprodução por afastamento/zoom, distinguindo distância de renderização (culling/LOD),
  LOS e oclusão; identificar quais atores somem e confirmar que continuam vivos/carregados.
  Critério: unidades e instalações relevantes permanecem visíveis no alcance/zoom do RTS.
  Falha funcional prioritária junto ao transporte: observar várias frentes não pode depender da proximidade
  do pawn do comandante. Rastrear LOS, ocultação nativa e oclusão da câmera separadamente; conferir atores
  vivos/carregados e HiddenInGame antes de concluir ausência. `rts.eyeTick` já acompanha o foco da câmera,
  mas isso não resolveu todo o desaparecimento relatado. Validar câmera afastada do grupo, foco em comboio, zoom alto, neve e instalações em
  diferentes ângulos; não resolver com bolinhas nem confundir contorno de seleção com visibilidade normal.
- **Linha/tremeluzir ao mover câmera (relato de 10/10):** usuário descreve uma linha no meio da tela,
  não desenhada, semelhante a atraso de renderização. Investigar temporalmente; tearing é hipótese,
  não diagnóstico. Separar sincronização/apresentação, atualização de câmera e LOS/pós-processamento.
  Comparar movimento parado/ativo e VSync sem alterar permanentemente configuração do usuário.
- **Caixa de seleção visível:** hoje arrastar seleciona uma área invisível. Desenhar o retângulo enquanto o botão
  está apertado. Caminho provável: um `Border`/`Image` semitransparente no mesmo widget do painel (clone do
  `CrosshairWidget_C` com `CanvasPanel`), posicionado pelas coordenadas do mouse. O desenho de depuração
  (`DrawDebug*`) costuma não existir em build Shipping.
- **Seleção (lote 17):** contorno amarelo brilhante no corpo SOMENTE selecionado, sem discos. A sonda do
  `M_OccludedOutline` mostrou preenchimento de partes encobertas, não borda visível; mantido também só na
  seleção. Corpo/cabeça/mãos/pernas/equipamento têm CustomDepth separado. Contorno completo usa cópias aderentes
  com MasterPose, sem IA/física; aparência aprovada, mas quedas nativas UE4SS ao ampliar às peças ainda NÃO
  resolvidas. Prioridade ao retomar: stability/GC/reseleção/morte; depois seleção grande/zoom alto. Shader cooked é
  alternativa caso o custo das cópias pese. Não expandir interface neste encerramento autorizado.
- **Mais interface, quando fizer sentido:** painel de logística (fábrica, depósitos, caminhões) em vez de linha de
  texto; ícones de ordem; barra de produção; mini-mapa da região; botões clicáveis para quem não decora teclas.
  **Minimapa confirmado pelo usuário:** implementar junto à evolução da UI, sem prioridade no lote atual.

## Fase 3 — Logística numa região
**Em andamento (2026-10-09).** Feito: lote 12 (cadeia de sucata a depósito, consumo de camisas e munição,
caminhões que podem ser destruídos) e lote 13 (comboio inimigo que pode ser emboscado e encolhe as ondas).
Lote 17 validou a cadeia própria em CallumsCapeHex: implantação explícita com orçamento/rollback e entrega
de caixas na base. Falta: caminhões pela estrada (água/pontes/colisão), mais tipos de caixa, cadeia inimiga
mais completa e equilíbrio/combate prolongado no hex. Detalhes no topo do `MODLOG.md`.

**Escopo corrigido pelo usuário (2026-10-09):** HomeRegionW é bancada de teste, não o destino da fase 3.
Antes de expandir a cadeia, reconhecer um mapa `*Hex` local: carregamento/streaming, posição inicial segura,
terreno, estradas, campos e estruturas realmente presentes. Ter o `.umap` no cliente não prova que toda
a população de uma guerra exista offline. Escolher uma região com uma cadeia curta após esse inventário.
Descobrir a rede por mundo carregado, sem reutilizar coordenadas/cache do lobby. Se faltar uma instalação
ou acesso, indicar a ausência; não considerar uma entrega concluída nem inventar uma instalação silenciosa.
**Primeiro reconhecimento local:** `data/trace_regions.txt`. Deadlands carregou com estradas e instalações
em ruínas; CallumsCape tem um campo de sucata ativo e ruínas de refinaria/fábricas próximas, mas não caminhões
ativos nas sondas. Candidata à cadeia pequena **após** rastrear reconstrução nos locais nativos e criar
veículos reais do cenário. Não concluir ausência por imagem: LOS/oclusão pode esconder estruturas e veículos.

**Lote 16 — contrato parcial:** `data/trace_rebuild.txt`. Corrigido o schema dos custos:
refinaria/fábrica 400 bmat cada, TruckW 100. Spawn das classes ativas na transformação da ruína validou
classe/HP, mas não é conclusão nativa de construção. Canteiro cru veio sem alvo; estacionamento ingênuo
pegou telhado e ator já em destruição.

**Lote 17 — implantação própria:** Alt+L reusa estruturas ativas ou substitui ruínas nos locais nativos,
com 1100 bmat do cenário (400+400+3×100), estacionamento Landscape validado e rollback sem débito/limpeza
da partida. Repetir não duplica. Em 65,21 s no hex produziu três caixas e entregou munição/camisas.
Não é chamada nativa de conclusão de canteiro nem facilities; carteira/infraestrutura não persistem no save.
Acesso por estrada ainda necessário antes de considerar o cenário pronto.

**Construção tem dois ramos:** fábricas/refinarias tradicionais são estruturas do mundo em locais fixos;
facilities são complexos industriais construídos pelos jogadores. Não tratar toda fábrica como livremente
construível nem dar a toda facility as mesmas receitas da fábrica urbana. Contexto:
[estruturas fixas e construídas](https://foxhole.wiki.gg/wiki/Structure) e
[devblog oficial de facilities](https://www.foxholegame.com/post/devblog-foxhole-inferno).
Confirmar classes, requisitos e fluxo no cliente instalado antes de implementar; economia e IA continuam
próprias do mod, sem servidor/RPC/inventário. Construção de facilities ainda não foi implementada.

Trocar a "mão de obra" abstrata por uma cadeia de verdade, pequena:
1. **Coleta:** soldados ou caminhões tiram sucata de um campo.
2. **Refino:** a refinaria transforma sucata em material de construção (bmat).
3. **Fábrica:** bmat vira caixas (fuzil, munição, médico, granada).
4. **Transporte:** caminhões levam as caixas da base até a frente por estrada (podem ser emboscados).
5. **Consumo:** soldados recrutados e reabastecidos só onde há caixas; a frente sem suprimento definha.
A IA inimiga roda a mesma cadeia: cortar a estrada dela vira estratégia.

**Decisão de design (2026-10-09, delegada pelo usuário ao Claude): de onde vêm os soldados.** No Foxhole cada
soldado é um jogador que renasce numa estrutura de spawn e gasta camisas (Soldier Supplies) do estoque dela. O RTS
segue esse modelo, sem andar do fundo do mapa até a frente (o mapa é grande demais):
- **Pontos de spawn = estruturas:** a base principal e **bases avançadas** construídas perto da frente (classe real
  `ForwardBase1`, 300 bmat, estoque 15, em `data/game_costs.txt`; outras classes de spawn só depois de rastrear).
- **Recrutar gasta o estoque do ponto:** 1 camisa por soldado, mais a arma da função (fuzil para fuzileiro etc.).
  Nasce no ponto abastecido mais próximo do cursor/frente; sem estoque ali, recusa com aviso (sem mão de obra mágica).
  Na partida com logística a mão de obra abstrata deixa de ser o limite; ela continua no modo Assalto.
- **A logística move suprimento, não soldados:** caminhões levam camisas e armas às bases avançadas; cortar o
  abastecimento de uma base impede reforço nela. Transporte de tropa fica para a fase 4.
- **Trabalhadores no estilo aldeão (Age of Empires):** a partida começa sem caminhão de recurso; soldados sem fuzil,
  nascidos na base principal (1 camisa), coletam sucata à mão; a fábrica produz o caminhão como melhoria; perder o
  caminhão volta à coleta. A base mantém sozinha o número de trabalhadores de `CFG` enquanto houver camisas.

## Fase 4 — Veículos e armas pesadas
Caminhões dirigidos pela IA do mod, blindados, artilharia com munição produzida, construção de base avançada.

## Fase 5 — Várias regiões e o mundo
Duas ou mais regiões ligadas, frentes múltiplas de verdade, portos e navios de transporte, aviões; por fim, uma
campanha pelo mapa do mundo.

Cada fase segue o fluxo do projeto: construir em lotes, testar no laboratório, registrar no `MODLOG.md`.
