"""Lease/lifetime Lua reais; mocks nao certificam GC, engine ou explosao ao vivo."""
from pathlib import Path
from lupa import LuaRuntime

source = (Path(__file__).parents[1] / "mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")
block = source[source.index("function rts.nativeAcquire()"):source.index("-- Oclusao:")]


def setup(borrow=False):
    lua = LuaRuntime()
    lua.execute('''
        rts, S, actors, clock, constructions, authority = {}, {}, {}, 0, 0, true
        function object(id)
            return {IsValid=function() return true end, GetAddress=function() return id end}
        end
        valid=function(x) return x ~= nil and x:IsValid() end
        gi=object(1); w=object(2); w.OwningGameInstance=gi
        world=function() return w end
        isLocalAuthority=function() return authority end
        StaticFindObject=function() return object(3) end
        StaticConstructObject=function() constructions=constructions+1; return object(100+constructions) end
        gs=function() return {GetRealTimeSeconds=function() return clock end} end
        FindAllOf=function(class)
            local found={}
            for _,p in ipairs(actors) do
                if p.class==class then found[#found+1]=p end
            end
            return found
        end
        function projectile(name,class)
            local p=object(200)
            p.class=class or 'BPGrenadeW_C'
            p.GetFullName=function() return name end
            p.GetClass=function() return {GetFName=function() return {ToString=function() return p.class end} end} end
            p.K2_DestroyActor=function() p.bActorIsBeingDestroyed=true end
            return p
        end
    ''')
    lua.execute(block)
    if borrow:
        lua.execute("prior=object(99); gi.ServerSettings=prior")
    return lua


l = setup()
l.execute('''
    assert(rts.nativeAcquire() and constructions==1)
    local anchored=gi.ServerSettings
    assert(rts.nativeAcquire() and gi.ServerSettings==anchored and constructions==1)
    own=projectile('own'); foreign=projectile('foreign'); actors={own,foreign}
    assert(rts.nativeTrack(own))
    rts.nativeRelease() -- outro spawn falhou; ainda retido pelo projétil vivo
    assert(S.nativeContext and gi.ServerSettings==anchored)
    rts.nativeTick(); assert(S.nativeContext)
    own.bExploded=true; clock=1; rts.nativeTick()
    assert(not S.nativeContext and gi.ServerSettings==nil)
    assert(not foreign.bActorIsBeingDestroyed)
''')
l = setup(borrow=True)
l.execute("assert(rts.nativeAcquire()); rts.nativeRelease(); assert(gi.ServerSettings==prior and constructions==0)")
l = setup()
l.execute("assert(rts.nativeAcquire()); replacement=object(77); gi.ServerSettings=replacement; rts.nativeRelease(); assert(gi.ServerSettings==replacement)")
l = setup()
l.execute('''
    assert(rts.nativeAcquire()); own=projectile('own'); foreign=projectile('foreign'); actors={own,foreign}
    assert(rts.nativeTrack(own)); rts.nativeClear()
    assert(own.bActorIsBeingDestroyed and not foreign.bActorIsBeingDestroyed)
    assert(not S.nativeContext and gi.ServerSettings==nil)
''')
l = setup()
l.execute("authority=false; assert(not rts.nativeAcquire() and constructions==0)")
l = setup()
l.execute("assert(rts.nativeAcquire()); assert(not rts.nativeTrack(nil)); rts.nativeRelease(); assert(gi.ServerSettings==nil)")
l = setup()
l.execute('''
    assert(rts.nativeAcquire()); own=projectile('own'); actors={own}; assert(rts.nativeTrack(own))
    actors={}; rts.nativeTick(); assert(not S.nativeContext and gi.ServerSettings==nil)
''')
l = setup()
l.execute('''
    assert(rts.nativeAcquire()); own=projectile('own'); actors={own}; assert(rts.nativeTrack(own))
    w.GetAddress=function() return 9 end; rts.nativeTick()
    assert(own.bActorIsBeingDestroyed and not S.nativeContext and gi.ServerSettings==nil)
''')
l = setup()
l.execute('''
    assert(rts.nativeAcquire())
    warden=projectile('warden'); assert(rts.nativeTrack(warden))
    assert(rts.nativeAcquire())
    colonial=projectile('colonial','Grenade_C'); assert(rts.nativeTrack(colonial))
    foreign=projectile('foreign','Grenade_C'); actors={warden,colonial,foreign}
    rts.nativeTick(); assert(S.nativeContext)
    warden.bExploded=true; clock=1; rts.nativeTick()
    assert(S.nativeContext and gi.ServerSettings and not S.nativeContext.names.warden)
    rts.nativeClear()
    assert(colonial.bActorIsBeingDestroyed and not foreign.bActorIsBeingDestroyed)
    assert(not S.nativeContext and gi.ServerSettings==nil)
''')
print("PASS: contexto nativo proprio/emprestado, leases, nomes, explosao, cleanup, autoridade, troca externa/mundo")
print("NAO prova: lifetime/GC nativo nem integracao viva do lancamento")
