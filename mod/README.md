# Foxhole RTS — protótipo local v0.9 (totalmente offline)

Mod Lua desenvolvido com assistência de IA, usando UE4SS e Universal Modder.
Personagens e efeitos pertencem ao jogo e não estão incluídos aqui.

**Lote logístico v4.1 em desenvolvimento:** coleta manual, bases avançadas, economia ampliada, cadeia inimiga e save v2. Testes offline passaram; criação/recrutamento em base e save/restore passaram em HomeRegionW. Transporte, hex e equilíbrio ainda pendentes. Crash de teclas e flicker continuam abertos por decisão do usuário.

## Requisitos e instalação no laboratório

- Cópia própria do Foxhole; build testado anteriormente: Steam 25730371 / UE 4.24.
- Steam aberto e autenticado; não modificar verificações de posse.
- Cópia separada do jogo com isolamento de rede conferido antes de executar.
- UE4SS já configurado para essa cópia e versão da engine.
- Backup de `%LOCALAPPDATA%\Foxhole` antes de cada lançamento modificado.

Com o processo encerrado, copie `FoxholeRTS` para
`War\Binaries\Win64\ue4ss\Mods` **da cópia de laboratório**. `enabled.txt`
habilita o mod. Nunca instale no cliente oficial nem conecte a cópia aos servidores
oficiais. Não há garantia de compatibilidade ou de segurança de conta.
Não distribua a cópia do jogo, suas DLLs ou assets extraídos.

F9 abre a sessão local; F10 ativa a câmera RTS. O autostart e o canal de comandos
são opcionais de desenvolvimento, habilitados por `FoxholeRTS/autostart.txt`;
o canal executa Lua local arbitrário, não é uma sandbox.

**Começo rápido:** com o modo RTS ligado, Shift+F6 inicia uma partida (esquadrão de 6, três pontos de
controle, ondas automáticas). Capture os pontos, recrute com Ctrl+1–4 e vença 10 ondas — ou segure os três pontos por 90 s. F5 mostra as teclas.
Em um hex sem cadeia ativa, Alt+L tenta a implantação inicial descrita em **Logística**, depois Shift+F6.

## Controles

