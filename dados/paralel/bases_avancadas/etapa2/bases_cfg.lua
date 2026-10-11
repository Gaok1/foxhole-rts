-- BASES AVANCADAS (CLAUDE_BASES_AVANCADAS etapa 2, 2026-10-09; ESPECIFICACAO.md + DECISOES.md). Tudo em CFG.FWD, CFG.SPAWN, S e na
-- tabela logi (nenhum local de topo novo). Valores de custo/vida/estoque vem de dados/custos_do_jogo.txt (ForwardBase1: 300 bmat,
-- 1725 de vida, StoredItemCapacity 15 lido como 15 slots de caixa: PROVISORIO ate as sondas A3/B1). O resto e PROPOSTA de design.
-- pointSpawn=false: no ramo logistico (fora do Assalto) ponto de controle sem base nao e local de reforco (true restaura o antigo).
CFG.SPAWN.pointSpawn = false
CFG.SPAWN.roles.rifle = { shirts = 1, rifle = 1 }
CFG.SPAWN.roles.mg = { shirts = 1 }        -- mg/sniper/medic/officer gastam so camisa: bonus abstrato (nao ha caixa dessas armas no mod)
CFG.SPAWN.roles.sniper = { shirts = 1 }
CFG.SPAWN.roles.medic = { shirts = 1 }
CFG.SPAWN.roles.officer = { shirts = 1 }
CFG.FWD = {
    code = "ForwardBase1", visual = "native",     -- visual "mesh" (plano B) esta DECLARADO mas NAO implementado
    asset = "/Game/Blueprints/Structures/Bases/BPForwardBase1.BPForwardBase1_C",
    ruinAsset = "/Game/Blueprints/Structures/Bases/BPDestroyedForwardBase1.BPDestroyedForwardBase1_C",
    ruin = false,         -- criar a ruina nativa ao perder a base: so depois do ensaio B1 (classe nunca instanciada)
    strict = true,        -- exige Health == MaxHealth == hp e CodeName == code no ator recem-nascido (confirmar no ensaio B1)
    teamId = nil,         -- nil = nao escreve TeamId no ator (B1 decide 255 x FRIENDLY_TEAM)
    cost = 300, hp = 1725, cap = 15, max = 3,     -- cost/hp/cap: DADO do jogo; max: PROPOSTA (<= POINT_MAX)
    confirm = 4.0,        -- s (tempo real) para o 2o toque de Shift+J
    pending = 180.0,      -- s de pedido pendente (reserva de bmat) antes de cancelar
    half = 600.0, clear = 150.0, maxSlope = 60.0, maxHeight = 250.0, minExits = 3, exitR = 800.0,   -- footprint provisorio (A3/B1)
    minFromBase = 3000.0, maxToEnemyPoint = 4000.0,   -- "avancada": longe da base principal OU perto de um ponto inimigo
    blastMul = 2.0,       -- morteiro inimigo: dano x2 (como o caminhao); vida e do MOD, o ator nativo nao e escrito
}
S.fwdStage, S.fwdRuins = {}, {}
logi.fwd = {}
