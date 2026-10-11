-- ---- PLANO B: visual da base avancada (CFG.FWD.visual = "class" | "mesh" | "auto"; "native" = "class") ----
-- Modo configurado: "class" | "mesh" | "auto" | nil (valor desconhecido).
function logi.fwdMode()
    local v = CFG.FWD.visual
    if v == "native" then v = "class" end
    if v == "class" or v == "mesh" or v == "auto" then return v end
    return nil
end

-- Destroi SO o que o mod criou (ator principal + partes extras), com as guardas de endereco reaproveitado/em destruicao.
function logi.fwdKill(actor, parts)
    for _, o in ipairs(parts or {}) do
        if o and valid(o) and not o.bActorIsBeingDestroyed then pcall(function() o:K2_DestroyActor() end) end
    end
    if actor and valid(actor) and not actor.bActorIsBeingDestroyed then pcall(function() actor:K2_DestroyActor() end) end
end

-- Primeira malha da parte que carrega (nil se nenhuma). So carrega assets; nao cria ator.
function logi.fwdMeshPath(P)
    for _, p in ipairs(P.mesh or {}) do
        if findAsset(p) then return p end
    end
    return nil
end

-- Plano B: ator principal + partes, todos StaticMeshActor do mod (meshActor, o mesmo caminho de barraca/arame/caixa). Tudo ou nada:
-- qualquer falha destroi o que ja nasceu. Retorna principal, partes | nil, motivo.
function logi.fwdMeshSpawn(x, y, z, yaw)
    local F, M = CFG.FWD, CFG.FWD.mesh
    local made = {}
    local ok, why = pcall(function()
        assert(type(M) == "table" and type(M.parts) == "table" and #M.parts > 0, "sem malhas configuradas")
        local cy, sy = math.cos(math.rad(yaw)), math.sin(math.rad(yaw))
        for i, P in ipairs(M.parts) do
            local path = logi.fwdMeshPath(P)
            if not path then
                assert(i > 1, "malha principal da base avançada não carregou")
            else
                local lx, ly = P.lx or 0, P.ly or 0
                local px, py = x + lx * cy - ly * sy, y + lx * sy + ly * cy
                local gz = logi.parkingGround(px, py, { Z = z })
                if not gz or math.abs(gz - z) > 2 * F.maxSlope then gz = z end
                local s = (P.scale or 1) * (M.scale or 1)
                local a = meshActor(px, py, gz + (P.dz or 0), path, { X = s, Y = s, Z = s })
                if a then made[#made + 1] = a end
                local alive = a ~= nil and valid(a) and not a.bActorIsBeingDestroyed
                if i == 1 then
                    assert(alive, "malha principal não nasceu ativa")
                    assert(flatDist(a:K2_GetActorLocation(), { X = px, Y = py }) < 100, "malha principal deslocada")
                end
                if alive then
                    pcall(function() a:K2_SetActorRotation({ Pitch = 0, Yaw = yaw + (P.yaw or 0), Roll = 0 }, false) end)
                end
            end
        end
    end)
    if not ok then
        logi.fwdKill(made[1], { table.unpack(made, 2) })
        return nil, tostring(why)
    end
    local parts = {}
    for i = 2, #made do
        if valid(made[i]) and not made[i].bActorIsBeingDestroyed then parts[#parts + 1] = made[i] end
    end
    return made[1], parts
end

-- Aviso unico (por sessao) de que a classe nativa nao serviu e o visual cai para as malhas.
function logi.fwdFallback(why)
    log("BASES: classe BPForwardBase1_C recusada (" .. tostring(why) .. "); usando o visual de malhas do mod (plano B)")
    if not S.fwdWarned then
        S.fwdWarned = true
        notify("base avançada: a classe nativa não serviu; usando o visual de malhas do mod (plano B)", 6.0)
    end
end

-- Cria o visual da base conforme o modo. `cls` (opcional) = classe ja carregada. Retorna ator, partes, tipo ("class"|"mesh")
-- ou nil, nil, nil, motivo. "auto": a classe vai primeiro; spawn nulo, em destruicao ou fora do contrato (fwdSpawn ja destroi o
-- que nasceu) cai na malha, sem repetir a classe naquele pedido.
function logi.fwdCreate(x, y, z, yaw, cls)
    local F, mode = CFG.FWD, logi.fwdMode()
    if mode == nil then return nil, nil, nil, "visual '" .. tostring(F.visual) .. "' desconhecido (class, mesh ou auto)" end
    local why
    if mode ~= "mesh" then
        local a, err
        if cls then a, err = logi.fwdSpawn(cls, x, y, z, yaw)
        else
            local okL, c = pcall(LoadAsset, F.asset)
            if okL and valid(c) then a, err = logi.fwdSpawn(c, x, y, z, yaw)
            else err = okL and "classe da base avançada não carregou" or ("LoadAsset falhou: " .. tostring(c)) end
        end
        if a then return a, nil, "class" end
        if mode == "class" then return nil, nil, nil, err end
        why = err
        logi.fwdFallback(err)
    end
    local a, parts = logi.fwdMeshSpawn(x, y, z, yaw)
    if not a then return nil, nil, nil, (why and (tostring(why) .. "; malha: ") or "") .. tostring(parts) end
    return a, parts, "mesh"
end

-- Pura: da para criar o visual? (class: a classe carrega; mesh: a malha principal carrega; auto: qualquer das duas.) true | nil, motivo.
function logi.fwdVisualReady()
    local F, mode = CFG.FWD, logi.fwdMode()
    if mode == nil then return nil, "visual '" .. tostring(F.visual) .. "' desconhecido (class, mesh ou auto)" end
    if mode == "class" then
        local cls = LoadAsset(F.asset)
        if not valid(cls) then return nil, "classe da base avançada não carregou" end
        return true
    end
    local okC = false
    if mode == "auto" then
        local okL, c = pcall(LoadAsset, F.asset)
        okC = okL and valid(c) and true or false
    end
    local P = CFG.FWD.mesh and CFG.FWD.mesh.parts and CFG.FWD.mesh.parts[1]
    if okC or (P and logi.fwdMeshPath(P)) then return true end
    return nil, mode == "auto" and "nem a classe nem a malha da base avançada carregaram" or "malha da base avançada não carregou"
end

