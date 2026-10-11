# Snapshot observacional do lobby, não região jogável

Exportação recebida do coordenador: 127 CP, 122 segmentos, 468 nós com curvas.
95 segmentos têm somente assets em Environment/Roads; 27 não são classificados
como estrada. EditorLandscapeResources/SplineEditorMesh explicitamente excluído.
Incidência completa com dois CP distintos e End diferentes, curva compatível com
endpoints dentro de 1cm: nenhum segmento rejeitado por ambiguidade nesta exportação.

Grafo nativo possui componentes de 259/114/45/22/17/10/1 nós; filtrado por estrada
restam duas componentes conectadas de 259/114 e 95 nós isolados. Não há ligação
inventada entre componentes: atravessar a lacuna exige acesso/ponte real validado.
Todas as arestas têm validated=false; não-estrada também blocked=true.

`home-region-snapshot.json` preserva coordenadas/IDs/nome de asset, sem arquivos do
jogo nem conteúdo de mesh. Epoch combina mundo e hash da exportação; adaptador vivo
ainda deve adicionar identidade de sessão para rejeitar recarga igual da região.
Não utilizar esse snapshot como cache para CallumsCapeHex.

## Acessos possíveis, não autorizados
Qualquer CP ou ponto intermediário de uma das duas componentes de estrada é
candidato topológico. Ainda não há exportação das paradas de campo/refinaria/fábrica
neste snapshot; portanto não se pode afirmar conexão entre instalações e estrada.
Precisa obter parking exterior real, plano estrito de acesso e confirmar envelope,
superfície, água/tabuleiro de ponte e obstrução dinâmica. Asset road não comprova isso.

`python data/parallel/roads/build_snapshot.py` reproduz conversão da saída externa;
`python data/parallel/roads/test_snapshot.py` passou contra snapshot real.
Transporte permanece não integrado/não validado fisicamente.