| Tecla | Ação |
|---|---|
| F6 | Criar esquadrão misto grátis (caixa de areia; até 12) |
| Ctrl+1 / 2 / 3 / 4 / 0 | Recrutar fuzileiro (20) / metralhador (35) / atirador (45) / médico (30) / oficial (40, só um) com mão de obra no Assalto; na logística usa camisas e, para fuzileiro, fuzil |
| 1–5 / 0 | Seleciona o grupo (dois toques rápidos = câmera vai até ele) / todos |
| Alt+1–5 | Põe os selecionados no grupo (um grupo por frente; cada soldado nasce no 1 ou no 2) |
| Espaço | Câmera vai ao último alerta; de novo (em 4 s) = alertas anteriores |
| Q / E | Câmera no ponto de controle anterior / próximo |
| L | O próximo caminhão de suprimentos vai ao depósito sob o cursor (base ou ponto seu); fora deles = automático |
| Shift+L | Prioridade da fábrica: automático → munição → camisas → fuzis → bandagens |
| Ctrl+L | Câmera passa pela fábrica, refinaria, campo de sucata e caminhões |
| Alt+L | Implantar refinaria/fábrica nos locais nativos e caminhões faltantes, com orçamento inicial do cenário |
| Botão esquerdo | Selecionar soldado; arrastar = caixa; Shift soma (contorno amarelo brilhante = selecionado) |
| Botão direito / F7 | Mover selecionados em formação; sobre um inimigo = atacar esse alvo |
| Shift+botão direito / Shift+F7 | Pôr o destino na fila (percorrem os pontos em sequência) |
| Ctrl+botão direito / Ctrl+F7 | Fogo de supressão em área por 20 s (sem visada só suprime; gasta munição) |
| K | Erguer barreira de concreto sob o cursor (15 de mão de obra, até 30; cobertura baixa; F11 remove) |
| Ctrl+5 | Fogo de morteiro sob o cursor (40 de mão de obra, recarga 20 s; 3 granadas após 2,5 s; só ferem o inimigo) |
| J | Criar ponto de controle sob o cursor (até 5) |
| Home | Recuar: selecionados correm ao ponto seu mais próximo (ou ao comandante) sem atirar e levam metade dos acertos |
| End | Segurar posição: param e não buscam cobertura; continuam atirando; nova ordem libera |
| Shift+F6 | Nova partida: limpa tudo, esquadrão de 6, ondas automáticas e três pontos de controle |
| Alt+F6 | Assalto: o inimigo começa dono dos três pontos, entrincheirado e com arame; tome todos |
| Ctrl+F6 | Continuar a partida salva (gravada sozinha a cada 30 s durante as ondas automáticas) |
| F4 / Shift+F4 | Criar onda / alternar ondas automáticas |
| F11 | Limpar soldados, inimigos, corpos, barreiras e pontos |
| F2 / WASD ou setas / roda do mouse ou PageUp, PageDown | Centralizar / pan / zoom |
| Pause ou Ctrl+Espaço | Pausa tática: o jogo para, mas a câmera, a seleção e as ordens funcionam |
| Insert | Velocidade 1x / 2x / 3x (desligar o RTS volta a 1x) |
| F3 | Alternar pan pela borda (desligado por padrão) |
| F5 | Mostrar/esconder a ajuda de teclas na tela (aparece sozinha por 40 s ao ligar o RTS) e registrar o status no log |
| Shift+F5 | Dificuldade: fácil / normal / difícil (precisão inimiga, tamanho das ondas, mão de obra); fica salva em `settings.txt` |
| Ctrl+6 | Caixa de suprimentos sob o cursor (−25): recarrega munição a até 4,5 m por 60 s (máx. 3) |
| Ctrl+7 | Trincheira sob o cursor (−20): até 4 soldados dentro; tiros acertam 60% menos e suprimem pela metade (granada e morteiro não) |
| Ctrl+8 | Posto de socorro sob o cursor (−30, até 2): soldados seus a 6 m, fora de fogo pesado, curam 4 HP/s e param de sangrar |
| Ctrl+9 | Arame farpado sob o cursor (−10, até 10): faixa de 6 m atravessada à ameaça; quem passa (os dois lados) anda a 35% |

As teclas evitam os mapeamentos padrão do jogo (B = construir, H = callouts, F8 = esconder interface,
Shift+1–7 = comandos de admin). 1–5, 0, Espaço, Q e E são ações do soldado no jogo (arma, gestos, escalar,
montar, usar), sem efeito no RTS, que desliga a entrada do comandante.
No modo RTS a entrada do comandante fica desligada, para o clique esquerdo (Fire no jogo) não fazê-lo atacar.

## Classes e economia

Os custos de mão de obra da tabela valem no Assalto/fora da logística. Na logística, recrutamento gasta o estoque da base de nascimento, não esses custos.

Com o modo RTS ligado, um painel no canto superior esquerdo mostra mão de obra, esquadrão (selecionados),
onda, inimigos, abates, perdas e a contagem da próxima onda automática.

| Classe | Custo | Alcance | Tiro a cada | Dano | Precisão base | Munição | Notas |
|---|---|---|---|---|---|---|---|
| Fuzileiro | 20 | 22 m | 1,6 s | 34 | 60% | 40 | — |
| Metralhador | 35 | 26 m | 0,35 s | 14 | 30% | 150 | anda a 75%; só atira montado (parado 1 s): +30% de acerto, +50% de supressão |
| Atirador | 45 | 40 m | 3,5 s | 70 | 85% | 15 | — |
| Médico | 30 | 15 m | 2 s | 20 | 40% | 24 | cura 12 HP e estanca o mais ferido a ≤3,5 m a cada 1,5 s; vai até feridos a ≤12 m |
| Oficial | 40 | 18 m | 1,8 s | 25 | 50% | 24 | só um por esquadrão; aliados a ≤10 m acertam 15% mais e se recuperam da supressão 1,8× mais rápido; estandarte sobre a cabeça |

