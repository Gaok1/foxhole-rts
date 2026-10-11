# Colisão do TruckW — leitura viva, antes de iniciar logística

HomeRegionW, PID 21456, main 223788476973. Sonda externa `t_truck_collision_values.lua`,
saída completa `D:/tools/foxhole-lab/truck-collision-values-v41-live.txt`.
Sem alteração de física e antes de newGame: não é estado de colisão desligada pelo motorista.

- VehicleCollision: BoxComponent, perfil VehicleRoot, CollisionEnabled 3, ObjectType 6.
  Extents locais e escalados iguais: 400/162/140 cm; escala 1. Resposta Camera/Visibility: 2/2.
- CollisionCylinder: CapsuleComponent, raio 34 e meia altura 200; perfil VehicleCapsule,
  CollisionEnabled 1, Camera/Visibility 1/1.
- CharacterMesh0 e meshes CabinMesh/TrailerMesh também respondem 2 aos dois canais.
  Portanto a caixa VehicleCollision sozinha ainda não comprova envelope integral.

Próximo: relacionar caixa/meshes com impactos de traços e obter envelope conservador em coordenadas
do veículo. Não usar bounds de render como hull físico nem autorizar arestas só com esses extents.
Ainda faltam curvas reais, acesso às instalações, água/tabuleiro, sweep e obstrução dinâmica.
