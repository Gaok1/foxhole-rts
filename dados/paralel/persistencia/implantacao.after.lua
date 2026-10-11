-- Aplica um plano de implantacao (logi.deployPlan ou sv.infraPlan) SEM tocar na carteira. Retorna registros
-- puros do que nasceu (codigo/XYZ/yaw, nunca ator ou endereco) ou nil e o motivo, depois de desfazer tudo.
function logi.applyPlan(plan)
    local created, touched, built = {}, {}, {}
    local ok, why = pcall(function()
        for _, b in ipairs(plan.builds) do
            assert(valid(b.ruin) and not b.ruin.bActorIsBeingDestroyed, "ruína deixou de existir")
            touched[#touched+1] = b
            b.ruin:SetActorHiddenInGame(true); b.ruin:SetActorEnableCollision(false)
            local a = world():SpawnActor(b.cls, b.pos, b.rot)
            if valid(a) then created[#created+1] = a end
            assert(valid(a) and not a.bActorIsBeingDestroyed, "estrutura não nasceu ativa")
            assert(a.Health == b.spec.hp and a.MaxHealth == b.spec.hp and a.CodeName:ToString() == b.spec.code, "contrato da estrutura divergiu")
            assert(valid(a.BaseStructureClass) and a.BaseStructureClass:GetFullName() == b.ruin:GetClass():GetFullName(), "ruína incompatível")
            local l = a:K2_GetActorLocation()
            assert(flatDist(l, b.pos) < 100 and math.abs(l.Z-b.pos.Z) < 100, "estrutura deslocada")
            assert(math.abs(a:K2_GetActorRotation().Yaw-b.rot.Yaw) < 1, "rotação da estrutura divergiu")
            a.TeamId = CFG.FRIENDLY_TEAM
            built[#built+1] = { kind="site", code=b.spec.code, x=b.pos.X+0, y=b.pos.Y+0, z=b.pos.Z+0, yaw=b.rot.Yaw+0 }
        end
        for _, p in ipairs(plan.parking) do
            local a = world():SpawnActor(plan.truckClass, {X=p.X,Y=p.Y,Z=p.Z+CFG.DEPLOY.off}, {Pitch=0,Yaw=p.Yaw,Roll=0})
            if valid(a) then created[#created+1] = a end
            assert(valid(a) and not a.bActorIsBeingDestroyed and a.Health == CFG.LOGI.hp, "caminhão não nasceu íntegro")
            local l = a:K2_GetActorLocation()
            assert(flatDist(l,p) < 150 and math.abs(l.Z-p.Z-CFG.DEPLOY.off) < 100, "caminhão deslocado")
            a.TeamId = CFG.FRIENDLY_TEAM
            built[#built+1] = { kind="truck", x=p.X+0, y=p.Y+0, z=p.Z+0, yaw=p.Yaw+0 }
        end
        local setup, missing = logi.scan()
        assert(setup, missing)
    end)
    if not ok then
        for _, a in ipairs(created) do
            if valid(a) and not a.bActorIsBeingDestroyed then pcall(function() a:K2_DestroyActor() end) end
        end
        for _, b in ipairs(touched) do
            if valid(b.ruin) and not b.ruin.bActorIsBeingDestroyed then
                pcall(function() b.ruin:SetActorHiddenInGame(b.hidden); b.ruin:SetActorEnableCollision(b.collision) end)
            end
        end
        return nil, why
    end
    -- O desocultador da camera nao deve reexibir a ruina substituida ao sair de foco.
    for _, b in ipairs(touched) do S.occluders[b.ruin] = nil end
    return built
end

function logi.deploy()
    local ok, plan, why = pcall(logi.deployPlan)
    if not ok or not plan then notify("Implantação recusada: " .. tostring(ok and why or plan), 6); return false end
    if plan.cost == 0 then notify("Cadeia já implantada. Shift+F6 inicia a partida.", 4); return true end
    local built, err = logi.applyPlan(plan)
    if not built then notify("Implantação desfeita, sem débito: " .. tostring(err), 8); return false end
    local wallet = logi.deployWallet()
    wallet.bmat, wallet.spent = wallet.bmat-plan.cost, wallet.spent+plan.cost
    -- Registro do que foi pago (persistido pelo save; sv.infraPlan refaz sem cobrar de novo).
    wallet.built = wallet.built or {}
    for _, r in ipairs(built) do wallet.built[#wallet.built+1] = r end
    notify(string.format("IMPLANTAÇÃO: -%d bmat do cenário; saldo %d. Shift+F6 inicia (transporte ainda em reta).", plan.cost, wallet.bmat), 10)
    return true
end