**Munição:** cada soldado seu carrega a munição da tabela e para de atirar quando ela acaba (alerta e "SEM MUNIÇÃO" no painel; abaixo de 25%, "munição baixa" no painel e uma caixinha de munição sobre a cabeça). Dentro de um ponto seu ou a até 5 m da base (onde o comandante estava ao ligar o RTS; F2 centraliza nela), recarrega 15% por segundo. O inimigo não tem limite de munição.

Fuzileiros tentam lançar granada (recarga 18 s) contra cobertura baixa, até 18 m e dentro
dos limites de velocidade dos dados do jogo. **Lote offline de 11/10, ainda não publicado:**
projétil BPGrenadeW (Warden) ou Grenade_C (Colonial), dados de cada facção,
fusível real de 4 s, balística/colisão/dano/efeitos nativos; sem arco
teleportado ou dano próprio de granada. Se o solver/spawn recusar, não gasta recarga e
continua o tiro normal. Contexto local ancorado até os projéteis terminarem; reset cancela
somente os projéteis próprios. Equipe/atribuição/dano em soldados e integração logística
aguardam o batch vivo. Tiros de fuzil e morteiro ainda usam o protótipo próprio — dívida
explícita, não equivalentes a combate nativo completo.
**Morte:** aliados e inimigos param e caem com o ragdoll do próprio jogo. O mod retira o corpo do controle de
animação antes de acionar a morte nativa; o corpo fica no chão por 20 s e então é removido (não continua correndo).
Veterania: a cada 2 abates o soldado sobe um nível (até 3), com +10% de precisão por nível; vale também para o inimigo.
A precisão cai até a metade no alcance máximo. Todo tiro suprime o alvo (a MG mais rápido): suprimido erra mais e anda devagar,
e o inimigo muito suprimido fica preso no lugar. Alvo atrás de cobertura baixa (muro, barreira) leva metade dos acertos.
Soldados parados e sem ordem (aliados e inimigos) procuram sozinhos cobertura a até 4 m quando estão expostos; uma trincheira com vaga a até 4,5 m tem preferência. Mover para dentro de uma trincheira acomoda 4 nela e o resto em linha atrás. A mão de obra começa em 60,
regenera 1/s mais 0,5/s por ponto de controle seu (máx. 200) e rende +8 por abate e +30 por onda eliminada.
Nas ondas automáticas, vence quem eliminar a 10ª onda ou segurar todos os pontos de controle por 90 s seguidos; a derrota ocorre sem soldados e sem mão de obra
para um fuzileiro, ou quando o inimigo domina todos os pontos de controle. A precisão inimiga cresce 4% por onda (até +50%), e cada onda traz um inimigo a mais para cada ~2,5 soldados seus (até 16 por onda).

## Evacuação de feridos

Um soldado seu abaixo de 30% de vida, parado e sem ordem sua há 15 s, recua sozinho (sem atirar, como o Home) ao
posto de socorro mais perto; sem posto, a um ponto seu; sem ponto, ao médico. Quando chega a 80% ele se libera.
Qualquer ordem sua cancela a evacuação.

## Moral inimiga

Uma onda de 6 ou mais que cai a um quarto do tamanho quebra: os sobreviventes fogem de volta por onde vieram
(sem atirar e levando metade dos acertos) e somem ao chegar, sem contar abate. A morte de um oficial inimigo
também abala (suprime) quem estava perto dele. No assalto as guarnições não fogem.

## Oficial inimigo e metralhadora inimiga

A partir da onda 3, cada onda chega com um oficial (estandarte verde sobre a cabeça) que dá aos inimigos perto
dele a mesma aura do seu oficial; abatê-lo rende +20 de mão de obra. No assalto, a guarnição do ponto da frente
tem um oficial. A metralhadora inimiga que perde você de vista continua suprimindo por 8 s o lugar onde o viu
por último: esconder-se atrás de um muro não basta, é preciso sair da área ou flanqueá-la.

## Morteiro inimigo

