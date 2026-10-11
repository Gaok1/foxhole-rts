function rts.outlineDepth(m, on)
    if not valid(m.pawn) or m.pawn.bActorIsBeingDestroyed then return end
    if not m.outlineParts then
        m.outlineParts = {}
        for _, v in ipairs(m.pawn:K2_GetComponentsByClass(StaticFindObject('/Script/Engine.SkeletalMeshComponent'))) do
            local c = v:get()
            if valid(c) then m.outlineParts[#m.outlineParts + 1] = c end
        end
    end
    -- Corpo, cabeca, maos, pernas e equipamento sao componentes separados; o nativo reativa todos.
    for _, c in ipairs(m.outlineParts) do
        if valid(c) then
            -- O nativo pode reativar flags: conferir valor real a cada quadro, sem cache Lua.
            if c.bRenderCustomDepth ~= on then c:SetRenderCustomDepth(on) end
            if on and c.CustomDepthStencilValue ~= 1 then c:SetCustomDepthStencilValue(1) end
        end
    end
end