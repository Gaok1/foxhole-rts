function anim.track(m)
    local ok, inst = pcall(function() return m.pawn.Mesh:GetAnimInstance() end)
    if not (ok and inst and inst:IsValid()) then return end
    m.animAddr = inst:GetAddress()
    anim.units[m.animAddr] = m
    if not anim.hooked then
        local hk, err = pcall(RegisterHook, CFG.ANIM_ABP, anim.onUpdate)
        anim.hooked = hk == true
        if not hk then log("hook de animacao falhou: " .. tostring(err)) end
    end
end
