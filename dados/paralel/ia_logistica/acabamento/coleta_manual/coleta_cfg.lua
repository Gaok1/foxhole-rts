-- COLETA MANUAL (CLAUDE_COLETA_MANUAL, 2026-10-09). Comeco normal da partida estilo "aldeoes": sem caminhao de recurso
-- vivo, soldados livres do jogador coletam sucata a pe (campo -> refinaria) ate a fabrica produzir o caminhao
-- (LOGI.truckCost bmat). Valores de rate/cap/max sao PROPOSTA de design (nao ha numero do jogo em dados/); equilibrio
-- e do usuario. Tudo em CFG.COLETA e na tabela logi (nenhum local de topo novo).
CFG.COLETA = {
    manualStart = true,   -- partida nova SEM caminhao de recurso (false = comportamento anterior: 3 caminhoes na implantacao)
    bmat0 = 40,           -- bmat inicial da fabrica na partida manual (CFG.LOGI.bmat0 = 240 compraria o caminhao no 1o tick)
    resFirst = true,      -- caminhao de recurso (destruido/ainda nao construido) e reconstruido antes dos de suprimento
    rate = 0.5,           -- sucata/s por soldado parado no campo (PROPOSTA: ~1 golpe de 1 sucata a cada 2 s)
    cap = 40,             -- sucata que um soldado carrega (PROPOSTA; o caminhao de recurso leva LOGI.trip = 100)
    workers = 3,          -- a base mantem (enquanto a coleta e necessaria) ate 3 trabalhadores; 1 camisa do estoque da base cada
    spawnEvery = 3.0,     -- s entre tentativas de criar/repor um trabalhador
    delay = 5.0,          -- s sem caminhao de recurso antes de chamar alguem
    scan = 2.0,           -- s entre buscas de coletor livre
    fieldR = 1000.0,      -- cm: dentro deste raio do campo conta como coletando
    refR = 1500.0,        -- cm: dentro deste raio da refinaria a sucata e entregue (credito so aqui)
    stand = 600.0,        -- cm: ponto de espera, do lado de onde o soldado vem, a esta distancia do centro do lugar
    quiet = 60.0,         -- s (os.clock) sem ordem do jogador para o soldado contar como livre
    fireQuiet = 8.0, danger = 3500.0, minHp = 0.8,   -- fora de combate: sem tiro recente, inimigo a mais de danger cm, vida >= 80%
    pause = 60.0,         -- s de combate seguidos antes de largar a coleta (a carga se perde)
    leg = 180.0,          -- s maximos por trecho de caminhada (preso: larga a coleta, carga perdida)
    retry = 3.0,          -- s entre reenvios da rota
}
-- Trabalhador: soldado SEM fuzil (sem malha de arma, alcance 0: nunca atira), nasce na base (logi.workerDepot), custa 1 camisa
-- do estoque desse deposito, debitada so apos o spawn confirmado. Fica no esquadrao (inimigo o enxerga e o ataca, morte,
-- marcadores e save/continuar funcionam como em qualquer soldado). grip 0 = sem arma equipada (confirmar no laboratorio).
CFG.WEAPONS.worker = { name = "trabalhador", cost = 0, range = 0.0, interval = 9.0, hit = 0.0, dmg = 0.0, supp = 0.0, pitch = 1.0, ammo = 0, grip = 0 }

-- Interface comum de nascimento (ESPECIFICACAO de bases avancadas, 4.3): decidir (logi.spawnSite, pura) -> criar o ator ->
-- logi.spawnCommit (unico debito de camisa/fuzil). Aqui so o trabalhador e o local "base"; as bases avancadas estendem
-- CFG.SPAWN.roles (rifle, mg, ...) e os locais. startRifles: fuzis na base principal quando a partida comeca pela coleta manual.
CFG.SPAWN = CFG.SPAWN or {}
CFG.SPAWN.roles = CFG.SPAWN.roles or {}
CFG.SPAWN.roles.worker = { shirts = 1, sites = { "base" } }
CFG.SPAWN.startRifles = CFG.SPAWN.startRifles or 10
