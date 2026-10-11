# ESTRADAS — entrega offline (2026-10-09)

## Evidência atual
- `data/trace_regions.txt`: CallumsCapeHex carregou 431 LandscapeSplineSegment e 405
  LandscapeSplineControlPoint; Deadlands 634/596. Não foram exportadas conexões nem curvas.
- `tools/inspect_region.lua` enumera nomes/contagens, mas não propriedades de spline.
- `main.lua:2485`: logi.place usa SetActorLocation sem sweep e teleport=true, chão por groundZ.
- `main.lua:2760`: logi.drive anda em reta. `:2831` devolve instantaneamente a carga à fábrica
  quando o destino muda de dono, mesmo longe dela. Ambos contradizem transporte verificável.
- `kneeClear`/planStart já aceitam nav estrita e orçamento incremental. A altura e esfera de
  soldado NÃO são folga comprovada de TruckW. A opção estrita ainda consulta groundZ: água,
  tabuleiro de ponte e telhado precisam de classificação explícita.

## Código entregue e teste
`roads.lua` é módulo Lua puro, sem novos locais no main.lua. Dijkstra sobre conexões
explicitamente validadas, sem conectar vizinhos por distância, sem reta de fallback.
`advance` propõe um passo limitado; `commit` só progride após confirmação do adaptador.
Não movimenta atores nem debita/entrega recursos. Rotas carregam epoch para evitar cache do lobby.
O grafo sintético testa desconexão, epoch, aresta desconhecida/bloqueada, sweep recusado,
veículo destruído, confirmação e chegada. Teste passado via lupa; não comprova física Unreal.

## Integração proposta (ainda NÃO aplicada)
1. No laboratório, exportar reflection/schema das classes spline conhecidas antes de ler campos.
   Em UE padrão existem Connections/ControlPoint, Points e Location, mas esses nomes/formas
   são HIPÓTESES nesta build, não acesso autorizado por evidência local. Identificar também
   transformação local->world do LandscapeSplinesComponent. Não tratar spline decorativa como estrada.
2. Exportar somente IDs estáveis por snapshot, conexões explícitas, largura e amostras da curva
   para um grafo da região. A curva precisa de nós intermediários: ligar só os extremos corta curvas.
   Ponte exige conexão + suporte do tabuleiro confirmado; nunca ligar margens pela proximidade.
3. Validar trechos por amostras de superfície e envelope orientado do caminhão (bounds físicos,
   não bounds totais de volumes). Reaproveitar traces Camera medidos e planStart/planStep em
   fatias para o acesso curto estacionamento->rede. Não fazer A* síncrono de quilômetros no tick.
4. Instalações recebem parada exterior validada e acesso até estrada, não o centro do prédio.
   Origem e destino no roads.plan são IDs destas paradas, ambos conectados só após prova de acesso.
5. `logi.drive`: obter rota; rota ausente mantém parado com motivo. `advance` -> sweep/posição
   confirmada -> atualizar tr -> commit. Chegada apenas ao terminar rota na parada validada.
   Não chamar logi.place em cada passo: ele teleporta sem sweep e substitui Z da ponte por groundZ.
6. Destino perdido muda para retorno físico à fábrica mantendo tr.cargo. Devolver estoque somente
   na chegada confirmada. Rota ausente mantém carga no caminhão; morte perde carga uma vez.
   Caminhão nativo inválido/bActorIsBeingDestroyed entra em perda explícita, nunca entrega fantasma.
7. Troca de mundo invalida epoch, trabalhos e referências. Mesma região recarregada também muda
   epoch. Reconstrução de caminhão precisa spawn validado/parking, não reexibir pawn morto.
8. Exportar módulo para env somente se sondas precisarem; reset limpa rotas. Alertas de rota
   bloqueada/ausente devem ser legíveis sem emitir todo quadro.

## Matriz solicitada ao dono do laboratório
- Curva real campo->refinaria->fábrica; registrar caminho, velocidades e posições a 100ms.
- Prédio/barreira/veículo entre paradas: nenhum salto ou entrega apesar de rota bloqueada.
- Água sem ponte: recusa; ponte existente: Z acompanha tabuleiro e folga integral validada.
- Destino capturado: retorno físico, conservação de carga; destruído: perda única.
- Troca/regarga de região: grafo antigo recusado; câmera/LOS não usadas como prova de estrada.
- 3 caminhões, obstrução dinâmica e replano com orçamento: medir ms/tick e travamentos.

Task permanece em andamento; descoberta nativa e validação ao vivo são dependências reais.

## Sonda de metadados preparada, NÃO executada
`D:/tools/foxhole-lab/t_roads_schema.lua`: somente nomes/tipos de propriedades,
nomes de funções e herança de três classes já inventariadas. Sintaxe validada por lupa.
APIs ForEachProperty/GetSuperStruct demonstradas nas sondas anteriores externas
`t_rebuild_schema.lua`/`rebuild-schema.txt`; ForEachFunction usada em `t_outline_schema.lua`.
Não há exemplo destas APIs em `tools/` do repositório; a evidência é a sonda e saída
do laboratório, não uma suposta API nova. Não acessa Connections/Points/Location,
GetInner, conteúdos de arrays, structs de instância nem transformações especulativas.

Gate exato: o dono do laboratório precisa executar essa sonda e conservar a saída.
Se propriedades de conexões/pontos forem ArrayProperty, ainda falta metadata do tipo
interno comprovada para definir uma exportação específica; não fazer dump recursivo
genérico de dados. Campos podem não ser refletidos nesta build. Nesse caso obter schema
pela reflexão/SDK já existente antes de acessar valores. Mesmo a saída de schema não
autoriza presumir a semântica de estrada, orientação/local->world ou ponte.

O módulo isolado é preparação/teste de contrato, NÃO feature integrada de transporte.

## Avanço de evidência: schema vivo recebido do coordenador
`D:/tools/foxhole-lab/roads-schema-live.txt` confirmou em HomeRegionW 122 segmentos,
127 control points. Segment.Connections é **StructProperty**, não ArrayProperty;
SplineInfo/Bounds também structs; Points/LocalMeshComponents arrays. ControlPoint
Location/Rotation structs, Width FloatProperty, ConnectedSegments/Points arrays,
LocalMeshComponent ObjectProperty. Não reutilizar estas contagens/posições no hex.

Próxima sonda `D:/tools/foxhole-lab/t_roads_types.lua`, sintaxe OK, não executada:
até três exemplos de segmento/control point; metadata de structs explicitamente
confirmados (GetStruct já usado em reconstrução), largura e nome do mesh local.
Um mesh tem somente schema enumerado, sem ler asset/conteúdo desconhecido.
Connections não deve ser acessado como array por inferência UE padrão. Gate permanece
cardinalidade de Connections e tipos internos de Points/ConnectedSegments; classificação
da rede e transformação local->world ainda não provadas. Preferir validar um trecho
curvo real antes de exportar o mapa todo.