A partir da onda 4, cerca de 40% das ondas chegam em pinça (dois grupos por lados diferentes). A partir da onda 4 o inimigo dispara morteiro (2 granadas, 3 s de aviso com som e anel laranja) sobre
grupos de 3 ou mais soldados seus. Soldados sob o aviso correm para fora do anel sozinhos, exceto os
que estão segurando posição (End) ou muito suprimidos: esses levam o fogo.

## Pontos de controle

Ligar as ondas automáticas (Shift+F4) sem pontos cria três ao redor do esquadrão (frente e flancos),
em chão plano e livre de veículos; J cria outros sob o cursor. Cada ponto é um anel pontilhado laranja
de 5 m de raio com o estandarte do dono no centro (azul = seu, verde = inimigo, nenhum = neutro).

- Capturar: ter soldados dentro do anel sem inimigos. Um soldado leva 10 s de neutro a dono; até três aceleram.
  Os dois lados dentro = disputado (para). Para tirar o ponto do dono é preciso levá-lo de volta a neutro primeiro.
- Cada ponto seu rende +0,5 de mão de obra por segundo.
- Ao tomar um ponto, o inimigo cava de graça uma trincheira no centro dele; ela serve a quem estiver dentro, então retomá-lo pede granada ou morteiro.
  Ele também estende uma faixa de arame a 9 m do centro, do lado do seu esquadrão: contorne-a ou atravesse sob fogo de supressão.
- Ponto seu é posto de socorro e depósito: soldados dentro do anel recarregam 15% da munição por segundo e, sem supressão, recuperam 2 HP/s.
- Inimigos fora de combate marcham ao ponto mais próximo que ainda não dominam e o seguram.
- Ponto inimigo longe do seu esquadrão (>15 m) vira entrada das próximas ondas: retome-o para afastá-las.
- No Assalto, recrutar (Ctrl+1..4) dentro de um ponto seu faz o soldado nascer nele. Na logística, só base principal ou base avançada abastecida é local de recrutamento.
- O painel mostra `pontos 1/3 [A+ Bx Co]`: `+` seu, `x` inimigo, `o` neutro (com % durante a captura).

## Assalto (Alt+F6)

Outro jeito de jogar: você começa com 8 soldados e 120 de mão de obra, e o inimigo já é dono dos três pontos
(26–36 m à frente e nos flancos), cada um com trincheira, uma faixa de arame do seu lado e 4 soldados de
guarnição. Não há ondas: o inimigo só recebe reforços pela renda dos pontos que ainda segura, e cada ponto que
você toma provoca um contra-ataque em poucos segundos. Vence quem tomar os três pontos sem sobrar inimigo
vivo, ou segurá-los por 60 s. Perde quem ficar sem soldados e sem mão de obra para um fuzileiro. Fogo de
supressão em área, granadas e morteiro são as ferramentas para tirar a guarnição da trincheira.

## Salvar e continuar

**Validação integrada de 11/10:** granadas nativas por facção, Owner/Instigator,
reset/contextos e GC em voo passaram num lote único. Friendlyfire ocorreu.
Caminhão sem colisão não recebeu dano; a frota permanece assim, portanto interdição
nativa ainda não está entregue. A cadeia fresca falhou (0 sucata entregue, ~110
perdidas, sem caminhão de recurso), apesar de combate/reabastecimento. Build
experimental; detalhes e próxima prioridade no ROADMAP. Notas offline abaixo são históricas.

**Candidato offline de 11/10:** HP dos caminhões vem do ator do jogo e aparece no
painel. HP0 ou ator inválido interrompe transporte e registra a perda de carga uma
vez; o engine mantém explosão/casco/TTL. Removido DPS abstrato de emboscada e dano
próprio de morteiro contra caminhões. **Fuzis ainda não cortam comboios neste
candidato**: executor local nativo pendente; granada contra veículos também precisa
do gate de colisão. Sem publicação/validação integrada ainda. Save antigo não aplica
HP fictício ao ator; ferimentos nativos não são persistidos por enquanto.

Save **v2**, a cada30s durante ondas automáticas: estado de combate, estoques/produção/coleta, infraestrutura paga/carteira, cadeia inimiga e bases avançadas. Sem endereços de ator; rotas/ações em voo não persistem. Carga manual dos trabalhadores é descartada ao continuar.

