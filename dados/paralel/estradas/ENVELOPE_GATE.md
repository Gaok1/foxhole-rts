# Envelope TruckW: sonda preparada, não executada

`D:/tools/foxhole-lab/t_truck_collision_schema.lua` escolhe primeiro caminhão vivo
via logi.scan e enumera PrimitiveComponent usando API já utilizada no mod. Somente
nomes/classes/metadata de getters de colisão, extents e transformação. Sem bounds
totais do ator, MasterPoseComponent, AnimClass ou modificação de física.

Após saída metadata, preparar leitura dos getters confirmados para **cada** componente,
não assumir que o primeiro BoxComponent é corpo: pode ser interação ou outro volume.
Relacionar CollisionEnabled, ObjectType/profile, posição/rotação/escala e extents.
Envelope candidato deve envolver os componentes físicos que realmente bloqueiam Camera;
essa última semântica exige trace reproduzível e não é provada pelo nome do componente.

BoxExtent local + transformação dá OBB; GetScaledBoxExtent já inclui escala, não aplicar
escala duas vezes. Sphere/Capsule ou corpo mesh requer geometria física própria; bounds
render não são collision hull. Usar forma conservadora envolvendo corpo físico para
varrer trechos, incluindo comprimento nas curvas e largura nos acessos. Uma SphereTrace
com raio de soldado não prova folga de caminhão. Na ponte, amostras de suporte nas rodas
e tabuleiro são gate separado do envelope; groundZ central sozinho não basta.

Este documento define próximo passo após metadata, não autoriza rotas validated=true.

## Metadata viva recebida
`D:/tools/foxhole-lab/truck-collision-schema-live.txt`: Truck_2 tem
CollisionCylinder CapsuleComponent, VehicleCollision BoxComponent, vários meshes,
partículas e SeatTrigger/TowHitch. Nenhum escolhido por nome como corpo autorizado.
Box getters scaled/unscaled retornam struct; CapsuleRadius/HalfHeight floats;
collision profile/enabled/objecttype e transform getters confirmados.

Preparada `D:/tools/foxhole-lab/t_truck_collision_values.lua`, syntax OK, não executada:
todos os PrimitiveComponents com collision settings/transform; Box extents e capsule
dimensões locais somente classes exatas. GetCollisionResponseToChannel primeiro
confirmado via metadata Channel/ReturnValue ByteProperty e então leitura Camera1 e
Visibility0. Não muda colisão. Valores da instância podem refletir colisão desativada
pelo motorista atual: distinguir perfil nativo de estado alterado pelo mod antes
de concluir que Camera não bloqueia o corpo.

## Retomada 11/10 — rastrear motorista nativo antes de integrar
Valores de colisão foram lidos (VALORES_CAMINHAO_20261010.md); scan de raios em
dados/rastro_envelope_caminhao.txt atingiu CharacterMesh0 fora da caixa400/162/140.
Flags de penetração não são prova do hull integral; nenhuma aresta autorizada.

Nova sonda somente leitura: tools/probe_native_truck_movement.lua. Confirma
assinaturas dos getters RootComponent/MovementComponent antes de chamar, lê
UpdatedComponent/UpdatedPrimitive somente se ObjectProperty e a flag
bIgnoreNonRootComponentsDuringVehicleMovement somente se BoolProperty. Enumera
assinaturas de movimento/input, não executa essas funções. Teste offline PASS;
NÃO executada no Unreal. Guardar no próximo lote saída antes/depois da logística.
Root ou UpdatedComponent identificado não prova por si só sweep integral: a
cápsula34/200, caixa e meshes têm papéis diferentes. Sem mover/desligar colisão
para forçar sucesso; primeiro rastrear o caminho de movimento já existente.

## Sonda executada no lote logístico 2 (11/10)
Mesmo TruckW observado antes/depois: raiz VehicleCollision(BoxComponent),
UpdatedComponent/UpdatedPrimitive iguais; RWDVehicleMovementComponent herda
SimpleVehicleMovementComponent e CharacterMovementComponent. Flag
bIgnoreNonRootComponentsDuringVehicleMovement=true nos dois estados, ActorCollision
true antes/false ativo. Rastros próprios em dados/rastro_truck_movement_*_20261011.txt.
Isso distingue escolha nativa da raiz de bounds visuais, não prova clearance/suporte
ou autoriza flag/rota. Partida posterior caiu; próximo desenvolvimento permanece
offline, sem reiniciar por esta descoberta.
