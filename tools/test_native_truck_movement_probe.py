"""Valida sonda somente leitura e recusas de getters; nao prova movimento Unreal."""
from pathlib import Path
from lupa import LuaRuntime

source = Path(__file__).with_name('probe_native_truck_movement.lua').read_text(encoding='utf-8')
for signature in ('good', 'wrong_return', 'extra_parameter', 'missing'):
    lua = LuaRuntime()
    lua.globals().signature = signature
    lua.execute('''
    calls=0;rows={}
    out=function(...) rows[#rows+1]={...} end
    valid=function(o) return type(o)=='table' end
    local function fname(s) return {ToString=function() return s end} end
    local function prop(n,k) return {GetFName=function() return fname(n) end,
      GetClass=function() return {GetFName=function() return fname(k) end} end} end
    local cls={GetFullName=function() return 'Class Mock' end,GetSuperStruct=function() return nil end,
      ForEachProperty=function() end,ForEachFunction=function() end}
    local component={GetClass=function() return cls end,GetFullName=function() return 'Component Mock' end}
    local truck=setmetatable({GetClass=function() return cls end,GetFullName=function() return 'Truck Mock' end,
      GetActorEnableCollision=function() return true end,
      K2_GetRootComponent=function() calls=calls+1;return component end,
      GetMovementComponent=function() calls=calls+1;return component end},
      {__newindex=function() error('escrita no truck proibida') end})
    world=function() return {GetFullName=function() return 'World Mock' end} end
    logi={scan=function() return {trucks={truck}} end}
    StaticFindObject=function(path)
      local name=path=='/Script/Engine.Actor' and 'K2_GetRootComponent' or 'GetMovementComponent'
      return {ForEachFunction=function(_,cb)
        if signature=='missing' then return end
        cb({GetFName=function() return fname(name) end,ForEachProperty=function(_,p)
          p(prop('ReturnValue',signature=='wrong_return' and 'IntProperty' or 'ObjectProperty'))
          if signature=='extra_parameter' then p(prop('Input','FloatProperty')) end
        end})
      end}
    end
    ''')
    lua.execute(source)
    assert lua.globals().calls == (2 if signature == 'good' else 0), signature
    lua.execute("logi.scan=function() return nil,'absent' end")
    lua.execute(source)
    assert lua.globals().calls == (2 if signature == 'good' else 0)
print('PASS: sonda read-only, getters confirmados, schema divergente/ausente e scan recusado sem chamadas')