Ctrl+F6 valida arquivo/mundo/posições antes de apagar a partida atual. Infraestrutura paga é reconstruída sem novo débito, tudo ou nada. Save inválido recusa preservando estado; seção inimiga inválida descarta somente ela e avisa reinício do estoque de cenário. Restauração incompleta suspende autosave.

Grava temporário com releitura e backup; recuperação tenta save, tmp, bak. Saves antigos são aceitos; a versão anterior do mod não aceita campos novos. Vitória/derrota limpam os arquivos. Save/restore de base avançada e estoques passou em HomeRegionW. Em CallumsCape, infraestrutura paga e carteira foram restauradas após reinício, sem débito novo ou duplicação ao repetir.

## Fogo de supressão em área

Ctrl+botão direito (ou Ctrl+F7) manda os selecionados atirarem por 20 s num círculo de 4,5 m sob o cursor;
os médicos ficam de fora. Quem está fora do alcance anda até ele. Sem visada não há dano: cada tiro suprime
todo inimigo dentro do círculo (a MG montada suprime mais), o que prende quem está atrás de um muro ou numa
trincheira enquanto outro grupo flanqueia. Inimigo que aparece à vista leva tiro normal. Gasta munição;
qualquer ordem nova cancela. Um anel de pontos laranja marca o círculo enquanto a ordem vale.

## Reforços inimigos

Cada ponto que o inimigo segura rende mão de obra para ele (0,6/s). Durante uma onda, a cada 20 s, ele manda
2 ou 3 reforços (até 6 por onda), que surgem atrás do ponto dele mais perto do seu esquadrão. O painel mostra
"reforço inimigo N". Retomar os pontos corta essa renda.

## Animação

Os soldados seguram a arma com as duas mãos e, parados e em combate, levam o fuzil ao ombro e miram no alvo,
com coice a cada tiro. Ao andar, levam a arma em posição de descanso.
Dentro de uma trincheira, ou sob fogo pesado, ficam agachados; ao recuar (Home), correm curvados. O médico
faz a animação de primeiros socorros ao curar, e o fuzileiro a de arremesso ao jogar granada.
Cada classe dispara com o som da própria arma do jogo, e os dois lados soam diferente (fuzil Warden x carabina
Colonial, metralhadoras, fuzis de precisão, pistola).
Soldados seus feridos mostram uma barra de vida sobre a cabeça (verde, amarela abaixo de 60%, vermelha abaixo de
30%), que some quando se recuperam. Inimigos não têm barra: ela revelaria quem o jogo esconde por falta de visão.

O aviso "Falha ao baixar informações do servidor" no menu vem do próprio jogo (a cópia de laboratório não
acessa a rede de propósito) e não pode ser fechado pelo mod; o autostart sai do menu em 2 s.

## Visual com a câmera alta

O jogo foi feito para a câmera baixa de um soldado. Com o RTS ligado o mod desenha objetos pequenos e sombras
mais longe (`r.ViewDistanceScale 3`, `r.Shadow.DistanceScale 2.5`), desliga o sombreamento de linha de visão
do jogo (as faixas escuras que irradiavam do "olho"). O zoom vai até 160 m, para olhar várias frentes: a
distância de desenho cresce com a altura (`r.ViewDistanceScale` = altura / 20 m, no mínimo 3). Desligar o RTS
restaura essas alterações. VSync fica ligado no RTS para evitar o corte horizontal observado ao mover
a câmera; ao desligar o modo, restaura o valor anterior, sem gravar configurações do jogo.

## Logística

**Novo lote integrado; validação ao vivo pendente.** Sistemas próprios offline, sem inventário/RPC do jogo.

