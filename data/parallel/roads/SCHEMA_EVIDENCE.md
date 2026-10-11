# Evidência recebida (HomeRegionW, 2026-10-09)

Saídas do dono do laboratório: `D:/tools/foxhole-lab/roads-schema-live.txt` e
`D:/tools/foxhole-lab/roads-types-live.txt`. Não executadas por este agente.

- Connections -> LandscapeSplineSegmentConnection: ControlPoint ObjectProperty,
  TangentLen FloatProperty, SocketName NameProperty. **Cardinalidade não exportada.**
- SplineInfo -> InterpCurveVector: Points ArrayProperty, bIsLooped BoolProperty,
  LoopKeyOffset FloatProperty. Tipo de cada ponto ainda desconhecido.
- ControlPoint.Location -> Vector(X,Y,Z floats); Rotation -> Rotator(Pitch,Yaw,Roll).
- Três control points observados: Width1000, LocalMeshComponent ausente. Não prova
  ausência de meshes dos segmentos ou estradas, nem tamanho útil transitável.

Sonda preparada `D:/tools/foxhole-lab/t_roads_inner.lua`, sintaxe OK, não executada.
Encontra tipos internos somente de arrays explicitamente confirmados e schemas
imediatos dos elementos struct, sem ler valores ou fazer dump recursivo.
GetInner confirmado na [documentação oficial UE4SS](https://docs.ue4ss.com/lua-api/classes/arrayproperty.html).
Compatibilidade da versão instalada deve ser verificada pelo dono do laboratório.

**Gate cardinalidade Connections:** a [API Lua Property oficial](https://docs.ue4ss.com/dev/lua-api/classes/property.html)
consultada não expõe GetArrayDim. Não o chamar por inferência de API C++/UE.
Consultar SDK/header gerado ou dumper de metadata que imprima ArrayDim antes de
indexar endpoints. O schema permite estudar Connections.ControlPoint do elemento
representado, mas um endpoint único não define uma aresta; a sonda deliberadamente
não infere segundo endpoint, offsets nem leitura raw memory.

**Gate geometria:** tipos internos de Points e InterpCurveVector.Points precisam
ser confirmados; então exportar até três pontos de um segmento. Local->world e
classificação estrada/mesh continuam requisitos antes de criar grafo transitável.

## INNER vivo recebido: rota alternativa para endpoints
`D:/tools/foxhole-lab/roads-inner-live.txt` confirmou ConnectedSegments como array
de LandscapeSplineConnection, com Segment ObjectProperty e End BoolProperty.
Portanto incidência **CP->segment** pode identificar endpoints sem ler Connections
de cardinalidade desconhecida. End true/false é rótulo observado, não orientação
assumida. Para grafo completo será preciso inventário completo de CP e exigir dois
CP distintos por segmento; segmento parcial/ambíguo não autoriza uma aresta.

Points é array de LandscapeSplineInterpPoint com Center StructProperty. Sonda
`D:/tools/foxhole-lab/t_roads_incidence.lua` preparada, sintaxe OK, não executada:
até três CP (Location Vector já comprovado), oito incidências por CP, três segmentos,
três pontos e nomes de três meshes por segmento. Center só é lido depois de metadata
comprovar exatamente CoreUObject.Vector e X/Y/Z FloatProperty. Output POINT_LOCAL
deliberadamente não é world. Sem inferência de estrada ou ligação por proximidade.
