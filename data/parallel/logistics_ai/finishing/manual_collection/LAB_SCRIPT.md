# Roteiro do laboratório — COLETA MANUAL (candidato v3)

Só rodar quando o usuário autorizar a sessão no laboratório. Nenhum passo foi executado pelo agente. Entrada real é do usuário.
Pré-requisito: publicar `candidate_v3/main.lua` (SHA256 em `candidate_v3/SHA256.txt`) como `main.lua` do mod só depois da integração dos outros candidatos.

1. **Partida nova** (Alt+L, depois nova partida): conferir custo 1000, 2 caminhões de suprimento, nenhum caminhão de recurso no mapa, bmat 40 no painel.
2. **Nascimento** (~5 s): 3 soldados **sem arma** perto da base; sem T-pose; camisas da base 30 → 27; nada de crash (`UE4SS.log`, `Saved\Crashes`).
3. **Caminhada**: eles chegam ao campo de sucata, ficam parados coletando, voltam e entregam na refinaria; tempo da 1ª entrega e do 1º caminhão (comparar com 165 s a 80 m / 359 s a 470 m no harness). Anotar distância real campo–refinaria e se algum fica preso.
4. **Caminhão**: ao chegar a 100 bmat a fábrica constrói o de recurso; ele aparece no campo, em pé no chão, sem estar preso; a mensagem "coleta manual encerrada" sai; o painel perde a linha da coleta.
5. **Ordem do jogador**: selecionar e mandar um trabalhador a outro lugar; ele sai da coleta; 60 s depois volta sozinho.
6. **Perda do caminhão**: destruir o de recurso com bmat/sucata zerados (canal de comandos); a coleta reativa e o caminhão volta.
7. **Combate**: levar um inimigo perto do campo; trabalhadores pausam; morrer repõe por 1 camisa.
8. **Salvar/continuar** com trabalhadores em campo: carga em mãos descartada (log), 3 trabalhadores, coleta recomeça.
9. Custo por quadro: comparar tempo de quadro com e sem coleta ativa.

Voltar o jogo a fechado ao terminar (apenas o PID da cópia em `D:\FoxholeLab\Foxhole`).