- **Alt+L:** implantação explícita nos locais nativos, agora com carteira de **1000 bmat**: refinaria400 + fábrica400 + dois caminhões de suprimento100 cada. Rollback e idempotência preservados. Ruínas não são instalações ativas.
- **Início (Shift+F6):** três trabalhadores sem fuzil coletam sucata a pé; não nasce caminhão de recurso. A refinaria converte2sucata em1bmat; a fábrica começa com40bmat e reserva100para produzir/repor o caminhão de recurso. Perder esse caminhão reativa coleta manual.
- **CallumsCape:** os ensaios antigos ficaram presos no muro/rochas. Com amostragem fina, três trabalhadores entregaram120 sucata sem perdas nem intervenção. Isso aprova esse percurso, não toda a cadeia ou qualquer terreno.
- A coleta recusa a reta quando a busca falha, freia e indica **sem rota**. Tentativas no mesmo trecho não renovam o prazo. Procura chegada acessível dentro da área de serviço.
- Micro-resgate experimental: após quatro segundos imóvel, tenta80/160cm com colisão varrida; teleporte excepcional só para destino com cápsula livre quando a origem já está penetrada. Não dá recursos nem estende a viagem. Passou offline, mas **não resgatou os presos no ensaio real**.
- Rota da coleta amostra o relevo a cada50cm para não pular rochas estreitas durante simplificação. No ensaio CallumsCape, os três entregaram120 sucata sem perdas/resgate. A cadeia inteira ainda não está aprovada: a reconstrução do caminhão de recurso deixou estado ativo sem ator físico.
- Reconstrução transacional: busca vaga segura na fábrica e exige ator íntegro900HP antes de cobrar100bmat/ativar. Falha preserva estoque/estado morto e tenta novamente em5s. Bateria29/29 PASS; sonda no hex criou ator real e confirmou débito único. Transporte pela estrada continua pendente.
- **Trabalhadores:** reposição custa camisa da base; sem camisas não há reposição mágica. Não contam no tamanho das ondas nem no centro do esquadrão de combate.
- **Produção:** munição, camisas, fuzis e bandagens, com receitas próprias baseadas nos dados extraídos. Granadas exigem explosivo e não foram adicionadas como receita gratuita. Shift+L alterna prioridade; estoque/reserva/produção aparecem no painel.
- **Transporte:** dois caminhões abastecem depósitos; L aponta o destino. Carga em retorno só é creditada na chegada, não ao perder destino. Transporte ainda em reta/sem colisão; rede de estradas não integrada. Não considerar cenário regional pronto.
- **Recrutamento:** nasce na base principal ou base avançada abastecida; custa camisa e, no fuzileiro, fuzil. Ponto de controle comum não reforça por padrão. No Assalto permanece mão de obra.
- **Bases avançadas (Shift+J):** num ponto seu elegível, primeiro toque apresenta local/custo; segundo em4s confirma300bmat da fábrica. Até3bases, classeForwardBase1. Posição/terreno/ator exigem validação. Estrutura, estoque e perda afetam reforços; ainda pendente validar spawn/fluxo no engine.
- **Cadeia inimiga:** retaguarda produz, caminhões levam suprimento à frente e ondas consomem estoque; cortar o transporte reduz reforços. Existe piso de tropas de cenário, explícito no painel/configuração; não é bloqueio absoluto por falta de carga.

HomeRegionW é bancada de teste. O destino é uma cadeia curta em CallumsCapeHex; carregar mapa/terreno/instalações não prova equilíbrio, estrada transitável ou visibilidade pela câmera. Facilities não implementadas.

## Várias frentes

