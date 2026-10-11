# Roteiro de teste manual (teclado e mouse reais) — FoxholeRTS v0.9

## Visual — atualização de 10/10
- [x] Linha horizontal/tremeluzir durante movimento: usuário informou que sumiu após VSync temporário.
- [ ] Build publicada: repetir movimento vertical/horizontal com zoom baixo/alto; verificar ausência da linha.
- [ ] Olho acompanha foco: visitar caminhão longe do esquadrão, também durante pausa, e conferir malha.
- [ ] Visibilidade nas bordas da tela, neve e instalações em vários ângulos (não aprovada globalmente).
- Soldados presos continuam pendentes; um percurso de coleta aprovado não certifica navegação geral.

## Lote logístico v4.1 — pendente no jogo

O usuário adiou crashes e amarelo residual. Não repetir agora o ensaio rápido de 1/2.
A lista antiga abaixo contém valores históricos; para a logística nova, conferir:

- Shift+F6: além do esquadrão inicial, três trabalhadores desarmados surgem nos primeiros ticks de coleta.
- Ctrl+1–4: recrutamento logístico consome camisa e fuzil na base elegível; ponto comum não é spawn.
- Alt+L: implantação de 1000 bmat, refinaria, fábrica e dois caminhões de suprimento.
  Caminhão de recurso é produzido depois; transporte ainda em reta.
- Shift+J: base avançada em ponto próprio elegível, 300 bmat; confirmar em até 4 s, máximo três bases.
  J sem Shift continua criando ponto de controle.
- Shift+L: produção/entrega de munição, camisas, fuzis e bandagens.
- Ctrl+F6: continuação do save v2, incluindo carteira e infraestrutura.

Ainda sem aprovação de teclado real, aparência ou equilíbrio deste lote.

As rotinas foram verificadas pelo canal de comandos; integração de teclado/mouse e aparência em todos os
ângulos/zooms ainda precisam desta confirmação manual. Marque o que funcionou
e anote o que não funcionou. Para mandar o resultado, basta colar esta lista com as marcações.

Preparação: abra a cópia de laboratório (Steam aberto). O mod entra no mapa e liga o modo RTS sozinho;
a ajuda de teclas aparece no canto inferior esquerdo por 40 s.
Os testes da cadeia abaixo usam HomeRegionW. Num hex sem instalações ativas/caminhões suficientes,
Shift+F6/Alt+F6 recusam a partida com diagnóstico; isso não significa que os prédios não existam como ruínas
ou não estejam apenas ocultos na imagem. O inventário vem dos atores carregados.

