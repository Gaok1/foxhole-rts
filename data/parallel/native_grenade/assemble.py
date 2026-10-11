"""Monta candidato a partir da fonte-base; nunca publica nem altera main real."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
source = (ROOT / 'mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
start = source.index('-- Granada: o fuzileiro')
end = source.index('local strikes = {}', start)
source = source[:start] + '''-- Granada nativa: dados do jogo, timer/colisao/movimento/dano/FX do engine.
CFG.GRENADE = { range = 1800.0, cooldown = 18.0, roles = { rifle = true },
                pin = "/Game/Audio/SFX/Weapons/Grenade/GrenadePinPull_Cue.GrenadePinPull_Cue" }
''' + source[end:]
start = source.index('-- Lanca a granada de m em target')
end = source.index('local function mortarTick()', start)
source = source[:start] + (HERE / 'grenade.lua').read_text(encoding='utf-8') + '\n' + source[end:]
start = source.index('        if st.proj and valid(st.proj) and t < st.t then')
end = source.index('        if t >= st.t then', start)
source = source[:start] + source[end:]
source = source.replace('        if st.proj and valid(st.proj) then st.proj:K2_DestroyActor() end\n', '')
source = source.replace('            if st.proj and valid(st.proj) then st.proj:K2_DestroyActor(); st.proj = nil end\n', '')
source = source.replace('    local M = st.grenade and CFG.GRENADE or CFG.MORTAR', '    local M = CFG.MORTAR -- divida separada: morteiro ainda abstrato')
source = source.replace('                    local stat = st.grenade and mortar.gdmg or mortar.dmg', '                    local stat = mortar.dmg')
source = source.replace('        throwGrenade(shooter, target)\n        return\n', '        if throwGrenade(shooter, target) then return end\n')
(HERE / 'main_candidate.lua').write_text(source, encoding='utf-8')