- **Seleção em qualquer zoom:** somente soldados aliados selecionados recebem contorno amarelo brilhante,
  acompanhando posição e animação. Partes encobertas recebem preenchimento amarelo do pós-processo nativo.
  Desmarcar, morrer ou sair do RTS remove ambos. Sem círculo no pé nem bolinhas de unidades/caminhões.
  Inclui casaco, cabeça, capacete, mãos, pernas, mochila e arma. Compartilha a pose com quatro cópias por peça
  visível (28 atores no soldado atual). **Experimental:** aparência aprovada pelo usuário, mas houve quedas
  nativas UE4SS após ampliar às peças; estabilidade/GC/reseleção/morte e seleção grande ainda pendentes.
  A retomada acrescentou proteções para pawn/clone/câmera em destruição e fonte inválida, incluindo a
  limpeza de CustomDepth. Regressão offline passou; isso não identifica nem certifica a correção das quedas nativas.
  Otimização integrada: uma transformação nativa completa por cópia substitui três setters; conversão de rotação
  uma vez por peça. Equivalência geométrica verificada offline e por oráculo ao vivo. Em carga limpa, seis
  selecionados mantiveram 168 cópias com stratTick inicialmente 7,91 ms/quadro (antes 16,72 ms);
  após GC/reseleção uma nova janela mediu 16,40 ms. Ganho sustentado ainda não demonstrado.
  GC e reseleção passaram funcionalmente; não é certificação prolongada nem benchmark de FPS/renderização.
  A carga seguinte caiu no UE4SS com erro de Registry; guards/otimizações não resolveram a estabilidade.
  Registro do hook de animação agora permite tentar novamente após falha inicial; correção Lua independente,
  sem evidência de que explique a queda nativa.
  Retomada de 10/10: repetição limpa com seis selecionados/168 cópias passou 195 s;
  controle sem seleção passou 201 s. A causa antiga não foi reproduzida nem isolada;
  isso não libera o lote logístico candidato. Contorno mediu ~11–12 ms/quadro em stratTick,
  contra ~0,5 ms sem seleção. Evidências em `dados/paralel/estabilidade/RETOMADA_20261010.md`.
  Outra carga limpa completou 620 s com seis selecionados/168 cópias, seguida de GC/morte/recriação
  e mais 186 s sem queda observada. Entrada real e causa antiga continuam pendentes;
  gate manual de dez minutos em `TESTE_MANUAL.md`.
  **Gate manual reprovado em 10/10:** fatal error durante teste dos números, após log de grupo1.
  A build continua experimental; os ensaios automáticos não cobriram essa falha com interação real.
  Variante de diagnóstico: as teclas agora entram numa fila Lua drenada pelo loop persistente
  antes do gate de autoridade (F9/F10 continuam disponíveis no menu). Evita criar um callback
  ExecuteInGameThread por pressão; FIFO/erros/reentrância passaram offline. Não é correção
  certificada do crash: entrada rápida real e sincronização do UE4SS ainda precisam validação.
  Também passaram 100 ciclos de des/reseleção e 20 mortes/recriações; GC deixou 168 cópias
  rastreadas e zero atores em destruição. O cache de componentes da unidade viva desmarcada
  permanece intencionalmente para limpar o CustomDepth que o jogo reativa; na morte é removido.
  Ver `dados/rastro_selecao.txt`. Se pesar, o próximo caminho é shader de borda, não voltar aos discos.
- **Alertas de frente:** ponto seu sob ataque, ponto perdido, onda chegando e baixa entram numa fila (até 8) com o
  lugar; o painel mostra "! N alertas (Espaço)". Espaço leva a câmera ao mais novo; apertado de novo, aos
  anteriores. O mesmo alerta no mesmo lugar não se repete por 20 s.
- **Grupos por frente:** Alt+1–5 põe os selecionados num grupo; 1–5 seleciona; dois toques vão até ele; 0 = todos.
- **Pontos:** Q/E passam a câmera de ponto em ponto, com o dono no aviso.

## Visão

O jogo só desenha inimigos que o pawn do comandante enxerga (relevo e prédios bloqueiam). No modo RTS o
comandante vira um "olho" invisível que acompanha o foco da câmera no chão, inclusive durante pausa.
Antes ficava no soldado mais próximo e escondia caminhões longe do grupo; o foco em caminhão foi validado
no hex. Isso ainda não certifica visibilidade em toda a tela/zoom/relevo. A base (depósito de munição, F2)
fica onde o comandante estava ao ligar o RTS.

## Limitações e verificação

- Totalmente offline, com modelo de combate próprio (dano, efeitos e malhas do jogo).
  Não usa inventário nem RPCs de servidor do Foxhole.
- Ordens de marcha e o avanço inimigo usam rota própria (A* em grade, sem NavMesh), calculada em
  fatias por frame quando a linha reta está bloqueada.
