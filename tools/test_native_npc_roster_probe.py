"""Contrato read-only da sonda; mocks não provam IDs/voz/lifecycle no Unreal."""
from pathlib import Path
from lupa import LuaRuntime

source = Path(__file__).with_name('probe_native_npc_roster.lua').read_text(encoding='utf-8')
for signature in ('good', 'missing', 'wrong', 'extra', 'state_wrong', 'state_extra'):
    lua = LuaRuntime()
    lua.globals().signature = signature
    lua.execute('''
    rows={}; calls=0
    out=function(...) rows[#rows+1]={...} end
    valid=function(v) return type(v)=='table' end
    local function fn(n) return {ToString=function() return n end} end
    local function prop(n,t) return {GetFName=function() return fn(n) end,
      GetClass=function() return {GetFName=function() return fn(t) end} end} end
    StaticFindObject=function(path) return {ForEachFunction=function(_,cb)
      if path=='/Script/Engine.GameplayStatics' then
        cb({GetFName=function() return fn('GetGameState') end,
          ForEachProperty=function(_,p)
            p(prop('ReturnValue',signature=='state_wrong' and 'IntProperty' or 'ObjectProperty'))
            p(prop('WorldContextObject','ObjectProperty'))
            if signature=='state_extra' then p(prop('Unexpected','BoolProperty')) end
          end})
        return
      end
      if signature=='missing' then return end
      cb({GetFName=function() return fn('IsLocalController') end,
        ForEachProperty=function(_,p)
          p(prop('ReturnValue',signature=='wrong' and 'IntProperty' or 'BoolProperty'))
          if signature=='extra' then p(prop('Input','BoolProperty')) end
        end})
    end} end
    -- Proxies rejeitam toda escrita; nenhuma propriedade de ID é acessada.
    local function readonly(v)
      return setmetatable({}, {__index=function(_,k)
        assert(k~='UniqueId','ID privado nao deve ser lido'); return v[k]
      end, __newindex=function() error('escrita proibida') end})
    end
    local ps=readonly({bIsABot=true,bIsInactive=false,GetAddress=function() return 1 end})
    local missing=readonly({bIsABot=true,bIsInactive=false,GetAddress=function() return 2 end})
    local c=readonly({PlayerState=ps,Pawn={},IsLocalController=function() calls=calls+1;return true end,
      GetAddress=function() return 3 end})
    local pooled=readonly({PlayerState=missing,IsLocalController=function() calls=calls+1;return true end,
      GetAddress=function() return 4 end})
    local dead=readonly({bActorIsBeingDestroyed=true,IsLocalController=function() error('morto') end})
    local state=readonly({PlayerArray={ForEach=function(_,cb)
      cb(0,{get=function() return ps end})
      cb(1,{get=function() return dead end})
    end}})
    world=function() return {} end
    gs=function() return {GetGameState=function() return state end} end
    playerController=function() return c end
    squad=function() return {{hpc=c},{hpc=dead}} end
    enemies=function() return {} end
    hpcPool=function() return {pooled} end
    ''')
    lua.execute(source)
    assert lua.globals().calls == (2 if signature == 'good' else 0), signature
    if signature == 'good':
        rows = [list(row.values()) for row in lua.globals().rows.values()]
        assert ['ROSTER', 'TOTAL', 1, 'OBSERVED_CONTROLLERS', 2, 'MEMBERS', 1] in rows
        assert any(row[0] == 'NPC_CONTRACT' and row[1] == 'pool' and row[11] is False for row in rows)
    lua.execute('gs=function() return {GetGameState=function() return nil end} end')
    lua.execute(source)
    assert lua.globals().calls == (2 if signature == 'good' else 0)
print('PASS: sonda NPC sem escrita/IDs, assinatura estrita, deduplicacao, pool fora do roster e ator destruindo')
