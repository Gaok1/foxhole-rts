-- pv4_cmd_deploy.lua - equivale a Alt+L (logi.deploy) pelo canal; NAO injeta teclado. Preparado e NAO executado.
-- Cria ATORES nativos (refinaria e fabrica sobre as ruinas, caminhoes de suprimento). So em hex com ruinas correspondentes
-- (CallumsCapeHex). Na v4 (coleta manual): orcamento 1000 = refinaria 400 + fabrica 400 + 2 caminhoes de suprimento 100 (sem o de recurso).
-- Esperado: "IMPLANTACAO: -1000 bmat do cenario; saldo 0" na 1a vez; "Cadeia ja implantada" ao repetir (sem atores novos).
-- Leitura da carteira: S.deploy (bmat/spent/built). Atores novos: contar BPRefinery_C, BPFactory_C, BPTruckW_C ativos antes e depois.
local function count(cls)
    local n = 0
    for _, a in ipairs(FindAllOf(cls) or {}) do if valid(a) and not a.bActorIsBeingDestroyed then n = n + 1 end end
    return n
end
local function snap(tag)
    local W = logi.deployWallet()   -- cria a carteira desta carga do mundo se ainda nao existe (o proprio logi.deploy faz o mesmo)
    out(tag, "refinarias", count("BPRefinery_C"), "fabricas", count("BPFactory_C"), "caminhoesW", count("BPTruckW_C"),
        "carteira bmat", W.bmat, "gasto", W.spent, "built", W.built and #W.built or "-")
end
snap("ANTES")
local ok = logi.deploy()
out("logi.deploy", tostring(ok))
snap("DEPOIS")
out("esperado v4 apos a 1a vez: refinarias+1, fabricas+1, caminhoesW ate 2, carteira 0, gasto 1000, built 4; repetir nao muda nada")