- Testado em HomeRegionW (padrão) e HomeRegionC. Para trocar, ponha o caminho do mapa na 1ª linha de
  `FoxholeRTS/map.txt` (ex.: `/Game/Maps/HomeRegionC`). Das hexes grandes de `Maps/Master`, `DeadLandsHex` foi testada; nela o painel "Introdução ao Foxhole"
  aparece por cima e precisa ser fechado com o mouse (seta).
- Cada mecânica até a v0.8 foi validada no jogo pelo canal de comandos e por capturas de tela, e partidas
  inteiras foram jogadas por um "jogador-robô" scriptado. Teclas e mouse ainda **não foram testados com
  entrada real**: o roteiro está em `TESTE_MANUAL.md`.
- Desempenho medido: o mod gasta ~1,5–4 ms por quadro com ~25 soldados; o resto do custo é dos
  personagens do próprio jogo (com 12 soldados, ~60 ms por quadro na máquina de teste, janela sem foco).
- A escolha automática do lugar dos pontos foi ajustada em HomeRegionW; em outros mapas,
  use J para pôr os pontos onde quiser.
- Não use hot reload repetido do UE4SS: já houve travamento. Reinicie a cópia.
- Para desativar, com o jogo fechado retire `enabled.txt` da pasta do mod.
  Isso não remove o loader nem torna a cópia apropriada para jogar online.
# Estado do MVP (11/10)

DPS abstrato de caminhões removido: HP vem do ator real. Fuzil local em veículo
continua pendente; granadas não atingem a frota com colisão desligada.
Rastreamento offline distingue consultas de tiro/HitNotify de aplicação de impacto;
callbacks de apresentação e armas de veículos não comprovam executor do rifle.

Ajuste publicado experimental: evacuação automática de coletor ferido conserva a sucata nas
mãos e retoma a rota após cura. Não coleta nem entrega durante o recuo; morte e
ordens explícitas ainda perdem carga. Testes offline PASS, validação interrompida por crash.
Reposição automática aguarda a saída da base ficar sem inimigo a35m,
sem gastar camisa nem criar trabalhador durante a recusa. O aviso pede proteger
a base; combatentes continuam recrutáveis. Ainda sem aprovação Unreal.

Prioridade: provar a cadeia jogável na região pequena; acabamento de chegada/espera dos
trabalhadores foi adiado. Coleta entrega por proximidade (15 m), não pela porta da refinaria.
Caminhões ainda usam movimento reto sem colisão e podem atravessar/subir estruturas.
Grafo regional extraído, ainda sem validação física ou integração. Sonda viva
confirmou movimento RWD e raiz/updated VehicleCollision(Box); não é driver integrado.
O lote recente caiu (PID4696/158s); último autosave60s sem crescimento de bmat.
Relatório final perdido, causa completa pendente; não considerar build estável.
Diagnóstico offline ligou o crash à lista nativa de UniqueId dos participantes.
IDs vazios de bots são hipótese, não causa completa comprovada; desligar voz não
protege todo o fluxo. Correção de controlador/NPC ainda em investigação.
Correção candidata de save: observa morte nativa do comboio antes de converter
carga viva em pendente e registra a recompensa na mesma carteira salva. Testes
offline passaram; ainda não publicada/validada no laboratório. Ferimentos de
veículos continuam sem persistência, não considerar esta correção um save completo deles.
HP nativo desconhecido também recusa o save inteiro e preserva o arquivo anterior,
sem inventar morte/perda. Candidato offline. A carga manual em mãos dos coletores
ainda não é persistida; continuar durante a coleta pode perdê-la.
Oracle offline das funções nativas reproduziu esse fluxo com voz false e mesmo
sem PlayerSaveGame; fixtures não comprovam causa completa nem correção no jogo.
Sonda de contrato NPC/roster preparada para o próximo lote, sem ler IDs Steam
ou alterar atores; teste offline não comprova estabilidade no jogo.
Criar HeadlessLocalPlayer sozinho também não é correção comprovada: o init
nativo é separado e seu vínculo ao PlayerState local permanece pendente.
Navegação usa raio real50 cm do soldado; casos antigos de medevac preso não estão resolvidos.

