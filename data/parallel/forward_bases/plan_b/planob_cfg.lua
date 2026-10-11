-- PLANO B (visual da base avancada). visual: "class" (ator BPForwardBase1_C, o antigo "native") | "mesh" (so malhas estaticas do jogo,
-- sem ator nativo) | "auto" (tenta a classe; se faltar/nascer errada, desfaz e usa as malhas). Estado, vida, estoque, perda e save
-- sao identicos nos tres modos (o registro `fb` do mod manda; o ator e so visual). Tamanhos reais: SO o laboratorio mede (sonda
-- plan_b/probes/pb_malhas.lua): ajuste `scale`, `lx/ly/dz` (cm; lx/ly no referencial da base, girado por yaw) e `scale` global.
-- Cada parte tenta as malhas de `mesh` na ordem (a primeira que carrega); a parte 1 e obrigatoria (e o ator "principal" da base);
-- as demais, se nao carregarem, sao omitidas. Sem colisao (como CFG.TENT/WIRE): o A* e os caminhoes nao desviam.
CFG.FWD.mesh = { scale = 1.0, parts = {
    { name = "barraca", lx = 0.0, ly = 0.0, dz = 0.0, yaw = 0.0, scale = 0.6,       -- 06 e a barraca ja usada pelo mod (CFG.TENT)
      mesh = { "/Game/Meshes/Environment/Props/CanvasTentCamoflauge.CanvasTentCamoflauge",
               "/Game/Meshes/Environment/Props/CanvasTent07.CanvasTent07",
               "/Game/Meshes/Environment/Props/CanvasTent06.CanvasTent06" } },
    { name = "sacos", lx = 0.0, ly = 350.0, dz = 0.0, yaw = 0.0, scale = 1.0,       -- parede de sacos de areia na frente
      mesh = { "/Game/Meshes/Environment/Props/SandbagLargePile.SandbagLargePile",
               "/Game/Meshes/Environment/Props/SandbagSmallPile.SandbagSmallPile" } },
    { name = "caixas", lx = -300.0, ly = -150.0, dz = 0.0, yaw = 20.0, scale = 1.0, -- estoque a vista
      mesh = { "/Game/Meshes/Environment/Props/BasicCrates04.BasicCrates04",
               "/Game/Meshes/Environment/Props/AmmoCrate.AmmoCrate" } },
} }