| # | Faça | Esperado | OK? |
|---|---|---|---|
| 1 | F5 | A ajuda some; F5 de novo, ela volta | |
| 1b | Shift+F5 (três vezes) | Painel alterna "RTS (difícil)", "(fácil)", "(normal)"; a ajuda **não** some | |
| 2 | Shift+F6 | Alerta "NOVA PARTIDA"; 6 soldados selecionados com contorno amarelo; três anéis pontilhados (pontos A, B, C) | |
| 3 | Clique esquerdo num soldado | Só ele recebe contorno brilhante amarelo e preenchimento das partes encobertas; o comandante **não** ataca | |
| 3b | Mover o selecionado, girar a visão; desmarcar clicando no chão; selecionar outro; F10 duas vezes | Contorno acompanha corpo inteiro, arma, capacete, mãos e animação, sem vulto parado nem disco; preenchimento também desaparece ao desmarcar e fora do RTS. Armas/mãos de NÃO selecionados não ficam amarelas. Aparência aprovada nesta sessão; estabilidade prolongada ainda pendente | |
| 4 | Arrastar com o botão esquerdo sobre o grupo | Caixa seleciona os soldados dentro; Shift+arrastar soma | |
| 5 | 1, 2, 3, 0 | Seleciona grupo 1, 2, 3 (vazio), todos | |
| 6 | Botão direito no chão | Selecionados marcham em formação até lá (desviam de caminhões e prédios) | |
| 6b | Shift+botão direito em dois ou três lugares | Selecionados percorrem os pontos em sequência | |
| 7 | Botão direito dentro de um anel | Ao chegar, painel mostra o ponto subindo em %, depois "A+" e estandarte azul | |
| 8 | Ctrl+1 / Ctrl+2 / Ctrl+3 / Ctrl+4 | Recruta fuzileiro / metralhador / atirador / médico (desconta mão de obra) | |
| 9 | Ctrl+1 com o cursor dentro de um ponto seu | O recruta nasce no ponto (alerta "no ponto A") | |
| 10 | K com o cursor no chão | Barreira de concreto aparece (−15) | |
| 11 | J com o cursor no chão livre | Novo ponto de controle (anel) | |
| 12 | Esperar a onda; Ctrl+5 sobre os inimigos | Som de artilharia, anel de aviso, 3 explosões após ~2,5 s | |
| 12b | Ctrl+6 com o cursor ao lado do esquadrão | Caixa de munição aparece (−25); painel "caixas 1"; some após 60 s | |
| 12c | Ctrl+7 no chão; depois botão direito dentro do buraco com 6 selecionados | Buraco de raposa aparece (−20); 4 entram nele, 2 ficam em linha atrás | |
| 12d | Ctrl+botão direito num ponto vazio à frente | Alerta "fogo de supressão"; selecionados (menos médico) miram e atiram lá; terra levanta no ponto | |
| 12e | Jogar 30 s com ondas automáticas, fechar o jogo, reabrir e apertar Ctrl+F6 | Alerta "há uma partida salva" ao ligar o RTS; Ctrl+F6 traz soldados, pontos e construções de volta | |
| 12f | Ctrl+8 ao lado do esquadrão; levar um ferido até a barraca | Barraca de lona aparece (−30); o ferido recupera vida | |
| 12g | Ctrl+9 no caminho; mandar um soldado atravessar | Cavalete de arame aparece (−10); o soldado fica lento ao passar | |
| 12h | Alt+F6 | Alerta "ASSALTO"; três pontos verdes com trincheira, arame e guarnição; painel "ASSALTO: pontos inimigos 3/3" | |
| 12i | Ctrl+0 (e de novo) | Oficial recrutado (−40) com estandarte azul sobre a cabeça; o 2º é recusado | |
| 12j | Deixar o esquadrão levar tiros | Barra de vida sobre os feridos (verde → amarela → vermelha); some ao curar | |
| 12w | Observar um aliado e um inimigo morrerem enquanto se movem | Param e caem no chão; não correm no lugar; o corpo é removido após 20 s | |
| 12x | No laboratório configurado para CallumsCapeHex, tentar Shift+F6 e Alt+F6 | Alerta de instalações/caminhões ativos faltantes; não apaga soldados existentes nem inicia uma cadeia fictícia | |
| 12y | Em CallumsCapeHex, antes da partida, Alt+L; repetir; depois Shift+F6 | Alerta de implantação: −1100 bmat do cenário, saldo 0; repetição não duplica; partida pode iniciar com refinaria/fábrica e três caminhões reais. Transporte ainda é protótipo em reta | |
| 12k | Ouvir um tiroteio | Fuzil, metralhadora, atirador e pistola com sons diferentes; inimigo soa diferente do seu lado | |
| 12m | Pause; mover a câmera, selecionar e dar uma ordem; Pause de novo | Painel "PAUSADO"; tudo parado, mas câmera e ordens respondem; ao continuar, a ordem é cumprida | |
| 12n | Insert três vezes | Painel "2x", "3x" e volta ao normal | |
| 12o | Selecionar alguns, Alt+4; depois 4, e 4 duas vezes rápido | "N soldados no grupo 4"; 4 seleciona só eles; dois toques levam a câmera até eles | |
| 12p | Com uma onda chegando ("Espaço: ver" no alerta), apertar Espaço, e de novo | Câmera vai à onda; depois ao alerta anterior; o "! N alertas" some do painel | |
| 12q | Q e E com 3 pontos | Câmera passa de ponto em ponto com "ponto A (nosso) [1/3]" | |
| 12s | Nova partida (Shift+F6), Ctrl+L algumas vezes | Câmera vai à fábrica, refinaria, campo e caminhões; caminhão de recurso anda sozinho | |
| 12t | L com o cursor num ponto seu; olhar a 2ª linha do painel | "próximo caminhão vai para o ponto X"; depois "caminhão entregou em ponto X" e o estoque do ponto sobe | |
| 12u | Shift+L | "fábrica: munição", "camisas", "automático" | |
| 12v | Nova partida; no alerta "COMBOIO INIMIGO", Espaço e mandar soldados para o meio da rota | Soldados atiram no caminhão; "COMBOIO INIMIGO DESTRUÍDO (+25)"; na onda seguinte "faltou suprimento ao inimigo" | |
| 12r | Selecionar 6–12 soldados; roda do mouse até o máximo (160 m); mover o grupo | Contorno só nos selecionados, sem bolinhas; avaliar legibilidade/desempenho e acompanhar movimento. Verificar LOS sem concluir ausência de estruturas pela imagem | |
| 12l | Deixar um soldado cair abaixo de 30% com um posto de socorro (Ctrl+8) por perto | Alerta "ferido recua sozinho"; ele vai à barraca e volta a lutar curado | |
| 13 | Botão direito sobre um inimigo | Selecionados focam nele | |
| 14 | Home com feridos selecionados | Correm ao ponto seu mais próximo sem atirar; lá recuperam vida | |
| 15 | End | Selecionados param e seguram posição | |
| 16 | Setas, PageUp/PageDown, F2, F3 | Câmera anda, zoom, centraliza, pan pela borda liga/desliga | |
| 16b | Ouvir ao erguer barreira (K) e ao vencer/perder | Som de construção; som de vitória/derrota do jogo | |
| 17 | F11 | Remove soldados, inimigos, barreiras e pontos | |

