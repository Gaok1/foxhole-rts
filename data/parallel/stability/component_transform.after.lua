function rts.updateOutline(m)
    -- IsValid pode continuar true durante destruicao. Invalidar o conjunto antes de tocar nas fontes.
    if not valid(m.pawn) or m.pawn.bActorIsBeingDestroyed then rts.clearOutline(m); return end
    for i, a in ipairs(m.outline or {}) do
        if not valid(a) or a.bActorIsBeingDestroyed or not valid((m.outlineSources or {})[i]) then
            rts.clearOutline(m); return
        end
    end
    if not valid(rts.cam) or rts.cam.bActorIsBeingDestroyed then return end
    local camera = rts.cam:K2_GetActorLocation()
    local pitch, back = math.rad(CFG.CAM_PITCH), CFG.OUTLINE.back
    local previous, meshScale, dx, dy, dz, scale, radius, transform
    -- Homotetia centrada na camera: C + q*(P-C), escala q. Cada vertice conserva a projecao,
    -- mesmo longe do centro da tela; deslocar pelo forward fixo criava um vulto lateral.
    for i, a in ipairs(m.outline or {}) do
        local src = m.outlineSources[i]
        if src ~= previous then
            local native = src:K2_GetComponentToWorld()
            local p = native.Translation
            meshScale = native.Scale3D
            dx, dy, dz = p.X-camera.X, p.Y-camera.Y, p.Z-camera.Z
            scale = 1 + back / math.max(math.sqrt(dx*dx+dy*dy+dz*dz), 1)
            radius = math.max(dx*math.cos(pitch)+dz*math.sin(pitch), 100) * scale / CFG.OUTLINE.pixels
            local q = native.Rotation
            transform = { Rotation = { X=q.X, Y=q.Y, Z=q.Z, W=q.W },
                Scale3D = { X=meshScale.X*scale, Y=meshScale.Y*scale, Z=meshScale.Z*scale } }
            previous = src
        end
        local angle = ((i - 1) % CFG.OUTLINE.copies) * 2 * math.pi / CFG.OUTLINE.copies
        transform.Translation = { X = camera.X + dx*scale - math.sin(pitch)*math.sin(angle)*radius,
            Y = camera.Y + dy*scale + math.cos(angle)*radius,
            Z = camera.Z + dz*scale + math.cos(pitch)*math.sin(angle)*radius }
        a:K2_SetActorTransform(transform, false, {}, true)
    end
end
