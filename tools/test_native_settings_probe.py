"""Testa somente as recusas/nao escrita da sonda Lua; nao prova binding ou engine."""
from pathlib import Path
from lupa import LuaError, LuaRuntime

SOURCE = (Path(__file__).parent / "probe_native_settings.lua").read_text(encoding="utf-8")


def run(existing=False, bad_default=False, bad_super=False, bad_spawn=False):
    lua = LuaRuntime()
    lua.globals().existing = existing
    lua.globals().bad_default = bad_default
    lua.globals().bad_super = bad_super
    lua.globals().bad_spawn = bad_spawn
    lua.execute('''
        calls, rows = 0, {}
        valid = function(x) return x ~= nil and x ~= false end
        out = function(...) rows[#rows+1] = {...} end
        local prior = existing and {GetAddress=function() return 123 end} or nil
        local gi = setmetatable({}, {
            __index=function(_, key)
                assert(key == 'ServerSettings')
                return prior
            end,
            __newindex=function() error('escrita proibida no GameInstance') end,
        })
        world = function() return {OwningGameInstance=gi} end
        local cls = {GetSuperStruct=function() return {
            GetFName=function() return {ToString=function()
                return bad_super and 'Object' or 'SaveGame'
            end} end,
        } end}
        StaticFindObject=function(path)
            assert(path == '/Script/War.ServerSettings')
            return cls
        end
        StaticConstructObject=function(c, outer)
            assert(c == cls and outer == gi)
            calls = calls + 1
            if bad_spawn then return nil end
            return {
                GetFullName=function() return 'ServerSettings Mock' end,
                SpawnInvulnerabilityTime=3,
                GlobalRefineYieldModifier=1,
                WarTweakables={
                    MinTankArmourMultiplier=bad_default and 2 or 1,
                    BallisticPenetrationMaxDistance=4000,
                    BallisticPenetrationDistanceExponent=1.5,
                },
            }
        end
    ''')
    try:
        lua.execute(SOURCE)
    except LuaError as exc:
        return lua, str(exc)
    return lua, None


for existing in (False, True):
    runtime, error = run(existing=existing)
    assert error is None, error
    assert runtime.globals().calls == 1
    assert runtime.globals().rows[7][1] == "CONTEXT_UNCHANGED"

for options, message, calls in (
    ({"bad_default": True}, "default divergente", 1),
    ({"bad_super": True}, "ancestral inesperado", 0),
    ({"bad_spawn": True}, "constructor nao retornou", 1),
):
    runtime, error = run(**options)
    assert error and message in error, error
    assert runtime.globals().calls == calls

print("PASS: sonda Lua recusa defaults/classe/spawn divergentes e preserva contexto mock")
print("NAO prova: binding UE4SS, construtor vivo, configuracao associada ou dano nativo")
