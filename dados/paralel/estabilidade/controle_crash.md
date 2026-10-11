# Controle repetido de estabilidade — proposta, não executada

Objetivo: distinguir seleção/clones de callbacks/anim comuns. Nenhuma entrada agente; pedir ao usuário
que não opere jogo/console durante cada janela. Não automatizar essa restrição nem usar teclado/mouse.
Laboratório exclusivo, botloop desligado, Steam/DRM/firewall preservados.

## Preparação comum

- Preservar fonte/hash atual e UE4SS binário/hash, mapHomeRegionW, PID/log/crashbaseline.
- Publicar só pelo restart.sh; esperar RTS/logvivo, não timeout isolado. Não usar hotpatch ou Ctrl+R.
- Mesmo mapa/câmera/home, sem inimigos/ondas/logística;6soldados vivos parados.
- Queue experimental NÃO integrado (ponte original permanece), anim.hooked correção atual documentada.
- Confirmar todos6m.sel estado, hp/retired, quantidade clones/fontes e anim.units. Somente propriedades
  já verificadas; não ler MasterPoseComponent/AnimClass.
- Alteração de sel via comando direto do mod, nenhum keybind fake nem callback temporário.
- Iniciar janela só depois5s de assentamento e reset perfil; guardar timestamp gameRealTime e monotonic
  externo, evitar confundir tempo desdegrupo com duração perfil.

## Sequência por carga limpa,4execuções independentes

| Execução | Estado | Janela | Requisitos |
|---|---|---|---|
| A1 |6não selecionados;anim ativo;0clones |180s | mínimo excede crash111s;logantes/depois |
| B1 |6selecionados;anim ativo;168clones |180s | mesmas6classes/câmera/estado |
| B2 |nova carga6selecionados |180s | repetir ordem invertida |
| A2 |nova carga6não selecionados |180s | repetir controle |

Nunca transformar A→B no mesmo processo para comparar baseline: criação/destruição prévia confunde.
Dentro janela nenhum comando de GC/reseleção/morte nem captura/sonda callback; três checkpoints por
canal direto em60/120/180s para perfil/contagem, aplicados igualmente aA/B. Cada profile reset
identifica fase/timestamp. Captura final só depois janela. Não reiniciar por uma observação timeout:
confirmar terminal/crash/processo; gameNotResponding carregando não é prova de travamento.

## Coleta em checkpoint/fim

PID,status processo/log timestamp,framecount,perfilstratTick/total,selected/tracked e total atores vivos/
destruindo/não rastreados. Registry erros:timestamp e contexto50linhas antes/depois; preservars stack
XML completo se crash. Roda/seleção logs informados como eventos observados, não causa atribuída.
Se processo cair antes111s, guardar fim real; não chamar janela concluída. Se sobreviver180s,
resultado é PASS dessa janela, não build estável.

## Decisões

- FalhaA com0clones: contorno não é necessário para reprodução dessa falha; investigar callbacks/anim comum.
- FalhaB e2A sobreviveram: seleção/clones estão associados, ainda não causa; próxima variante isola fonte/peça.
- FalhaA/B: ponte comum merece símbolos/trace; não misturar queue toggle ao controle atual.
- Nenhuma falha: ampliar repetição/duração e transiçõesGC/morte em lote posterior; causa continua não isolada.
- Comparar queuefalse/true só depois,duas cargas equivalentes com usuário realizando entrada real autorizada
  e roteiro idêntico; agente não injeta. Toggle deve ser único fator. Compatibilidadeinput gate do usuário.

Ao encerrar teste/robot ou voltar offline: fechar somente PID verificado da cópiaLab;preservarSteam.
