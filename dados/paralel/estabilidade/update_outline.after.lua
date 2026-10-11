function rts.outlineDepth(m, on)
    if not valid(m.pawn) or m.pawn.bActorIsBeingDestroyed then return end

function rts.updateOutline(m)
    -- IsValid pode continuar true durante destruicao. Invalidar o conjunto antes de tocar nas fontes.
    if not valid(m.pawn) or m.pawn.bActorIsBeingDestroyed then rts.clearOutline(m); return end
    for i, a in ipairs(m.outline or {}) do
        if not valid(a) or a.bActorIsBeingDestroyed or not valid((m.outlineSources or {})[i]) then
            rts.clearOutline(m); return
        end
    end
    if not valid(rts.cam) or rts.cam.bActorIsBeingDestroyed then return end