Se algo travar ou o painel parar de atualizar, o log fica em
`D:\FoxholeLab\Foxhole\War\Binaries\Win64\ue4ss\UE4SS.log` (linhas com `[FoxholeRTS]`).

## Gate de estabilidade com entrada real — pendente (10/10/2026)

**Reprovado em 10/10:** fatal error no teste dos números; último log selecionou grupo1.
Não repetir o roteiro completo até investigação. No próximo ensaio combinado, faremos
um passo de cada vez: `1` seleciona grupo1, `2` grupo2, `0` todos; não é necessário
jogar partida, recrutar ou vencer ondas. Avisar imediatamente se cair.
Variante de fila preparada após reproduzir Registry: no próximo teste combinado, primeiro
um toque1, depois2; só após confirmar ambos, alternar1/2 parado. Movimento e duplo toque
ficam para etapas separadas. Não operar o jogo durante o controle automático do agente.

Separado da matriz de teclas: o agente passou mais de dez minutos com seis selecionados
parados, sem entrada real. Isso não valida os callbacks das teclas nem roda/clique/zoom.
Combine uma sessão com o agente antes de iniciar; o laboratório fica fechado quando ocioso.

1. Começar numa carga limpa em HomeRegionW, com seis soldados e ondas desligadas pelo canal.
2. Durante dez minutos, alternar clique/arrasto/Shift+arrasto, grupos 1/2/0, movimento no chão,
   parada (H), setas, roda e PageUp/PageDown. Variar zoom e posição do grupo na tela.
3. Desmarcar/reselecionar e alternar F10 duas vezes; verificar todas as peças do contorno,
   sem vultos no comandante nem brilho nos não selecionados. Não usar Ctrl+R.
4. Informar aqui se houve travamento, queda, contorno desalinhado ou comandos perdidos e
   aproximadamente em que momento. O agente preserva log/PID/hash antes de reiniciar.

Sobreviver a esse roteiro é evidência de integração, não prova da causa do crash antigo.
Ainda faltam repetição prolongada, grupos maiores e desempenho aceitável.
