"""Run with lupa installed/on PYTHONPATH. Does not load UE4SS or contact the game."""
from pathlib import Path
from lupa import LuaRuntime, LuaError

source = Path(__file__).with_name("probe_inventory.lua").read_text(encoding="utf-8")
lua = LuaRuntime()
lua.execute('''
lines = {}
function out(...) local t={...}; for i,v in ipairs(t) do t[i]=tostring(v) end
    table.insert(lines,table.concat(t,"|")) end
server, dedicated, menu = true, false, false
function valid(o) return o ~= nil and o.valid ~= false end
local w={GetFullName=function() return menu and "MainMenu" or "HomeRegionW" end}
function world() return w end
function ksl() return {IsServer=function() return server end,
    IsDedicatedServer=function() return dedicated end} end
local function named(s) return {GetFullName=function() return s end} end
local p=named("pawn")
p.GetClass=function() return named("Character_C") end
p.Health=100; p.CharacterActivityStateInternal=0; p.Controller=named("controller")
p.ItemHolder=named("holder"); p.EquipmentItemHolder=named("equipment")
local item={CodeName={ToString=function() return "Rifle" end},StackSize=1,PickupCDO=named("cdo")}
p.ItemHolderItems={GetArrayNum=function() return 1 end,
    ForEach=function(_,f) f(1,{get=function() return item end}) end}
-- Missing equipment array exercises a failed read without aborting the diagnostic.
function squad() return {{group=1,pawn=p,hpc={PlayerState=named("ps"),bIsLocalPlayerController=true}},
    {group=2,pawn={valid=false}}} end
''')
lua.execute(source)
output = lua.eval(r'table.concat(lines,"\n")')
assert "Rifle|1|cdo" in output and "atividade|0" in output
assert "INDISPONIVEL:" in output and "pawn invalido: ignorado" in output
assert output.splitlines()[-1].startswith("FIM:")
for state in ("server=false", "server=true; dedicated=true", "dedicated=false; menu=true"):
    lua.execute(state + "; lines={}")
    try:
        lua.execute(source)
    except LuaError:
        assert lua.eval("#lines") == 0
    else:
        raise AssertionError("probe accepted unsafe context")
print("PASS: probe reads both arrays, tolerates missing fields/invalid pawns, rejects non-local contexts")
