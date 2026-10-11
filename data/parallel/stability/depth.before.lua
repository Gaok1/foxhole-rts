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
            c:SetRenderCustomDepth(on)
            if on then c:SetCustomDepthStencilValue(1) end
        end
    end
end