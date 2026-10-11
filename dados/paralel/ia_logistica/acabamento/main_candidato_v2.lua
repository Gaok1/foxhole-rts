-- FoxholeRTS v0.9 (UE4SS Lua, UE 4.24). Solo contra IA, controle por esquadrao, sessao local totalmente offline.
-- Esquadrao misto: fuzileiros, metralhadores (3o/7o), medicos (4o/12o) e atirador (6o), armas do modelo proprio (WEAPONS).
-- Teclas (escolhidas fora dos mapeamentos padrao do jogo, lidos de Default__InputSettings; ver MODLOG):
--   F9   no menu: abre /Game/Maps/HomeRegionW como sessao local (?listen)
--   F10  liga/desliga o modo RTS (camera de cima + cursor). Liga sozinho apos o autostart.
--   F6   cria um esquadrao (SQUAD_SIZE soldados) ao lado do comandante
--   Shift+F6  nova partida: limpa tudo, esquadrao de 6, ondas automaticas e tres pontos de controle
--   Ctrl+F6   continua a partida salva (gravada a cada 30 s durante as ondas automaticas)
--   Alt+F6    assalto: o inimigo comeca com os tres pontos entrincheirados; tome todos
--   F4   onda inimiga (Colonial) sob o cursor; sem RTS, a frente do esquadrao
--   Shift+F4  liga/desliga ondas automaticas (reforco a cada onda eliminada; derrota se o esquadrao cair)
--   1 / 2 / 3   seleciona o grupo de tiro 1, o 2 ou todos (com o modo RTS ligado)
--   Botao esquerdo  seleciona o soldado sob o cursor; arrastar = caixa; Shift soma (disco laranja = selecionado)
--   Botao direito / F7   manda os selecionados para o ponto sob o cursor (atiram sozinhos no alcance);
--        sobre um inimigo: ordem de ataque (avancam ate o alcance e focam nele)
--   Shift+botao direito / Shift+F7   poe o destino na fila (percorrem os pontos em sequencia)
--   Ctrl+1 / 2 / 3 / 4   recruta fuzileiro (20) / metralhador (35) / atirador (45) / medico (30) com mao de obra
--        (cursor sobre um ponto de controle nosso: o recruta nasce nele)
--        (regenera 1/s + 0,5/s por ponto de controle, +8 por abate, +30 por onda eliminada; maximo 200)
--   Ctrl+5   fogo de morteiro sob o cursor (40 de mao de obra, recarga 20 s; 3 granadas, so ferem o inimigo)
--   Ctrl+7   trincheira sob o cursor (20 de mao de obra): ate 4 soldados; tiro acerta 60% menos, supressao pela metade
--   Ctrl+6   caixa de suprimentos sob o cursor (25 de mao de obra): recarrega municao a 4,5 m por 60 s
--   Ctrl+8   posto de socorro sob o cursor (30): cura 4 HP/s e estanca a 6 m
--   Ctrl+9   arame farpado sob o cursor (10): quem atravessa (os dois lados) anda a 35%
--   Ctrl+botao direito / Ctrl+F7   fogo de supressao em area por 20 s
--   K    ergue uma barreira de concreto sob o cursor (15 de mao de obra; cobertura baixa; F11 remove)
--   J    cria um ponto de controle sob o cursor (Shift+F4 sem pontos cria tres ao redor do esquadrao)
--        capturar = ficar dentro do anel sem inimigos; +0,5/s de mao de obra por ponto; perder todos = derrota
--   Home recuo: selecionados correm ao ponto nosso mais proximo (ou ao comandante) sem atirar, levando
--        metade dos acertos; dentro de um ponto nosso, fora de combate, recuperam 2 HP/s
--   End  segura posicao: para os selecionados e nao buscam cobertura (continuam atirando; nova ordem libera)
--   F11  remove esquadrao, inimigos, barreiras e pontos
--   F2   centraliza a camera no comandante;  PageUp/PageDown  zoom;  setas  mover camera;  F3  pan pela borda
--   Shift+F5  dificuldade: fácil / normal / difícil (precisão inimiga, tamanho das ondas, mão de obra)
--   F5   mostra/esconde a ajuda de teclas (aparece sozinha por 40 s ao ligar o RTS) e registra o status no log
-- Regra de seguranca: so age quando este processo e o servidor de uma sessao local (listen).
-- Receitas validadas no laboratorio: ver MODLOG.md (2026-10-07).

local UEHelpers = require("UEHelpers")

-- Constantes de ajuste numa tabela: o chunk do Lua aceita no maximo 200 locais (atingido na v0.5).
local CFG = {}
local S = {}    -- estados pequenos do mod (mesmo motivo: limite de 200 locais)

CFG.SQUAD_SIZE = 4
CFG.SQUAD_MAX = 12
CFG.SLOT_SPACING = 160.0   -- cm entre membros na formacao
CFG.ARRIVE_RADIUS = 60.0   -- cm
CFG.TICK_MS = 33

CFG.CAM_PITCH = -60.0
CFG.CAM_DIST_DEFAULT = 2800.0
CFG.CAM_DIST_MIN, CFG.CAM_DIST_MAX = 1200.0, 16000.0  -- alto: varias frentes; o visual acompanha (rts.zoomGfx)
CFG.CAM_EDGE_PX = 6
CFG.CAM_EDGE_PAN_DEFAULT = false  -- sem foco na janela o mouse "fica" na borda e a camera foge; F3 alterna
CFG.CAM_PAN_SPEED = 1.1    -- fracao da distancia da camera por segundo

local squad = {}       -- { hpc = AHeadlessPlayerController, pawn = ASimCharacter, slot = {X, Y}, target = {X, Y, Z} | nil }

local function log(msg) print("[FoxholeRTS] " .. tostring(msg) .. "\n") end

local function ksl() return UEHelpers.GetKismetSystemLibrary() end
local function gs() return UEHelpers.GetGameplayStatics() end

local function valid(o) return o ~= nil and o:IsValid() end

-- Cache por quadro. UEHelpers.GetWorld() faz FindAllOf("PlayerController") (varre todos os UObjects;
-- medido: 0,3 ms por chamada) e now()/tracos/spawns o chamavam centenas de vezes por quadro: com ~25
-- soldados o mod gastava ~80 ms/quadro. Dentro do laco por quadro (tick.inFrame) world, now e a trava de
-- autoridade valem para o quadro todo; fora dele (teclas, canal) sao recalculados a cada chamada.
local tick = { n = 0, inFrame = false }

local function world()
    if tick.inFrame and tick.wn == tick.n and tick.w then return tick.w end
    local w = UEHelpers.GetWorld()
    tick.w, tick.wn = w, tick.n
    return w
end

-- Trava: so com autoridade local, nunca como cliente de outro servidor.
local function isLocalAuthority()
    if tick.inFrame and tick.an == tick.n then return tick.a end
    local function check()
        local w = world()
        if not valid(w) then return false end
        if not ksl():IsServer(w) then return false end
        if ksl():IsDedicatedServer(w) then return false end
        -- o menu principal tambem e "servidor" (standalone), mas nao tem sessao
        if string.find(w:GetFullName(), "MainMenu", 1, true) then return false end
        return true
    end
    local a = check()
    tick.a, tick.an = a, tick.n
    return a
end

-- Controlador local pelo GameplayStatics (indice 0): UEHelpers.GetPlayerController faz FindAllOf e aceita
-- qualquer PlayerController, inclusive os HeadlessPlayerController dos soldados.
local function playerController()
    local w = world()
    if not valid(w) then return nil end
    local pc = gs():GetPlayerController(w, 0)
    if valid(pc) then return pc end
    return UEHelpers.GetPlayerController()
end

-- Alerta no HUD do jogo (canto superior esquerdo) + log.
local function notify(msg, secs)
    log(msg)
    pcall(function()
        local pc = playerController()
        if valid(pc) then pc:ClientAlertMessage("RTS: " .. msg, secs or 6.0) end
    end)
end

local function playerPawn()
    local pc = playerController()
    if not valid(pc) then return nil end
    local p = pc.Pawn
    if valid(p) then return p end
    return nil
end

local function gameMode() return gs():GetGameMode(world()) end

local function xform(x, y, z, yaw)
    local h = math.rad((yaw or 0) / 2)
    return { Translation = { X = x, Y = y, Z = z }, Rotation = { X = 0, Y = 0, Z = math.sin(h), W = math.cos(h) },
             Scale3D = { X = 1, Y = 1, Z = 1 } }
end

-- Chao sob (x, y): traco vertical no canal Visibility. nil se nao achar.
local function groundZ(x, y)
    local hit = {}
    local ok = ksl():LineTraceSingle(world(), { X = x, Y = y, Z = 20000 }, { X = x, Y = y, Z = -5000 }, 0, false, {}, 0, hit, true,
        { R = 0, G = 0, B = 0, A = 0 }, { R = 0, G = 0, B = 0, A = 0 }, 0)
    if ok and hit.ImpactPoint then return hit.ImpactPoint.Z end
    return nil
end

-- Posicao k de n numa linha de ate FORM_WIDTH soldados (fileiras para tras), girada para olhar na direcao dir.
CFG.FORM_WIDTH = 4
local function lineSlot(k, n, dir)
    local w = math.max(1, math.min(n, CFG.FORM_WIDTH))
    local row, col = math.floor((k - 1) / w), (k - 1) % w
    local inRow = math.min(w, n - row * w)                       -- ultima fileira pode ser incompleta: centraliza
    local fx, fy = -row * CFG.SLOT_SPACING, (col - (inRow - 1) / 2) * CFG.SLOT_SPACING
    local c, s = math.cos(dir), math.sin(dir)
    return { X = fx * c - fy * s, Y = fx * s + fy * c }
end

local function slotFor(i)
    -- coluna de 2: (0,0) (0,1) (1,0) (1,1) ... atras do ponto de destino
    local row = math.floor((i - 1) / 2)
    local col = (i - 1) % 2
    return { X = -row * CFG.SLOT_SPACING, Y = (col - 0.5) * CFG.SLOT_SPACING }
end

------------------------------------------------------------------------------------------------
-- Comandante (o jogador local). RestartPlayer sozinho nasce sobre o vazio e morre na queda;
-- RestartPlayerAtTransform em chao firme funciona sem stub de perfil. O fluxo normal de spawn
-- nunca desfaz o fade preto da camera, entao ele e zerado aqui.
------------------------------------------------------------------------------------------------
-- Chao firme para o comandante: veiculos estacionados do mapa (Warden/Colonial); por ultimo um PlayerStart.
CFG.ANCHOR_CLASSES = { "BPArmoredCarW_C", "BPArmoredCarC_C", "BPFlatbedTruck_C", "BPCrane_C", "BPHarvester_C", "PlayerStart", "BPSalvageField_C" }

local function spawnAnchor()
    for _, cn in ipairs(CFG.ANCHOR_CLASSES) do
        local all = FindAllOf(cn)
        if all and all[1] and valid(all[1]) then
            local v = all[1]:K2_GetActorLocation()
            return { X = v.X + 600, Y = v.Y, Z = v.Z }
        end
    end
    return nil
end

local function clearFade(pc)
    local cm = pc.PlayerCameraManager
    if valid(cm) then
        cm:StopCameraFade()
        cm:SetManualCameraFade(0.0, { R = 0, G = 0, B = 0, A = 1 }, false)
    end
end

local function ensureCommander()
    local pc = playerController()
    if not valid(pc) then return nil end
    local p = pc.Pawn
    -- o jogo pode ter criado o pawn sozinho sobre o vazio (ainda caindo, HP cheio): so aceita no chao
    if valid(p) and type(p.Health) == "number" and p.Health > 0 and (S.eye or p.CharacterMovement:IsMovingOnGround()) then return p end
    local a = spawnAnchor()
    if not a then log("sem ponto de spawn conhecido neste mapa"); return nil end
    local z = groundZ(a.X, a.Y) or a.Z
    if valid(p) then p:K2_DestroyActor() end
    gameMode():RestartPlayerAtTransform(pc, xform(a.X, a.Y, z + 150, 0))
    clearFade(pc)
    if valid(pc.Pawn) then
        local v = pc.Pawn:K2_GetActorLocation()
        log(string.format("comandante em (%.0f, %.0f, %.0f)", v.X, v.Y, v.Z))
    else
        log("falha ao criar o comandante")
    end
    return pc.Pawn
end

------------------------------------------------------------------------------------------------
-- Camera RTS: um CameraActor como view target, olhando para camFocus de cima.
------------------------------------------------------------------------------------------------
local rts = { active = false, cam = nil, focus = nil, dist = CFG.CAM_DIST_DEFAULT, edgePan = CFG.CAM_EDGE_PAN_DEFAULT, sel = 0 }

-- Oclusao: a cada CAM_OCCLUDE_EVERY s traca da camera ao foco (canal Camera) e esconde ate CAM_OCCLUDE_MAX
-- atores no caminho (telhado, estrutura, arvore; nunca a paisagem nem personagens); quem deixa de bloquear
-- reaparece. Em HomeRegionC a camera ficava atras de uma estrutura grande perto do inicio.
CFG.CAM_OCCLUDE_EVERY, CFG.CAM_OCCLUDE_MAX = 0.4, 4
S.occluders = {}  -- ator -> true (escondidos por nos)

local function unhideOccluders()
    for a in pairs(S.occluders) do if valid(a) then pcall(function() a:SetActorHiddenInGame(false) end) end end
    S.occluders = {}
end

local function occlusionTick()
    local t = gs():GetTimeSeconds(world())
    if t < (rts.nextOccT or 0) then return end
    rts.nextOccT = t + CFG.CAM_OCCLUDE_EVERY
    if not (valid(rts.cam) and rts.focus) then return end
    local from = rts.cam:K2_GetActorLocation()
    local to = { X = rts.focus.X, Y = rts.focus.Y, Z = rts.focus.Z + 100 }
    local found, ignore = {}, {}
    for _ = 1, CFG.CAM_OCCLUDE_MAX do
        local hit = {}
        if not ksl():LineTraceSingle(world(), from, to, 1, false, ignore, 0, hit, true, CFG.NOCOL, CFG.NOCOL, 0) then break end
        local a = hit.Actor and hit.Actor:get()
        if not (a and a:IsValid()) then break end
        local cls = a:GetClass():GetFName():ToString()
        if cls:find("Landscape") or cls:find("Character") or cls:find("Foliage") then break end  -- foliage: 1 ator = toda a vegetacao
        found[a] = true
        ignore[#ignore + 1] = a
    end
    for a in pairs(S.occluders) do
        if not found[a] and valid(a) then pcall(function() a:SetActorHiddenInGame(false) end) end
    end
    for a in pairs(found) do
        if not S.occluders[a] then pcall(function() a:SetActorHiddenInGame(true) end) end
    end
    S.occluders = found
end

local function camForward()
    local p = math.rad(CFG.CAM_PITCH)
    return { X = math.cos(p), Y = 0.0, Z = math.sin(p) }
end

local function newCamera()
    if valid(rts.cam) then rts.cam:K2_DestroyActor() end
    rts.cam = world():SpawnActor(StaticFindObject("/Script/Engine.CameraActor"), { X = 0, Y = 0, Z = 0 },
        { Pitch = 0, Yaw = 0, Roll = 0 })
    rts.cam:K2_SetActorRotation({ Pitch = CFG.CAM_PITCH, Yaw = 0, Roll = 0 }, false)
end

local function placeCamera()
    if not valid(rts.cam) or not rts.focus then return end
    local f0 = rts.focus
    if f0.X ~= f0.X or f0.Y ~= f0.Y or f0.Z ~= f0.Z then return end  -- foco NaN: ignora
    -- com a posicao atual NaN o SetActorLocation move por um delta NaN e a camera nunca volta (tela preta,
    -- visto apos focusOn(0/0)); recria a camera
    local cur = rts.cam:K2_GetActorLocation()
    if cur.X ~= cur.X or cur.Y ~= cur.Y or cur.Z ~= cur.Z then
        newCamera()
        if rts.active then playerController():SetViewTargetWithBlend(rts.cam, 0, 0, 0, false) end
    end
    local f = camForward()
    rts.cam:K2_SetActorLocation({ X = rts.focus.X - f.X * rts.dist, Y = rts.focus.Y - f.Y * rts.dist, Z = rts.focus.Z - f.Z * rts.dist },
        false, {}, false)
end

-- Base: onde o comandante estava ao ligar o RTS (deposito de municao, referencia de ondas e construcao).
-- Com o olho ligado o pawn do comandante passeia pelo mapa, entao quem precisa da base usa rts.base().
function rts.base()
    if rts.home then return rts.home end
    local p = playerPawn()
    return p and p:K2_GetActorLocation() or nil
end

-- Olho do comandante: a visao do jogo (PlayerLOSRasterComponent + AlwaysVisibleRadius 7 m) sai do pawn
-- do comandante, entao inimigos perto de soldados longe dele nao eram desenhados. No modo RTS o comandante
-- vira um olho invisivel, sem colisao nem gravidade, levado ao soldado mais perto do foco da camera (eyeTick).
CFG.EYE = true
CFG.EYE_EVERY = 0.2

function rts.eyeOn(pp)
    if not CFG.EYE or S.eye or not valid(pp) then return end
    local l = pp:K2_GetActorLocation()
    rts.home = { X = l.X, Y = l.Y, Z = l.Z }
    pcall(function() pp.CharacterMovement:SetMovementMode(0, 0) end)   -- MOVE_None: sem gravidade
    pp:SetActorEnableCollision(false)
    pp:SetActorHiddenInGame(true)
    S.outlineEye = { pawn = pp }
    S.eye = true
end

-- Visual do modo RTS (pedido: "linhas artefatuais e objetos desaparecendo" com a camera alta). O jogo foi feito
-- para a camera baixa do soldado: com o RTS ligado, objetos pequenos e sombras sao desenhados mais longe
-- (r.ViewDistanceScale / r.Shadow.DistanceScale) e o sombreamento de linha de visao (LOSPostProcess do
-- comandante, faixas escuras irradiando do "olho") fica desligado; os inimigos fora de visao continuam
-- escondidos pelo proprio jogo. Desligar o RTS restaura tudo.
CFG.GFX = { view = 3.0, shadow = 2.5, per = 2000.0 }
function rts.gfx(pc, on)
    rts.viewScale = on and CFG.GFX.view or nil
    ksl():ExecuteConsoleCommand(world(), "r.ViewDistanceScale " .. (on and CFG.GFX.view or 1), pc)
    ksl():ExecuteConsoleCommand(world(), "r.Shadow.DistanceScale " .. (on and CFG.GFX.shadow or 1), pc)
    local pp = playerPawn()
    if not valid(pp) then return end
    for _, v in ipairs(pp:K2_GetComponentsByClass(StaticFindObject("/Script/Engine.PostProcessComponent"))) do
        local c = v.get and v:get() or v
        if c:GetFName():ToString() == "LOSPostProcess" then c.BlendWeight = on and 0.0 or 1.0 end
    end
end

function rts.eyeOff()
    if not S.eye then return end
    S.eye = false
    S.outlineEye = nil
    local pp = playerPawn()
    if valid(pp) and rts.home then
        pp:K2_SetActorLocation({ X = rts.home.X, Y = rts.home.Y, Z = rts.home.Z + 20 }, false, {}, true)
        pp:SetActorEnableCollision(true)
        pcall(function() pp.CharacterMovement:SetMovementMode(1, 0) end)  -- MOVE_Walking
        pp:SetActorHiddenInGame(false)
    end
    rts.home = nil
end

local function centerOnCommander()
    local v = rts.base()
    if v then
        rts.focus = { X = v.X, Y = v.Y, Z = v.Z }
        placeCamera()
    end
end

local function enableRTS()
    if not isLocalAuthority() then log("modo RTS ignorado: sem autoridade local"); return end
    local pc = playerController()
    if not ensureCommander() then return end
    if not valid(rts.cam) then newCamera() end
    centerOnCommander()
    pc:SetViewTargetWithBlend(rts.cam, 0, 0, 0, false)
    pc.bShowMouseCursor = true
    clearFade(pc)
    -- sem o fluxo de perfil a UI pode ficar na tela de espera ("Foxhole Airborne"); ESimScreen::HUD = 0
    pc:ClientGotoScreen(0)
    -- no jogo o botao esquerdo e Fire e o direito Aim: sem isso, selecionar faz o comandante atacar
    pcall(function() pc.Pawn:DisableInput(pc) end)
    ksl():ExecuteConsoleCommand(world(), "r.MotionBlurQuality 0", pc)
    pcall(rts.gfx, pc, true)
    pcall(rts.eyeOn, pc.Pawn)
    rts.active = true
    rts.helpUntil = gs():GetTimeSeconds(world()) + CFG.HELP_SECS  -- now() ainda nao existe aqui
    log("modo RTS ligado")
end

-- Controle de tempo: pausa tatica (Pause / Ctrl+Espaco) e aceleracao 1x/2x/3x (Insert) pela dilatacao global
-- do tempo. Pausado (0,0001) o mundo e a logica do mod, que conta em tempo de jogo, param; a camera (tempo real),
-- a selecao e as ordens seguem, e a rota A* continua sendo calculada. Desligar o RTS volta ao normal.
CFG.SPEEDS = { 1.0, 2.0, 3.0 }
S.speedI, S.paused = 1, false
function rts.applyTime()
    gs():SetGlobalTimeDilation(world(), S.paused and 0.0001 or CFG.SPEEDS[S.speedI])
end

function rts.togglePause()
    if not isLocalAuthority() then return end
    S.paused = not S.paused
    pcall(rts.applyTime)
    notify(S.paused and "PAUSADO: mova a câmera e dê ordens (Pause ou Ctrl+Espaço continua)" or "continuando", 2.0)
end

function rts.cycleSpeed()
    if not isLocalAuthority() then return end
    S.speedI = S.speedI % #CFG.SPEEDS + 1
    if not S.paused then pcall(rts.applyTime) end
    notify(string.format("velocidade %.0fx", CFG.SPEEDS[S.speedI]), 2.0)
end

function rts.resetTime()
    if S.paused or S.speedI ~= 1 then
        S.paused, S.speedI = false, 1
        pcall(rts.applyTime)
    end
end

local function disableRTS()
    local pc = playerController()
    rts.active = false
    if valid(rts.outlineVolume) then rts.outlineVolume.BlendWeight = 0 end
    pcall(rts.resetTime)
    pcall(rts.gfx, pc, false)
    pcall(rts.eyeOff)
    unhideOccluders()
    if valid(pc) and valid(pc.Pawn) then
        pc:SetViewTargetWithBlend(pc.Pawn, 0, 0, 0, false)
        pcall(function() pc.Pawn:EnableInput(pc) end)
    end
    log("modo RTS desligado")
end

local function keyDown(pc, name) return pc:IsInputKeyDown({ KeyName = FName(name) }) end

local function cameraTick()
    if not rts.active or not rts.focus then return end
    local pc = playerController()
    if not valid(pc) or not valid(rts.cam) then return end
    -- os.clock e tempo de CPU; o delta do mundo e o tempo real do frame
    local rt = gs():GetRealTimeSeconds(world())  -- tempo real: pausa/aceleracao dilatam o delta do mundo
    local dt = math.min(math.max(rt - (rts.camRT or rt), 0.0), 0.1)
    rts.camRT = rt
    local mx, my, sx, sy = {}, {}, {}, {}  -- UE4SS grava os dois valores de saida na primeira tabela
    local dx, dy = 0, 0
    if rts.edgePan and pc:GetMousePosition(mx, my) then
        pc:GetViewportSize(sx, sy)
        local w, h = sx.SizeX or 0, sx.SizeY or 0
        if w > 0 and h > 0 then
            if mx.LocationX <= CFG.CAM_EDGE_PX then dy = dy - 1 elseif mx.LocationX >= w - CFG.CAM_EDGE_PX then dy = dy + 1 end
            if mx.LocationY <= CFG.CAM_EDGE_PX then dx = dx + 1 elseif mx.LocationY >= h - CFG.CAM_EDGE_PX then dx = dx - 1 end
        end
    end
    -- setas ou WASD (no RTS a entrada do comandante esta desligada, entao WASD fica livre)
    if keyDown(pc, "Up") or keyDown(pc, "W") then dx = dx + 1 end
    if keyDown(pc, "Down") or keyDown(pc, "S") then dx = dx - 1 end
    if keyDown(pc, "Left") or keyDown(pc, "A") then dy = dy - 1 end
    if keyDown(pc, "Right") or keyDown(pc, "D") then dy = dy + 1 end
    local ok, wheel = pcall(rts.wheel, pc, rt)
    if ok and wheel ~= 0 then  -- mesmo calculo de zoom() (declarada mais abaixo)
        local f = wheel > 0 and CFG.CAM_WHEEL_IN or 1 / CFG.CAM_WHEEL_IN
        rts.dist = math.max(CFG.CAM_DIST_MIN, math.min(CFG.CAM_DIST_MAX, rts.dist * f))
        placeCamera()
        pcall(rts.zoomGfx)
    end
    if dx ~= 0 or dy ~= 0 then
        local s = CFG.CAM_PAN_SPEED * rts.dist * dt
        rts.focus.X = rts.focus.X + dx * s
        rts.focus.Y = rts.focus.Y + dy * s
        placeCamera()
    end
    -- o jogo pode reabrir o fade (morte, respawn); mantem a tela limpa
    clearFade(pc)
    occlusionTick()
end

-- Roda do mouse: nao e tecla de VK (o RegisterKeyBind nao a ve). Le os eventos MouseScrollUp/Down do
-- PlayerInput (valem o quadro da rolagem), no maximo um passo de zoom a cada CAM_WHEEL_GAP s reais. O eixo
-- MouseWheelAxis NAO serve: guarda o ultimo valor ate a proxima amostra (medido: -1 parado, a camera fugia).
-- O log registra a primeira leitura (so da para conferir com a roda de verdade).
CFG.CAM_WHEEL_IN, CFG.CAM_WHEEL_GAP = 0.85, 0.06
function rts.wheel(pc, rt)
    if rt < (rts.wheelT or 0) then return 0 end
    local v = 0
    if pc:WasInputKeyJustPressed({ KeyName = FName("MouseScrollUp") }) then v = 1
    elseif pc:WasInputKeyJustPressed({ KeyName = FName("MouseScrollDown") }) then v = -1 end
    if v == 0 then return 0 end
    rts.wheelT = rt + CFG.CAM_WHEEL_GAP
    if not rts.wheelSeen then rts.wheelSeen = true; log("roda do mouse lida (" .. (v > 0 and "aproximar" or "afastar") .. ")") end
    return v
end

-- Distancia de desenho acompanha a altura (dist / GFX.per, no minimo GFX.view): de longe, o que o jogo
-- cortaria por distancia continua na tela. So reaplica quando muda meio ponto.
function rts.zoomGfx()
    if not rts.viewScale then return end
    local v = math.max(CFG.GFX.view, rts.dist / CFG.GFX.per)
    if math.abs(v - rts.viewScale) < 0.5 then return end
    rts.viewScale = v
    ksl():ExecuteConsoleCommand(world(), string.format("r.ViewDistanceScale %.1f", v), playerController())
end

local function zoom(factor)
    rts.dist = math.max(CFG.CAM_DIST_MIN, math.min(CFG.CAM_DIST_MAX, rts.dist * factor))
    placeCamera()
    pcall(rts.zoomGfx)
end

local function focusOn(x, y, z)
    if not x or not y or x ~= x or y ~= y then return end  -- NaN
    rts.focus = { X = x, Y = y, Z = z or groundZ(x, y) or 0.0 }
    placeCamera()
end

-- Alertas de frente: cada aviso com lugar (ponto sob ataque, ponto perdido, onda chegando, baixa) entra numa
-- fila curta; Espaco leva a camera ao mais novo e, apertado de novo em ALERTS.chain s, aos anteriores.
-- O mesmo tipo no mesmo lugar so avisa de novo depois de ALERTS.quiet s.
CFG.ALERTS = { keep = 8, quiet = 20.0, chain = 4.0, near = 1500.0 }
S.alerts, S.alertI, S.alertNew = {}, 0, 0
function rts.alert(kind, where, msg)
    if not where then notify(msg, 4.0); return end
    local rt = gs():GetRealTimeSeconds(world())
    for _, a in ipairs(S.alerts) do
        if a.kind == kind and (a.X - where.X) ^ 2 + (a.Y - where.Y) ^ 2 < CFG.ALERTS.near ^ 2 and rt - a.t < CFG.ALERTS.quiet then
            a.t = rt
            return
        end
    end
    table.insert(S.alerts, 1, { kind = kind, X = where.X, Y = where.Y, Z = where.Z, t = rt, msg = msg })
    if #S.alerts > CFG.ALERTS.keep then table.remove(S.alerts) end
    S.alertNew = math.min(S.alertNew + 1, CFG.ALERTS.keep)
    notify(msg .. " (Espaço: ver)", 4.0)
end

function rts.jumpAlert()
    if #S.alerts == 0 then notify("nenhum alerta", 2.0); return end
    local rt = gs():GetRealTimeSeconds(world())
    if rt - (S.alertJumpT or -1e9) > CFG.ALERTS.chain then S.alertI = 0 end
    S.alertJumpT = rt
    S.alertI = S.alertI % #S.alerts + 1
    S.alertNew = 0
    local a = S.alerts[S.alertI]
    focusOn(a.X, a.Y, a.Z)
    notify(string.format("[%d/%d] %s (há %.0f s)", S.alertI, #S.alerts, a.msg, rt - a.t), 3.0)
end

------------------------------------------------------------------------------------------------
-- Esquadrao. Soldado = AHeadlessPlayerController (o bot de teste de carga do jogo) sem LocalPlayer:
-- tem PlayerState, o que evita que o jogo recolha o personagem (pawns de AIController sao
-- desapossados e estacionados em (0,0,0) apos ~20 s). bIsLocalPlayerController=true faz o
-- CharacterMovement simular o input no servidor; frenagem zero mantem a velocidade entre pulsos.
------------------------------------------------------------------------------------------------
-- EFactionId: Colonials = 0, Wardens = 1. O jogador comanda Wardens (mapa HomeRegionW).
CFG.FRIENDLY_TEAM, CFG.ENEMY_TEAM = 1, 0

local function setTeam(m, team)
    m.team = team
    local pawn, hpc = m.pawn, m.hpc
    pcall(function() if valid(hpc.PlayerState) then hpc.PlayerState.TeamId = team end end)
    pcall(function() pawn.TeamId = team end)
    pcall(function() pawn:OnRep_TeamIdNotify() end)
    pcall(function() pawn:BPSetTeamVisuals(team) end)
end

-- Classes de soldado do modelo offline: a arma e nossa (perfil de tiro abaixo), a malha e a do jogo,
-- posta no componente WeaponMesh do personagem e presa ao socket S_GenericGun do corpo (no hand_r ela
-- ficava apontada para tras e o corpo de maos vazias). Nada passa pelo inventario nem por RPC de servidor.
-- grip: EEquippedWeaponGripType que a animacao usa (Rifle 1, Pistol 2, Sniper 4, HeavyMachinegun 5; com
-- LightMachineGun 24 a MG ficava atravessada).
-- hit = chance a queima-roupa (cai ate a metade no alcance maximo); interval = s entre tiros.
CFG.WEAPONS = {
    -- ammo: tiros carregados (so os nossos contam; ver fire e resupplyTick)
    rifle  = { name = "fuzileiro", cost = 20, range = 2200.0, interval = 1.6, hit = 0.60, dmg = 34.0, supp = 0.12, pitch = 1.0, ammo = 40,
               grip = 1, meshW = "/Game/Meshes/Weapons/SK_RifleW.SK_RifleW", meshC = "/Game/Meshes/Weapons/SK_RifleCarbineC.SK_RifleCarbineC" },
    mg     = { name = "metralhador", cost = 35, range = 2600.0, interval = 0.35, hit = 0.30, dmg = 14.0, supp = 0.20, pitch = 1.2, speed = 0.75, ammo = 150,
               grip = 5, meshW = "/Game/Meshes/Weapons/SK_MGW.SK_MGW", meshC = "/Game/Meshes/Weapons/SK_MGC.SK_MGC" },
    sniper = { name = "atirador", cost = 45, range = 4000.0, interval = 3.5, hit = 0.85, dmg = 70.0, supp = 0.30, pitch = 0.8, ammo = 15,
               grip = 4, meshW = "/Game/Meshes/Weapons/SniperRifle.SniperRifle", meshC = "/Game/Meshes/Weapons/SK_SniperRifleC.SK_SniperRifleC" },
    -- medico: pistola fraca; cura aliados feridos por perto (medicTick)
    medic  = { name = "medico", cost = 30, range = 1500.0, interval = 2.0, hit = 0.40, dmg = 20.0, supp = 0.05, pitch = 1.3, ammo = 24,
               grip = 2, meshW = "/Game/Meshes/Weapons/PistolBasic.PistolBasic", meshC = "/Game/Meshes/Weapons/PistolBasic.PistolBasic" },
    -- oficial: pistola; aura (OFFICER) melhora precisao e recuperacao da supressao de quem esta perto
    officer = { name = "oficial", cost = 40, range = 1800.0, interval = 1.8, hit = 0.50, dmg = 25.0, supp = 0.06, pitch = 1.1, ammo = 24,
               grip = 2, meshW = "/Game/Meshes/Weapons/PistolBasic.PistolBasic", meshC = "/Game/Meshes/Weapons/PistolBasic.PistolBasic" },
}
-- Som do tiro por classe e lado (sons do proprio jogo: fuzil Warden x carabina Colonial, MG, atirador, pistola).
-- Sem o som carregado, cai no FX.shot com o tom da arma.
local A = "/Game/Audio/SFX/Weapons/"
CFG.WEAPONS.rifle.sndW, CFG.WEAPONS.rifle.sndC = A .. "RifleLongW/RifleLongW_Cue.RifleLongW_Cue", A .. "CarbineC/CarbineCShot_Cue.CarbineCShot_Cue"
CFG.WEAPONS.mg.sndW, CFG.WEAPONS.mg.sndC = A .. "MGW/MGW-RFShot_Cue.MGW-RFShot_Cue", A .. "MGC/MGC-RFShot_Cue.MGC-RFShot_Cue"
CFG.WEAPONS.sniper.sndW, CFG.WEAPONS.sniper.sndC = A .. "Sniper/SniperShot_Cue.SniperShot_Cue", A .. "SniperC/SniperShotC_Cue.SniperShotC_Cue"
for _, r in ipairs({ "medic", "officer" }) do
    CFG.WEAPONS[r].sndW = A .. "PistolLightW/PistolLIghtWShot_Cue.PistolLIghtWShot_Cue"
    CFG.WEAPONS[r].sndC = CFG.WEAPONS[r].sndW
end
A = nil

-- Oficial: aliados a radius cm (ele incluso) acertam acc a mais e perdem a supressao decay vezes mais rapido.
-- Nosso lado: no maximo 1 vivo (Ctrl+0). Inimigo: a partida da onda wave, o 1o de cada onda e oficial;
-- abate-lo rende bounty de mao de obra.
CFG.OFFICER = { radius = 1000.0, acc = 0.15, decay = 1.8, wave = 3, bounty = 20, every = 0.5, shock = 0.5 }

-- Composicao por posicao no grupo: 3o e 7o metralhadores, 4o e 12o medicos, 6o atirador, o resto fuzileiros.
local function roleFor(i)
    if i % 4 == 3 then return "mg" end
    if i % 8 == 4 then return "medic" end
    if i % 6 == 0 then return "sniper" end
    return "rifle"
end

local function weapon(m) return CFG.WEAPONS[m.role or "rifle"] end
-- Municao dos nossos (fracao 0..1 do carregamento cheio; nil = cheio). Inimigos chegam com o que precisam.
local function ammoFrac(m) return m.ammo and m.ammo / weapon(m).ammo or 1.0 end

-- "3 fuzileiro, 1 metralhador" para HUD/log.
-- Veterania: a cada VET_KILLS abates o soldado sobe um nivel (ate VET_MAX); +VET_ACC de precisao por nivel.
-- Vale para os dois lados (inimigo que sobrevive a varias ondas nao existe hoje, mas o veterano de onda sim).
CFG.VET_KILLS, CFG.VET_MAX, CFG.VET_ACC = 2, 3, 0.10

local function rank(m) return math.min(CFG.VET_MAX, math.floor((m.kills or 0) / CFG.VET_KILLS)) end

local function credit(m)
    local before = rank(m)
    m.kills = (m.kills or 0) + 1
    if rank(m) > before and m.team == CFG.FRIENDLY_TEAM then
        notify(string.format("%s promovido a veterano %d (%d abates)", CFG.WEAPONS[m.role or "rifle"].name, rank(m), m.kills), 3.0)
    end
end

local function veterans(list, onlySel)
    local n = 0
    for _, m in ipairs(list) do if rank(m) > 0 and (not onlySel or m.sel) then n = n + 1 end end
    return n
end

local function composition(list)
    local n = {}
    for _, m in ipairs(list) do n[m.role or "rifle"] = (n[m.role or "rifle"] or 0) + 1 end
    local parts = {}
    for _, r in ipairs({ "rifle", "mg", "sniper", "medic" }) do
        if n[r] then parts[#parts + 1] = n[r] .. " " .. CFG.WEAPONS[r].name end
    end
    return table.concat(parts, ", ")
end

local function findAsset(path)
    local o = StaticFindObject(path)
    if not (o and o:IsValid()) then
        pcall(function() LoadAsset(path) end)
        o = StaticFindObject(path)
    end
    if o and o:IsValid() then return o end
    return nil
end

local function namedComponent(actor, name)
    for _, v in ipairs(actor:K2_GetComponentsByClass(StaticFindObject("/Script/Engine.SceneComponent"))) do
        local c = v.get and v:get() or v
        if c:GetFName():ToString() == name then return c end
    end
    return nil
end

-- Animacao de arma e tiro. A empunhadura, o aim offset e a mira do AnimInstance (CharacterAnimInstance)
-- sao recalculados pelo update nativo a cada quadro a partir do item equipado e do controle local, que
-- nossos soldados nao tem; mas o BlueprintUpdateAnimation do ABP roda depois do nativo, entao um hook nele
-- grava os nossos valores: grip da classe, aim offset zero (o corpo ja gira para o alvo), mira liberada
-- (canEnter*Scoping) quando o soldado esta parado e engajado, e ActivityState Firing por um instante a
-- cada tiro (coice). bIsInScopeMode no pawn liga a pose de fuzil no ombro.
CFG.ANIM_ABP = "/Game/Animation/Character/ABP_Male.ABP_Male_C:BlueprintUpdateAnimation"
CFG.AIM_HOLD = 1.5       -- s mirando depois do ultimo tiro/tentativa
CFG.FIRE_ANIM = 0.2      -- s de ActivityState Firing por tiro
local anim = { units = {}, hooked = false }

function anim.onUpdate(ctx)
    local a = ctx:get()
    local m = anim.units[a:GetAddress()]
    if not m then return end
    local w = CFG.WEAPONS[m.role or "rifle"]
    a.EquippedWeaponGripType = w.grip or 1
    a.AimOffsetYaw, a.AimOffsetPitch = 0.0, 0.0
    local c = os.clock()
    local aiming = c < (m.aimUntil or 0) and m.stillSince ~= nil
    m.aiming = aiming  -- bIsInScopeMode do pawn vai no postureTick: no hook so se toca no AnimInstance vivo
    if aiming then a.canEnterStandScoping = true; a.canEnterCrouchScoping = true end
    -- postura (ESimCharacterStance): agachado parado na trincheira ou suprimido; curvado correndo ao recuar
    local stance = 0
    if m.retreat and m.stillSince == nil then stance = 3
    elseif m.stillSince ~= nil and m.crouch then stance = 1 end
    a.CharacterStance = stance
    a.bStanceIsCrouched = stance == 1
    -- acao do momento (ECharacterActivityState): arremesso 6, primeiros socorros 20, tiro 3
    if c < (m.throwAnimUntil or 0) then a.ActivityState = 6
    elseif c < (m.healAnimUntil or 0) then a.ActivityState = 20
    elseif c < (m.fireAnimUntil or 0) then a.ActivityState = 3 end
end

-- Registra o soldado no hook (e liga o hook na primeira vez, quando o ABP ja esta carregado).
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

function anim.untrack(m)
    if m.animAddr and anim.units[m.animAddr] == m then anim.units[m.animAddr] = nil end
    m.animAddr = nil
end

local function armWith(m, role)
    m.role = role
    if role == "officer" then pcall(rts.officerFlag, m) end
    local w = CFG.WEAPONS[role]
    pcall(function()
        local wm = namedComponent(m.pawn, "WeaponMesh")
        local mesh = findAsset(m.team == CFG.ENEMY_TEAM and w.meshC or w.meshW)
        if wm and mesh then
            wm:SetSkeletalMesh(mesh, true)
            wm:K2_AttachToComponent(m.pawn.Mesh, FName("S_GenericGun"), 2, 2, 2, false)  -- SnapToTarget
            wm:SetHiddenInGame(false, false)
            wm:SetVisibility(true, false)
            m.wmesh = wm
        end
    end)
    pcall(anim.track, m)
    if w.speed then
        pcall(function() local cm = m.pawn.CharacterMovement; cm.MaxWalkSpeed = cm.MaxWalkSpeed * w.speed end)
    end
end

-- HeadlessPlayerController nao some com K2_DestroyActor (medido: apos ~150 mortes havia 180 controladores
-- validos, cada um com PlayerState, PlayerCameraManager e CameraActor; o quadro do jogo foi de ~30 para
-- ~350 ms com 12 soldados; um StaticMeshActor destruido some na coleta, o controlador nao). Por isso o
-- controlador do soldado morto (ou removido) larga o corpo e volta a um pool; spawnSoldier o reaproveita.
S.hpcPool = {}
S.poolStats = { reused = 0, created = 0 }

local function releaseController(hpc)
    if not valid(hpc) then return end
    pcall(function() hpc:UnPossess() end)
    S.hpcPool[#S.hpcPool + 1] = hpc
end

local function spawnSoldier(x, y, z, slot, team, role)
    local hpc = nil
    while not hpc and #S.hpcPool > 0 do
        local c = table.remove(S.hpcPool)
        if valid(c) then hpc = c end
    end
    if hpc then
        S.poolStats.reused = S.poolStats.reused + 1
        hpc.bIsLocalPlayerController = false  -- religada depois da posse, como num controlador novo
    else
        hpc = world():SpawnActor(StaticFindObject("/Script/War.HeadlessPlayerController"), { X = x, Y = y, Z = z },
            { Pitch = 0, Yaw = 0, Roll = 0 })
        if not valid(hpc) then return nil end
        S.poolStats.created = S.poolStats.created + 1
    end
    if not valid(hpc.PlayerInput) then
        hpc.PlayerInput = StaticConstructObject(StaticFindObject("/Script/Engine.PlayerInput"), hpc)
    end
    gameMode():RestartPlayerAtTransform(hpc, xform(x, y, z + 60, 0))
    local pawn = hpc.Pawn
    if not valid(pawn) then releaseController(hpc); return nil end
    -- depois da posse: com a flag ligada antes, o pawn nasce com MovementMode = None
    hpc.bIsLocalPlayerController = true
    local m = pawn.CharacterMovement
    local defaults = { friction = m.GroundFriction, brake = m.BrakingDecelerationWalking, accel = m.MaxAcceleration }
    m:SetMovementMode(1, 0)  -- MOVE_Walking
    m.BrakingDecelerationWalking = 0.0
    m.GroundFriction = 0.0
    m.MaxAcceleration = 20000.0
    local u = { hpc = hpc, pawn = pawn, slot = slot, target = nil, nextShot = 0, moveDefaults = defaults }
    setTeam(u, team or CFG.FRIENDLY_TEAM)
    armWith(u, role or "rifle")
    return u
end

local syncMarkers  -- definida junto da selecao; spawnSquad ja precisa dela
local logOnce      -- definida perto do loop por frame; issueMove ja precisa dela

-- n soldados (padrao SQUAD_SIZE, ate SQUAD_MAX no total) ao lado do primeiro soldado vivo ou do comandante,
-- ou em at (ponto no chao). role fixa a classe de todos; sem ela vale a composicao de roleFor.
-- Retorna quantos nasceram.
local function spawnSquad(n, role, at)
    if not isLocalAuthority() then log("ignorado: sem autoridade local (precisa de sessao ?listen)"); return 0 end
    local p = ensureCommander()
    if not p then return 0 end
    local ref = p
    if squad[1] and valid(squad[1].pawn) and (squad[1].pawn.Health or 0) > 0 then ref = squad[1].pawn end
    local base = at and { X = at.X - 300.0, Y = at.Y - 300.0, Z = at.Z } or ref:K2_GetActorLocation()
    local first = #squad
    local allSel = true  -- novos soldados entram selecionados se todos ja estavam (inclui esquadrao vazio)
    for _, o in ipairs(squad) do if not o.sel then allSel = false end end
    n = math.min(n or CFG.SQUAD_SIZE, CFG.SQUAD_MAX - first)
    if n <= 0 then notify("esquadrao no maximo (" .. CFG.SQUAD_MAX .. ")", 3.0); return 0 end
    for i = 1, n do
        local s = slotFor(first + i)
        local x, y = base.X + 300.0 + s.X, base.Y + 300.0 + s.Y
        local z = groundZ(x, y) or base.Z
        local m = spawnSoldier(x, y, z + 90, s, CFG.FRIENDLY_TEAM, role or roleFor(first + i))
        if m then
            m.group = (#squad % 2) + 1
            m.sel = allSel
            table.insert(squad, m)
        else
            log("falha ao criar soldado " .. (first + i))
        end
    end
    pcall(syncMarkers)
    notify("esquadrao: " .. #squad .. " soldados (" .. composition(squad) .. ")")
    return #squad - first
end

local function cursorPoint()
    local pc = playerController()
    if not valid(pc) then return nil end
    local hit = {}
    if pc:GetHitResultUnderCursorByChannel(0, false, hit) and hit.ImpactPoint then
        return { X = hit.ImpactPoint.X, Y = hit.ImpactPoint.Y, Z = hit.ImpactPoint.Z }
    end
    return nil
end

-- Selecao por soldado (m.sel). Teclas 1-5: grupo (cada soldado nasce no 1 ou no 2, alternado; Alt+1-5
-- muda os selecionados de grupo); 0: todos. Clique esquerdo: soldado sob o cursor; arrastar: caixa no chao (a camera olha para +X,
-- entao o retangulo X/Y do mundo acompanha o da tela, salvo o trapezio da perspectiva). Shift soma.
-- Selecionados ganham um disco laranja (cilindro da engine achatado + material de fantasma de construcao).
CFG.MARKER_MESH = "/Engine/BasicShapes/Cylinder.Cylinder"
CFG.MARKER_MAT = "/Game/Blueprints/Structures/Facilities/Materials/BuildGhostHighlight.BuildGhostHighlight"
CFG.PICK_RADIUS = 150.0   -- cm do clique ate o soldado
CFG.DRAG_MIN = 120.0      -- cm no chao entre apertar e soltar; abaixo disso e clique

local function selected(m) return m.sel == true end

local function countSelected()
    local n = 0
    for _, m in ipairs(squad) do if m.sel then n = n + 1 end end
    return n
end

local function destroyMarker(m)
    pcall(anim.untrack, m)
    pcall(rts.clearOutline, m)
    if m.icon and valid(m.icon) then pcall(function() m.icon:K2_DestroyActor() end) end
    m.icon = nil
    if m.flag and valid(m.flag) then pcall(function() m.flag:K2_DestroyActor() end) end
    if m.hpBar and valid(m.hpBar) then pcall(function() m.hpBar:K2_DestroyActor() end) end
    m.flag, m.hpBar = nil, nil
    if m.marker and valid(m.marker) then m.marker:K2_DestroyActor() end
    if m.ammoIcon and valid(m.ammoIcon) then m.ammoIcon:K2_DestroyActor() end
    m.marker, m.ammoIcon = nil, nil
end

local function showMarker(m, on)
    rts.setOutline(m, on)
end

-- Marcadores so com o modo RTS ligado; o loop por frame chama de novo quando rts.active muda.
function syncMarkers()
    rts.markersOn = rts.active
    for _, m in ipairs(squad) do
        if valid(m.pawn) and (m.pawn.Health or 0) > 0 then pcall(showMarker, m, rts.active and m.sel) end
    end
end

-- Toque duplo (GROUP_TAP s reais) no mesmo grupo leva a camera ao centro dele.
CFG.GROUP_TAP = 0.45
local function selectGroup(g)
    local rt = gs():GetRealTimeSeconds(world())
    local again = rts.sel == g and rt - (rts.selT or -1e9) <= CFG.GROUP_TAP
    rts.sel, rts.selT = g, rt
    local sx, sy, n = 0, 0, 0
    for _, m in ipairs(squad) do
        m.sel = (g == 0 or m.group == g)
        if m.sel and valid(m.pawn) and (m.pawn.Health or 0) > 0 then
            local l = m.pawn:K2_GetActorLocation()
            sx, sy, n = sx + l.X, sy + l.Y, n + 1
        end
    end
    syncMarkers()
    if again and n > 0 then focusOn(sx / n, sy / n); return end
    notify(g == 0 and string.format("selecionado: todos (%d)", n) or string.format("selecionado: grupo %d (%d)", g, n), 3.0)
end

-- Alt+1..5: os selecionados passam para o grupo g (um grupo por frente).
function rts.assignGroup(g)
    local n = 0
    for _, m in ipairs(squad) do
        if m.sel then m.group = g; n = n + 1 end
    end
    rts.sel = g
    notify(n > 0 and string.format("%d soldados no grupo %d", n, g) or "selecione soldados antes", 2.5)
end

-- Clique: o soldado vivo mais perto de p (ate PICK_RADIUS). Sem add, troca a selecao (clique no vazio
-- limpa); com add (Shift), alterna so esse soldado. Retorna o soldado ou nil.
local function selectAt(p, add)
    local best, bd = nil, CFG.PICK_RADIUS
    for _, m in ipairs(squad) do
        if valid(m.pawn) and (m.pawn.Health or 0) > 0 then
            local l = m.pawn:K2_GetActorLocation()
            local d = math.sqrt((l.X - p.X) ^ 2 + (l.Y - p.Y) ^ 2)
            if d < bd then best, bd = m, d end
        end
    end
    if add then
        if best then best.sel = not best.sel end
    else
        for _, m in ipairs(squad) do m.sel = (m == best) end
    end
    syncMarkers()
    return best
end

-- Caixa no chao entre a e b. Sem add, quem fica fora sai da selecao. Retorna quantos ficaram dentro.
local function selectBox(a, b, add)
    local x0, x1 = math.min(a.X, b.X) - 50, math.max(a.X, b.X) + 50
    local y0, y1 = math.min(a.Y, b.Y) - 50, math.max(a.Y, b.Y) + 50
    local n = 0
    for _, m in ipairs(squad) do
        local inside = false
        if valid(m.pawn) and (m.pawn.Health or 0) > 0 then
            local l = m.pawn:K2_GetActorLocation()
            inside = l.X >= x0 and l.X <= x1 and l.Y >= y0 and l.Y <= y1
        end
        if inside then m.sel = true; n = n + 1 elseif not add then m.sel = false end
    end
    syncMarkers()
    notify(string.format("selecionados: %d", countSelected()), 2.0)
    return n
end

-- Botao esquerdo por sondagem (a caixa precisa do soltar; RegisterKeyBind so ve o apertar).
local mouse = { down = false, from = nil, add = false }
local function mouseTick()
    if not rts.active then mouse.down, mouse.from = false, nil; return end
    local pc = playerController()
    if not valid(pc) then return end
    local down = keyDown(pc, "LeftMouseButton")
    if down and not mouse.down then
        mouse.from = cursorPoint()
        mouse.add = keyDown(pc, "LeftShift") or keyDown(pc, "RightShift")
    elseif not down and mouse.down and mouse.from then
        local to = cursorPoint()
        if to then
            local d = math.sqrt((to.X - mouse.from.X) ^ 2 + (to.Y - mouse.from.Y) ^ 2)
            if d < CFG.DRAG_MIN then selectAt(to, mouse.add) else selectBox(mouse.from, to, mouse.add) end
        end
        mouse.from = nil
    end
    mouse.down = down
end

-- Caminho. Os mapas nao tem NavMesh: com a linha reta livre (traco na altura do joelho) vai direto; senao
-- A* numa grade de PATH_CELL cm em volta de origem e destino, cada aresta testada com traco no joelho e
-- desnivel <= PATH_STEP, ignorando os soldados. Depois encurta (pula waypoints com linha reta livre). Sem
-- caminho dentro do limite de nos, cai na linha reta com o desvio de moveToward.
CFG.PATH_CELL, CFG.PATH_MARGIN, CFG.PATH_MAX_NODES, CFG.PATH_STEP, CFG.PATH_KNEE = 150.0, 2000.0, 2500, 60.0, 40.0
-- ~1 ms por no expandido (8 varreduras): o A* roda em fatias de PATH_NODES_PER_TICK nos por frame.
CFG.PATH_NODES_PER_TICK = 40   -- teto de nos por quadro
CFG.PATH_MS = 4.0              -- orcamento de tempo do A* por quadro (40 nos custavam ~70 ms: o jogo caia a ~6 FPS)
CFG.PATH_CHUNK = 4             -- nos por chamada de planStep dentro do orcamento
-- Folga do corpo: arestas da grade usam esfera (raio PATH_BODY a PATH_BODY_Z do chao); so as que tocam a
-- origem ou o destino usam linha, senao soldado encostado num muro ficaria sem caminho. Medido: com linha,
-- o trecho rente a barreira passava e o soldado ficava preso na quina.
CFG.PATH_BODY, CFG.PATH_BODY_Z = 32.0, 75.0
CFG.NOCOL = { R = 0, G = 0, B = 0, A = 0 }
-- Canal de movimento: TraceTypeQuery2 (Camera). O Visibility (0) atravessa veiculos; o Camera acerta
-- caminhoes (BoxComponent), motos, predios e as barreiras, e ignora os volumes BPNoBuild_C (medido).
CFG.MOVE_CHANNEL = 1

local function kneeClear(a, b, ignore, thin, nav)
    local hit = {}
    if thin and not nav then
        return not ksl():LineTraceSingle(world(), { X = a.X, Y = a.Y, Z = a.Z + CFG.PATH_KNEE }, { X = b.X, Y = b.Y, Z = b.Z + CFG.PATH_KNEE },
            CFG.MOVE_CHANNEL, false, ignore, 0, hit, true, CFG.NOCOL, CFG.NOCOL, 0)
    end
    local body, h = nav and nav.body or CFG.PATH_BODY, nav and nav.bodyZ or CFG.PATH_BODY_Z
    if ksl():SphereTraceSingle(world(), { X = a.X, Y = a.Y, Z = a.Z + h }, { X = b.X, Y = b.Y, Z = b.Z + h },
        body, CFG.MOVE_CHANNEL, false, ignore, 0, hit, true, CFG.NOCOL, CFG.NOCOL, 0) then return false end
    if nav then
        local n = math.max(1, math.ceil(math.sqrt((a.X - b.X)^2 + (a.Y - b.Y)^2) / nav.cell))
        local prev = a.Z
        for i = 1, n do
            local f = i / n
            local z = groundZ(a.X + (b.X - a.X) * f, a.Y + (b.Y - a.Y) * f)
            if not z or math.abs(z - prev) > nav.step or math.abs(z - (a.Z + (b.Z - a.Z) * f)) > nav.step then return false end
            prev = z
        end
    end
    return true
end

local function heapPush(h, node, f)
    h[#h + 1] = { node = node, f = f }
    local i = #h
    while i > 1 do
        local pi = i // 2
        if h[pi].f <= h[i].f then break end
        h[pi], h[i] = h[i], h[pi]
        i = pi
    end
end

local function heapPop(h)
    local top = h[1]
    local last = table.remove(h)
    if #h > 0 then
        h[1] = last
        local i = 1
        while true do
            local l, r, m = 2 * i, 2 * i + 1, i
            if l <= #h and h[l].f < h[m].f then m = l end
            if r <= #h and h[r].f < h[m].f then m = r end
            if m == i then break end
            h[m], h[i] = h[i], h[m]
            i = m
        end
    end
    return top and top.node
end

-- A* em estado explicito (o UE4SS nao aceita chamar UFunctions de dentro de corrotina: "lua state has no
-- instance"). planStart cria o trabalho; planStep expande ate budget nos e devolve a rota quando termina.
-- from/to: pontos no chao. Rota: waypoints no chao terminando em to (ou so { to } se nao achar).
local function planStart(from, to, ignore, nav)
    local job = { from = from, to = to, ignore = ignore, expanded = 0, nav = nav }
    if (not nav or (from.X - to.X)^2 + (from.Y - to.Y)^2 <= (nav.cell * 2)^2) and kneeClear(from, to, ignore, true, nav) and kneeClear(from, to, ignore, false, nav) then
        job.result = { to }
        return job
    end
    local cell, margin = nav and nav.cell or CFG.PATH_CELL, nav and nav.margin or CFG.PATH_MARGIN
    job.cell = cell
    job.x0 = math.min(from.X, to.X) - margin
    job.y0 = math.min(from.Y, to.Y) - margin
    job.ni = math.floor((math.max(from.X, to.X) + margin - job.x0) / cell)
    job.nj = math.floor((math.max(from.Y, to.Y) + margin - job.y0) / cell)
    local function near(pt) return math.floor((pt.X - job.x0) / cell + 0.5), math.floor((pt.Y - job.y0) / cell + 0.5) end
    local si, sj = near(from)
    job.gi, job.gj = near(to)
    job.start = { X = from.X, Y = from.Y, Z = from.Z, i = si, j = sj, k = si * 100000 + sj }
    job.pts = { [job.start.k] = job.start }
    job.g, job.came, job.closed, job.open = { [job.start.k] = 0 }, {}, {}, {}
    heapPush(job.open, job.start, math.sqrt((from.X - to.X) ^ 2 + (from.Y - to.Y) ^ 2))
    return job
end

local function planCell(job, i, j)
    if i < 0 or j < 0 or i > job.ni or j > job.nj then return nil end
    local k = i * 100000 + j
    local c = job.pts[k]
    if c == nil then
        local x, y = job.x0 + i * job.cell, job.y0 + j * job.cell
        local z = groundZ(x, y)
        c = (z and math.abs(z - job.from.Z) < (job.nav and job.nav.height or 400)) and { X = x, Y = y, Z = z, i = i, j = j, k = k } or false
        job.pts[k] = c
    end
    return c or nil
end

local function planFinish(job, goal)
    local to, start, ignore = job.to, job.start, job.ignore
    if not goal then job.result, job.failed = job.nav and {} or { to }, true; return end
    local chain = {}
    local c = goal
    while c and c ~= start do table.insert(chain, 1, c); c = job.came[c.k] end
    if kneeClear(chain[#chain] or start, to, ignore, true, job.nav) then chain[#chain + 1] = to
    elseif job.nav then job.result, job.failed = {}, true; return end
    -- encurta: do ponto atual, pula ate o waypoint mais distante com linha reta livre
    local out, anchor, i = {}, start, 1
    while i <= #chain do
        local j = #chain
        while j > i and not kneeClear(anchor, chain[j], ignore, false, job.nav) do j = j - 1 end
        out[#out + 1] = { X = chain[j].X, Y = chain[j].Y, Z = chain[j].Z }
        anchor, i = chain[j], j + 1
    end
    job.result = out
end

-- Retorna a rota quando pronta (e nil enquanto ainda ha nos a expandir).
local function planStep(job, budget)
    if job.result then return job.result end
    local to, ignore = job.to, job.ignore
    local function h(c) return math.sqrt((c.X - to.X) ^ 2 + (c.Y - to.Y) ^ 2) end
    local done = 0
    while #job.open > 0 and job.expanded < (job.nav and job.nav.maxNodes or CFG.PATH_MAX_NODES) and done < budget do
        local c = heapPop(job.open)
        if not job.closed[c.k] then
            job.closed[c.k] = true
            job.expanded, done = job.expanded + 1, done + 1
            -- chegada: celula do destino ou vizinha com linha livre ate ele (destino rente a muro fica sem
            -- celula alcancavel com a folga da esfera)
            if (c.i == job.gi and c.j == job.gj)
                or (math.abs(c.i - job.gi) <= 1 and math.abs(c.j - job.gj) <= 1 and kneeClear(c, to, ignore, true, job.nav)) then
                planFinish(job, c)
                return job.result
            end
            for di = -1, 1 do
                for dj = -1, 1 do
                    if di ~= 0 or dj ~= 0 then
                        local n = planCell(job, c.i + di, c.j + dj)
                        if n and not job.closed[n.k] then
                            local step = (di ~= 0 and dj ~= 0) and job.cell * 1.4142 or job.cell
                            local ng = job.g[c.k] + step
                            if (job.g[n.k] == nil or ng < job.g[n.k]) and math.abs(n.Z - c.Z) <= (job.nav and job.nav.step or CFG.PATH_STEP) * step / job.cell
                                and kneeClear(c, n, ignore, c == job.start, job.nav) then
                                job.g[n.k], job.came[n.k] = ng, c
                                heapPush(job.open, n, ng + h(n))
                            end
                        end
                    end
                end
            end
        end
    end
    if #job.open == 0 or job.expanded >= (job.nav and job.nav.maxNodes or CFG.PATH_MAX_NODES) then planFinish(job, nil) end
    return job.result
end

-- Versao sincrona (testes e canal de comandos).
local function planPath(from, to, ignore, nav)
    local job = planStart(from, to, ignore, nav)
    local r = planStep(job, math.huge)
    return r, job.expanded
end

local function soldierPawns()
    local list = {}
    for _, m in ipairs(squad) do if valid(m.pawn) then list[#list + 1] = m.pawn end end
    return list
end

local enemies = {}  -- declarada aqui: rotas e ordens ja precisam dela (preenchida pelas ondas)
local points = {}   -- pontos de controle { X, Y, Z, name, owner = nil|0|1, prog, dots, banner }; recrutar ja os usa

local function allPawns()
    local list = soldierPawns()
    for _, e in ipairs(enemies) do if valid(e.pawn) then list[#list + 1] = e.pawn end end
    return list
end

-- Manda os selecionados para goal em formacao (slots contados so entre eles).
-- Trabalhos de caminho em andamento (planStart). Cada soldado guarda m.pathJob ate a rota sair;
-- enquanto isso espera parado. Ordem nova troca o trabalho; o antigo termina sem efeito.
local pathJobs = {}
S.routeStats = { squad = 0, enemy = 0 }  -- rotas A* entregues (com desvio), para o F5

local function pathTick()
    local budget = CFG.PATH_NODES_PER_TICK
    local deadline = os.clock() + CFG.PATH_MS / 1000
    local i = 1
    while i <= #pathJobs and budget > 0 and os.clock() < deadline do
        local job = pathJobs[i]
        local before = job.expanded
        local ok, r = pcall(planStep, job, math.min(budget, CFG.PATH_CHUNK))
        budget = budget - math.max(1, job.expanded - before)
        if not ok then
            logOnce("planPath", r)
            r = nil
        end
        if not ok or r then
            job.done = true
            if not ok then job.result, job.failed = {}, true end
            table.remove(pathJobs, i)
            if r and #r > 1 then
                S.routeStats[job.owner or "squad"] = (S.routeStats[job.owner or "squad"] or 0) + 1
                if job.owner == "squad" then log(string.format("caminho: %d waypoints (%d nos)", #r, job.expanded)) end
            end
            for _, list in ipairs({ squad, enemies }) do
                for _, m in ipairs(list) do
                    if m.pathJob == job then
                        m.pathJob, m.path = nil, nil
                        if r and #r > 1 then
                            m.path = {}
                            for w = 1, #r - 1 do m.path[w] = r[w] end
                        end
                    end
                end
            end
        else
            i = i + 1
        end
    end
end

-- Trincheiras (Ctrl+7, digTrench): buraco de raposa do jogo (pvpFoxhole01). Quem esta dentro (qualquer
-- lado) leva TRENCH.hit dos acertos de tiro e TRENCH.supp da supressao; granada e morteiro ignoram.
CFG.TRENCH = { cost = 20, max = 8, radius = 170.0, hit = 0.4, supp = 0.5, cap = 4, seek = 450.0,
    mesh = "/Game/Meshes/Environment/pvpFoxhole01.pvpFoxhole01" }
S.trenches = {}
local fort = {}   -- funcoes de fortificacao (tabela para nao gastar locais do chunk)
local sv = {}     -- salvar/continuar partida (definida perto de newGame)
local logi = {}   -- logistica: sucata, refinaria, fabrica, caminhoes, depositos (definida depois de pointsTick)

-- Trincheira cujo anel contem p (so X/Y), ou nil.
local function trenchAt(p)
    for _, tr in ipairs(S.trenches) do
        local dx, dy = p.X - tr.X, p.Y - tr.Y
        if dx * dx + dy * dy <= CFG.TRENCH.radius ^ 2 then return tr end
    end
    return nil
end

-- k-esima vaga (1..n) dentro da trincheira: anel de meio raio.
local function trenchSlot(tr, k, n)
    if n == 1 then return { X = tr.X, Y = tr.Y, Z = tr.Z + 90 } end
    local a = 2 * math.pi * (k - 1) / n
    local r = CFG.TRENCH.radius * 0.5
    return { X = tr.X + math.cos(a) * r, Y = tr.Y + math.sin(a) * r, Z = tr.Z + 90 }
end

local function issueMove(goal)
    if not isLocalAuthority() then return 0 end
    -- um caminho para o grupo, a partir do primeiro selecionado vivo; cada um segue os mesmos waypoints
    local job = nil
    for _, m in ipairs(squad) do
        if selected(m) and valid(m.pawn) and m.pawn.Health > 0 then
            local l = m.pawn:K2_GetActorLocation()
            local from = { X = l.X, Y = l.Y, Z = groundZ(l.X, l.Y) or (l.Z - 90) }
            local to = { X = goal.X, Y = goal.Y, Z = groundZ(goal.X, goal.Y) or goal.Z }
            job = planStart(from, to, allPawns())
            job.owner = "squad"
            table.insert(pathJobs, 1, job)  -- ordem do jogador fura a fila dos inimigos
            break
        end
    end
    -- formacao no destino: linha de ate FORM_WIDTH, perpendicular a direcao da marcha (centro do grupo -> goal)
    local n, cx, cy = 0, 0, 0
    for _, m in ipairs(squad) do
        if selected(m) and valid(m.pawn) and m.pawn.Health > 0 then
            local l = m.pawn:K2_GetActorLocation()
            n, cx, cy = n + 1, cx + l.X, cy + l.Y
        end
    end
    local dir = (n > 0) and math.atan(goal.Y - cy / n, goal.X - cx / n) or 0
    -- destino dentro de uma trincheira: os primeiros TRENCH.cap ocupam vagas nela, o resto forma linha
    local tr = trenchAt(goal)
    local inside = tr and math.min(n, CFG.TRENCH.cap) or 0
    local k = 0
    for _, m in ipairs(squad) do
        if selected(m) and valid(m.pawn) and m.pawn.Health > 0 then
            k = k + 1
            if k <= inside then
                local v = trenchSlot(tr, k, inside)
                m.slot = { X = v.X - goal.X, Y = v.Y - goal.Y }
            else
                m.slot = lineSlot(k - inside, n - inside, dir)
                if tr then  -- quem sobra fica em linha logo atras da trincheira
                    local back = CFG.TRENCH.radius + 120.0
                    m.slot = { X = m.slot.X - math.cos(dir) * back, Y = m.slot.Y - math.sin(dir) * back }
                end
            end
            m.target = { X = goal.X + m.slot.X, Y = goal.Y + m.slot.Y, Z = goal.Z }
            m.path, m.pathJob = nil, job
            m.focus, m.hold, m.retreat, m.queue, m.area = nil, false, nil, nil, nil
            m.detour, m.stuckAt, m.lastMoveT = nil, nil, nil
            m.medevac, m.orderT = nil, os.clock()
        end
    end
    return k
end

-- Rota propria de um soldado ate goal (volta apos fugir do morteiro): sem ela, a volta em linha reta
-- prendia soldados atras do carro blindado (2 de 6 no teste).
local function routeTo(m, goal)
    local l = m.pawn:K2_GetActorLocation()
    local job = planStart({ X = l.X, Y = l.Y, Z = groundZ(l.X, l.Y) or (l.Z - 90) },
        { X = goal.X, Y = goal.Y, Z = groundZ(goal.X, goal.Y) or (goal.Z - 90) }, allPawns())
    job.owner = "squad"
    pathJobs[#pathJobs + 1] = job
    m.target, m.path, m.pathJob = goal, nil, job
    m.detour, m.stuckAt, m.lastMoveT = nil, nil, nil
end

-- Fila de ordens (Shift+botao direito / Shift+F7): acrescenta goal ao fim da fila de cada selecionado
-- (mantendo a posicao na formacao); quem esta parado parte ja. Chegar a um destino puxa o proximo.
-- Qualquer ordem nova (mover, atacar, End, Home) descarta a fila.
local function queueMove(goal)
    if not isLocalAuthority() or not goal then return 0 end
    local k = 0
    for _, m in ipairs(squad) do
        if selected(m) and valid(m.pawn) and (m.pawn.Health or 0) > 0 then
            k = k + 1
            local sl = m.slot or slotFor(k)
            local g = { X = goal.X + sl.X, Y = goal.Y + sl.Y, Z = goal.Z }
            m.hold, m.retreat = false, nil
            if m.target or m.pathJob or m.focus then
                m.queue = m.queue or {}
                m.queue[#m.queue + 1] = g
            else
                routeTo(m, g)
            end
        end
    end
    return k
end

-- Recuo (Home): selecionados correm ao ponto de controle nosso mais proximo do grupo (sem ponto, ao
-- comandante), cada um com rota propria; nao param para atirar e levam RETREAT_HIT dos acertos.
-- Chegar ou receber outra ordem encerra o recuo. Dentro de um ponto nosso, fora de combate, curam-se.
CFG.RETREAT_HIT = 0.5
local function retreatSelected()
    if not isLocalAuthority() then return 0 end
    local cx, cy, n = 0, 0, 0
    for _, m in ipairs(squad) do
        if selected(m) and valid(m.pawn) and (m.pawn.Health or 0) > 0 then
            local l = m.pawn:K2_GetActorLocation()
            cx, cy, n = cx + l.X, cy + l.Y, n + 1
        end
    end
    if n == 0 then return 0 end
    cx, cy = cx / n, cy / n
    local dest, bd, name = nil, math.huge, nil
    for _, pt in ipairs(points) do
        local d = (pt.X - cx) ^ 2 + (pt.Y - cy) ^ 2
        if pt.owner == CFG.FRIENDLY_TEAM and d < bd then dest, bd, name = pt, d, pt.name end
    end
    if not dest then
        local l = rts.base()
        if not l then return 0 end
        dest = { X = l.X, Y = l.Y, Z = l.Z }
    end
    local k = 0
    for _, m in ipairs(squad) do
        if selected(m) and valid(m.pawn) and (m.pawn.Health or 0) > 0 then
            k = k + 1
            local s = slotFor(k)
            routeTo(m, { X = dest.X + s.X, Y = dest.Y + s.Y, Z = dest.Z })
            m.focus, m.hold, m.retreat, m.halted, m.queue, m.area = nil, false, true, false, nil, nil
            m.medevac, m.orderT = nil, os.clock()
        end
    end
    notify(string.format("recuando: %d soldados para %s", k, name and ("o ponto " .. name) or "o comandante"), 3.0)
    return k
end


------------------------------------------------------------------------------------------------
-- Combate. Ainda sem a arma de verdade (pegar item/disparar pelo servidor esta em estudo): o tiro
-- e simulado com GameplayStatics:ApplyDamage (validado: HP 100 -> 70) e os efeitos do proprio jogo
-- (clarao do rifle, som do tiro, sangue/poeira no alvo). Linha de visada por traco no canal Visibility.
------------------------------------------------------------------------------------------------
-- Perfis de arma (alcance, cadencia, precisao, dano): tabela WEAPONS, junto de spawnSoldier.
CFG.ENEMY_SQUAD_SIZE = 4
CFG.ENEMY_SPAWN_DIST = 3500.0
CFG.ENEMY_ENGAGE = 0.8        -- inimigo para de avancar a esta fracao do alcance
CFG.CORPSE_TTL = 20.0         -- s ate remover o corpo
CFG.ENEMY_ACCURACY = 0.7      -- multiplicador da chance de acerto do inimigo (dificuldade; era 0,6)
CFG.WAVE_ACC_GROWTH, CFG.WAVE_ACC_CAP = 0.04, 1.5  -- precisao inimiga +4% por onda alem da 1a, ate x1,5
CFG.WAVES_TO_WIN = 10          -- ondas automaticas: vence ao eliminar esta onda
CFG.HOLD_TO_WIN = 90.0         -- ... ou ao segurar todos os pontos de controle por tanto tempo
CFG.ENEMY_AIM_TIME = 0.8      -- s para mirar depois de parar (inimigo nao atira andando)
CFG.ENEMY_REPLAN = 4.0          -- s entre reavaliacoes da rota do inimigo que avanca
CFG.ENEMY_BOUND_SUPP = 0.25    -- supressao que faz o inimigo avancar em lances (de cobertura em cobertura)
CFG.ENEMY_BOUND_WAIT = 2.5     -- s abrigado antes do proximo lance
CFG.SCAN_EVERY = 0.25          -- s entre buscas de alvo + traco de visada por soldado (antes: todo quadro)
-- O jogo segura o personagem em 1 HP (ferido, sangrando) antes de morrer: matar exige um acerto a mais.
-- Ondas automaticas (Shift+F4): a cada onda eliminada o esquadrao recebe reforco e a proxima vem maior.
CFG.WAVE_DELAY = 15.0
CFG.WAVE_GROWTH = 0.8         -- inimigos extras por onda (0,5 era facil: robo venceu as 10 com 3 perdas)
CFG.WAVE_MAX = 16
CFG.WAVE_SQUAD_SCALE = 0.4    -- inimigos extras por soldado nosso vivo (contra a bola de neve de 12 soldados)

local corpses = {}               -- { pawn, at }
-- Q/E: camera de ponto em ponto (ordem de criacao), com o dono no aviso.
function rts.cyclePoint(dir)
    if #points == 0 then notify("sem pontos (J cria)", 2.0); return end
    S.pointI = ((S.pointI or 0) - 1 + dir) % #points + 1
    local pt = points[S.pointI]
    focusOn(pt.X, pt.Y, pt.Z)
    local who = (pt.owner == CFG.FRIENDLY_TEAM and "nosso") or (pt.owner == CFG.ENEMY_TEAM and "inimigo") or "neutro"
    notify(string.format("ponto %s (%s) [%d/%d]", pt.name, who, S.pointI, #points), 2.0)
end

local combat = { wave = 0, kills = 0, losses = 0, auto = false, nextWaveAt = nil,
                 shots = { [0] = 0, [1] = 0 }, hits = { [0] = 0, [1] = 0 }, dmg = { [0] = 0, [1] = 0 },
                 covered = { [0] = 0, [1] = 0 } }

-- Economia: mao de obra regenera com o tempo e rende por abate/onda; recrutar custa WEAPONS[r].cost.
-- F6 continua criando o esquadrao misto de graca (modo caixa de areia).
CFG.MANPOWER_START, CFG.MANPOWER_MAX, CFG.MANPOWER_RATE = 60.0, 200.0, 1.0   -- rate: por segundo (era 1,5; pontos de controle rendem o resto)
CFG.KILL_BOUNTY, CFG.WAVE_BOUNTY = 8.0, 30.0
local economy = { manpower = CFG.MANPOWER_START, lastT = nil }

CFG.FX = {
    muzzle = "/Game/FX/RifleMF.RifleMF",
    blood = "/Game/FX/BloodSplat.BloodSplat",
    dirt = "/Game/FX/SimpleRifleImpact.SimpleRifleImpact",
    shot = "/Game/Audio/SFX/Weapons/RifleShot_Cue.RifleShot_Cue",
}
S.fxCache, S.fxTried = {}, {}
local function asset(path)
    local o = S.fxCache[path]
    if o == nil or not o:IsValid() then
        o = StaticFindObject(path)
        if not (o and o:IsValid()) and not S.fxTried[path] then  -- fora da memoria: carrega uma vez
            S.fxTried[path] = true
            pcall(function() LoadAsset(path) end)
            o = StaticFindObject(path)
        end
        S.fxCache[path] = o
    end
    if o and o:IsValid() then return o end
    return nil
end

local function now()
    if tick.inFrame and tick.tn == tick.n then return tick.t end
    local t = gs():GetTimeSeconds(world())
    tick.t, tick.tn = t, tick.n
    return t
end

local function economyTick()
    local t = now()
    if economy.lastT then
        economy.manpower = math.min(CFG.MANPOWER_MAX, economy.manpower + CFG.MANPOWER_RATE * (t - economy.lastT))
    end
    economy.lastT = t
end

local function earn(amount)
    economy.manpower = math.min(CFG.MANPOWER_MAX, economy.manpower + amount)
end

-- Reforco avancado: com o cursor dentro de um ponto de controle nosso, o recruta nasce nele.
local function deployPoint()
    if not rts.active then return nil end
    local c = cursorPoint()
    if not c then return nil end
    for _, pt in ipairs(points) do
        local dx, dy = c.X - pt.X, c.Y - pt.Y  -- flatDist ainda nao existe aqui
        if pt.owner == CFG.FRIENDLY_TEAM and dx * dx + dy * dy <= CFG.POINT_RADIUS ^ 2 then return pt end
    end
    return nil
end

-- Recruta um soldado da classe role ao lado do esquadrao/comandante (ou no ponto at / sob o cursor),
-- se houver mao de obra e vaga.
local function recruit(role, at)
    if not isLocalAuthority() then return false end
    local w = CFG.WEAPONS[role]
    if #squad >= CFG.SQUAD_MAX then notify("esquadrao no maximo (" .. CFG.SQUAD_MAX .. ")", 3.0); return false end
    if role == "officer" then
        for _, o in ipairs(squad) do
            if o.role == "officer" and valid(o.pawn) and (o.pawn.Health or 0) > 0 then notify("já há um oficial no esquadrão", 3.0); return false end
        end
    end
    if economy.manpower < w.cost then
        notify(string.format("mao de obra insuficiente para %s: %.0f/%d", w.name, economy.manpower, w.cost), 3.0)
        return false
    end
    at = at or deployPoint()
    local dep = logi.on and (at and at.name and logi.depotOf(at) or logi.base) or nil
    if dep and ((dep.shirts or 0) < 1 or (role == "rifle" and (dep.rifle or 0) < 1)) and dep ~= logi.base then
        notify(string.format("sem suprimento de recrutamento no ponto %s: o recruta nasce na base", at.name), 3.0)
        at, dep = nil, logi.base
    end
    if dep and (dep.shirts or 0) < 1 then
        notify("sem camisas na base: a fábrica e os caminhões trazem (L manda um caminhão)", 3.0)
        return false
    end
    if dep and role == "rifle" and (dep.rifle or 0) < 1 then
        notify("sem fuzis na base: produza e entregue pela logística", 3.0); return false
    end
    -- Game thread síncrono: debitar só após spawn confirmado; falha não consome estoque.
    if spawnSquad(1, role, at) < 1 then return false end
    if dep then
        dep.shirts = dep.shirts - 1
        if role == "rifle" then dep.rifle = dep.rifle - 1 end
    end
    economy.manpower = economy.manpower - w.cost
    notify(string.format("recrutado %s%s (-%d) | mao de obra %.0f", w.name, at and at.name and (" no ponto " .. at.name) or "",
        w.cost, economy.manpower), 3.0)
    return true
end

local function emit(path, loc, yaw)
    local ps = asset(path)
    if ps then
        gs():SpawnEmitterAtLocation(world(), ps, loc, { Pitch = 0, Yaw = yaw or 0, Roll = 0 }, { X = 1, Y = 1, Z = 1 }, true, 0, true)
    end
end

local function alive(m) return valid(m.pawn) and (m.pawn.Health or 0) > 0 end

-- Posicao em cache por quadro (tick.n): cada chamada Lua->Unreal custa caro e loc e chamada dezenas
-- de vezes por soldado por quadro (nearest e O(aliados x inimigos)). Ninguem altera a tabela retornada.
local function loc(m)
    if m._lf == tick.n and m._l then return m._l end
    local l = m.pawn:K2_GetActorLocation()
    m._l, m._lf = l, tick.n
    return l
end

local function flatDist(a, b)
    local dx, dy = b.X - a.X, b.Y - a.Y
    return math.sqrt(dx * dx + dy * dy), dx, dy
end

local function nearest(m, foes)
    local here = loc(m)
    local best, bd = nil, math.huge
    for _, f in ipairs(foes) do
        if alive(f) then
            local d = flatDist(here, loc(f))
            if d < bd then best, bd = f, d end
        end
    end
    return best, bd
end

-- Visada livre se o traco olho->olho nao bate em nada antes de chegar perto do alvo.
local function hasLOS(a, b)
    local la, lb = loc(a), loc(b)
    local from = { X = la.X, Y = la.Y, Z = la.Z + 60 }
    local to = { X = lb.X, Y = lb.Y, Z = lb.Z + 60 }
    local hit = {}
    local blocked = ksl():LineTraceSingle(world(), from, to, 0, false, { a.pawn, b.pawn }, 0, hit, true,
        { R = 0, G = 0, B = 0, A = 0 }, { R = 0, G = 0, B = 0, A = 0 }, 0)
    return not blocked
end

-- Supressao (0..1): todo tiro contra um soldado soma weapon.supp, acertando ou nao; decai SUPP_DECAY/s.
-- Suprimido erra mais (ate -SUPP_ACC) e anda mais devagar (ate -SUPP_SLOW); inimigo acima de SUPP_PIN
-- fica preso no lugar (continua atirando). Cobertura: com a visada dos olhos livre, se o traco ate a
-- cintura do alvo bate em algo, o alvo esta atras de cobertura baixa: acerto x COVER_MULT e o tiro
-- perdido levanta poeira no obstaculo.
CFG.SUPP_DECAY, CFG.SUPP_ACC, CFG.SUPP_SLOW, CFG.SUPP_PIN = 0.35, 0.6, 0.5, 0.7
CFG.COVER_MULT = 0.5
CFG.COVER_LOW_Z = -20.0   -- cm relativos ao centro da capsula (~70 cm do chao)

-- Ha oficial vivo do lado de m a OFFICER.radius? Cache por OFFICER.every s por soldado.
function rts.officerNear(m)
    local t = now()
    if t < (m.ofT or 0) then return m.ofNear end
    m.ofT = t + CFG.OFFICER.every
    m.ofNear = false
    local list = (m.team == CFG.ENEMY_TEAM) and enemies or squad
    for _, o in ipairs(list) do
        if o.role == "officer" and alive(o) and flatDist(loc(m), loc(o)) <= CFG.OFFICER.radius then m.ofNear = true; break end
    end
    return m.ofNear
end

local function suppression(m)
    local t = now()
    if m.supp and m.suppT and m.supp > 0 then
        local k = (m.pawn and rts.officerNear(m)) and CFG.OFFICER.decay or 1.0
        m.supp = math.max(0.0, m.supp - CFG.SUPP_DECAY * k * (t - m.suppT))
    end
    m.suppT = t
    return m.supp or 0.0
end

local function inTrench(m) return #S.trenches > 0 and trenchAt(loc(m)) ~= nil end

CFG.CROUCH_SUPP = 0.4   -- supressao a partir da qual o soldado parado se agacha (so animacao)
function anim.postureTick()
    local c = os.clock()
    if c < (anim.nextPosture or 0) then return end
    anim.nextPosture = c + 0.3
    for _, list in ipairs({ squad, enemies }) do
        for _, m in ipairs(list) do
            if alive(m) then
                local ok, v = pcall(function() return inTrench(m) or (m.supp or 0) >= CFG.CROUCH_SUPP end)
                m.crouch = ok and v or false
                local aim = m.aiming == true
                if aim ~= m.scoped then m.scoped = aim; pcall(function() m.pawn.bIsInScopeMode = aim end) end
            end
        end
    end
end

-- ApplyDamage no host muda Health, mas nao dispara OnRep_Health: o rastro deixou HP=0 com Speed=500.
-- Devolver o movimento e chamar a notificacao nativa de morte, sem RPC/inventario. Ela pode substituir
-- a malha/AnimInstance; remover o cache ANTES da chamada (IsValid continua true ate o GC).
function anim.retire(m)
    anim.untrack(m)
    if m.retired then return end
    m.retired = true
    if not valid(m.pawn) then return end
    m.aiming, m.scoped, m.crouch = false, false, false
    pcall(function() m.pawn:ConsumeMovementInputVector() end)
    pcall(function()
        local cm, defaults = m.pawn.CharacterMovement, m.moveDefaults
        cm:StopMovementImmediately()
        if defaults then
            cm.GroundFriction, cm.BrakingDecelerationWalking, cm.MaxAcceleration = defaults.friction, defaults.brake, defaults.accel
        end
    end)
    pcall(function() m.pawn.bIsInScopeMode = false end)
    if (m.pawn.Health or 0) <= 0 then m.pawn:OnRep_Health() end
end

local function suppress(m, amount)
    if inTrench(m) then amount = amount * CFG.TRENCH.supp end
    m.supp = math.min(1.0, suppression(m) + amount)
end

-- Ponto do obstaculo se o alvo estiver atras de cobertura baixa; nil se exposto.
local function coverPoint(a, b)
    local la, lb = loc(a), loc(b)
    local hit = {}
    local blocked = ksl():LineTraceSingle(world(), { X = la.X, Y = la.Y, Z = la.Z + 60 }, { X = lb.X, Y = lb.Y, Z = lb.Z + CFG.COVER_LOW_Z },
        0, false, { a.pawn, b.pawn }, 0, hit, true, { R = 0, G = 0, B = 0, A = 0 }, { R = 0, G = 0, B = 0, A = 0 }, 0)
    if not blocked then return nil end
    local ip = hit.ImpactPoint
    return ip and { X = ip.X, Y = ip.Y, Z = ip.Z } or lb
end

local function face(m, dx, dy)
    m.hpc:SetControlRotation({ Pitch = 0, Yaw = math.deg(math.atan(dy, dx)), Roll = 0 })
end

local throwGrenade  -- definida junto do morteiro; fire ja precisa dela

-- Metralhadora monta o tripe: so atira parada ha MG_SETUP s (stillSince, marcado por halt e apagado por
-- moveToward) e, montada, acerta MG_SET_HIT vezes mais e suprime MG_SET_SUPP vezes mais.
CFG.MG_SETUP, CFG.MG_SET_HIT, CFG.MG_SET_SUPP = 1.0, 1.3, 1.5

-- Clarao no cano (socket S_Muzzle da arma; sem ele, a frente do soldado) e som do tiro.
function rts.shotFx(shooter, dx, dy, d)
    local from, w = loc(shooter), weapon(shooter)
    local nx, ny = dx / math.max(d, 1), dy / math.max(d, 1)
    local okM, muzzle = pcall(function() return shooter.wmesh:GetSocketLocation(FName("S_Muzzle")) end)
    if not (okM and muzzle and muzzle.X == muzzle.X) then muzzle = { X = from.X + nx * 50, Y = from.Y + ny * 50, Z = from.Z + 50 } end
    pcall(emit, CFG.FX.muzzle, muzzle, math.deg(math.atan(dy, dx)))
    pcall(function()
        local own = asset(shooter.team == CFG.ENEMY_TEAM and w.sndC or w.sndW)
        local cue, pitch = own or asset(CFG.FX.shot), own and (0.95 + 0.1 * math.random()) or w.pitch
        if cue then gs():PlaySoundAtLocation(world(), cue, from, { Pitch = 0, Yaw = 0, Roll = 0 }, 1.0, pitch, 0.0, nil, nil, nil) end
    end)
end

local function fire(shooter, target, d, dx, dy)
    local t = now()
    shooter.aimUntil = os.clock() + CFG.AIM_HOLD
    if t < shooter.nextShot then return end
    local mg = shooter.role == "mg"
    if mg and t - (shooter.stillSince or math.huge) < CFG.MG_SETUP then return end
    local w = weapon(shooter)
    local ours = shooter.team ~= CFG.ENEMY_TEAM
    if ours and (shooter.ammo or w.ammo) < 1 then
        if not shooter.dry then
            shooter.dry = true; combat.dryOut = (combat.dryOut or 0) + 1
            if t >= (S.dryNoteAt or 0) then
                S.dryNoteAt = t + 15.0
                notify("soldado sem munição: leve-o a um ponto seu ou à base (Home recua)", 5.0)
            end
        end
        return
    end
    shooter.nextShot = t + w.interval * (0.85 + 0.3 * math.random())
    face(shooter, dx, dy)
    local to = loc(target)
    local yaw = math.deg(math.atan(dy, dx))
    shooter.fireAnimUntil = os.clock() + CFG.FIRE_ANIM
    rts.shotFx(shooter, dx, dy, d)
    local p = w.hit * (1.0 - 0.5 * math.min(d / w.range, 1.0))
    if shooter.team == CFG.ENEMY_TEAM then
        p = p * CFG.ENEMY_ACCURACY * math.min(1.0 + CFG.WAVE_ACC_GROWTH * math.max(0, combat.wave - 1), CFG.WAVE_ACC_CAP)
    end
    p = p * (1.0 - CFG.SUPP_ACC * suppression(shooter))
    p = p * (1.0 + CFG.VET_ACC * rank(shooter))
    if rts.officerNear(shooter) then p = p * (1.0 + CFG.OFFICER.acc) end
    if mg then p = p * CFG.MG_SET_HIT end
    local cover = coverPoint(shooter, target)
    local dug = inTrench(target)
    if (cover or dug) and CFG.GRENADE.roles[shooter.role or "rifle"] and d <= CFG.GRENADE.range and t >= (shooter.nextGrenade or 0) then
        throwGrenade(shooter, target)
        return
    end
    if ours then shooter.ammo = (shooter.ammo or w.ammo) - 1 end
    if cover then p = p * CFG.COVER_MULT end
    if dug then p = p * CFG.TRENCH.hit end
    if target.retreat then p = p * CFG.RETREAT_HIT end
    suppress(target, w.supp * (mg and CFG.MG_SET_SUPP or 1.0))
    local tm = shooter.team or 0
    combat.shots[tm] = (combat.shots[tm] or 0) + 1
    if math.random() < p then
        combat.hits[tm] = (combat.hits[tm] or 0) + 1
        local hp0 = target.pawn.Health or 0
        gs():ApplyDamage(target.pawn, w.dmg, shooter.hpc, shooter.pawn, nil)
        combat.dmg[tm] = (combat.dmg[tm] or 0) + (hp0 - (target.pawn.Health or 0))
        if hp0 > 0 and (target.pawn.Health or 0) <= 0 then credit(shooter) end
        pcall(emit, CFG.FX.blood, { X = to.X, Y = to.Y, Z = to.Z + 40 }, yaw)
    elseif cover or dug then
        combat.covered[tm] = (combat.covered[tm] or 0) + 1
        pcall(emit, CFG.FX.dirt, cover or { X = to.X, Y = to.Y, Z = to.Z - 40 }, yaw)
    else
        local r = 80 + math.random() * 120
        local a = math.random() * 2 * math.pi
        local mx, my = to.X + math.cos(a) * r, to.Y + math.sin(a) * r
        pcall(emit, CFG.FX.dirt, { X = mx, Y = my, Z = groundZ(mx, my) or to.Z - 90 }, yaw)
    end
end

function rts.officerDown(m)
    earn(CFG.OFFICER.bounty)
    local ml = loc(m)
    for _, e in ipairs(enemies) do  -- abalo: quem estava perto do oficial fica suprimido
        if e ~= m and alive(e) and flatDist(loc(e), ml) <= CFG.OFFICER.radius then suppress(e, CFG.OFFICER.shock) end
    end
    notify(string.format("OFICIAL INIMIGO ABATIDO (+%d): os inimigos perto dele perdem a coordenação", CFG.OFFICER.bounty), 4.0)
end

-- Remove mortos de uma lista; o controller sai na hora (senao o jogo tenta o respawn), o corpo fica um tempo.
local function reap(list, what)
    local lost = 0
    for i = #list, 1, -1 do
        local m = list[i]
        if not alive(m) then
            if m.role == "officer" and m.team == CFG.ENEMY_TEAM then pcall(rts.officerDown, m) end
            if m.team ~= CFG.ENEMY_TEAM and valid(m.pawn) then
                pcall(rts.alert, "baixa", m.pawn:K2_GetActorLocation(), weapon(m).name .. " abatido")
            end
            pcall(destroyMarker, m)
            pcall(anim.retire, m)
            releaseController(m.hpc)
            if valid(m.pawn) then table.insert(corpses, { pawn = m.pawn, at = now() }) end
            table.remove(list, i)
            lost = lost + 1
            log(what .. " abatido")
        end
    end
    return lost
end

local function corpseTick()
    local t = now()
    for i = #corpses, 1, -1 do
        local c = corpses[i]
        if not valid(c.pawn) then
            table.remove(corpses, i)
        elseif t - c.at > CFG.CORPSE_TTL then
            c.pawn:K2_DestroyActor()
            table.remove(corpses, i)
        end
    end
end

-- Anda em linha reta; se ficar preso (moveu < STUCK_DIST em STUCK_TIME), desvia de lado por DETOUR_TIME.
CFG.STUCK_TIME, CFG.STUCK_DIST, CFG.DETOUR_TIME = 0.6, 25.0, 0.9
CFG.WAYPOINT_RADIUS = 70.0   -- cm: waypoint intermediario conta como alcancado (120 cortava quinas)

-- Arame farpado (Ctrl+9): cavalete de arame do jogo (BarbedWire04, 7,5 m; o centro da malha fica a pivot cm
-- do pivo no eixo X) em escala; quem esta dentro da faixa (dos dois lados) anda a WIRE.slow da velocidade.
-- Sem colisao: o A* nao desvia, o arame so atrasa quem atravessa.
CFG.WIRE = { cost = 10, max = 10, seg = 1, len = 600.0, depth = 110.0, slow = 0.35, scale = 0.8, pivot = 306.0,
             mesh = "/Game/Meshes/Environment/Props/BarbedWire04.BarbedWire04" }
S.wires = {}

function fort.wireFactor(l)
    for _, w in ipairs(S.wires) do
        local rx, ry = l.X - w.X, l.Y - w.Y
        local along, across = rx * w.ux + ry * w.uy, -rx * w.uy + ry * w.ux
        if math.abs(across) <= CFG.WIRE.depth and math.abs(along) <= CFG.WIRE.seg * CFG.WIRE.len / 2 then
            return CFG.WIRE.slow
        end
    end
    return 1.0
end

-- Sem atrito nem frenagem o CMC mantem a velocidade ao entrar numa zona lenta (a escala do input so limita a
-- aceleracao; medido: 5,8 m/s constantes atravessando o arame). Corta a velocidade horizontal direto.
function fort.capSpeed(m, scale)
    local cm = m.pawn.CharacterMovement
    local v = m.pawn:GetVelocity()
    local sp = math.sqrt(v.X * v.X + v.Y * v.Y)
    local cap = (cm.MaxWalkSpeed or 500.0) * scale
    if sp > cap and sp > 1 then
        local k = cap / sp
        cm.Velocity = { X = v.X * k, Y = v.Y * k, Z = v.Z }
    end
end

local function moveToward(m, tx, ty)
    local l = loc(m)
    local d, dx, dy = flatDist(l, { X = tx, Y = ty })
    if d <= CFG.ARRIVE_RADIUS then return true end
    local t = now()
    local nx, ny = dx / d, dy / d
    if not m.lastMoveT or t - m.lastMoveT > 0.25 then m.stuckAt = nil end  -- estava parado: recomeca a medir
    m.lastMoveT = t
    if not m.stuckAt then
        m.stuckAt = { X = l.X, Y = l.Y, t = t }
    elseif t - m.stuckAt.t >= CFG.STUCK_TIME then
        if not m.detour and flatDist(l, m.stuckAt) < CFG.STUCK_DIST then
            local s = (math.random() < 0.5) and 1 or -1
            m.detour = { X = -ny * s, Y = nx * s, untilT = t + CFG.DETOUR_TIME }
        end
        m.stuckAt = { X = l.X, Y = l.Y, t = t }
    end
    if m.detour then
        if t < m.detour.untilT then nx, ny = m.detour.X, m.detour.Y else m.detour = nil end
    end
    face(m, nx, ny)
    m.stillSince = nil
    local scale = 1.0 - CFG.SUPP_SLOW * suppression(m)
    if #S.wires > 0 then scale = scale * fort.wireFactor(l) end
    m.pawn:AddMovementInput({ X = nx, Y = ny, Z = 0.0 }, scale, false)
    if scale < 0.9 then pcall(fort.capSpeed, m, scale) end
    return false
end

-- Sem atrito nem frenagem (spawnSoldier), um unico impulso residual vira deslizamento sem fim:
-- medido em jogo, soldados parados pela ordem de parar andaram 6-10 m em 1,5 s. Por isso halt descarta a entrada
-- pendente e trava a velocidade sempre que chamado, e o tick chama halt em todo soldado sem ordem.
local function halt(m)
    m.halted = true
    m.stillSince = m.stillSince or now()
    pcall(function() m.pawn:ConsumeMovementInputVector() end)
    local v = m.pawn:GetVelocity()
    if v.X * v.X + v.Y * v.Y > 1.0 then m.pawn.CharacterMovement:StopMovementImmediately() end
end

-- Cancela a marcha sem desligar o combate automatico. Sem frenagem, apenas apagar target
-- deixa o soldado deslizando; e preciso zerar a velocidade no CharacterMovement.
local function stopSelected()
    if not isLocalAuthority() then return 0 end
    local n = 0
    for _, m in ipairs(squad) do
        if selected(m) and alive(m) then
            m.target, m.focus, m.detour, m.stuckAt, m.lastMoveT, m.path, m.pathJob = nil, nil, nil, nil, nil, nil, nil
            m.hold, m.retreat, m.queue, m.area = true, nil, nil, nil
            m.medevac, m.orderT = nil, os.clock()
            halt(m)
            n = n + 1
        end
    end
    notify(string.format("parar: %d soldados", n), 3.0)
    return n
end

-- Ordem de ataque: botao direito/F7 sobre um inimigo (ate ATTACK_PICK do ponto) faz os selecionados
-- focarem nele: avancam ate ter alcance e visada, param e atiram so nele ate cair. No caminho atiram no
-- inimigo mais proximo, como na marcha. Ordem de marcha ou End (segurar) cancelam o foco.
CFG.ATTACK_PICK = 250.0

local function enemyAt(p)
    local best, bd = nil, CFG.ATTACK_PICK
    for _, e in ipairs(enemies) do
        if alive(e) then
            local d = flatDist(p, loc(e))
            if d < bd then best, bd = e, d end
        end
    end
    return best
end

local function issueAttack(e)
    if not isLocalAuthority() or not (e and alive(e)) then return 0 end
    local k = 0
    for _, m in ipairs(squad) do
        if selected(m) and alive(m) then
            m.focus, m.target, m.detour, m.stuckAt, m.lastMoveT, m.path, m.pathJob = e, nil, nil, nil, nil, nil, nil
            m.hold, m.retreat, m.queue, m.area = false, nil, nil, nil
            m.medevac, m.orderT = nil, os.clock()
            k = k + 1
        end
    end
    return k
end

local function orderMove(queued)
    if not isLocalAuthority() then return end
    if #squad == 0 then log("sem esquadrao (F6)"); return end
    local goal = cursorPoint()
    if not goal then log("cursor sem alvo"); return end
    local e = enemyAt(goal)
    if e then
        notify(string.format("atacar: %d soldados contra %s inimigo", issueAttack(e), weapon(e).name), 3.0)
        return
    end
    if queued then
        notify(string.format("ordem na fila: %d soldados", queueMove(goal)), 2.0)
        return
    end
    local k = issueMove(goal)
    log(string.format("ordem: %d soldados para (%.0f, %.0f)", k, goal.X, goal.Y))
end

-- Ordem de fogo em area em p para os selecionados (medicos ficam de fora). Retorna quantos receberam.
function rts.areaOrder(p)
    if not isLocalAuthority() or not p then return 0 end
    local k, t = 0, now()
    local area = { X = p.X, Y = p.Y, Z = p.Z, untilT = t + CFG.AREA.dur }
    for _, m in ipairs(squad) do
        if selected(m) and alive(m) and m.role ~= "medic" then
            m.area = area
            m.target, m.focus, m.path, m.pathJob, m.queue = nil, nil, nil, nil, nil
            m.retreat, m.hold, m.areaScan, m.areaSeen = nil, false, 0, false
            m.medevac, m.orderT = nil, os.clock()
            k = k + 1
        end
    end
    if k > 0 then
        pcall(rts.areaMarkAt, area)
        notify(string.format("fogo de supressão: %d soldados por %.0f s (sem visada só suprime; gasta munição)", k, CFG.AREA.dur), 3.0)
    end
    return k
end

-- Busca de cobertura (aliados e inimigos): soldado parado, sem ordem e sem H, com adversario ao alcance e exposto,
-- procura a cada COVER_SEEK_EVERY s, em aneis de 1,5/2,8/4 m, o ponto mais perto onde o traco do olho do
-- inimigo ate a cintura bate em algo e ate os olhos passa (protegido e ainda atirando). Mesmo chao (+-80 cm)
-- e caminho livre na altura do joelho (sem isso escolhia o outro lado do muro, inalcancavel).
CFG.COVER_SEEK_EVERY = 2.0
CFG.COVER_SEEK_RINGS = { 150.0, 280.0, 400.0 }
CFG.NO_COLOR = { R = 0, G = 0, B = 0, A = 0 }

local function traceBlocked(a, b, ignore)
    local hit = {}
    return ksl():LineTraceSingle(world(), a, b, 0, false, ignore, 0, hit, true, CFG.NO_COLOR, CFG.NO_COLOR, 0)
end

local function seekCover(m, foes)
    local foe, d = nearest(m, foes)
    if not foe or d > weapon(foe).range + 600.0 then return false end
    if coverPoint(foe, m) or inTrench(m) then return false end  -- ja coberto
    local here, fe = loc(m), loc(foe)
    -- trincheira com vaga por perto vem antes dos aneis de busca
    local list = (m.team == CFG.ENEMY_TEAM) and enemies or squad
    for _, tr in ipairs(S.trenches) do
        if flatDist(here, tr) <= CFG.TRENCH.seek then
            local used = 0
            for _, o in ipairs(list) do if o ~= m and alive(o) and flatDist(loc(o), tr) <= CFG.TRENCH.radius then used = used + 1 end end
            if used < CFG.TRENCH.cap then
                m.target, m.path, m.pathJob = trenchSlot(tr, used + 1, CFG.TRENCH.cap), nil, nil
                combat.coverMoves = (combat.coverMoves or 0) + 1
                return true
            end
        end
    end
    local eye = { X = fe.X, Y = fe.Y, Z = fe.Z + 60 }
    local ignore = { m.pawn, foe.pawn }
    for _, r in ipairs(CFG.COVER_SEEK_RINGS) do
        local best, bd = nil, math.huge
        for k = 0, 11 do
            local a = k * math.pi / 6
            local x, y = here.X + math.cos(a) * r, here.Y + math.sin(a) * r
            local gz = groundZ(x, y)
            if gz and math.abs(gz + 90 - here.Z) < 80
                and not traceBlocked({ X = here.X, Y = here.Y, Z = here.Z - 50 }, { X = x, Y = y, Z = gz + 40 }, ignore)  -- alcancavel em linha reta
                and traceBlocked(eye, { X = x, Y = y, Z = gz + 70 }, ignore)
                and not traceBlocked(eye, { X = x, Y = y, Z = gz + 150 }, ignore) then
                local dd = flatDist({ X = x, Y = y }, fe)
                if dd < bd then best, bd = { X = x, Y = y, Z = gz + 90 }, dd end  -- no anel, o mais avancado
            end
        end
        if best then
            m.target, m.path, m.pathJob = best, nil, nil
            combat.coverMoves = (combat.coverMoves or 0) + 1
            return true
        end
    end
    return false
end

-- Fogo de supressao em area (Ctrl+botao direito / Ctrl+F7): os selecionados atiram por AREA.dur s num circulo
-- de AREA.radius. Sem visada nao ha dano, so supressao (AREA.supp do valor da arma) em todo inimigo dentro do
-- circulo; quem aparecer ao alcance e a vista leva tiro normal. Gasta municao; ordem nova cancela.
CFG.AREA = { radius = 450.0, dur = 20.0, supp = 0.7 }

-- MG inimiga: por ENEMY_AREA s depois de perder a visada, fica e suprime em area onde viu o alvo pela ultima
-- vez (quem se esconde atras de um muro continua preso). Nao atravessa nada: so supressao, como a nossa.
CFG.ENEMY_AREA = 8.0
function rts.enemyArea(e)
    local s = e.seen
    if not s or now() - s.t > CFG.ENEMY_AREA then e.area = nil; return false end
    local d, dx, dy = flatDist(loc(e), s)
    if d > weapon(e).range then return false end
    e.area = e.area or { X = s.X, Y = s.Y, Z = s.Z, untilT = s.t + CFG.ENEMY_AREA }
    e.target = nil
    halt(e)
    e.aimUntil = os.clock() + CFG.AIM_HOLD
    rts.areaShot(e, d, dx, dy)
    return true
end

function rts.areaShot(m, d, dx, dy)
    local t, w, a = now(), weapon(m), m.area
    if t < (m.nextShot or 0) then return end
    if m.role == "mg" and t - (m.stillSince or math.huge) < CFG.MG_SETUP then return end
    local ours = m.team ~= CFG.ENEMY_TEAM
    if ours and (m.ammo or w.ammo) < 1 then m.area = nil; return end
    m.nextShot = t + w.interval * (0.85 + 0.3 * math.random())
    m.fireAnimUntil = os.clock() + CFG.FIRE_ANIM
    face(m, dx, dy)
    rts.shotFx(m, dx, dy, d)
    if ours then m.ammo = (m.ammo or w.ammo) - 1 end
    local r, ang = math.sqrt(math.random()) * CFG.AREA.radius, math.random() * 2 * math.pi
    local x, y = a.X + math.cos(ang) * r, a.Y + math.sin(ang) * r
    pcall(emit, CFG.FX.dirt, { X = x, Y = y, Z = groundZ(x, y) or a.Z }, math.deg(math.atan(dy, dx)))
    local amt = w.supp * CFG.AREA.supp * (m.role == "mg" and CFG.MG_SET_SUPP or 1.0)
    for _, e in ipairs(ours and enemies or squad) do
        if alive(e) and flatDist(loc(e), a) <= CFG.AREA.radius then suppress(e, amt) end
    end
    if ours then combat.areaShots = (combat.areaShots or 0) + 1 else combat.enemyAreaShots = (combat.enemyAreaShots or 0) + 1 end
end

-- Um quadro do soldado com ordem de area: true enquanto a ordem vale (anda ate o alcance ou atira);
-- m.areaShooting diz se esta atirando (o scan normal fica de fora).
function rts.areaStep(m)
    local a, t = m.area, now()
    m.areaShooting = false
    if t > a.untilT then m.area = nil; return false end
    m.aimUntil = os.clock() + CFG.AIM_HOLD
    local d, dx, dy = flatDist(loc(m), a)
    if d > weapon(m).range * 0.95 then m.halted = false; moveToward(m, a.X, a.Y); return true end
    halt(m)
    if t >= (m.areaScan or 0) then  -- inimigo a vista e ao alcance: tiro normal pelo scan
        m.areaScan = t + CFG.SCAN_EVERY
        local foe, fd = nearest(m, enemies)
        m.areaSeen = foe ~= nil and fd <= weapon(m).range and hasLOS(m, foe)
    end
    if m.areaSeen then return true end
    m.areaShooting = true
    rts.areaShot(m, d, dx, dy)
    return true
end

-- Medico: a cada MEDIC_PERIOD s escolhe o aliado vivo mais ferido (proporcao de HP) a ate MEDIC_SEEK; a ate
-- MEDIC_RANGE estanca o sangramento e cura MEDIC_HEAL (bIsBleeding/Health + OnRep_*, validado: 60 -> 90 e
-- mantem). Mais longe, se o medico estiver livre (sem ordem, foco, H ou rota pendente), vai ate o ferido.
CFG.MEDIC_PERIOD, CFG.MEDIC_RANGE, CFG.MEDIC_SEEK, CFG.MEDIC_HEAL = 1.5, 350.0, 1200.0, 12.0
S.healStats = { [0] = 0, [1] = 0 }

local function medicTick(m, allies)
    if m.role ~= "medic" or not alive(m) then return end
    local t = now()
    if t < (m.nextHealT or 0) then return end
    local here = loc(m)
    local best, bestRatio, bestD = nil, 1.0, 0
    for _, a in ipairs(allies) do
        if alive(a) then
            local maxh = a.pawn.MaxHealth or 100
            local ratio = (a.pawn.Health or 0) / maxh
            local d = flatDist(here, loc(a))
            if ratio < 0.999 and d <= CFG.MEDIC_SEEK and ratio < bestRatio then best, bestRatio, bestD = a, ratio, d end
        end
    end
    if not best then return end
    if bestD <= CFG.MEDIC_RANGE then
        local supply = nil
        if logi.on and m.team ~= CFG.ENEMY_TEAM then
            supply = logi.medicalDepot(m)
            if not supply then return end
        end
        local p = best.pawn
        pcall(function() if p.bIsBleeding then p.bIsBleeding = false; p:OnRep_IsBleeding() end end)
        local before = p.Health
        p.Health = math.min(p.MaxHealth or 100, p.Health + CFG.MEDIC_HEAL)
        pcall(function() p:OnRep_Health() end)
        if supply and p.Health > before then supply.medical = supply.medical - 1 end
        m.healAnimUntil = os.clock() + 1.2
        local tm = m.team or 0
        S.healStats[tm] = (S.healStats[tm] or 0) + (p.Health - before)
        m.nextHealT = t + CFG.MEDIC_PERIOD
    elseif not best.retreat and not m.target and not m.focus and not m.hold and not m.pathJob then  -- quem recua vem ate ele
        local bl = loc(best)
        local d = math.max(bestD, 1)
        m.target = { X = bl.X + (here.X - bl.X) / d * 150, Y = bl.Y + (here.Y - bl.Y) / d * 150, Z = bl.Z }
        m.path = nil
        m.nextHealT = t + 0.5
    end
end

-- Evacuacao automatica: soldado nosso abaixo de MEDEVAC.below da vida, sem ordem do jogador ha MEDEVAC.quiet s
-- (nem foco, area, segurar ou marcha), recua sozinho (sem atirar, como o Home) ao posto de socorro mais perto;
-- sem posto, ao ponto nosso; sem ponto, ao medico vivo. Chegando, espera curar ate MEDEVAC.done e se libera.
CFG.MEDEVAC = { below = 0.3, done = 0.8, quiet = 15.0, every = 1.0, giveUp = 45.0 }
function rts.medevacStep(m)
    local t = now()
    local frac = (m.pawn.Health or 0) / (m.pawn.MaxHealth or 100)
    if m.medevac then
        if frac >= CFG.MEDEVAC.done or (not m.target and t - m.medevac > CFG.MEDEVAC.giveUp) then m.medevac, m.retreat = nil, nil end
        return
    end
    if t < (m.nextEvacT or 0) then return end
    m.nextEvacT = t + CFG.MEDEVAC.every
    if frac >= CFG.MEDEVAC.below or m.hold or m.focus or m.area or m.retreat or m.target or m.pathJob then return end
    if os.clock() - (m.orderT or -1e9) < CFG.MEDEVAC.quiet then return end  -- orderT em os.clock (issueMove vem antes de now)
    local here, dest, bd, what = loc(m), nil, math.huge, nil
    for _, tn in ipairs(S.tents) do
        local d = flatDist(here, tn)
        if d <= CFG.TENT.radius then return end  -- ja esta sendo curado
        if d < bd then dest, bd, what = tn, d, "o posto de socorro" end
    end
    for _, pt in ipairs(points) do
        if pt.owner == CFG.FRIENDLY_TEAM and flatDist(here, pt) <= CFG.POINT_RADIUS then return end  -- idem
    end
    if not dest then
        for _, pt in ipairs(points) do
            local d = flatDist(here, pt)
            if pt.owner == CFG.FRIENDLY_TEAM and d < bd then dest, bd, what = pt, d, "o ponto " .. pt.name end
        end
    end
    if not dest then
        for _, o in ipairs(squad) do
            if o ~= m and o.role == "medic" and alive(o) then
                local d = flatDist(here, loc(o))
                if d < bd then dest, bd, what = loc(o), d, "o médico" end
            end
        end
    end
    if not dest or bd < 250 then return end
    local a = math.random() * 2 * math.pi
    routeTo(m, { X = dest.X + math.cos(a) * 150, Y = dest.Y + math.sin(a) * 150, Z = dest.Z or here.Z })
    m.medevac, m.retreat, m.halted = t, true, false
    combat.medevacs = (combat.medevacs or 0) + 1
    if t >= (S.medevacNote or 0) then
        S.medevacNote = t + 10.0
        notify(string.format("%s ferido recua sozinho para %s", weapon(m).name, what), 3.0)
    end
end

-- Aliados: cumprem a ordem (marcha ou ataque); fora do foco atiram no inimigo mais proximo ao alcance.
local function squadTick()
    local lost = reap(squad, "soldado")
    if lost > 0 then
        combat.losses = combat.losses + lost
        for i, m in ipairs(squad) do m.slot = slotFor(i) end  -- fecha os buracos da formacao
    end
    for _, m in ipairs(squad) do
        medicTick(m, squad)
        if alive(m) then pcall(rts.medevacStep, m) end
        if m.focus and not alive(m.focus) then m.focus = nil end
        local engaged = false
        if m.focus then
            local d, dx, dy = flatDist(loc(m), loc(m.focus))
            if now() >= (m.nextFocusScan or 0) then
                m.focusLos = d <= weapon(m).range and hasLOS(m, m.focus)
                m.nextFocusScan = now() + CFG.SCAN_EVERY
            end
            if d <= weapon(m).range and m.focusLos then
                halt(m)
                fire(m, m.focus, d, dx, dy)
                engaged = true
            else
                local fl = loc(m.focus)
                m.halted = false
                moveToward(m, fl.X, fl.Y)
            end
        elseif m.target and m.pathJob then
            halt(m)  -- rota sendo calculada
        elseif m.target then
            m.halted = false
            local wp = m.path and m.path[1]
            if wp then
                if flatDist(loc(m), wp) <= CFG.WAYPOINT_RADIUS then table.remove(m.path, 1) else moveToward(m, wp.X, wp.Y) end
            elseif moveToward(m, m.target.X, m.target.Y) then
                m.target, m.retreat = nil, nil
                halt(m)
                if m.queue and #m.queue > 0 then routeTo(m, table.remove(m.queue, 1)) end
            end
        elseif m.area and rts.areaStep(m) then
            engaged = m.areaShooting
        else
            halt(m)
            if not m.hold and #enemies > 0 and now() >= (m.nextCoverT or 0) then
                m.nextCoverT = now() + CFG.COVER_SEEK_EVERY
                seekCover(m, enemies)
            end
        end
        if not engaged and not m.retreat and now() >= math.max(m.nextShot or 0, m.nextScan or 0) then
            m.nextScan = now() + CFG.SCAN_EVERY * (0.8 + 0.4 * math.random())
            local foe, d = nearest(m, enemies)
            if foe and d <= weapon(m).range and hasLOS(m, foe) then
                local _, dx, dy = flatDist(loc(m), loc(foe))
                fire(m, foe, d, dx, dy)
            end
        end
    end
end

-- Superficie sob (x, y) incluindo veiculos: o canal Visibility (groundZ) atravessa caminhoes; a busca por
-- tipos de objeto WorldStatic(0)+WorldDynamic(1) os acerta (Truck24 a Z=357 sobre chao a 95, medido).
-- Tambem acerta volumes invisiveis (BPNoBuild_C: BoxComponent com topo a Z=4746): esses vao para
-- surfaceIgnore e o traco e refeito sem eles.
S.surfaceIgnore = {}
local function surfaceZ(x, y)
    for _ = 1, 4 do
        local hit = {}
        local ok = ksl():LineTraceSingleForObjects(world(), { X = x, Y = y, Z = 20000 }, { X = x, Y = y, Z = -5000 }, { 0, 1 }, false,
            S.surfaceIgnore, 0, hit, true, CFG.NOCOL, CFG.NOCOL, 0)
        if not (ok and hit.ImpactPoint) then return nil end
        local comp = hit.Component and hit.Component:get()
        local cls = (comp and comp:IsValid()) and comp:GetClass():GetFName():ToString() or ""
        if cls ~= "BoxComponent" and cls ~= "SphereComponent" then return hit.ImpactPoint.Z end
        local a = hit.Actor and hit.Actor:get()
        if not (a and a:IsValid()) then return nil end
        S.surfaceIgnore[#S.surfaceIgnore + 1] = a
    end
    return nil
end

-- Pontos de controle: anel pontilhado laranja no raio de captura (cada ponto no chao local; um disco
-- unico de 10 m ficava cortado pelo relevo e cobria o terreno) + estandarte enrolado do dono no centro (azul =
-- Wardens/jogador, verde = Colonials; neutro sem estandarte). Progresso prog em [-1, 1] (+1 = jogador):
-- so um lado presente empurra o progresso (1 soldado leva POINT_CAPTURE_TIME s de neutro a dono; ate 3
-- somam); os dois lados presentes = disputado, congela; ninguem = volta devagar ao estado do dono.
-- O dono perde o ponto quando prog cruza 0 (neutro). Cada ponto do jogador rende POINT_INCOME/s.
-- Inimigos que nao estao em combate avancam ate o ponto mais proximo que ainda nao dominam.
CFG.POINT_RADIUS = 500.0
CFG.POINT_CAPTURE_TIME = 10.0
CFG.POINT_INCOME = 0.5          -- mao de obra por segundo por ponto
CFG.POINT_HEAL = 2.0             -- HP/s dos nossos dentro de um ponto nosso, sem supressao
CFG.ENEMY_DIG = true             -- inimigo abre trincheira (gratis, uma por ponto) ao tomar um ponto
CFG.AMMO_REFILL = 0.15           -- fracao do carregamento por s dentro de um ponto nosso ou perto do comandante
CFG.AMMO_LOW = 0.25              -- abaixo disso o painel avisa "munição baixa"
CFG.POINT_MAX = 5
CFG.POINT_HOLD = 0.6             -- fracao do raio onde o inimigo para e segura o ponto
CFG.WAVE_POINT_MIN = 1500.0      -- ponto inimigo a menos disso do esquadrao nao serve de entrada da onda
CFG.POINT_BANNER = { [1] = "/Game/Blueprints/Structures/Banners/BannerTWPickup.BannerTWPickup",
                     [0] = "/Game/Blueprints/Structures/Banners/BannerTCPickup.BannerTCPickup" }
CFG.POINT_DOTS = 24

local function meshActor(x, y, z, mesh, scale)
    local a = world():SpawnActor(StaticFindObject("/Script/Engine.StaticMeshActor"), { X = x, Y = y, Z = z },
        { Pitch = 0, Yaw = 0, Roll = 0 })
    if not valid(a) then return nil end
    local c = a.StaticMeshComponent
    c:SetMobility(2)
    c:SetStaticMesh(findAsset(mesh))
    c:SetCollisionEnabled(0)
    a:SetActorEnableCollision(false)
    a:SetActorScale3D(scale)
    return a
end

-- Abre uma trincheira em p sem custo nem aviso; nil se encostada em outra, no limite ou sem chao.
function fort.place(p)
    local T = CFG.TRENCH
    if #S.trenches >= T.max then return nil, "limite" end
    for _, tr in ipairs(S.trenches) do
        local dx, dy = p.X - tr.X, p.Y - tr.Y
        if dx * dx + dy * dy < (2 * T.radius) ^ 2 then return nil, "perto" end
    end
    local z = groundZ(p.X, p.Y)
    if not z then return nil, "chao" end
    local a = meshActor(p.X, p.Y, z, T.mesh, { X = 1, Y = 1, Z = 1 })
    if a then pcall(function() a:K2_SetActorRotation({ Pitch = 0, Yaw = math.random() * 360, Roll = 0 }, false) end) end
    local tr = { actor = a, X = p.X, Y = p.Y, Z = z }
    table.insert(S.trenches, tr)
    return tr
end

local function pointVisual(pt)
    if not valid(pt.banner) then return end
    if pt.owner == nil then pt.banner:SetActorHiddenInGame(true); return end
    pt.banner.StaticMeshComponent:SetStaticMesh(findAsset(CFG.POINT_BANNER[pt.owner]))
    pt.banner:SetActorHiddenInGame(false)
end

-- Cria um ponto em (x, y) no chao; recusa no limite ou perto demais de outro ponto.
local function addPoint(x, y)
    if #points >= CFG.POINT_MAX then notify("limite de pontos de controle (" .. CFG.POINT_MAX .. ")", 3.0); return nil end
    for _, q in ipairs(points) do
        if flatDist({ X = x, Y = y }, q) < 2 * CFG.POINT_RADIUS then notify("perto demais de outro ponto", 2.0); return nil end
    end
    local z = surfaceZ(x, y)
    if not z then return nil end
    local mat = findAsset(CFG.MARKER_MAT)
    local dots = {}
    for i = 1, CFG.POINT_DOTS do
        local a = 2 * math.pi * i / CFG.POINT_DOTS
        local dx, dy = x + math.cos(a) * CFG.POINT_RADIUS, y + math.sin(a) * CFG.POINT_RADIUS
        local dz = surfaceZ(dx, dy)
        local dot = dz and meshActor(dx, dy, dz + 1, CFG.MARKER_MESH, { X = 0.5, Y = 0.5, Z = 0.02 })
        if dot then
            if mat then dot.StaticMeshComponent:SetMaterial(0, mat) end
            dots[#dots + 1] = dot
        end
    end
    local pt = { X = x, Y = y, Z = z, name = string.char(64 + #points + 1), owner = nil, prog = 0.0, dots = dots,
                 banner = meshActor(x, y, z + 10, CFG.POINT_BANNER[1], { X = 3, Y = 3, Z = 3 }) }
    pointVisual(pt)
    points[#points + 1] = pt
    log(string.format("ponto %s em (%.0f, %.0f, %.0f)", pt.name, x, y, z))
    return pt
end

local function clearPoints()
    for _, pt in ipairs(points) do
        for _, d in ipairs(pt.dots or {}) do if valid(d) then d:K2_DestroyActor() end end
        if valid(pt.banner) then pt.banner:K2_DestroyActor() end
    end
    points = {}
end

local function pointsOwned(team)
    local n = 0
    for _, pt in ipairs(points) do if pt.owner == team then n = n + 1 end end
    return n
end

local function presence(list, pt)
    local n = 0
    for _, m in ipairs(list) do
        if alive(m) and flatDist(loc(m), pt) <= CFG.POINT_RADIUS then n = n + 1 end
    end
    return n
end

-- Avanca o progresso de cada ponto (pura: testavel fora do jogo). a/b = aliados/inimigos no raio.
local function pointStep(pt, a, b, dt)
    local rate = dt / CFG.POINT_CAPTURE_TIME
    local before = pt.owner
    if a > 0 and b == 0 then
        pt.prog = math.min(1.0, pt.prog + rate * math.min(a, 3))
    elseif b > 0 and a == 0 then
        pt.prog = math.max(-1.0, pt.prog - rate * math.min(b, 3))
    elseif a == 0 and b == 0 then
        local rest = (pt.owner == CFG.FRIENDLY_TEAM and 1.0) or (pt.owner == CFG.ENEMY_TEAM and -1.0) or 0.0
        local step = rate * 0.5
        if pt.prog < rest then pt.prog = math.min(rest, pt.prog + step) else pt.prog = math.max(rest, pt.prog - step) end
    end
    if pt.prog >= 1.0 then pt.owner = CFG.FRIENDLY_TEAM
    elseif pt.prog <= -1.0 then pt.owner = CFG.ENEMY_TEAM
    elseif (pt.owner == CFG.FRIENDLY_TEAM and pt.prog <= 0) or (pt.owner == CFG.ENEMY_TEAM and pt.prog >= 0) then pt.owner = nil end
    return pt.owner ~= before
end

S.pointsT = nil
-- Recarrega municao; a base (rts.base) tambem e deposito (supplyTick), senao perder todos os pontos
-- deixaria o esquadrao sem tiro nenhum.
local function resupply(m, dt, rate, dep)
    local full = weapon(m).ammo
    if (m.ammo or full) >= full then return end
    local add = math.min(full * (rate or CFG.AMMO_REFILL) * dt, full - (m.ammo or full))
    if dep then  -- deposito da logistica: cada caixa de municao vale LOGI.reloads carregamentos completos
        local need = add / full / CFG.LOGI.reloads
        if (dep.ammo or 0) < need then dep.dryT = now(); return end
        dep.ammo = dep.ammo - need
    end
    m.ammo = math.min(full, m.ammo + add)
    if m.ammo >= 1 then m.dry = nil end
    combat.resupplied = (combat.resupplied or 0) + add
end

-- Caixas de suprimento (Ctrl+6, dropCrate): deposito temporario lancado sob o cursor.
CFG.CRATE = { cost = 25, life = 60.0, radius = 450.0, refill = 0.25, max = 3, cooldown = 10.0,
    mesh = "/Game/Meshes/Environment/Props/AmmoCrate.AmmoCrate", scale = { X = 1.5, Y = 1.5, Z = 1.5 } }
S.crates = {}

local function clearCrates()
    for _, c in ipairs(S.crates) do if valid(c.actor) then pcall(function() c.actor:K2_DestroyActor() end) end end
    S.crates = {}
end

-- Caixinha de municao sobre a cabeca de quem esta com municao baixa (so no modo RTS); a cada 0,5 s.
local function ammoIcons()
    for _, m in ipairs(squad) do
        local want = rts.active and alive(m) and ammoFrac(m) < CFG.AMMO_LOW
        if want and not (m.ammoIcon and valid(m.ammoIcon)) then
            local l = loc(m)
            local a = meshActor(l.X, l.Y, l.Z + 190, CFG.CRATE.mesh, { X = 0.6, Y = 0.6, Z = 0.6 })
            if a then a:K2_AttachToActor(m.pawn, FName("None"), 1, 1, 1, false); m.ammoIcon = a end
        end
        if m.ammoIcon and valid(m.ammoIcon) then m.ammoIcon:SetActorHiddenInGame(not want) end
    end
end

local function supplyTick(dt)
    local t = now()
    if t >= (S.ammoIconT or 0) then S.ammoIconT = t + 0.5; pcall(ammoIcons) end
    for i = #S.crates, 1, -1 do
        local c = S.crates[i]
        if t >= c.untilT then
            if valid(c.actor) then pcall(function() c.actor:K2_DestroyActor() end) end
            table.remove(S.crates, i)
            notify("caixa de suprimentos esgotada", 2.0)
        end
    end
    pcall(rts.areaMarkTick)
    if #S.tents > 0 then
        for _, m in ipairs(squad) do
            if alive(m) and suppression(m) < CFG.TENT.calm then
                local here = loc(m)
                for _, tn in ipairs(S.tents) do
                    if flatDist(here, tn) <= CFG.TENT.radius then
                        local pw = m.pawn
                        local maxh = pw.MaxHealth or 100
                        pcall(function() if pw.bIsBleeding then pw.bIsBleeding = false; pw:OnRep_IsBleeding() end end)
                        if (pw.Health or 0) < maxh then
                            pw.Health = math.min(maxh, pw.Health + CFG.TENT.heal * dt)
                            pcall(function() pw:OnRep_Health() end)
                        end
                        break
                    end
                end
            end
        end
    end
    local ok, base = pcall(rts.base)
    if not ok then base = nil end
    for _, m in ipairs(squad) do
        if alive(m) and m.ammo then
            local here = loc(m)
            if base and flatDist(here, base) <= CFG.POINT_RADIUS then
                resupply(m, dt, nil, logi.on and logi.base or nil)
            else
                for _, c in ipairs(S.crates) do
                    if flatDist(here, c) <= CFG.CRATE.radius then resupply(m, dt, CFG.CRATE.refill); break end
                end
            end
        end
    end
end

local function pointsTick()
    local t = now()
    local dt = S.pointsT and math.min(t - S.pointsT, 1.0) or 0
    S.pointsT = t
    if dt > 0 then pcall(supplyTick, dt) end
    if #points == 0 or dt <= 0 then return end
    for _, pt in ipairs(points) do
        local nA, nB = presence(squad, pt), presence(enemies, pt)
        if nB > 0 and pt.owner == CFG.FRIENDLY_TEAM then
            pcall(rts.alert, "ataque", pt, string.format("ponto %s sob ataque (%d inimigos)", pt.name, nB))
        end
        if pointStep(pt, nA, nB, dt) then
            pointVisual(pt)
            if pt.owner == CFG.FRIENDLY_TEAM then
                notify("ponto " .. pt.name .. " capturado", 4.0)
                if combat.mode == "assault" then pcall(rts.counter) end  -- contra-ataque logo
            elseif pt.owner == CFG.ENEMY_TEAM then
                -- o inimigo se entrincheira no ponto tomado (de graca); a trincheira serve a quem estiver dentro
                local dug = CFG.ENEMY_DIG and not pt.dug and fort.place({ X = pt.X, Y = pt.Y })
                if dug then pt.dug = true end
                if CFG.ENEMY_WIRE and not pt.wired then pcall(fort.enemyWire, pt) end
                if pt.dep then for _, kind in ipairs(CFG.LOGI.products) do pt.dep[kind] = 0 end end  -- estoque perdido
                pcall(rts.alert, "perdido", pt, "o inimigo tomou o ponto " .. pt.name .. (dug and " e cavou uma trincheira" or ""))
            else notify("ponto " .. pt.name .. " neutralizado", 3.0) end
        end
    end
    local own = pointsOwned(CFG.FRIENDLY_TEAM)
    if own > 0 then earn(own * CFG.POINT_INCOME * dt) end
    -- ponto nosso e posto de socorro e deposito: dentro do anel recarrega AMMO_REFILL do carregamento
    -- por s; sem supressao recente, tambem recupera POINT_HEAL HP/s
    for _, m in ipairs(squad) do
        if alive(m) then
            local inPoint = false
            for _, pt in ipairs(points) do
                if pt.owner == CFG.FRIENDLY_TEAM and flatDist(loc(m), pt) <= CFG.POINT_RADIUS then inPoint = pt; break end
            end
            if inPoint then
                resupply(m, dt, nil, logi.on and logi.depotOf(inPoint) or nil)
                local p = m.pawn
                local maxh = p.MaxHealth or 100
                if suppression(m) < 0.05 and (p.Health or 0) < maxh then
                    p.Health = math.min(maxh, p.Health + CFG.POINT_HEAL * dt)
                    pcall(function() p:OnRep_Health() end)
                end
            end
        end
    end
end

-- Logistica v1 (lote 12; ESTUDO_MECANICAS.md). Cadeia: campo de sucata -> caminhao de recurso -> refinaria
-- (2 sucata = 1 bmat) -> fabrica (caixas com o custo e o tempo da tabela do jogo x LOGI.time) -> caminhoes de
-- suprimento -> depositos (base e pontos nossos). Recrutar gasta uma camisa do deposito onde o soldado nasce;
-- recarregar gasta caixas de municao do deposito. Lugares: os predios do proprio mapa (o mais perto da base);
-- sem eles, a partida recusa iniciar. Caminhoes: os BPTruckW_C ativos do mapa, movidos pelo mod em linha reta
-- (o movimento deles e de personagem, sem fisica: K2_SetActorLocation fica). Inimigo a LOGI.ambush de um caminhao
-- em movimento o danifica; destruido, perde a carga e volta em LOGI.rebuild s por LOGI.truckCost bmat.
CFG.LOGI = {
    time = 0.2, refine = 4.0, ratio = 2,                     -- tempos da fabrica x0,2; refinaria 4 sucata/s, 2:1
    bmat0 = 240, ammo0 = 6, shirts0 = 30,                     -- inicio: bmat na fabrica; caixas e camisas na base
    trip = 100, load = 4.0, speed = 1400.0, cap = 15,         -- sucata por viagem, s carregando, cm/s, caixas
    reloads = 6,                                              -- carregamentos completos por caixa de municao
    want = { ammo = 6, shirts = 20, rifle = 4, medical = 20 },
    products = { "ammo", "shirts", "rifle", "medical" },                         -- alvo por deposito
    recipes = { ammo = { name = "munição", bmat = 80, time = 50 }, shirts = { name = "camisas", bmat = 80, time = 80, units = 10 },
        rifle = { name = "fuzis", bmat = 100, time = 70, units = 20 },
        medical = { name = "bandagens", bmat = 80, time = 40, units = 50 } },
    hp = 900, ambush = 1500.0, dps = 25.0, rebuild = 30.0, truckCost = 100, supply = 2,
}
logi.on, logi.prio = false, "auto"

function logi.reset()
    for _, tr in ipairs(logi.trucks or {}) do
        if tr.icon and valid(tr.icon) then pcall(function() tr.icon:K2_DestroyActor() end) end
        tr.icon = nil
        if tr.pawn and valid(tr.pawn) then pcall(function() tr.pawn:SetActorHiddenInGame(false) end) end
    end
    for _, tr in ipairs(logi.foes or {}) do
        if tr.icon and valid(tr.icon) then pcall(function() tr.icon:K2_DestroyActor() end) end
        if tr.pawn and valid(tr.pawn) then pcall(function() tr.pawn:K2_DestroyActor() end) end
    end
    logi.foes, logi.convoyT, logi.en, combat.cargo = {}, nil, nil, 0
    logi.on, logi.trucks, logi.job, logi.pin, logi.t = false, {}, nil, nil, nil
    logi.salvage, logi.bmat, logi.made = 0, 0, 0
    logi.fac = { ammo = 0, shirts = 0, rifle = 0, medical = 0 }
end

-- Ator ativo mais perto de ref; invisibilidade nao e ausencia.
function logi.nearest(cls, ref)
    local best, bd = nil, math.huge
    for _, a in ipairs(FindAllOf(cls) or {}) do
        if valid(a) and not a.bActorIsBeingDestroyed then
            local l = a:K2_GetActorLocation()
            local d = flatDist(ref, l)
            if d < bd then best, bd = a, d end
        end
    end
    return best
end

function logi.site(cls, ref)
    local a = logi.nearest(cls, ref)
    if not a then return nil end
    local l = a:K2_GetActorLocation()
    return { X = l.X, Y = l.Y, Z = l.Z }
end

function logi.place(tr, x, y)
    local z = groundZ(x, y) or tr.Z or 0
    tr.X, tr.Y, tr.Z = x, y, z
    if tr.pawn and valid(tr.pawn) then tr.pawn:K2_SetActorLocation({ X = x, Y = y, Z = z + tr.off }, false, {}, true) end
end

-- Apenas atores ativos carregados: nao infere existencia por visibilidade, nem substitui
-- uma ruina/instalacao ausente por coordenadas imaginarias. Construir/reconstruir e outra mecanica.
function logi.scan()
    local b = rts.base()
    if not b then return nil, "sem base" end
    local setup = { field = logi.site("BPSalvageField_C", b), refinery = logi.site("BPRefinery_C", b), trucks = {} }
    setup.factory = logi.site("BPFactory_C", setup.refinery or b)
    for _, a in ipairs(FindAllOf("BPTruckW_C") or {}) do
        if valid(a) and not a.bActorIsBeingDestroyed then setup.trucks[#setup.trucks + 1] = a end
    end
    local missing = {}
    for _, pair in ipairs({ {"field", "campo de sucata"}, {"refinery", "refinaria"}, {"factory", "fábrica"} }) do
        if not setup[pair[1]] then missing[#missing + 1] = pair[2] end
    end
    if #setup.trucks < CFG.LOGI.supply + 1 then
        missing[#missing + 1] = string.format("caminhões (%d/%d)", #setup.trucks, CFG.LOGI.supply + 1)
    end
    if #missing > 0 then return nil, "sem atores ativos carregados: " .. table.concat(missing, ", ") end
    table.sort(setup.trucks, function(x, y) return flatDist(setup.factory, x:K2_GetActorLocation()) < flatDist(setup.factory, y:K2_GetActorLocation()) end)
    return setup
end

-- Implantacao inicial propria do mod, NAO conclusao do canteiro/inventario do jogo.
-- Orcamento de cenario separado do estoque de producao; custos conferidos no lote 16.
CFG.DEPLOY = { budget = 1100, truckCost = 100, off = 174, radius = 160, half = 220,
    spacing = 850, maxSlope = 60, maxHeight = 250, range = 40000,
    truck = "/Game/Blueprints/Vehicles/Truck/BPTruckW.BPTruckW_C",
    sites = { { active = "BPRefinery_C", ruin = "BPDestroyedRefinery_C", cost = 400, hp = 2700, code = "Refinery",
                asset = "/Game/Blueprints/Structures/BPRefinery.BPRefinery_C" },
              { active = "BPFactory_C", ruin = "BPDestroyedFactory_C", cost = 400, hp = 2000, code = "Factory",
                asset = "/Game/Blueprints/Structures/BPFactory.BPFactory_C" } } }

function logi.deployWallet()
    local id = world():GetFullName() .. ":" .. tostring(world():GetAddress())
    if not S.deploy or S.deploy.world ~= id then S.deploy = { world = id, bmat = CFG.DEPLOY.budget, spent = 0 } end
    return S.deploy
end

-- Apenas terreno, nunca telhado. Restricao conservadora ao nivel da instalacao.
function logi.parkingGround(x, y, ref)
    local h = {}
    if not ksl():LineTraceSingle(world(), { X=x, Y=y, Z=20000 }, { X=x, Y=y, Z=-5000 },
        0, false, {}, 0, h, true, CFG.NOCOL, CFG.NOCOL, 0) then return nil end
    local a = h.Actor and h.Actor:get()
    if not valid(a) or not a:GetClass():GetFName():ToString():find("Landscape", 1, true) then return nil end
    local z = h.ImpactPoint.Z
    if math.abs(z - ref.Z) > CFG.DEPLOY.maxHeight then return nil end
    return z
end

function logi.parking(ref, n, occupied)
    local C, slots = CFG.DEPLOY, {}
    occupied = occupied or {}
    for ring = 1, 6 do
        for k = 0, 11 do
            local yaw = k * math.pi / 6
            local dx, dy = math.cos(yaw), math.sin(yaw)
            local x, y = ref.X + dx * ring * 700, ref.Y + dy * ring * 700
            local z = logi.parkingGround(x, y, ref)
            local good = z ~= nil
            for _, p in ipairs(occupied) do
                if flatDist({X=x,Y=y}, p) < C.spacing then good = false; break end
            end
            if good then
                for _, corner in ipairs({{-C.half,-C.radius},{-C.half,C.radius},{C.half,-C.radius},{C.half,C.radius}}) do
                    local gz = logi.parkingGround(x+dx*corner[1]-dy*corner[2], y+dy*corner[1]+dx*corner[2], ref)
                    if not gz or math.abs(gz-z) > C.maxSlope then good = false; break end
                end
            end
            if good and not ksl():SphereTraceSingle(world(),
                {X=x-dx*C.half,Y=y-dy*C.half,Z=z+C.radius+40},
                {X=x+dx*C.half,Y=y+dy*C.half,Z=z+C.radius+40}, C.radius,
                CFG.MOVE_CHANNEL, false, {}, 0, {}, true, CFG.NOCOL, CFG.NOCOL, 0) then
                local p = { X=x, Y=y, Z=z, Yaw=math.deg(yaw) }
                slots[#slots+1], occupied[#occupied+1] = p, p
                if #slots == n then return slots end
            end
        end
    end
    return nil
end

-- Preflight sem alterar atores; exponivel pelo canal para conferir custo/vagas antes de aplicar.
function logi.deployPlan()
    if not rts.active or not isLocalAuthority() then return nil, "precisa de RTS e autoridade local" end
    if logi.on then return nil, "logística já está ativa" end
    if logi.scan() then return { builds={}, parking={}, cost=0 } end
    local field = logi.site("BPSalvageField_C", rts.base())
    if not field then return nil, "sem campo de sucata ativo carregado" end
    local plan, ref = { builds={}, cost=0 }, field
    for _, spec in ipairs(CFG.DEPLOY.sites) do
        local a = logi.nearest(spec.active, ref)
        if not a then
            local ruin = logi.nearest(spec.ruin, ref)
            if not ruin or flatDist(ref, ruin:K2_GetActorLocation()) > CFG.DEPLOY.range then
                return nil, "sem local nativo próximo: " .. spec.ruin
            end
            local cls = LoadAsset(spec.asset)
            if not valid(cls) then return nil, "classe não carregou: " .. spec.active end
            local hidden, collision = ruin.bHidden, ruin:GetActorEnableCollision()
            if type(hidden) ~= "boolean" or type(collision) ~= "boolean" then return nil, "não leu estado da ruína" end
            plan.builds[#plan.builds+1] = { spec=spec, ruin=ruin, cls=cls, hidden=hidden, collision=collision,
                pos=ruin:K2_GetActorLocation(), rot=ruin:K2_GetActorRotation() }
            plan.cost, a = plan.cost + spec.cost, ruin
        end
        ref = a:K2_GetActorLocation()
    end
    local occupied = {}
    for _, a in ipairs(FindAllOf("BPTruckW_C") or {}) do
        if valid(a) and not a.bActorIsBeingDestroyed then occupied[#occupied+1] = a:K2_GetActorLocation() end
    end
    local missing = math.max(0, CFG.LOGI.supply+1-#occupied)
    plan.cost = plan.cost + missing * CFG.DEPLOY.truckCost
    if plan.cost > logi.deployWallet().bmat then return nil, "orçamento de implantação insuficiente" end
    if missing > 0 then plan.parking = logi.parking(ref, missing, occupied) else plan.parking = {} end
    if not plan.parking then return nil, "sem vagas de terreno com folga para caminhões" end
    if missing > 0 then
        plan.truckClass = LoadAsset(CFG.DEPLOY.truck)
        if not valid(plan.truckClass) then return nil, "classe TruckW não carregou" end
    end
    return plan
end

function logi.deploy()
    local ok, plan, why = pcall(logi.deployPlan)
    if not ok or not plan then notify("Implantação recusada: " .. tostring(ok and why or plan), 6); return false end
    if plan.cost == 0 then notify("Cadeia já implantada. Shift+F6 inicia a partida.", 4); return true end
    local created, touched = {}, {}
    ok, why = pcall(function()
        for _, b in ipairs(plan.builds) do
            assert(valid(b.ruin) and not b.ruin.bActorIsBeingDestroyed, "ruína deixou de existir")
            touched[#touched+1] = b
            b.ruin:SetActorHiddenInGame(true); b.ruin:SetActorEnableCollision(false)
            local a = world():SpawnActor(b.cls, b.pos, b.rot)
            if valid(a) then created[#created+1] = a end
            assert(valid(a) and not a.bActorIsBeingDestroyed, "estrutura não nasceu ativa")
            assert(a.Health == b.spec.hp and a.MaxHealth == b.spec.hp and a.CodeName:ToString() == b.spec.code, "contrato da estrutura divergiu")
            assert(valid(a.BaseStructureClass) and a.BaseStructureClass:GetFullName() == b.ruin:GetClass():GetFullName(), "ruína incompatível")
            local l = a:K2_GetActorLocation()
            assert(flatDist(l, b.pos) < 100 and math.abs(l.Z-b.pos.Z) < 100, "estrutura deslocada")
            assert(math.abs(a:K2_GetActorRotation().Yaw-b.rot.Yaw) < 1, "rotação da estrutura divergiu")
            a.TeamId = CFG.FRIENDLY_TEAM
        end
        for _, p in ipairs(plan.parking) do
            local a = world():SpawnActor(plan.truckClass, {X=p.X,Y=p.Y,Z=p.Z+CFG.DEPLOY.off}, {Pitch=0,Yaw=p.Yaw,Roll=0})
            if valid(a) then created[#created+1] = a end
            assert(valid(a) and not a.bActorIsBeingDestroyed and a.Health == CFG.LOGI.hp, "caminhão não nasceu íntegro")
            local l = a:K2_GetActorLocation()
            assert(flatDist(l,p) < 150 and math.abs(l.Z-p.Z-CFG.DEPLOY.off) < 100, "caminhão deslocado")
            a.TeamId = CFG.FRIENDLY_TEAM
        end
        local setup, missing = logi.scan()
        assert(setup, missing)
    end)
    if not ok then
        for _, a in ipairs(created) do
            if valid(a) and not a.bActorIsBeingDestroyed then pcall(function() a:K2_DestroyActor() end) end
        end
        for _, b in ipairs(touched) do
            if valid(b.ruin) and not b.ruin.bActorIsBeingDestroyed then
                pcall(function() b.ruin:SetActorHiddenInGame(b.hidden); b.ruin:SetActorEnableCollision(b.collision) end)
            end
        end
        notify("Implantação desfeita, sem débito: " .. tostring(why), 8); return false
    end
    local wallet = logi.deployWallet()
    wallet.bmat, wallet.spent = wallet.bmat-plan.cost, wallet.spent+plan.cost
    -- O desocultador da camera nao deve reexibir a ruina substituida ao sair de foco.
    for _, b in ipairs(touched) do S.occluders[b.ruin] = nil end
    notify(string.format("IMPLANTAÇÃO: -%d bmat do cenário; saldo %d. Shift+F6 inicia (transporte ainda em reta).", plan.cost, wallet.bmat), 10)
    return true
end

function logi.ready()
    local setup, why = logi.scan()
    if not setup then
        log("logistica indisponivel: " .. why)
        notify("Partida não iniciada: " .. why .. ". Alt+L tenta implantação nos locais nativos.", 8.0)
    end
    return setup
end

function logi.start(setup)
    setup = setup or logi.ready()
    if not setup then return false end  -- nao apaga a partida anterior numa recusa
    logi.reset()
    local C, b = CFG.LOGI, rts.base()
    logi.base = { name = "base", X = b.X, Y = b.Y, Z = b.Z, ammo = C.ammo0, shirts = C.shirts0, rifle = 0, medical = 0 }
    logi.field, logi.refinery, logi.factory = setup.field, setup.refinery, setup.factory
    logi.bmat = C.bmat0
    combat.convoys, combat.convoysCut = 0, 0
    logi.eReset()
    logi.convoyT = now() + CFG.ECONVOY.first
    local pool = setup.trucks
    for i = 1, C.supply + 1 do
        local a = pool[i]
        local tr = { kind = (i == 1) and "res" or "sup", pawn = a, hp = C.hp, off = 0, state = "idle", n = i }
        if a then
            local l = a:K2_GetActorLocation()
            tr.off = l.Z - (groundZ(l.X, l.Y) or l.Z)
            pcall(function() a:SetActorEnableCollision(false) end)  -- atravessa o que houver no caminho
            logi.place(tr, l.X, l.Y)  -- preservar estacionamento real, nao teletransportar para offset de predio
        end
        logi.trucks[i] = tr
    end
    logi.on = true
    log(string.format("logistica: campo (%.0f, %.0f) refinaria (%.0f, %.0f) fabrica (%.0f, %.0f), %d caminhoes do mapa",
        logi.field.X, logi.field.Y, logi.refinery.X, logi.refinery.Y, logi.factory.X, logi.factory.Y, math.min(#pool, C.supply + 1)))
    return true
end

-- Deposito de um ponto (criado na primeira vez, vazio).
function logi.depotOf(pt)
    pt.dep = pt.dep or { name = pt.name, X = pt.X, Y = pt.Y, Z = pt.Z, ammo = 0, shirts = 0, rifle = 0, medical = 0, pt = pt }
    return pt.dep
end

function logi.depots()
    local list = { logi.base }
    for _, pt in ipairs(points) do
        if pt.owner == CFG.FRIENDLY_TEAM then list[#list + 1] = logi.depotOf(pt) end
    end
    return list
end

-- Falta de um deposito (caixas de municao, caixas de camisa), descontando o que ja vai a caminho.
function logi.needs(dep)
    local C, result = CFG.LOGI, {}
    for _, kind in ipairs(C.products) do
        local units = C.recipes[kind].units or 1
        local missing = C.want[kind] - (dep[kind] or 0)
        for _, tr in ipairs(logi.trucks) do
            if tr.state ~= "dead" and tr.dest == dep and tr.cargo then missing = missing - (tr.cargo[kind] or 0) * units end
        end
        local rounding = (kind == "ammo" or kind == "shirts") and 0.5 or 0
        result[kind] = math.max(0, math.ceil(missing / units - rounding))
    end
    return result
end
function logi.need(dep)
    local n = logi.needs(dep)
    return n.ammo, n.shirts
end
function logi.nextKind()
    local C = CFG.LOGI
    if logi.prio ~= "auto" then return C.recipes[logi.prio] and logi.prio or nil end
    local deps, best, ratio = logi.depots(), nil, 2.0
    for _, kind in ipairs(C.products) do
        local units = C.recipes[kind].units or 1
        local have = (logi.fac[kind] or 0) * units
        for _, d in ipairs(deps) do have = have + (d[kind] or 0) end
        for _, tr in ipairs(logi.trucks) do
            if tr.state ~= "dead" and tr.cargo then have = have + (tr.cargo[kind] or 0) * units end
        end
        if logi.job and logi.job.kind == kind then have = have + units end
        local r = have / (C.want[kind] * #deps)
        if r < ratio then best, ratio = kind, r end
    end
    return best
end
-- Comprimento de estoque/cargo centralizado: caixas -> caixas (retorno) ou unidades (depósito).
function logi.moveCargo(cargo, dest, unpack)
    for _, kind in ipairs(CFG.LOGI.products) do
        local n = cargo[kind] or 0
        dest[kind] = (dest[kind] or 0) + n * (unpack and (CFG.LOGI.recipes[kind].units or 1) or 1)
    end
end
-- Regra própria: médico recebe uma bandagem de depósito aliado próximo a cada tratamento efetivo.
function logi.medicalDepot(m)
    local here, best, distance = loc(m), nil, CFG.POINT_RADIUS
    for _, dep in ipairs(logi.depots()) do
        local d = flatDist(here, dep)
        if (dep.medical or 0) >= 1 and d <= distance then best, distance = dep, d end
    end
    return best
end

function logi.factoryStep(dt)
    local C = CFG.LOGI
    if logi.job then
        logi.job.left = logi.job.left - dt
        if logi.job.left <= 0 then
            logi.fac[logi.job.kind] = (logi.fac[logi.job.kind] or 0) + 1
            logi.made = logi.made + 1
            logi.job = nil
        end
        return
    end
    local kind = logi.nextKind()
    local rc = kind and C.recipes[kind]
    if not rc or type(rc.bmat) ~= "number" or rc.bmat <= 0 or type(rc.time) ~= "number" or rc.time <= 0 or logi.bmat < rc.bmat then return end
    logi.bmat = logi.bmat - rc.bmat
    logi.job = { kind = kind, left = rc.time * C.time, total = rc.time * C.time }
end

-- Anda tr em direcao a dest; true ao chegar (a 2 m).
function logi.drive(tr, dest, dt, speed)
    local d, dx, dy = flatDist(tr, dest)
    if d <= 200 then return true end
    local stepLen = math.min(d, (speed or CFG.LOGI.speed) * dt)
    logi.place(tr, tr.X + dx / d * stepLen, tr.Y + dy / d * stepLen)
    if tr.pawn and valid(tr.pawn) then
        tr.pawn:K2_SetActorRotation({ Pitch = 0, Yaw = math.deg(math.atan(dy, dx)), Roll = 0 }, false)
    end
    tr.moving = true
    return false
end

-- Deposito para onde o proximo caminhao vai: o fixado pelo jogador (L), senao o mais carente.
function logi.pickDest()
    if logi.pin then
        if logi.pin == logi.base or (logi.pin.pt and logi.pin.pt.owner == CFG.FRIENDLY_TEAM) then return logi.pin end
        logi.pin = nil
    end
    local best, score = nil, 0
    for _, d in ipairs(logi.depots()) do
        local needs, n = logi.needs(d), 0
        for _, kind in ipairs(CFG.LOGI.products) do n = n + needs[kind] * (CFG.LOGI.recipes[kind].units or 1) / CFG.LOGI.want[kind] end
        if n > score then best, score = d, n end
    end
    return best
end

function logi.truckStep(tr, dt, t)
    local C = CFG.LOGI
    tr.moving = false
    if tr.state == "dead" then
        if t >= tr.rebuildT and logi.bmat >= C.truckCost then
            logi.bmat = logi.bmat - C.truckCost
            tr.hp, tr.state, tr.cargo, tr.dest, tr.salv = C.hp, "idle", nil, nil, nil
            local home = tr.kind == "res" and logi.field or logi.factory
            logi.place(tr, home.X + 400, home.Y + 300)
            if tr.pawn and valid(tr.pawn) then tr.pawn:SetActorHiddenInGame(false) end
            notify("novo caminhão pronto na fábrica (-" .. C.truckCost .. " bmat)", 3.0)
        end
        return
    end
    if tr.kind == "res" then
        if tr.state == "idle" or tr.state == "toField" then
            tr.state = "toField"
            if logi.drive(tr, logi.field, dt) then tr.state, tr.waitT = "loading", t + C.load end
        elseif tr.state == "loading" then
            if t >= tr.waitT then tr.state, tr.salv = "toRef", C.trip end
        elseif tr.state == "toRef" then
            if logi.drive(tr, logi.refinery, dt) then
                logi.salvage = logi.salvage + (tr.salv or 0)
                tr.salv, tr.state = nil, "toField"
            end
        end
        return
    end
    if tr.state == "idle" then
        if not logi.drive(tr, logi.factory, dt) then return end
        local ready = 0
        for _, kind in ipairs(C.products) do ready = ready + (logi.fac[kind] or 0) end
        if ready < 1 then return end
        local dest = logi.pickDest()
        if not dest then return end
        local needs, cargo, remaining = logi.needs(dest), {}, C.cap
        for _, kind in ipairs(C.products) do
            local stock = logi.fac[kind] or 0
            local wanted = logi.pin == dest and stock or needs[kind]
            local n = math.min(stock, wanted, remaining)
            cargo[kind], remaining = n, remaining - n
        end
        if remaining == C.cap then return end
        for _, kind in ipairs(C.products) do logi.fac[kind] = (logi.fac[kind] or 0) - cargo[kind] end
        tr.cargo, tr.dest, tr.state = cargo, dest, "toDep"
        if logi.pin == dest then logi.pin = nil end
    elseif tr.state == "returnCargo" then
        if not tr.cargo then tr.dest, tr.state = nil, "idle"; return end
        -- Crédito apenas após chegada confirmada; driver seguro de ESTRADAS é gate de integração.
        if logi.drive(tr, logi.factory, dt) then
            logi.moveCargo(tr.cargo, logi.fac, false)
            tr.cargo, tr.dest, tr.state = nil, nil, "idle"
        end
    elseif tr.state == "toDep" then
        local d = tr.dest
        if d ~= logi.base and not (d.pt and d.pt.owner == CFG.FRIENDLY_TEAM) then  -- ponto perdido no caminho: volta
            tr.dest, tr.state = logi.factory, "returnCargo"
            tr.route, tr.routeDest, tr.pathJob = nil, nil, nil
            return
        end
        if logi.drive(tr, d, dt) then
            logi.moveCargo(tr.cargo, d, true)
            notify(string.format("caminhão entregou em %s: %d munição, %d camisas, %d fuzis, %d bandagens",
                d.name, tr.cargo.ammo or 0, (tr.cargo.shirts or 0) * C.recipes.shirts.units,
                (tr.cargo.rifle or 0) * C.recipes.rifle.units, (tr.cargo.medical or 0) * C.recipes.medical.units), 3.0)
            logi.delivered = (logi.delivered or 0) + 1
            tr.cargo, tr.dest, tr.state = nil, nil, "idle"
        end
    end
end

-- Emboscada: inimigo vivo perto de um caminhao em movimento tira vida; destruido, some com a carga.
function logi.ambushStep(tr, dt, t)
    if tr.state == "dead" or not tr.moving then return end
    local n = 0
    for _, e in ipairs(enemies) do
        if alive(e) and flatDist(loc(e), tr) <= CFG.LOGI.ambush then n = n + 1 end
    end
    if n == 0 then return end
    pcall(rts.alert, "sobfogo", tr, "caminhão sob fogo")
    logi.hit(tr, n * CFG.LOGI.dps * dt, t)
end

function logi.tick()
    if not logi.on then return end
    local t = now()
    local dt = math.min(t - (logi.t or t), 0.5)
    logi.t = t
    if dt <= 0 then return end
    local r = math.min(logi.salvage, CFG.LOGI.refine * dt)
    logi.salvage, logi.bmat = logi.salvage - r, logi.bmat + r / CFG.LOGI.ratio
    logi.factoryStep(dt)
    for _, tr in ipairs(logi.trucks) do
        logi.truckStep(tr, dt, t)
        logi.ambushStep(tr, dt, t)
    end
    pcall(logi.convoyTick, dt, t)
    for _, d in ipairs(logi.depots()) do
        if d.dryT and t - d.dryT < 1.0 then
            pcall(rts.alert, "seco", d, d == logi.base and "base sem munição" or ("ponto " .. d.name .. " sem munição"))
        end
    end
end

-- L: o proximo caminhao vai ao deposito sob o cursor (base ou ponto nosso); fora deles volta ao automatico.
function logi.sendTo(c)
    if not logi.on then notify("logística só numa partida (Shift+F6)", 3.0); return end
    if not c then return end
    local pick = nil
    for _, d in ipairs(logi.depots()) do
        if flatDist(c, d) <= CFG.POINT_RADIUS * 1.5 then pick = d; break end
    end
    logi.pin = pick
    notify(pick and ("próximo caminhão vai para " .. (pick == logi.base and "a base" or ("o ponto " .. pick.name)))
        or "caminhões no automático (vão ao depósito mais carente)", 3.0)
end

-- Shift+L: prioridade da fabrica (automatico -> municao -> camisas).
function logi.cyclePrio()
    local order = { "auto", "ammo", "shirts", "rifle", "medical" }
    local i = 1
    for k, v in ipairs(order) do if v == logi.prio then i = k end end
    logi.prio = order[i % #order + 1]
    notify("fábrica: " .. (logi.prio == "auto" and "automático" or CFG.LOGI.recipes[logi.prio].name), 2.5)
end

-- Ctrl+L: camera passa por fabrica, refinaria, campo de sucata e caminhoes.
function logi.cycleView()
    if not logi.on then return end
    local stops = { { logi.factory, "fábrica" }, { logi.refinery, "refinaria" }, { logi.field, "campo de sucata" } }
    for _, tr in ipairs(logi.trucks) do
        if tr.state ~= "dead" then stops[#stops + 1] = { tr, (tr.kind == "res" and "caminhão de recurso " or "caminhão de suprimentos ") .. tr.n } end
    end
    logi.viewI = (logi.viewI or 0) % #stops + 1
    local s = stops[logi.viewI]
    focusOn(s[1].X, s[1].Y, s[1].Z)
    notify(s[2], 2.0)
end

function logi.extraHud()
    local parts = { string.format("Fuzis: fábrica %d caixas | bandagens: fábrica %d caixas", logi.fac.rifle or 0, logi.fac.medical or 0) }
    for _, dep in ipairs(logi.depots()) do parts[#parts+1] = string.format("%s: %d fuzis, %d bandagens", dep.name, dep.rifle or 0, dep.medical or 0) end
    for i, tr in ipairs(logi.trucks) do
        if tr.cargo then parts[#parts+1] = string.format("caminhão %d -> %s: %d caixas fuzis, %d caixas bandagens", i,
            tr.dest and tr.dest.name or "—", tr.cargo.rifle or 0, tr.cargo.medical or 0) end
    end
    return "\n" .. table.concat(parts, " | ")
end

function logi.hudLine()
    local C = CFG.LOGI
    local fab = logi.job and string.format("%s %.0f s", C.recipes[logi.job.kind].name, logi.job.left)
        or (logi.nextKind() and "sem bmat" or "parada (estoque cheio)")
    if logi.prio ~= "auto" then fab = fab .. " [só " .. C.recipes[logi.prio].name .. "]" end
    local moving, dead = 0, 0
    for _, tr in ipairs(logi.trucks) do
        if tr.state == "dead" then dead = dead + 1 elseif tr.state == "toDep" then moving = moving + 1 end
    end
    local deps = {}
    for _, d in ipairs(logi.depots()) do
        deps[#deps + 1] = string.format("%s m%.0f c%d", d == logi.base and "base" or d.name, d.ammo or 0, d.shirts or 0)
    end
    local foe = ""
    if combat.mode ~= "assault" then
        foe = logi.eHud()
    end
    return string.format("LOGÍSTICA | sucata %.0f > bmat %.0f | fábrica: %s, pronto m%d c%d | entregando %d%s | %s%s",
        logi.salvage, logi.bmat, fab, logi.fac.ammo, logi.fac.shirts, moving, dead > 0 and string.format(", %d destruído", dead) or "",
        table.concat(deps, " | "), foe) .. logi.extraHud()
end

-- Comboio inimigo (lote 13): com ondas automaticas (fora do assalto), a cada ECONVOY.every s um caminhao colonial
-- sai da retaguarda (ECONVOY.rear cm da base, do lado de onde veio a ultima onda) e vai ate a frente
-- (ECONVOY.front) levando caixas reais da retaguarda inimiga (CFG.ECHAIN, logi.e*); a onda so recebe, alem da
-- guarnicao gratuita, os soldados que a frente equipa. Nossos soldados a LOGI.ambush do caminhao o danificam (com tiro visivel) e o
-- morteiro tambem (logi.blast); destruido rende bounty de mao de obra. A rota e uma reta: da para emboscar.
CFG.ECONVOY = { first = 20.0, every = 35.0, rear = { 20000.0, 16000.0, 12000.0, 9000.0 }, front = 4500.0, speed = 900.0,
                hp = 900, bounty = 25, retry = 5.0, off = 174.0, fx = 0.8,
                sample = 1000.0, step = 400.0, climb = 1500.0,
                class = "/Game/Blueprints/Vehicles/Truck/BPTruckC.BPTruckC_C" }

-- Rota transitavel: chao a cada ECONVOY.sample cm, sem degrau maior que ECONVOY.step nem desnivel total maior que
-- ECONVOY.climb em relacao a base (senao o caminhao subia penhascos: captura b13_conv.png). Tenta primeiro a
-- direcao da ultima onda, depois o resto da volta.
function logi.routeOk(x1, y1, x2, y2, z0)
    local E = CFG.ECONVOY
    local len = math.sqrt((x2 - x1) ^ 2 + (y2 - y1) ^ 2)
    local n = math.max(1, math.floor(len / E.sample))
    local prev = nil
    for i = 0, n do
        local f = i / n
        local z = groundZ(x1 + (x2 - x1) * f, y1 + (y2 - y1) * f)
        if not z or math.abs(z - z0) > E.climb or (prev and math.abs(z - prev) > E.step) then return false end
        prev = z
    end
    return true
end

function logi.convoyRoute()
    local c, E = logi.base, CFG.ECONVOY
    local ls = combat.lastSpawn
    local a0 = ls and math.atan(ls.Y - c.Y, ls.X - c.X) or math.random() * 2 * math.pi
    for _, dist in ipairs(E.rear) do
        for k = 0, 17 do
            local a = a0 + ((k % 2 == 0) and 1 or -1) * math.floor((k + 1) / 2) * math.rad(20)
            local x, y = c.X + math.cos(a) * dist, c.Y + math.sin(a) * dist
            local fx, fy = c.X + math.cos(a) * E.front, c.Y + math.sin(a) * E.front
            if logi.routeOk(x, y, fx, fy, c.Z) then
                return { X = x, Y = y, Z = groundZ(x, y) }, { X = fx, Y = fy, Z = groundZ(fx, fy) or c.Z }
            end
        end
    end
    return nil
end

-- Dano num caminhao (nosso ou inimigo); true se destruiu.
function logi.hit(tr, amount, t)
    if tr.state == "dead" then return false end
    tr.hp = tr.hp - amount
    if tr.hp > 0 then return false end
    pcall(emit, CFG.MORTAR.fx, { X = tr.X, Y = tr.Y, Z = tr.Z + 100 })
    if tr.team == CFG.ENEMY_TEAM then
        tr.state = "dead"
        if tr.pawn and valid(tr.pawn) then pcall(function() tr.pawn:SetActorHiddenInGame(true) end) end
        if tr.icon and valid(tr.icon) then pcall(function() tr.icon:SetActorHiddenInGame(true) end) end
        combat.convoysCut = (combat.convoysCut or 0) + 1
        local lost = logi.eLose(tr, "destruído")
        earn(CFG.ECONVOY.bounty)
        pcall(rts.alert, "comboioX", tr, string.format("COMBOIO INIMIGO DESTRUÍDO (+%d): %s", CFG.ECONVOY.bounty, lost))
        return true
    end
    tr.state, tr.rebuildT, tr.cargo, tr.dest, tr.salv = "dead", t + CFG.LOGI.rebuild, nil, nil, nil
    if tr.pawn and valid(tr.pawn) then tr.pawn:SetActorHiddenInGame(true) end
    logi.lost = (logi.lost or 0) + 1
    pcall(rts.alert, "caminhao", tr, "CAMINHÃO DESTRUÍDO: carga perdida")
    return true
end

-- Morteiro/granada: caminhoes do outro lado a radius levam dmg x2 (alvo grande e parado).
function logi.blast(hit, radius, dmg, team)
    if not logi.on then return end
    local list = (team == CFG.ENEMY_TEAM) and logi.trucks or logi.foes
    for _, tr in ipairs(list) do
        if tr.state ~= "dead" and flatDist(hit, tr) <= radius * 1.5 then logi.hit(tr, dmg * 2, now()) end
    end
end

-- IA_LOGISTICA (proposta 2026-10-09, CLAUDE_IA_LOGISTICA): cadeia inimiga com contabilidade fechada.
-- Inserido por build_patch.py no lugar de convoySpawn/convoyTick/waveCut; NAO cria locais de topo
-- (tudo em CFG.ECHAIN e na tabela logi). Mesmas regras do jogador: sucata por viagem (LOGI.trip), refinaria
-- LOGI.refine/s a LOGI.ratio:1, receitas de CFG.LOGI.recipes (custo/tempo da tabela do jogo x LOGI.time; debito
-- ao iniciar, caixa ao concluir), caminhao de LOGI.cap caixas que custa LOGI.truckCost bmat para reconstruir
-- (TruckC: Cloth100, 900 HP, carga 15 em dados/custos_do_jogo.txt). Producao fica na retaguarda fora do mapa;
-- o trecho retaguarda -> frente e um caminhao real (BPTruckC) movido por logi.drive, o mesmo contrato de rota do
-- jogador (ESTRADAS troca o driver; chegada so com drive == true). Unidades: caixas na retaguarda e na carga;
-- unidades de produto na frente (municao: caixa; camisas: LOGI.recipes.shirts.units).
-- Razao: inicial + produzido == retaguarda + em transito + pendente + frente + consumido + perdido (por produto);
-- bmat0 + refinado/ratio == bmat + gasto; sucata colhida == sucata + refinada. logi.eAudit() confere.
CFG.ECHAIN = {
    kinds = { "ammo", "shirts" },             -- o que a frente inimiga consome (receitas reais em CFG.LOGI.recipes)
    shirts = 1,                               -- camisas por soldado pago (= recrutamento do jogador)
    free = 5,                                 -- BONUS ABSTRATO explicito: guarnicao minima gratuita por onda = piso com a cadeia cortada (v1: 3; calibrado em acabamento/RELATORIO.md)
    trip = 20.0,                              -- s por viagem do caminhao de recurso da retaguarda (v1: 25; > 25 ja enfraquece a onda SEM corte: a refinaria satura em 25 s)
    bmat0 = 240, front0 = { ammo = 2, shirts = 10 },  -- estoque de cenario (entra no razao como "inicial")
    want = { ammo = 4, shirts = 20 },         -- alvo da frente em unidades (~20 soldados; a fabrica para em 2x; v1: 6/30)
    trucks = 2,                               -- frota de comboio (= LOGI.supply do jogador)
    minLoad = 3,                              -- caixas minimas por comboio (ou tudo que a frente pede, se menos)
    stuck = 20.0,                             -- s com rota ausente/bloqueada (driver de ESTRADAS) antes de voltar carregado
    keep = 40,                                -- eventos e registros de onda guardados
    tol = 0.05,                               -- folga do razao lido do save (sv.ser grava numeros com 3 casas)
}

-- Unidades por caixa e consumo por soldado pago. Municao: um carregamento completo = 1/LOGI.reloads caixa.
function logi.eUnits(k) return (CFG.LOGI.recipes[k] and CFG.LOGI.recipes[k].units) or 1 end
function logi.eNeed(k)
    if k == "ammo" then return 1 / CFG.LOGI.reloads end
    return CFG.ECHAIN[k] or 0
end

function logi.eEvent(msg)
    local en = logi.en
    if not en then return end
    en.events[#en.events + 1] = string.format("%.0f %s", now(), msg)
    if #en.events > CFG.ECHAIN.keep then table.remove(en.events, 1) end
    log("cadeia inimiga: " .. msg)
end

-- Estado novo da cadeia (logi.start). Receita sem custo/tempo positivo recusa a cadeia inteira (fail-closed):
-- sem producao, a onda recebe so a guarnicao gratuita; nunca custo zero por erro de schema.
function logi.eReset()
    local E = CFG.ECHAIN
    local en = { salvage = 0, bmat = E.bmat0, tripT = E.trip, job = nil, fac = {}, front = {}, pending = nil,
        ready = E.trucks, rebuild = {}, seq = 0, events = {}, waves = {}, ghost = {}, delivered = 0,
        led = { bmat0 = E.bmat0, salv = 0, refined = 0, spent = 0, init = {}, made = {}, used = {}, lost = {} } }
    for _, k in ipairs(E.kinds) do
        local rc = CFG.LOGI.recipes[k]
        if type(rc) ~= "table" or type(rc.bmat) ~= "number" or rc.bmat <= 0 or type(rc.time) ~= "number" or rc.time <= 0
            or (rc.units ~= nil and (type(rc.units) ~= "number" or rc.units < 1)) then
            en.err = "receita inválida: " .. tostring(k)
        end
        en.fac[k], en.front[k], en.ghost[k] = 0, (E.front0[k] or 0), 0
        en.led.init[k], en.led.made[k], en.led.used[k], en.led.lost[k] = en.front[k], 0, 0, 0
    end
    logi.en = en
    combat.cargo = logi.eSoldiers()
    if en.err then log("cadeia inimiga recusada: " .. en.err) end
    return en
end

-- Ativa so numa partida com logistica e fora do assalto (assalto e partidas sem logistica seguem abstratos).
function logi.eActive()
    return logi.on == true and logi.en ~= nil and combat.mode ~= "assault"
end

-- Soldados que a frente consegue equipar (camisa + carregamento), e o produto que limita.
function logi.eSoldiers(st)
    local en = logi.en
    st = st or (en and en.front)
    if not st then return 0 end
    local n, lim = math.huge, nil
    for _, k in ipairs(CFG.ECHAIN.kinds) do
        local q = logi.eNeed(k)
        if q > 0 then
            local m = math.floor((st[k] or 0) / q + 1e-6)
            if m < n then n, lim = m, k end
        end
    end
    if n == math.huge then return 0, nil end
    return n, lim
end

-- Unidades em transito (comboios vivos + carga pendente de reenvio apos continuar o save).
function logi.eTransit(k)
    local n = 0
    for _, tr in ipairs(logi.foes or {}) do
        if tr.cargo then n = n + (tr.cargo[k] or 0) end
    end
    if logi.en and logi.en.pending then n = n + (logi.en.pending[k] or 0) end
    return n * logi.eUnits(k)
end

function logi.eHave(k)
    local en = logi.en
    return en.fac[k] * logi.eUnits(k) + en.front[k] + logi.eTransit(k)
end

-- Fabrica inimiga: o produto com menos estoque total frente ao alvo; tudo >= 2x o alvo para (regra do jogador).
function logi.eNextKind()
    local en, E = logi.en, CFG.ECHAIN
    local best, ratio = nil, 2.0
    for _, k in ipairs(E.kinds) do
        local have = logi.eHave(k) + ((en.job and en.job.kind == k) and logi.eUnits(k) or 0)
        local r = have / E.want[k]
        if r < ratio then best, ratio = k, r end
    end
    return best
end

-- Producao da retaguarda (pura: sem UE). dt ja limitado pelo chamador (logi.tick: <= 0,5 s).
function logi.eTick(dt, t)
    local en, C, E = logi.en, CFG.LOGI, CFG.ECHAIN
    if not logi.eActive() or en.err or not (dt > 0) then return end
    local L = en.led
    en.tripT = en.tripT - dt
    if en.tripT <= 0 then
        en.tripT = en.tripT + E.trip
        en.salvage, L.salv = en.salvage + C.trip, L.salv + C.trip
    end
    local r = math.min(en.salvage, C.refine * dt)
    en.salvage, L.refined, en.bmat = en.salvage - r, L.refined + r, en.bmat + r / C.ratio
    if en.job then
        en.job.left = en.job.left - dt
        if en.job.left <= 0 then
            local k = en.job.kind
            en.fac[k], L.made[k] = en.fac[k] + 1, L.made[k] + logi.eUnits(k)
            en.job = nil
        end
    end
    -- Reconstrucao antes da fabrica: sem caminhao livre, caixa nova nao anda; a fabrica guarda bmat para ele
    -- (decisao da IA; sem isso a fabrica gastava cada 80 bmat e o caminhao de 100 nunca voltava).
    local due = false
    for i = #en.rebuild, 1, -1 do
        if t >= en.rebuild[i] then
            if en.bmat >= C.truckCost then
                en.bmat, L.spent = en.bmat - C.truckCost, L.spent + C.truckCost
                table.remove(en.rebuild, i)
                en.ready = en.ready + 1
                logi.eEvent(string.format("caminhão de comboio reconstruído (-%d bmat)", C.truckCost))
            else
                due = true
            end
        end
    end
    if not en.job and not (due and en.ready == 0) then
        local k = logi.eNextKind()
        local rc = k and C.recipes[k]
        if rc and en.bmat >= rc.bmat then
            en.bmat, L.spent = en.bmat - rc.bmat, L.spent + rc.bmat
            en.job = { kind = k, left = rc.time * C.time, total = rc.time * C.time }
        end
    end
end

-- Carga do proximo comboio sem debitar: primeiro a pendente (save), senao o que falta na frente, ate LOGI.cap caixas.
function logi.eLoad()
    local en, E = logi.en, CFG.ECHAIN
    local cargo, room, boxes, wanted = {}, CFG.LOGI.cap, 0, 0
    local src = en.pending
    for _, k in ipairs(E.kinds) do
        local n
        if src then
            n = math.min(src[k] or 0, room)
        else
            local want = math.ceil(math.max(0, E.want[k] - en.front[k] - logi.eTransit(k)) / logi.eUnits(k) - 1e-9)
            n = math.min(en.fac[k], want, room)
            wanted = wanted + want
        end
        cargo[k], room, boxes = n, room - n, boxes + n
    end
    if boxes < 1 then return nil, false end
    -- Decisao da IA: nao arriscar um caminhao (100 bmat) por uma caixa; sai com ECHAIN.minLoad caixas ou
    -- com tudo o que a frente pede (o que for menor). Carga pendente do save sai sempre.
    if not src and boxes < math.min(E.minLoad, math.min(wanted, CFG.LOGI.cap)) then return nil, false end
    return cargo, src ~= nil
end

function logi.eFmt(c)
    return string.format("%d cx munição, %d cx camisas", c.ammo or 0, c.shirts or 0)
end

-- Comboio: so sai com caminhao livre, carga real e ator ativo; a retaguarda so e debitada depois do spawn.
function logi.convoySpawn(t)
    local en, E = logi.en, CFG.ECONVOY
    if not en or en.err or en.ready < 1 then return false end
    local cargo, fromPending = logi.eLoad()
    if not cargo then return false end  -- sem carga, sem comboio fantasma
    local R, F = logi.convoyRoute()
    if not R then return false end
    local ok, cls = pcall(LoadAsset, E.class)
    if not (ok and cls and cls:IsValid()) then return false end
    local a = world():SpawnActor(cls, { X = R.X, Y = R.Y, Z = R.Z + E.off }, { Pitch = 0, Yaw = 0, Roll = 0 })
    if not valid(a) or a.bActorIsBeingDestroyed then return false end  -- IsValid continua true ate o GC
    local tr = { kind = "foe", team = CFG.ENEMY_TEAM, hp = E.hp, off = E.off, state = "toFront", from = R, to = F,
        n = #logi.foes + 1, cargo = {} }
    pcall(function() a:SetActorEnableCollision(false) end); tr.pawn = a
    logi.place(tr, R.X, R.Y)
    -- transacao: daqui em diante nada falha antes do debito
    local src = fromPending and en.pending or en.fac
    local left = 0
    for _, k in ipairs(CFG.ECHAIN.kinds) do
        tr.cargo[k] = cargo[k] or 0
        src[k] = src[k] - tr.cargo[k]
        left = left + (fromPending and src[k] or 0)
    end
    if fromPending and left == 0 then en.pending = nil end
    en.ready, en.seq = en.ready - 1, en.seq + 1
    tr.id = en.seq
    logi.foes[#logi.foes + 1] = tr
    combat.convoys = (combat.convoys or 0) + 1
    logi.eEvent(string.format("comboio %d saiu: %s", tr.id, logi.eFmt(tr.cargo)))
    pcall(rts.alert, "comboio", { X = (R.X + F.X) / 2, Y = (R.Y + F.Y) / 2, Z = F.Z },
        string.format("COMBOIO INIMIGO a caminho da frente (%s): destrua para enfraquecer a próxima onda", logi.eFmt(tr.cargo)))
    return true
end

-- Chegada confirmada a frente: caixas viram unidades uma unica vez.
function logi.eDeliver(tr)
    local en = logi.en
    if not (en and tr.cargo) then return end
    local add = {}
    for _, k in ipairs(CFG.ECHAIN.kinds) do
        add[k] = (tr.cargo[k] or 0) * logi.eUnits(k)
        en.front[k] = en.front[k] + add[k]
    end
    tr.cargo = nil
    en.delivered = en.delivered + 1
    logi.eEvent(string.format("comboio %s entregou na frente: +%g munição, +%g camisas", tostring(tr.id), add.ammo or 0, add.shirts or 0))
    notify(string.format("comboio inimigo chegou à frente: equipa %d soldados", (logi.eSoldiers())), 3.0)
end

-- Caminhao perdido (destruido, ator invalido ou removido): carga sai do razao como perda, uma unica vez;
-- o caminhao entra na fila de reconstrucao (LOGI.rebuild s e LOGI.truckCost bmat, como o do jogador).
function logi.eLose(tr, why)
    local en = logi.en
    if tr.lostDone then return "já registrado" end
    tr.lostDone = true
    if not en then tr.cargo = nil; return "sem cadeia" end
    local units = {}
    for _, k in ipairs(CFG.ECHAIN.kinds) do
        local u = ((tr.cargo and tr.cargo[k]) or 0) * logi.eUnits(k)
        en.led.lost[k] = en.led.lost[k] + u
        en.ghost[k] = en.ghost[k] + u  -- carga que a frente teria (diagnostico de atribuicao, fora do razao)
        units[k] = u
    end
    tr.cargo = nil
    en.rebuild[#en.rebuild + 1] = now() + CFG.LOGI.rebuild
    local msg = string.format("comboio %s perdido (%s): -%g munição, -%g camisas", tostring(tr.id), why or "?", units.ammo or 0, units.shirts or 0)
    logi.eEvent(msg)
    return string.format("a frente perde %g munição e %g camisas", units.ammo or 0, units.shirts or 0)
end

-- Caminhao de volta a retaguarda: devolve carga nao entregue (so na chegada fisica) e volta a frota.
function logi.eHome(tr)
    local en = logi.en
    if not en then return end
    if tr.cargo then
        for _, k in ipairs(CFG.ECHAIN.kinds) do en.fac[k] = en.fac[k] + (tr.cargo[k] or 0) end
        logi.eEvent(string.format("comboio %s voltou com a carga: %s", tostring(tr.id), logi.eFmt(tr.cargo)))
        tr.cargo = nil
    end
    en.ready = en.ready + 1
end

-- Rota ausente/bloqueada por CFG.ECHAIN.stuck s (status escrito pelo driver de ESTRADAS em tr.routeStatus).
function logi.eStuck(tr, dt)
    local s = tr.routeStatus
    if s == "rota_ausente" or s == "regiao_invalida" or s == "bloqueado" then tr.stuck = (tr.stuck or 0) + dt
    else tr.stuck = 0 end
    return tr.stuck >= CFG.ECHAIN.stuck
end

function logi.convoyTick(dt, t)
    local E = CFG.ECONVOY
    logi.eTick(dt, t)
    if combat.auto and combat.mode ~= "assault" and t >= (logi.convoyT or 0) then
        logi.convoyT = t + (logi.convoySpawn(t) and E.every or E.retry)
    end
    for i = #logi.foes, 1, -1 do
        local tr = logi.foes[i]
        local gone = tr.state == "dead"
        if not gone and tr.pawn ~= nil and (not valid(tr.pawn) or tr.pawn.bActorIsBeingDestroyed) then
            tr.state = "dead"
            logi.eLose(tr, "ator do caminhão inválido")  -- perda explicita, nunca entrega fantasma
            gone = true
        end
        if not gone then
            if tr.state == "toFront" then
                if logi.drive(tr, tr.to, dt, E.speed) then
                    logi.eDeliver(tr)
                    tr.state = "back"
                elseif logi.eStuck(tr, dt) then
                    tr.state = "back"  -- volta carregado; credito so na chegada a retaguarda
                    logi.eEvent(string.format("comboio %s sem rota: voltando com a carga", tostring(tr.id)))
                end
            elseif tr.state == "back" and logi.drive(tr, tr.from, dt, E.speed) then
                logi.eHome(tr)
                tr.home = true
                gone = true
            end
            -- nossos soldados perto atiram no caminhao
            local n, shooter = 0, nil
            for _, m in ipairs(squad) do
                if alive(m) and flatDist(loc(m), tr) <= CFG.LOGI.ambush then n, shooter = n + 1, m end
            end
            if n > 0 and not tr.home then
                if t >= (tr.fxT or 0) and shooter then
                    tr.fxT = t + E.fx
                    local d, dx, dy = flatDist(loc(shooter), tr)
                    pcall(rts.shotFx, shooter, dx, dy, d)
                end
                if logi.hit(tr, n * CFG.LOGI.dps * dt, t) then gone = true end
            end
        end
        if gone then
            if not tr.home and not tr.lostDone then logi.eLose(tr, "removido") end  -- nunca some carga sem registro
            if tr.icon and valid(tr.icon) then pcall(function() tr.icon:K2_DestroyActor() end) end
            if tr.pawn and valid(tr.pawn) then pcall(function() tr.pawn:K2_DestroyActor() end) end
            table.remove(logi.foes, i)
        end
    end
    if logi.en then combat.cargo = logi.eSoldiers() end
end

-- Consumo real na frente: k soldados pagos levam camisa + carregamento. Retorna o que foi debitado.
function logi.eConsume(k, why)
    if not logi.eActive() or not (k and k > 0) then return 0 end
    local en = logi.en
    k = math.min(math.floor(k), (logi.eSoldiers()))
    if k < 1 then return 0 end
    for _, kind in ipairs(CFG.ECHAIN.kinds) do
        local q = math.min(en.front[kind], k * logi.eNeed(kind))
        en.front[kind], en.led.used[kind] = en.front[kind] - q, en.led.used[kind] + q
    end
    combat.cargo = logi.eSoldiers()
    return k
end

-- Reforco pelos pontos (ai.tick): limita ao que a frente equipa; o debito vem depois do spawn (eConsume).
function logi.eAfford(n)
    if not logi.eActive() then return n end
    return math.min(n, (logi.eSoldiers()))
end

-- Onda (waveTick): guarnicao gratuita + soldados pagos ate o que a frente equipa. So decide; o debito e
-- logi.eCommit depois do spawn (soldado que nao nasceu nao consome). Registro da onda: pedido, enviado,
-- produto limitante e quantos soldados a carga perdida em comboios desde a onda anterior teria equipado.
function logi.waveCut(n)
    if not logi.eActive() then return n end
    local en, E = logi.en, CFG.ECHAIN
    local free = math.min(n, E.free)
    local can, lim = logi.eSoldiers()
    local paid = math.min(n - free, can)
    local short = n - free - paid
    -- Atribuicao (contrafactual): com a carga perdida ainda nao "gasta" (ghost), quantos soldados a mais a frente
    -- equiparia? Esses faltam por interdicao; o ghost e gasto como se tivessem saido. Diagnostico, fora do razao.
    local with = {}
    for _, k in ipairs(E.kinds) do with[k] = en.front[k] + en.ghost[k] end
    local byCut = math.min(short, math.max(0, (logi.eSoldiers(with)) - can))
    local rec = { wave = combat.wave + 1, asked = n, free = free, paid = paid, short = short, limit = short > 0 and lim or nil,
        front = { ammo = en.front.ammo, shirts = en.front.shirts }, ghost = { ammo = en.ghost.ammo, shirts = en.ghost.shirts },
        byCut = byCut }
    for _, k in ipairs(E.kinds) do en.ghost[k] = math.max(0, en.ghost[k] - byCut * logi.eNeed(k)) end
    en.waves[#en.waves + 1] = rec
    if #en.waves > E.keep then table.remove(en.waves, 1) end
    en.plan = { w0 = combat.wave, free = free, paid = paid, rec = rec }
    if short > 0 then
        notify(string.format("faltou suprimento ao inimigo: a onda vem com %d a menos (falta %s%s)", short,
            lim == "ammo" and "munição" or "camisas", rec.byCut > 0 and string.format("; %d por comboios destruídos", rec.byCut) or ""), 4.0)
    end
    logi.eEvent(string.format("onda %d: pedido %d, grátis %d, pagos %d, faltaram %d (%s), atribuídos à interdição %d",
        rec.wave, n, free, paid, short, tostring(rec.limit), rec.byCut))
    return free + paid
end

-- Depois do spawn da onda: debita so os soldados pagos que nasceram (a guarnicao gratuita conta primeiro).
function logi.eCommit(made)
    local en = logi.en
    local p = en and en.plan
    if not p then return 0 end
    en.plan = nil
    if combat.wave == p.w0 then made = 0 end  -- spawn recusado antes de abrir a onda: nada nasceu
    local k = logi.eConsume(math.max(0, math.min(p.paid, (made or 0) - p.free)), "onda")
    p.rec.sent, p.rec.paidMade = made or 0, k
    return k
end

-- Conservacao verificavel (canal/laboratorio: out(logi.eAudit())).
function logi.eAudit()
    local en = logi.en
    if not en then return true, "sem cadeia" end
    local L, bad = en.led, {}
    for _, k in ipairs(CFG.ECHAIN.kinds) do
        local diff = (L.init[k] + L.made[k]) - (logi.eHave(k) + L.used[k] + L.lost[k])
        if math.abs(diff) > 1e-6 then bad[#bad + 1] = string.format("%s desvio %.6f", k, diff) end
        if en.front[k] < -1e-9 or en.fac[k] < 0 then bad[#bad + 1] = k .. " negativo" end
    end
    local db = (L.bmat0 + L.refined / CFG.LOGI.ratio) - (en.bmat + L.spent)
    if math.abs(db) > 1e-6 then bad[#bad + 1] = string.format("bmat desvio %.6f", db) end
    local ds = L.salv - (en.salvage + L.refined)
    if math.abs(ds) > 1e-6 then bad[#bad + 1] = string.format("sucata desvio %.6f", ds) end
    if en.bmat < -1e-9 or en.ready < 0 then bad[#bad + 1] = "bmat/frota negativo" end
    local road = 0  -- frota: livre + reconstruindo + na estrada == ECHAIN.trucks (nenhum caminhao criado do nada)
    for _, tr in ipairs(logi.foes or {}) do if not tr.lostDone and not tr.home then road = road + 1 end end
    if en.ready + #en.rebuild + road ~= CFG.ECHAIN.trucks then
        bad[#bad + 1] = string.format("frota %d+%d+%d ~= %d", en.ready, #en.rebuild, road, CFG.ECHAIN.trucks)
    end
    return #bad == 0, #bad == 0 and "razão fechado" or table.concat(bad, "; ")
end

function logi.eHud()
    local en = logi.en
    if not en then return "" end
    if en.err then return " | INIMIGO: cadeia recusada (" .. en.err .. ")" end
    local moving = 0
    for _, tr in ipairs(logi.foes) do if tr.state ~= "dead" and tr.cargo then moving = moving + 1 end end
    return string.format(" | INIMIGO: frente equipa %d (m%.1f c%d) | retaguarda bmat %.0f, cx m%d c%d | comboios %d na estrada, %d perdidos",
        (logi.eSoldiers()), en.front.ammo, en.front.shirts, en.bmat, en.fac.ammo, en.fac.shirts, moving, combat.convoysCut or 0)
end

-- Relatorio para o canal/laboratorio: estado, razao, ultimas ondas e eventos.
function logi.eReport()
    local en = logi.en
    if not en then return "cadeia inimiga: inativa" end
    local ok, why = logi.eAudit()
    local L, out = en.led, {}
    out[#out + 1] = string.format("cadeia inimiga ativa=%s err=%s | sucata %.1f bmat %.1f job=%s | frota livre %d, reconstruindo %d, na estrada %d | pendente %s",
        tostring(logi.eActive()), tostring(en.err), en.salvage, en.bmat, en.job and (en.job.kind .. string.format(" %.1f s", en.job.left)) or "-",
        en.ready, #en.rebuild, #logi.foes, en.pending and logi.eFmt(en.pending) or "-")
    for _, k in ipairs(CFG.ECHAIN.kinds) do
        out[#out + 1] = string.format("  %s: inicial %g + produzido %g = retaguarda %g + trânsito %g + frente %g + consumido %g + perdido %g",
            k, L.init[k], L.made[k], en.fac[k] * logi.eUnits(k), logi.eTransit(k), en.front[k], L.used[k], L.lost[k])
    end
    out[#out + 1] = string.format("  razão: %s (%s) | bmat0 %g + refinado %g/%g = bmat %.3f + gasto %g", ok and "OK" or "FALHA", why,
        L.bmat0, L.refined, CFG.LOGI.ratio, en.bmat, L.spent)
    for i = math.max(1, #en.waves - 4), #en.waves do
        local w = en.waves[i]
        out[#out + 1] = string.format("  onda %d: pedido %d grátis %d pagos %d enviados %s faltaram %d (%s) interdição %d",
            w.wave, w.asked, w.free, w.paid, tostring(w.sent), w.short, tostring(w.limit), w.byCut)
    end
    return table.concat(out, "\n")
end

-- Save: carga em transito vira "pendente" (o ator nao e recriado; reenviada da retaguarda pelo proximo comboio),
-- caminhoes na estrada voltam a frota livre, reconstrucao guarda o tempo restante. Copias, sem userdata.
function logi.eSnapshot()
    local en = logi.en
    if not en then return nil end
    local t = now()
    local function copy(s) local d = {}; for _, k in ipairs(CFG.ECHAIN.kinds) do d[k] = s[k] or 0 end; return d end
    local pend, road = copy(en.pending or {}), 0
    for _, tr in ipairs(logi.foes or {}) do
        if tr.state ~= "dead" and not tr.lostDone then
            road = road + 1
            for _, k in ipairs(CFG.ECHAIN.kinds) do pend[k] = pend[k] + ((tr.cargo and tr.cargo[k]) or 0) end
        end
    end
    local rb = {}
    for i, r in ipairs(en.rebuild) do rb[i] = math.max(0, r - t) end
    local L = en.led
    return { v = 1, salvage = en.salvage, bmat = en.bmat, trip = en.tripT, ready = en.ready + road, rebuild = rb,
        fac = copy(en.fac), front = copy(en.front), pending = pend, seq = en.seq, delivered = en.delivered,
        job = en.job and { kind = en.job.kind, left = en.job.left, total = en.job.total } or nil,
        led = { bmat0 = L.bmat0, salv = L.salv, refined = L.refined, spent = L.spent,
            init = copy(L.init), made = copy(L.made), used = copy(L.used), lost = copy(L.lost) } }
end

-- Validacao completa antes de substituir (nunca soma): numeros finitos >= 0, frota coerente, receita do job
-- conhecida e o proprio razao do save fechado. Invalido/ausente: mantem o estado novo de logi.start e avisa.
function logi.eValid(d)
    local E = CFG.ECHAIN
    local function num(x) return type(x) == "number" and x == x and x >= 0 and x < math.huge end
    local function int(x) return num(x) and x % 1 == 0 end
    if type(d) ~= "table" then return false, "formato" end
    if d.v ~= 1 then return false, (type(d.v) == "number" and d.v > 1) and ("versão futura v" .. d.v) or "versão desconhecida" end
    for _, key in ipairs({ "salvage", "bmat", "trip" }) do if not num(d[key]) then return false, key end end
    if not int(d.ready) or type(d.rebuild) ~= "table" or not int(d.seq or 0) or not int(d.delivered or 0) then return false, "frota" end
    for _, r in ipairs(d.rebuild) do if not num(r) then return false, "reconstrução" end end
    if d.ready + #d.rebuild > E.trucks then return false, "frota maior que a configurada" end
    local L = d.led
    if type(L) ~= "table" then return false, "razão" end
    for _, key in ipairs({ "bmat0", "salv", "refined", "spent" }) do if not num(L[key]) then return false, "razão " .. key end end
    for _, grp in ipairs({ "fac", "front", "pending" }) do if type(d[grp]) ~= "table" then return false, grp end end
    for _, grp in ipairs({ "init", "made", "used", "lost" }) do if type(L[grp]) ~= "table" then return false, "razão " .. grp end end
    for _, k in ipairs(E.kinds) do
        if not int(d.fac[k]) or not int(d.pending[k]) or not num(d.front[k]) then return false, "estoque " .. k end
        for _, grp in ipairs({ "init", "made", "used", "lost" }) do if not num(L[grp][k]) then return false, "razão " .. k end end
        local u = logi.eUnits(k)
        local diff = (L.init[k] + L.made[k]) - ((d.fac[k] + d.pending[k]) * u + d.front[k] + L.used[k] + L.lost[k])
        if math.abs(diff) > E.tol then return false, "razão não fecha em " .. k end
    end
    if math.abs((L.bmat0 + L.refined / CFG.LOGI.ratio) - (d.bmat + L.spent)) > E.tol then return false, "razão bmat" end
    if math.abs(L.salv - (d.salvage + L.refined)) > E.tol then return false, "razão sucata" end
    if d.job ~= nil then
        local j = d.job
        if type(j) ~= "table" or not CFG.LOGI.recipes[j.kind] or not num(j.left) or not num(j.total) or j.left > j.total then return false, "job" end
    end
    return true
end

-- `dropped` (v2, PERSISTENCIA): motivo pelo qual a secao `elogi` do save foi descartada na leitura (invalida, versao
-- futura, sem logistica...). Politica unica: so esta secao e descartada; a cadeia inimiga recomeca do estoque de
-- cenario (logi.start ja fez eReset: razao 'inicial'), com aviso explicito, sem tocar na logistica do jogador.
function logi.eRestore(d, dropped)
    if not (logi.on and logi.en) then return false end
    if d == nil then
        if dropped then
            logi.eEvent("save da cadeia inimiga descartado (" .. tostring(dropped) .. "): recomeça do estoque de cenário")
            notify("cadeia inimiga do save descartada (" .. tostring(dropped) .. "): recomeça do estoque inicial; o resto da partida foi restaurado", 6.0)
        else
            logi.eEvent("save sem cadeia inimiga: começa do estoque de cenário")
        end
        return false
    end
    local ok, why = logi.eValid(d)
    if not ok then
        logi.eEvent("save da cadeia inimiga recusado (" .. tostring(why) .. "): começa do estoque de cenário")
        notify("cadeia inimiga do save inválida: recomeça do estoque inicial", 4.0)
        return false
    end
    local t, en = now(), logi.en
    local function copy(s) local r = {}; for _, k in ipairs(CFG.ECHAIN.kinds) do r[k] = s[k] or 0 end; return r end
    en.salvage, en.bmat, en.tripT, en.ready, en.seq, en.delivered = d.salvage, d.bmat, d.trip, d.ready, d.seq or 0, d.delivered or 0
    en.fac, en.front = copy(d.fac), copy(d.front)
    local pend = copy(d.pending)
    local any = false
    for _, k in ipairs(CFG.ECHAIN.kinds) do if pend[k] > 0 then any = true end end
    en.pending = any and pend or nil
    en.rebuild = {}
    for i, r in ipairs(d.rebuild) do en.rebuild[i] = t + r end
    en.job = d.job and { kind = d.job.kind, left = d.job.left, total = d.job.total } or nil
    en.led = { bmat0 = d.led.bmat0, salv = d.led.salv, refined = d.led.refined, spent = d.led.spent,
        init = copy(d.led.init), made = copy(d.led.made), used = copy(d.led.used), lost = copy(d.led.lost) }
    -- sv.ser arredonda a 3 casas: a sobra (<= ECHAIN.tol, ja validada) e absorvida nos termos de origem
    -- (inicial/bmat0/colhido) para o razao em memoria fechar exato; nunca vira estoque.
    local Ld = en.led
    for _, k in ipairs(CFG.ECHAIN.kinds) do Ld.init[k] = logi.eHave(k) + Ld.used[k] + Ld.lost[k] - Ld.made[k] end
    Ld.bmat0 = en.bmat + Ld.spent - Ld.refined / CFG.LOGI.ratio
    Ld.salv = en.salvage + Ld.refined
    en.plan = nil
    combat.cargo = logi.eSoldiers()
    logi.eEvent("cadeia inimiga restaurada do save" .. (en.pending and (" (reenviar " .. logi.eFmt(en.pending) .. ")") or ""))
    return true
end

function logi.snapshot()
    if not logi.on then return nil end
    local d = { version=2, salvage=logi.salvage, bmat=logi.bmat, fa=logi.fac.ammo, fs=logi.fac.shirts,
        fr=logi.fac.rifle or 0, fm=logi.fac.medical or 0, ba=logi.base.ammo, bs=logi.base.shirts,
        br=logi.base.rifle or 0, bm=logi.base.medical or 0, prio=logi.prio, pts={}, trucks={} }
    for i, pt in ipairs(points) do d.pts[i] = pt.dep and { a=pt.dep.ammo, s=pt.dep.shirts, r=pt.dep.rifle or 0, m=pt.dep.medical or 0 } or false end
    if logi.job then d.job={kind=logi.job.kind,left=logi.job.left,total=logi.job.total} end
    for i, tr in ipairs(logi.trucks) do
        local q={state=tr.state,hp=tr.hp,salv=tr.salv or 0,wait=math.max(0,(tr.waitT or now())-now()),
            rebuild=math.max(0,(tr.rebuildT or now())-now())}
        if tr.cargo then
            q.cargo={}
            for _, kind in ipairs(CFG.LOGI.products) do q.cargo[kind]=tr.cargo[kind] or 0 end
            q.dest=tr.state=="returnCargo" and -1 or 0
            if tr.state~="returnCargo" and tr.dest ~= logi.base then
                for k, pt in ipairs(points) do if pt.dep == tr.dest then q.dest=k end end
            end
        end
        d.trucks[i]=q
    end
    return d
end
-- Pré-validação completa antes de start/reset; save legado sem novos campos continua aceito.
function logi.validateSave(d)
    local function number(n) return type(n)=="number" and n==n and n>=0 and n<math.huge end
    local function integer(n) return number(n) and n%1==0 end
    if type(d)~="table" or (d.version and d.version~=2) then return false end
    for _, key in ipairs({"salvage","bmat","ba"}) do if not number(d[key] or 0) then return false end end
    for _, key in ipairs({"fa","fs","fr","fm","bs","br","bm"}) do if not integer(d[key] or 0) then return false end end
    if d.prio and d.prio~="auto" and not CFG.LOGI.recipes[d.prio] then return false end
    if d.job then
        local j=d.job
        if type(j)~="table" or not CFG.LOGI.recipes[j.kind] or not number(j.left) or not number(j.total) or j.left>j.total then return false end
    end
    if d.pts and type(d.pts)~="table" then return false end
    for i,q in pairs(d.pts or {}) do
        if not integer(i) or i<1 or not points[i] then return false end
        if q then
            if type(q)~="table" or not number(q.a or 0) then return false end
            for _, key in ipairs({"s","r","m"}) do if not integer(q[key] or 0) then return false end end
        end
    end
    if d.trucks and type(d.trucks)~="table" then return false end
    local states={idle=true,toField=true,loading=true,toRef=true,toDep=true,returnCargo=true,dead=true}
    for i,q in pairs(d.trucks or {}) do
        if not integer(i) or i<1 or i>CFG.LOGI.supply+1 or type(q)~="table" or not states[q.state]
            or not number(q.hp) or not integer(q.salv or 0) or not number(q.wait or 0) or not number(q.rebuild or 0) then return false end
        if (i==1 and (q.state=="toDep" or q.state=="returnCargo")) or (i>1 and (q.state=="toField" or q.state=="toRef" or q.state=="loading")) then return false end
        if q.state=="dead" and (q.cargo or (q.salv or 0)>0) then return false end
        if (q.state=="toDep" or q.state=="returnCargo") and not q.cargo then return false end
        if q.cargo then
            if i==1 or (q.state~="toDep" and q.state~="returnCargo") or type(q.cargo)~="table" then return false end
            if q.state=="returnCargo" then
                if q.dest~=-1 then return false end
            elseif not integer(q.dest) or (q.dest>0 and not points[q.dest]) then return false end
            local n=0
            for key,value in pairs(q.cargo) do if not CFG.LOGI.recipes[key] or not integer(value) then return false end;n=n+value end
            if n<1 or n>CFG.LOGI.cap then return false end
        end
    end
    return true
end
function logi.restore(d)
    if not logi.validateSave(d) then return false end
    -- ready é só preflight; nenhuma estrutura do save é restaurada ou construída aqui.
    local setup=logi.ready()
    if not setup then return false end
    if not logi.start(setup) then return false end
    logi.salvage,logi.bmat,logi.prio=d.salvage or 0,d.bmat or 0,d.prio or "auto"
    logi.fac={ammo=d.fa or 0,shirts=d.fs or 0,rifle=d.fr or 0,medical=d.fm or 0}
    logi.base.ammo,logi.base.shirts,logi.base.rifle,logi.base.medical=d.ba or 0,d.bs or 0,d.br or 0,d.bm or 0
    for i,q in pairs(d.pts or {}) do
        if q then local dep=logi.depotOf(points[i]);dep.ammo,dep.shirts,dep.rifle,dep.medical=q.a or 0,q.s or 0,q.r or 0,q.m or 0 end
    end
    if d.job then logi.job={kind=d.job.kind,left=d.job.left,total=d.job.total} end
    for i,q in pairs(d.trucks or {}) do
        local tr=logi.trucks[i]
        tr.state,tr.hp,tr.salv=q.state,q.hp,(q.salv or 0)>0 and q.salv or nil
        tr.waitT,tr.rebuildT=now()+(q.wait or 0),now()+(q.rebuild or 0)
        if q.cargo then
            tr.cargo={};for _, kind in ipairs(CFG.LOGI.products) do tr.cargo[kind]=q.cargo[kind] or 0 end
            tr.dest=q.state=="returnCargo" and logi.factory or q.dest==0 and logi.base or logi.depotOf(points[q.dest])
            if q.state~="returnCargo" and tr.dest~=logi.base and tr.dest.pt.owner~=CFG.FRIENDLY_TEAM then
                tr.dest,tr.state=logi.factory,"returnCargo"
            end
            -- Coordenadas/trajeto antigo não são prova de rota regional segura: replanejar.
            tr.route,tr.routeDest,tr.pathJob=nil,nil,nil
        end
        if tr.state=="dead" and tr.pawn and valid(tr.pawn) then tr.pawn:SetActorHiddenInGame(true) end
    end
    return true
end

-- Objetivo do inimigo fora de combate: ponto mais proximo que ele ainda nao domina por completo.
local function enemyObjective(e)
    local here, best, bd = loc(e), nil, math.huge
    for _, pt in ipairs(points) do
        if pt.prog > -1.0 then
            local d = flatDist(here, pt)
            if d < bd then best, bd = pt, d end
        end
    end
    return best, bd
end

-- Morteiro (Ctrl+5 sob o cursor): MORTAR.cost de mao de obra, recarga MORTAR.cooldown. Aviso (som de
-- artilharia chegando + anel de 8 discos) e, apos delay, MORTAR.shells granadas espalhadas ate spread
-- do alvo: efeito MortarBlast + som de explosao do jogo; dano com queda linear (ate 30% na borda do raio)
-- so no lado oposto (instigador do proprio lado, como no tiro); supressao em todos ate suppRadius.
-- O inimigo usa o mesmo fogo a partir da onda ENEMY_MORTAR_WAVE contra grupos de 3+ soldados nossos,
-- com aviso mais longo (enemyDelay); nossos soldados sob o aviso correm para fora do anel sozinhos (sem
-- isso, no teste, uma salva matou 4 de 6 em formacao; com isso, 0 de dano: correm ~18 m em 3 s). Quem
-- segura posicao (End) ou esta suprimido (>= SUPP_PIN) fica e leva o fogo: o morteiro inimigo desaloja.
-- Terminada a salva, quem fugiu e nao recebeu ordem nova volta ao lugar de antes.
CFG.MORTAR = { cost = 40, cooldown = 20.0, delay = 2.5, enemyDelay = 3.0, shells = 3, enemyShells = 2, gap = 0.6, spread = 250.0,
               radius = 350.0, dmg = 75.0, supp = 0.8, suppRadius = 700.0, scatter = 100.0,
               fx = "/Game/FX/MortarBlast.MortarBlast",
               boom = "/Game/Audio/SFX/Weapons/StaticArtillery/ArtilleryLightExplosion_Cue.ArtilleryLightExplosion_Cue",
               incoming = "/Game/Audio/SFX/Weapons/StaticArtillery/ArtilleryIncoming_Cue.ArtilleryIncoming_Cue" }
CFG.ENEMY_MORTAR_WAVE, CFG.ENEMY_MORTAR_EVERY, CFG.ENEMY_MORTAR_CLUSTER = 4, 35.0, 3
-- Granada: o fuzileiro (dos dois lados) cujo alvo esta atras de cobertura baixa a ate range lanca uma em
-- vez de atirar (recarga cooldown por soldado); explode apos fuse s a ate spread do alvo. A cobertura nao
-- protege da explosao (dano por distancia, sem traco), o que tira o inimigo entrincheirado do lugar.
CFG.GRENADE = { range = 1800.0, cooldown = 18.0, fuse = 1.4, spread = 150.0, radius = 300.0, dmg = 45.0, supp = 0.6,
                suppRadius = 500.0, roles = { rifle = true },
                fx = "/Game/FX/GrenadeBlast.GrenadeBlast",
                boom = "/Game/Audio/SFX/Weapons/Grenade/HELaunchedGrenadeHit_Cue.HELaunchedGrenadeHit_Cue",
                pin = "/Game/Audio/SFX/Weapons/Grenade/GrenadePinPull_Cue.GrenadePinPull_Cue",
                mesh = "/Game/FX/Mesh/Grenade01.Grenade01", meshScale = 3.0, arc = 250.0 }  -- projetil visivel em arco
local strikes = {}               -- { X, Y, Z, team, t, left, marks }
local mortar = { readyAt = 0, enemyNext = nil, dmg = { [0] = 0, [1] = 0 }, calls = { [0] = 0, [1] = 0 },
                 grenades = { [0] = 0, [1] = 0 }, gdmg = { [0] = 0, [1] = 0 } }

local function playCue(path, at)
    local cue = asset(path)
    if cue then gs():PlaySoundAtLocation(world(), cue, at, { Pitch = 0, Yaw = 0, Roll = 0 }, 1.0, 1.0, 0.0, nil, nil, nil) end
end

local function clearStrikes()
    for _, st in ipairs(strikes) do
        if st.proj and valid(st.proj) then st.proj:K2_DestroyActor() end
        for _, d in ipairs(st.marks) do if valid(d) then d:K2_DestroyActor() end end
    end
    strikes = {}
end

-- Pede fogo em p pelo lado team. Jogador paga e respeita a recarga; o inimigo nao (controlado pela IA).
local function callMortar(p, team)
    if not isLocalAuthority() or not p or p.X ~= p.X or p.Y ~= p.Y then return false end  -- p.X ~= p.X: NaN
    team = team or CFG.FRIENDLY_TEAM
    local M = CFG.MORTAR
    local t = now()
    if team == CFG.FRIENDLY_TEAM then
        if t < mortar.readyAt then notify(string.format("morteiro recarregando: %.0f s", mortar.readyAt - t), 2.0); return false end
        if economy.manpower < M.cost then
            notify(string.format("mao de obra insuficiente para morteiro: %.0f/%d", economy.manpower, M.cost), 3.0)
            return false
        end
        economy.manpower = economy.manpower - M.cost
        mortar.readyAt = t + M.cooldown
    end
    local z = groundZ(p.X, p.Y) or p.Z or 0
    local marks = {}
    local mat = findAsset(CFG.MARKER_MAT)
    for i = 1, 8 do
        local a = 2 * math.pi * i / 8
        local dx, dy = p.X + math.cos(a) * M.spread, p.Y + math.sin(a) * M.spread
        local dz = groundZ(dx, dy)
        local d = dz and meshActor(dx, dy, dz + 1, CFG.MARKER_MESH, { X = 0.7, Y = 0.7, Z = 0.02 })
        if d then
            if mat then d.StaticMeshComponent:SetMaterial(0, mat) end
            marks[#marks + 1] = d
        end
    end
    local delay = (team == CFG.FRIENDLY_TEAM) and M.delay or M.enemyDelay
    local shells = (team == CFG.FRIENDLY_TEAM) and M.shells or M.enemyShells
    local st = { X = p.X, Y = p.Y, Z = z, team = team, t = t + delay, left = shells, marks = marks }
    strikes[#strikes + 1] = st
    mortar.calls[team] = (mortar.calls[team] or 0) + 1
    pcall(playCue, M.incoming, { X = p.X, Y = p.Y, Z = z + 300 })
    if team == CFG.FRIENDLY_TEAM then
        notify(string.format("morteiro a caminho (-%d) | mao de obra %.0f", M.cost, economy.manpower), 3.0)
    else
        local n = 0
        for _, m in ipairs(squad) do
            if alive(m) and not m.hold and suppression(m) < CFG.SUPP_PIN then
                local l = loc(m)
                local d, dx, dy = flatDist(p, l)
                if d < M.spread + M.radius then
                    if d < 1 then local a = math.random() * 2 * math.pi; dx, dy, d = math.cos(a), math.sin(a), 1 end
                    local out = M.spread + M.radius + M.scatter
                    m.target = { X = p.X + dx / d * out, Y = p.Y + dy / d * out, Z = l.Z }
                    m.path, m.pathJob, m.focus, m.halted = nil, nil, nil, false
                    m.scatter = { st = st, to = m.target, back = { X = l.X, Y = l.Y, Z = l.Z } }
                    n = n + 1
                end
            end
        end
        notify(string.format("MORTEIRO INIMIGO chegando! %d soldados saindo da area", n), 4.0)
    end
    return true
end

-- Quem assina o dano do lado team (o jogo exige instigador; mesmo lado do atirador, como em fire()).
local function instigatorOf(team)
    local list = (team == CFG.FRIENDLY_TEAM) and squad or enemies
    for _, m in ipairs(list) do if alive(m) and valid(m.hpc) then return m.hpc, m.pawn end end
    if team == CFG.FRIENDLY_TEAM then return playerController(), playerPawn() end
    return nil, nil
end

local function shell(st)
    local M = st.grenade and CFG.GRENADE or CFG.MORTAR
    local r, a = math.sqrt(math.random()) * M.spread, math.random() * 2 * math.pi
    local x, y = st.X + math.cos(a) * r, st.Y + math.sin(a) * r
    local hit = { X = x, Y = y, Z = groundZ(x, y) or st.Z }
    pcall(emit, M.fx, hit, 0)
    pcall(playCue, M.boom, hit)
    pcall(logi.blast, hit, M.radius, M.dmg, st.team)
    local ctrl, causer = instigatorOf(st.team)
    for _, list in ipairs({ squad, enemies }) do
        for _, m in ipairs(list) do
            if alive(m) then
                local d = flatDist(hit, loc(m))
                if d <= M.suppRadius then suppress(m, M.supp * (1.0 - 0.5 * d / M.suppRadius)) end
                if d <= M.radius and (m.team or 0) ~= st.team and ctrl then
                    local hp0 = m.pawn.Health or 0
                    gs():ApplyDamage(m.pawn, M.dmg * (1.0 - 0.7 * d / M.radius), ctrl, causer, nil)
                    local stat = st.grenade and mortar.gdmg or mortar.dmg
                    stat[st.team] = (stat[st.team] or 0) + (hp0 - (m.pawn.Health or 0))
                    if st.by and hp0 > 0 and (m.pawn.Health or 0) <= 0 then credit(st.by) end
                end
            end
        end
    end
end

-- Lanca a granada de m em target (ja decidido em fire): som do pino no lancador, explosao em fuse s.
function throwGrenade(m, target)
    local G = CFG.GRENADE
    m.throwAnimUntil = os.clock() + 0.8
    local tl, ml = loc(target), loc(m)
    local st = { X = tl.X, Y = tl.Y, Z = tl.Z - 90, team = m.team or 0, t = now() + G.fuse, left = 1, marks = {},
                 grenade = true, by = m, t0 = now(), from = { X = ml.X, Y = ml.Y, Z = ml.Z + 40 } }
    local ok, proj = pcall(meshActor, st.from.X, st.from.Y, st.from.Z, G.mesh, { X = G.meshScale, Y = G.meshScale, Z = G.meshScale })
    if ok and proj then st.proj = proj end
    strikes[#strikes + 1] = st
    m.nextGrenade = now() + G.cooldown
    local tm = m.team or 0
    mortar.grenades[tm] = (mortar.grenades[tm] or 0) + 1
    pcall(playCue, G.pin, loc(m))
end

local function mortarTick()
    local t = now()
    local i = 1
    while i <= #strikes do
        local st = strikes[i]
        if st.proj and valid(st.proj) and t < st.t then
            local a = math.min(1.0, (t - st.t0) / math.max(st.t - st.t0, 0.01))
            local f = st.from
            st.proj:K2_SetActorLocation({ X = f.X + (st.X - f.X) * a, Y = f.Y + (st.Y - f.Y) * a,
                Z = f.Z + (st.Z + 20 - f.Z) * a + 4 * CFG.GRENADE.arc * a * (1 - a) }, false, {}, true)
        end
        if t >= st.t then
            if st.proj and valid(st.proj) then st.proj:K2_DestroyActor(); st.proj = nil end
            local ok, err = pcall(shell, st)
            if not ok then logOnce("shell", err) end
            st.left = st.left - 1
            st.t = t + CFG.MORTAR.gap
        end
        if st.left <= 0 then
            for _, d in ipairs(st.marks) do if valid(d) then d:K2_DestroyActor() end end
            -- quem fugiu desta salva e nao recebeu ordem nova volta ao lugar
            for _, m in ipairs(squad) do
                if m.scatter and m.scatter.st == st then
                    if alive(m) and not m.hold and not m.focus and (m.target == m.scatter.to or m.target == nil) then
                        routeTo(m, m.scatter.back)
                        m.halted = false
                    end
                    m.scatter = nil
                end
            end
            table.remove(strikes, i)
        else
            i = i + 1
        end
    end
    -- IA: fogo no maior grupo nosso (3+ soldados a ate 400 cm de um deles), so com inimigos vivos
    -- o relogio nao zera entre ondas: com ondas eliminadas em ~15 s ele nunca chegava a disparar
    if combat.wave < CFG.ENEMY_MORTAR_WAVE then mortar.enemyNext = nil; return end
    if #enemies == 0 then return end
    if not mortar.enemyNext then mortar.enemyNext = t + CFG.ENEMY_MORTAR_EVERY * 0.3; return end
    if t < mortar.enemyNext then return end
    local best, bn = nil, CFG.ENEMY_MORTAR_CLUSTER - 1
    for _, m in ipairs(squad) do
        if alive(m) then
            local n, lm = 0, loc(m)
            for _, o in ipairs(squad) do if alive(o) and flatDist(lm, loc(o)) <= 400 then n = n + 1 end end
            if n > bn then best, bn = lm, n end
        end
    end
    mortar.enemyNext = t + (best and CFG.ENEMY_MORTAR_EVERY or 5.0)
    if best then callMortar(best, CFG.ENEMY_TEAM) end
end

-- Inimigos: avancam ate o soldado aliado mais proximo, param ao alcance com visada e atiram.
-- Guarnicao (assalto): enquanto o ponto e dela, quem nao tem alvo a tiro volta ao ponto e segura (a busca de
-- cobertura prefere a trincheira do ponto). Ponto perdido solta a guarnicao, que contra-ataca como os outros.
function rts.holdPost(e)
    local pt = e.post
    if pt.owner ~= CFG.ENEMY_TEAM then e.post = nil; return false end
    e.target = nil
    if flatDist(loc(e), pt) > CFG.ASSAULT.leash then
        e.halted = false
        moveToward(e, pt.X, pt.Y)
    else
        halt(e)
        e.halted = true
    end
    return true
end

-- Moral (ondas, nao no assalto): uma onda de MORALE.min+ soldados que cai a MORALE.broken do tamanho foge; os
-- sobreviventes correm de volta a entrada (sem atirar, levando metade dos acertos) e somem ao chegar, sem contar
-- abate. Assim a onda acaba sem caca aos ultimos e a proxima vem.
CFG.MORALE = { broken = 0.25, min = 6, home = 300.0, regroup = 15.0 }
function rts.moraleCheck()
    if combat.mode == "assault" or combat.broken or (combat.waveSize or 0) < CFG.MORALE.min or #enemies == 0 then return end
    if #enemies > math.max(1, math.floor(combat.waveSize * CFG.MORALE.broken)) then return end
    combat.broken = true
    local n = 0
    for _, e in ipairs(enemies) do
        if alive(e) and e.home and not e.post then
            e.flee, e.retreat, e.target, e.path, e.pathJob, e.bound = e.home, true, nil, nil, nil, nil
            n = n + 1
        end
    end
    if n > 0 then
        combat.routs = (combat.routs or 0) + 1
        earn(n * CFG.KILL_BOUNTY)  -- quem foge sai do campo: rende como abate (sem isso a economia encolhia)
        notify(string.format("A ONDA %d QUEBROU: %d inimigos fogem (+%d)", combat.wave, n, n * CFG.KILL_BOUNTY), 4.0)
    end
end

-- Um quadro de quem foge: corre para casa; chegando, some (sai da lista no proximo enemyTick).
function rts.fleeStep(e)
    if flatDist(loc(e), e.flee) <= CFG.MORALE.home then e.fled = true; halt(e); return true end
    e.halted = false
    moveToward(e, e.flee.X, e.flee.Y)
    return true
end

function rts.purgeFled()
    for i = #enemies, 1, -1 do
        local e = enemies[i]
        if e.fled then
            pcall(destroyMarker, e)
            if valid(e.pawn) then e.pawn:K2_DestroyActor() end
            releaseController(e.hpc)
            table.remove(enemies, i)
            combat.fled = (combat.fled or 0) + 1
        end
    end
end

local function enemyTick()
    pcall(rts.purgeFled)
    local k = reap(enemies, "inimigo")
    if k > 0 then
        combat.kills = combat.kills + k
        earn(k * CFG.KILL_BOUNTY)
        if #enemies == 0 then notify(string.format("onda %d eliminada (abates %d, perdas %d)", combat.wave, combat.kills, combat.losses)) end
    end
    pcall(rts.moraleCheck)
    for _, e in ipairs(enemies) do
        if e.flee and alive(e) and rts.fleeStep(e) then goto nextEnemy end
        medicTick(e, enemies)
        local foe, d, los
        if now() >= (e.nextScan or 0) or not (e.foe and alive(e.foe)) then
            foe, d = nearest(e, squad)
            los = foe ~= nil and d <= weapon(e).range and hasLOS(e, foe)
            e.foe, e.los, e.nextScan = foe, los, now() + CFG.SCAN_EVERY * (0.8 + 0.4 * math.random())
        else
            foe, los = e.foe, e.los
            d = flatDist(loc(e), loc(foe))
        end
        if foe then
            local fl = loc(foe)
            local _, dx, dy = flatDist(loc(e), fl)
            local range = weapon(e).range
            los = los and d <= range
            if los then e.seen = { X = fl.X, Y = fl.Y, Z = fl.Z, t = now() } end
            local pinned = suppression(e) >= CFG.SUPP_PIN
            if los and (d <= range * CFG.ENEMY_ENGAGE or pinned) then
                e.bound = nil
                -- em posicao de tiro: se exposto, vai para cobertura proxima (sem atirar no caminho);
                -- preso pela supressao nao se move
                if e.target and not pinned then
                    e.halted = false
                    if moveToward(e, e.target.X, e.target.Y) then e.target = nil; halt(e) end
                else
                    e.target = nil
                    if not e.halted then e.nextShot = math.max(e.nextShot, now() + CFG.ENEMY_AIM_TIME) end
                    halt(e)
                    fire(e, foe, d, dx, dy)
                    if not pinned and now() >= (e.nextCoverT or 0) then
                        e.nextCoverT = now() + CFG.COVER_SEEK_EVERY
                        seekCover(e, squad)
                    end
                end
            elseif e.role == "mg" and rts.enemyArea(e) then
                -- MG sem visada: suprime onde viu o alvo pela ultima vez
            elseif e.post and rts.holdPost(e) then
                -- guarnicao do assalto: sem alvo a tiro, fica no ponto
            else
                e.target = nil
                local obj, od = enemyObjective(e)
                if obj and od < d then
                    if e.goalPt ~= obj then e.goalPt, e.path, e.nextPlanT = obj, nil, 0 end
                    fl = obj
                elseif e.goalPt then
                    e.goalPt, e.path, e.nextPlanT = nil, nil, 0
                end
                local wp = e.path and e.path[1]
                -- avanco em lances: sob fogo (supressao >= ENEMY_BOUND_SUPP) corre para a cobertura mais
                -- avancada por perto (seekCover), espera ENEMY_BOUND_WAIT e segue; antes avancava reto
                if not e.bound and suppression(e) >= CFG.ENEMY_BOUND_SUPP and now() >= (e.nextCoverT or 0) then
                    e.nextCoverT = now() + CFG.COVER_SEEK_EVERY
                    if seekCover(e, squad) then
                        e.bound, e.target = e.target, nil
                        combat.bounds = (combat.bounds or 0) + 1
                    end
                end
                if e.bound then
                    e.halted = false
                    if moveToward(e, e.bound.X, e.bound.Y) then
                        e.bound, e.boundWait = nil, now() + CFG.ENEMY_BOUND_WAIT
                        halt(e)
                    end
                elseif now() < (e.boundWait or 0) then
                    halt(e)
                    e.halted = true
                elseif obj and fl == obj and od <= CFG.POINT_RADIUS * CFG.POINT_HOLD then
                    halt(e)  -- no ponto: segura ate o ponto virar ou o inimigo aparecer
                    e.halted = true
                elseif wp then
                    e.halted = false
                    if flatDist(loc(e), wp) <= CFG.WAYPOINT_RADIUS then table.remove(e.path, 1) else moveToward(e, wp.X, wp.Y) end
                else
                    e.halted = false
                    moveToward(e, fl.X, fl.Y)
                end
                -- reavalia a rota de tempos em tempos; planStart so abre A* se a reta estiver bloqueada
                if not e.pathJob and now() >= (e.nextPlanT or 0) then
                    e.nextPlanT = now() + CFG.ENEMY_REPLAN
                    local l = loc(e)
                    local from = { X = l.X, Y = l.Y, Z = groundZ(l.X, l.Y) or (l.Z - 90) }
                    local to = { X = fl.X, Y = fl.Y, Z = groundZ(fl.X, fl.Y) or ((fl.Z or loc(e).Z) - 90) }
                    local job = planStart(from, to, allPawns())
                    job.owner = "enemy"
                    e.pathJob = job
                    pathJobs[#pathJobs + 1] = job
                end
            end
        else
            local obj, od = enemyObjective(e)
            if obj and od > CFG.POINT_RADIUS * CFG.POINT_HOLD then moveToward(e, obj.X, obj.Y) else halt(e) end
        end
        ::nextEnemy::
    end
end

-- Onda inimiga: no ponto sob o cursor (modo RTS) ou ENEMY_SPAWN_DIST a frente (+X) do esquadrao/comandante.
local function spawnEnemies(at, count, sameWave, quiet)
    if not isLocalAuthority() then log("ignorado: sem autoridade local"); return end
    count = count or CFG.ENEMY_SQUAD_SIZE
    local base = at
    if not base then
        local l = (squad[1] and alive(squad[1])) and squad[1].pawn:K2_GetActorLocation() or rts.base()
        if not l then log("sem referencia para posicionar inimigos"); return end
        base = { X = l.X + CFG.ENEMY_SPAWN_DIST, Y = l.Y, Z = l.Z }
    end
    if not sameWave then combat.wave = combat.wave + 1; combat.waveSize, combat.broken = 0, false end  -- sameWave: 2o grupo de uma onda em pinca
    local made = 0
    for i = 1, count do
        local s = slotFor(i)
        local x, y = base.X - s.X, base.Y + s.Y  -- formacao virada para -X (para o jogador)
        local z = groundZ(x, y) or base.Z
        local role = (i == 1 and not sameWave and combat.wave >= CFG.OFFICER.wave) and "officer" or roleFor(i)
        local e = spawnSoldier(x, y, z + 90, s, CFG.ENEMY_TEAM, role)
        if e then e.home = { X = base.X, Y = base.Y, Z = base.Z }; table.insert(enemies, e); made = made + 1 end
    end
    -- direcao na tela (camera olha para +X): +X = cima, +Y = direita
    local side = ""
    local ref = (squad[1] and alive(squad[1])) and loc(squad[1]) or nil
    if ref then
        local dx, dy = base.X - ref.X, base.Y - ref.Y
        if math.abs(dx) >= math.abs(dy) then side = (dx > 0) and " vindo de cima" or " vindo de baixo"
        else side = (dy > 0) and " vindo da direita" or " vindo da esquerda" end
    end
    if at and at.from then side = side .. " (entrada pelo ponto " .. at.from .. ")" end
    combat.waveSize = (combat.waveSize or 0) + made
    if not sameWave then combat.lastSpawn = { X = base.X, Y = base.Y, Z = base.Z } end
    if not quiet then pcall(rts.alert, "onda", base, string.format("onda %d: %d inimigos%s", combat.wave, made, side)) end
    log("onda " .. combat.wave .. ": " .. composition(enemies))
    log(string.format("onda %d em (%.0f, %.0f)", combat.wave, base.X, base.Y))
end

local function squadCenter()
    local sx, sy, sz, n = 0, 0, 0, 0
    for _, m in ipairs(squad) do
        if alive(m) then
            local l = loc(m)
            sx, sy, sz, n = sx + l.X, sy + l.Y, sz + l.Z, n + 1
        end
    end
    if n == 0 then return nil end
    return { X = sx / n, Y = sy / n, Z = sz / n }
end

-- Tres pontos ao redor do esquadrao (frente e flancos, +X = cima na tela) em chao na altura dele e livre:
-- o chao no meio raio e no raio nao pode variar mais que POINT_FLAT (veiculo, casa ou barranco no anel
-- reprovam; no 1o teste um ponto caiu sob um caminhao). Senao gira o angulo e tenta outras distancias.
-- Chamado ao ligar as ondas automaticas sem pontos.
CFG.POINT_SETUP_DIST = { 1800.0, 1400.0, 2400.0 }
CFG.POINT_FLAT = 80.0
local function flatSpot(x, y, refZ)
    local z = surfaceZ(x, y)
    if not z or math.abs(z - refZ) > 250 then return false end
    for _, r in ipairs({ 0.5, 1.0 }) do
        for i = 0, 7 do
            local a = i * math.pi / 4
            local gz = surfaceZ(x + math.cos(a) * CFG.POINT_RADIUS * r, y + math.sin(a) * CFG.POINT_RADIUS * r)
            if not gz or math.abs(gz - z) > CFG.POINT_FLAT then return false end
        end
    end
    return true
end

local function setupPoints()
    local c = squadCenter()
    if not c then c = rts.base() end
    if not c then return 0 end
    local made = 0
    for _, base in ipairs({ 0, math.pi / 2, -math.pi / 2 }) do
        local done = false
        for _, dist in ipairs(CFG.POINT_SETUP_DIST) do
            for k = 0, 6 do
                local a = base + ((k % 2 == 0) and 1 or -1) * math.floor((k + 1) / 2) * math.pi / 12
                local x, y = c.X + math.cos(a) * dist, c.Y + math.sin(a) * dist
                if flatSpot(x, y, c.Z - 90) and addPoint(x, y) then made = made + 1; done = true; break end
            end
            if done then break end
        end
    end
    notify(string.format("%d pontos de controle: capture com soldados (+%.1f/s cada)", made, CFG.POINT_INCOME), 6.0)
    return made
end

-- Construcao (tecla B): divisor de concreto do proprio mapa (OCourseDividers_01, ~2,7 m de comprimento,
-- topo a ~1,24 m do chao). Perfil medido por tracos: bloqueia a cintura (70 cm) e libera os olhos (150 cm),
-- exatamente a cobertura baixa do modelo de tiro; tiro, busca de cobertura e A* o enxergam pelos tracos.
-- (BPSandBagWallStatic_C tem colisao ate ~2,25 m e bloqueia a visada; SandbagSmallPile_C so ~40 cm.)
CFG.BUILD_MESH = "/Game/Meshes/Environment/Props/OCourseDividers_01.OCourseDividers_01"
CFG.BUILD_COST, CFG.BUILD_MAX, CFG.BUILD_CLEAR = 15, 30, 180.0
CFG.SND_BUILD = "/Game/Audio/UI/StructureBuild_Cue.StructureBuild_Cue"

-- Cava uma trincheira em p (instantaneo): recusa no limite, sem mao de obra ou encostada em outra.
local function digTrench(p)
    if not isLocalAuthority() or not p then return false end
    local T = CFG.TRENCH
    if #S.trenches >= T.max then notify("limite de trincheiras (" .. T.max .. ")", 3.0); return false end
    if economy.manpower < T.cost then
        notify(string.format("mao de obra insuficiente para trincheira: %.0f/%d", economy.manpower, T.cost), 3.0)
        return false
    end
    local tr, why = fort.place(p)
    if not tr then
        if why == "perto" then notify("perto demais de outra trincheira", 2.0) end
        return false
    end
    economy.manpower = economy.manpower - T.cost
    pcall(playCue, CFG.SND_BUILD, { X = tr.X, Y = tr.Y, Z = tr.Z })
    notify(string.format("trincheira (-%d): até %d soldados; tiros acertam %.0f%% menos (granada e morteiro não)",
        T.cost, T.cap, (1 - T.hit) * 100), 4.0)
    return true
end

local function clearTrenches()
    for _, tr in ipairs(S.trenches) do if valid(tr.actor) then pcall(function() tr.actor:K2_DestroyActor() end) end end
    S.trenches = {}
end

-- Lanca uma caixa de suprimentos em p: por CRATE.life s, nossos soldados a CRATE.radius recarregam
-- CRATE.refill do carregamento por s (mais rapido que o ponto; sem cura).
local function dropCrate(p)
    if not isLocalAuthority() or not p then return false end
    local C, t = CFG.CRATE, now()
    if #S.crates >= C.max then notify("limite de caixas de suprimento (" .. C.max .. ")", 3.0); return false end
    if t < (S.crateReadyAt or 0) then notify(string.format("caixa disponivel em %.0f s", S.crateReadyAt - t), 2.0); return false end
    if economy.manpower < C.cost then
        notify(string.format("mao de obra insuficiente para caixa: %.0f/%d", economy.manpower, C.cost), 3.0)
        return false
    end
    local z = groundZ(p.X, p.Y)
    if not z then return false end
    local a = meshActor(p.X, p.Y, z, C.mesh, C.scale)
    economy.manpower = economy.manpower - C.cost
    S.crateReadyAt = t + C.cooldown
    table.insert(S.crates, { actor = a, X = p.X, Y = p.Y, Z = z, untilT = t + C.life })
    pcall(playCue, CFG.SND_BUILD, { X = p.X, Y = p.Y, Z = z })
    notify(string.format("caixa de suprimentos (−%d): recarrega munição a %.0f m por %.0f s", C.cost, C.radius / 100, C.life), 4.0)
    return true
end
local structures = {}

-- Giro para uma obra em p com o eixo longo perpendicular a ameaca: o adversario vivo mais proximo de p (lista
-- foes); sem adversarios, a direcao esquadrao (ou base) -> p. nil sem referencia.
function fort.facing(p, foes)
    local ref, bd = nil, math.huge
    for _, e in ipairs(foes) do
        if alive(e) then
            local d = flatDist(p, loc(e))
            if d < bd then ref, bd = loc(e), d end
        end
    end
    local dx, dy
    if ref then
        dx, dy = ref.X - p.X, ref.Y - p.Y
    else
        local c = squadCenter()
        if not c then c = rts.base() end
        if not c then return nil end
        dx, dy = p.X - c.X, p.Y - c.Y
    end
    return math.deg(math.atan(dy, dx)) + 90
end

-- Divisor de concreto em (x, y, z) girado em yaw; nil se o ator nao nasceu.
function fort.wall(x, y, z, yaw)
    local a = world():SpawnActor(StaticFindObject("/Script/Engine.StaticMeshActor"), { X = x, Y = y, Z = z },
        { Pitch = 0, Yaw = yaw, Roll = 0 })
    if not valid(a) then return nil end
    local c = a.StaticMeshComponent
    c:SetMobility(2)
    c:SetStaticMesh(findAsset(CFG.BUILD_MESH))
    return a
end

-- Ergue a barreira em p, de frente para a ameaca (inimigo mais proximo de p; sem inimigos, a direcao
-- esquadrao -> p). Recusa sem autoridade, sem mao de obra, no limite ou com soldado no local.
local function buildAt(p)
    if not isLocalAuthority() or not p then return false end
    if #structures >= CFG.BUILD_MAX then notify("limite de barreiras (" .. CFG.BUILD_MAX .. ")", 3.0); return false end
    if economy.manpower < CFG.BUILD_COST then
        notify(string.format("mao de obra insuficiente para barreira: %.0f/%d", economy.manpower, CFG.BUILD_COST), 3.0)
        return false
    end
    for _, list in ipairs({ squad, enemies }) do
        for _, m in ipairs(list) do
            if valid(m.pawn) and flatDist(p, m.pawn:K2_GetActorLocation()) < CFG.BUILD_CLEAR then
                notify("sem espaco: soldado no local", 2.0)
                return false
            end
        end
    end
    local z = groundZ(p.X, p.Y)
    if not z then return false end
    local yaw = fort.facing(p, enemies)
    if not yaw then return false end
    local a = fort.wall(p.X, p.Y, z, yaw)
    if not a then return false end
    structures[#structures + 1] = a
    pcall(playCue, CFG.SND_BUILD, { X = p.X, Y = p.Y, Z = z })
    economy.manpower = economy.manpower - CFG.BUILD_COST
    notify(string.format("barreira construida (-%d) | mao de obra %.0f", CFG.BUILD_COST, economy.manpower), 3.0)
    return true
end

-- Ao tomar um ponto o inimigo estende de graca uma faixa de arame a ENEMY_WIRE cm do centro, do lado do
-- nosso esquadrao (sem esquadrao vivo, nada).
CFG.ENEMY_WIRE = 900.0
function fort.enemyWire(pt)
    local c = squadCenter()
    if not c then return end
    local dx, dy = c.X - pt.X, c.Y - pt.Y
    local d = math.sqrt(dx * dx + dy * dy)
    if d < 1 then return end
    local x, y = pt.X + dx / d * CFG.ENEMY_WIRE, pt.Y + dy / d * CFG.ENEMY_WIRE
    if fort.wireAt(x, y, math.deg(math.atan(dy, dx)) + 90) then pt.wired = true end
end

-- Barra de vida sobre os nossos feridos (so com o RTS ligado; nos inimigos revelaria quem o jogo esconde por
-- falta de visao). Cubo fino com material dinamico do CalloutRed (Unlit, parametro Color): comprimento
-- proporcional a vida, verde/amarelo/vermelho; rotacao absoluta para nao girar com o soldado.
CFG.HP_BAR = { every = 0.3, z = 165.0, len = 0.8, mat = "/Game/Materials/Structures/CalloutRed.CalloutRed",
               colors = { { R = 0.1, G = 0.9, B = 0.1, A = 1 }, { R = 1.0, G = 0.8, B = 0.0, A = 1 }, { R = 1.0, G = 0.05, B = 0.05, A = 1 } } }
function rts.hpBar(m, frac)
    local H = CFG.HP_BAR
    if not (m.hpBar and valid(m.hpBar)) then
        local l = m.pawn:K2_GetActorLocation()
        local a = meshActor(l.X, l.Y, l.Z + H.z, CFG.MARKER_MESH:gsub("Cylinder", "Cube"), { X = 0.08, Y = H.len, Z = 0.04 })
        if not a then return end
        local c = a.StaticMeshComponent
        m.hpMid = c:CreateDynamicMaterialInstance(0, findAsset(H.mat), FName("None"))
        a:K2_AttachToActor(m.pawn, FName("None"), 1, 1, 1, false)
        c:SetAbsolute(false, true, false)
        m.hpBar, m.hpBand = a, nil
    end
    local band = frac > 0.6 and 1 or (frac > 0.3 and 2 or 3)
    if band ~= m.hpBand and m.hpMid then
        m.hpBand = band
        m.hpMid:SetVectorParameterValue(FName("Color"), H.colors[band])
    end
    m.hpBar:SetActorScale3D({ X = 0.08, Y = H.len * math.max(frac, 0.05), Z = 0.04 })
    m.hpBar:SetActorHiddenInGame(false)
end

function rts.hpTick()
    local t = now()
    if t < (rts.hpT or 0) then return end
    rts.hpT = t + CFG.HP_BAR.every
    for _, m in ipairs(squad) do
        if alive(m) then
            local frac = (m.pawn.Health or 0) / (m.pawn.MaxHealth or 100)
            local want = rts.active and frac < 0.99
            if want then
                if math.abs(frac - (m.hpFrac or -1)) > 0.01 or not (m.hpBar and valid(m.hpBar)) then
                    m.hpFrac = frac
                    pcall(rts.hpBar, m, frac)
                end
            elseif m.hpBar and valid(m.hpBar) and m.hpFrac then
                m.hpFrac = nil
                m.hpBar:SetActorHiddenInGame(true)
            end
        end
    end
end

-- Selecao: contorno amarelo aderente a pose, mais preenchimento nativo das partes encobertas.
CFG.OUTLINE = { back = 50, pixels = 500, copies = 4,
    color = { R = 3, G = 2.4, B = 0.01, A = 1 } }
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
            -- O nativo pode reativar flags: conferir valor real a cada quadro, sem cache Lua.
            if c.bRenderCustomDepth ~= on then c:SetRenderCustomDepth(on) end
            if on and c.CustomDepthStencilValue ~= 1 then c:SetCustomDepthStencilValue(1) end
        end
    end
end
function rts.clearOutline(m)
    -- Antes de OnRep_Health/destruir o pawn: MasterPose nao pode apontar para uma malha morta.
    for _, a in ipairs(m.outline or {}) do
        if valid(a) and not a.bActorIsBeingDestroyed then pcall(function() a:K2_DestroyActor() end) end
    end
    m.outline, m.outlineSources = nil, nil
    pcall(rts.outlineDepth, m, false)
    m.outlineParts = nil
    m.outlineDepth = false
end

function rts.outlineFill()
    if valid(rts.outlineVolume) and not rts.outlineVolume.bActorIsBeingDestroyed and valid(rts.outlineMid) then return end
    if valid(rts.outlineVolume) and not rts.outlineVolume.bActorIsBeingDestroyed then rts.outlineVolume:K2_DestroyActor() end
    rts.outlineVolume, rts.outlineMid = nil, nil
    local mat = findAsset('/Game/Materials/PostProcess/M_OccludedOutline.M_OccludedOutline')
    if not valid(mat) then return end
    local volume = world():SpawnActor(StaticFindObject('/Script/Engine.PostProcessVolume'),
        { X = 0, Y = 0, Z = 0 }, { Pitch = 0, Yaw = 0, Roll = 0 })
    if not valid(volume) then return end
    rts.outlineVolume = volume
    volume.bUnbound, volume.Priority, volume.BlendWeight = true, 100, 1
    local mid = StaticFindObject('/Script/Engine.Default__KismetMaterialLibrary'):CreateDynamicMaterialInstance(world(), mat, FName('None'))
    if not valid(mid) then return end
    -- A referencia do engine vem ANTES do cache Lua: userdata nao impede GC do MID.
    volume:AddOrUpdateBlendable(mid, 1)
    rts.outlineMid = mid
    for _, name in ipairs({ 'PlayerHighlightColor', 'FriendlyHighlightColor', 'NeutralHighlightColor', 'EnemyHighlightColor' }) do
        mid:SetVectorParameterValue(FName(name), { R = 1, G = 0.8, B = 0.01, A = name == 'PlayerHighlightColor' and 1 or 0 })
    end
    mid:SetScalarParameterValue(FName('Alpha'), 0.66)
    ksl():ExecuteConsoleCommand(world(), 'r.CustomDepth 3', playerController())
end

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

function rts.setOutline(m, on)
    on = on and rts.active and m.sel and alive(m) and m.team ~= CFG.ENEMY_TEAM
    if not on then
        if m.outline or m.outlineDepth ~= false then rts.clearOutline(m) end
        -- O jogo reativa CustomDepth nas malhas amigas: nao basta limpar so na transicao.
        rts.outlineDepth(m, false)
        return
    end
    if now() < (m.outlineRetry or 0) then return end
    local src = m.pawn.Mesh
    if not valid(src) then return end
    if not m.outline then
        m.outlineRetry = now() + 2
        local ok, err = pcall(function()
            rts.outlineFill()
            local mat = findAsset(CFG.HP_BAR.mat)
            if not valid(mat) then error('material do contorno ausente') end
            m.outline, m.outlineSources = {}, {}
            rts.outlineDepth(m, false)
            -- ponytail: 4 copias por peca visivel (soldado atual: 7 pecas/28 atores), sem IA/fisica.
            -- Se pesar com selecao grande, substituir por shader de borda cooked; nao adicionar discos.
            for _, part in ipairs(m.outlineParts) do
              if valid(part.SkeletalMesh) and part.bVisible and not part.bHiddenInGame then
               for i = 1, CFG.OUTLINE.copies do
                local a = world():SpawnActor(StaticFindObject('/Script/Engine.SkeletalMeshActor'),
                    part:K2_GetComponentLocation(), part:K2_GetComponentRotation())
                if not valid(a) then error('spawn do contorno falhou') end
                m.outline[#m.outline + 1] = a
                m.outlineSources[#m.outlineSources + 1] = part
                local c = a.SkeletalMeshComponent
                c:SetSkeletalMesh(part.SkeletalMesh, true)
                c:SetMasterPoseComponent(part, true)
                c:SetCollisionEnabled(0); a:SetActorEnableCollision(false); c:SetCastShadow(false)
                local mid = c:CreateDynamicMaterialInstance(0, mat, FName('None'))
                if not valid(mid) then error('MID do contorno falhou') end
                mid:SetVectorParameterValue(FName('Color'), CFG.OUTLINE.color)
                for k = 0, c:GetNumMaterials() - 1 do c:SetMaterial(k, mid) end
                -- KeepWorld: translacao nativa apos o tick Lua tambem acompanha o soldado.
                a:K2_AttachToComponent(part, FName('None'), 1, 1, 1, false)
               end
              end
            end
        end)
        if not ok then rts.clearOutline(m); logOnce('outline', err); return end
        m.outlineRetry = nil
    end
    rts.outlineDepth(m, true); m.outlineDepth = true
    rts.updateOutline(m)
end

function rts.stratTick()
    local selected = false
    for _, list in ipairs({ squad, enemies }) do
        for _, m in ipairs(list) do
            pcall(rts.setOutline, m, rts.active and m.sel)
            if m.outline then selected = true end
        end
    end
    -- O olho invisivel tem equipamento em componentes separados; nao pode deixar uma silhueta fantasma.
    if S.eye and S.outlineEye then pcall(rts.outlineDepth, S.outlineEye, false) end
    if valid(rts.outlineVolume) then rts.outlineVolume.BlendWeight = rts.active and selected and 1 or 0 end
end

-- Estandarte enrolado do lado (o mesmo dos pontos) sobre a cabeca do oficial: bandeiras de verdade sao planos
-- verticais e somem vistas de cima.
function rts.officerFlag(m)
    local l = m.pawn:K2_GetActorLocation()
    local a = meshActor(l.X, l.Y, l.Z + 230, CFG.POINT_BANNER[m.team == CFG.ENEMY_TEAM and 0 or 1], { X = 1.4, Y = 1.4, Z = 1.4 })
    if a then a:K2_AttachToActor(m.pawn, FName("None"), 1, 1, 1, false); m.flag = a end
end

-- Posto de socorro (Ctrl+8): barraca de lona; nossos soldados a TENT.radius, com pouca supressao, recuperam
-- TENT.heal HP/s e param de sangrar.
CFG.TENT = { cost = 30, max = 2, radius = 600.0, heal = 4.0, calm = 0.2,
             mesh = "/Game/Meshes/Environment/Props/CanvasTent06.CanvasTent06", scale = { X = 0.6, Y = 0.6, Z = 0.6 } }
S.tents = {}

function fort.tentAt(x, y, yaw)
    local z = groundZ(x, y)
    if not z then return nil end
    local a = meshActor(x, y, z, CFG.TENT.mesh, CFG.TENT.scale)
    if a then pcall(function() a:K2_SetActorRotation({ Pitch = 0, Yaw = yaw, Roll = 0 }, false) end) end
    local tn = { actor = a, X = x, Y = y, Z = z, yaw = yaw }
    table.insert(S.tents, tn)
    return tn
end

function fort.tent(p)
    if not isLocalAuthority() or not p then return false end
    local T = CFG.TENT
    if #S.tents >= T.max then notify("limite de postos de socorro (" .. T.max .. ")", 3.0); return false end
    if economy.manpower < T.cost then
        notify(string.format("mao de obra insuficiente para posto de socorro: %.0f/%d", economy.manpower, T.cost), 3.0)
        return false
    end
    for _, tn in ipairs(S.tents) do
        if flatDist(p, tn) < T.radius then notify("perto demais de outro posto de socorro", 2.0); return false end
    end
    local yaw = fort.facing(p, enemies) or 0
    if not fort.tentAt(p.X, p.Y, yaw) then return false end
    economy.manpower = economy.manpower - T.cost
    pcall(playCue, CFG.SND_BUILD, { X = p.X, Y = p.Y, Z = p.Z or 0 })
    notify(string.format("posto de socorro (−%d): cura %.0f HP/s e estanca quem estiver a %.0f m sem fogo pesado",
        T.cost, T.heal, T.radius / 100), 4.0)
    return true
end

-- Faixa de arame centrada em (x, y) com o eixo longo em yaw (graus).
function fort.wireAt(x, y, yaw)
    local W = CFG.WIRE
    if #S.wires >= W.max then return nil end
    local ux, uy = math.cos(math.rad(yaw)), math.sin(math.rad(yaw))
    local w = { X = x, Y = y, ux = ux, uy = uy, yaw = yaw, actors = {} }
    for k = 1, W.seg do
        local off = (k - (W.seg + 1) / 2) * W.len
        local sx, sy = x + ux * (off - W.pivot * W.scale), y + uy * (off - W.pivot * W.scale)
        local z = groundZ(x + ux * off, y + uy * off)
        local a = z and meshActor(sx, sy, z, W.mesh, { X = W.scale, Y = W.scale, Z = W.scale })
        if a then
            pcall(function() a:K2_SetActorRotation({ Pitch = 0, Yaw = yaw, Roll = 0 }, false) end)
            w.actors[#w.actors + 1] = a
        end
    end
    if #w.actors == 0 then return nil end
    table.insert(S.wires, w)
    return w
end

function fort.wire(p)
    if not isLocalAuthority() or not p then return false end
    local W = CFG.WIRE
    if #S.wires >= W.max then notify("limite de arame farpado (" .. W.max .. ")", 3.0); return false end
    if economy.manpower < W.cost then
        notify(string.format("mao de obra insuficiente para arame: %.0f/%d", economy.manpower, W.cost), 3.0)
        return false
    end
    local yaw = fort.facing(p, enemies)
    if not yaw or not fort.wireAt(p.X, p.Y, yaw) then return false end
    economy.manpower = economy.manpower - W.cost
    pcall(playCue, CFG.SND_BUILD, { X = p.X, Y = p.Y, Z = p.Z or 0 })
    notify(string.format("arame farpado (−%d): quem atravessa anda a %.0f%% (os dois lados)", W.cost, W.slow * 100), 4.0)
    return true
end

function fort.clearExtras()
    for _, tn in ipairs(S.tents) do if valid(tn.actor) then pcall(function() tn.actor:K2_DestroyActor() end) end end
    for _, w in ipairs(S.wires) do
        for _, a in ipairs(w.actors or {}) do if valid(a) then pcall(function() a:K2_DestroyActor() end) end end
    end
    S.tents, S.wires = {}, {}
    pcall(rts.areaUnmark)
end

-- Marcador do fogo em area: anel de pontos laranja no circulo, enquanto algum soldado tiver a ordem.
CFG.AREA_DOTS = 12
function rts.areaUnmark()
    for _, d in ipairs((S.areaMark and S.areaMark.dots) or {}) do if valid(d) then pcall(function() d:K2_DestroyActor() end) end end
    S.areaMark = nil
end

function rts.areaMarkAt(area)
    rts.areaUnmark()
    local mat = findAsset(CFG.MARKER_MAT)
    local dots = {}
    for i = 1, CFG.AREA_DOTS do
        local a = 2 * math.pi * i / CFG.AREA_DOTS
        local x, y = area.X + math.cos(a) * CFG.AREA.radius, area.Y + math.sin(a) * CFG.AREA.radius
        local z = groundZ(x, y)
        local d = z and meshActor(x, y, z + 1, CFG.MARKER_MESH, { X = 0.35, Y = 0.35, Z = 0.02 })
        if d then
            if mat then pcall(function() d.StaticMeshComponent:SetMaterial(0, mat) end) end
            dots[#dots + 1] = d
        end
    end
    S.areaMark = { area = area, dots = dots }
end

function rts.areaMarkTick()
    local mk = S.areaMark
    if not mk then return end
    for _, m in ipairs(squad) do if m.area == mk.area and alive(m) then return end end
    rts.areaUnmark()
end

local function clearStructures()
    for _, a in ipairs(structures) do if valid(a) then a:K2_DestroyActor() end end
    structures = {}
end

-- Ponto de chegada da onda: a ENEMY_SPAWN_DIST do esquadrao, no primeiro angulo cujo chao fica perto da
-- altura do esquadrao (evita telhados e buracos).
local function waveSpawnPoint()
    local c = squadCenter()
    if not c then return nil end
    -- ponto dominado pelo inimigo vira cabeca de ponte: a onda nasce nele (o mais distante do esquadrao,
    -- desde que a mais de WAVE_POINT_MIN); retomar o ponto corta essa entrada avancada
    local best, bd = nil, CFG.WAVE_POINT_MIN
    for _, pt in ipairs(points) do
        local d = flatDist(c, pt)
        if pt.owner == CFG.ENEMY_TEAM and d > bd then best, bd = pt, d end
    end
    if best then return { X = best.X, Y = best.Y, Z = best.Z, from = best.name } end
    local a0 = math.random() * 2 * math.pi
    for k = 0, 11 do
        local a = a0 + k * math.pi / 6
        local x, y = c.X + math.cos(a) * CFG.ENEMY_SPAWN_DIST, c.Y + math.sin(a) * CFG.ENEMY_SPAWN_DIST
        local z = groundZ(x, y)
        if z and math.abs(z - c.Z) < 250 then return { X = x, Y = y, Z = z } end
    end
    return nil
end

-- Segundo grupo da pinca: a 90-150 graus da entrada principal, a mesma distancia, em chao na altura do esquadrao.
CFG.FLANK_WAVE, CFG.FLANK_CHANCE, CFG.FLANK_MIN = 4, 0.4, 6  -- 3 e 0,5: robo caiu na onda 7
local function flankPoint(p)
    local c = squadCenter()
    if not c then return nil end
    local a1 = math.atan(p.Y - c.Y, p.X - c.X)
    local side = (math.random() < 0.5) and 1 or -1
    for _, deg in ipairs({ 120, 100, 140, 90, 150 }) do
        for _, sg in ipairs({ side, -side }) do
            local a = a1 + sg * math.rad(deg)
            local x, y = c.X + math.cos(a) * CFG.ENEMY_SPAWN_DIST, c.Y + math.sin(a) * CFG.ENEMY_SPAWN_DIST
            local z = groundZ(x, y)
            if z and math.abs(z - c.Z) < 250 then return { X = x, Y = y, Z = z } end
        end
    end
    return nil
end

local function clearEnemies()
    for _, m in ipairs(enemies) do
        pcall(destroyMarker, m)  -- hook de animacao (endereco reaproveitado), estandarte e marcadores
        if valid(m.pawn) then m.pawn:K2_DestroyActor() end
        releaseController(m.hpc)
    end
    enemies = {}
end

-- Resumo da partida (alerta longo + log) na vitoria ou derrota.
CFG.SND_VICTORY = "/Game/Audio/UI/WinResultVictory_Cue.WinResultVictory_Cue"
CFG.SND_DEFEAT = "/Game/Audio/UI/WinResultDefeat_Cue.WinResultDefeat_Cue"
local function endMatch(won)
    local ok, err = pcall(function()
        local cue = asset(won and CFG.SND_VICTORY or CFG.SND_DEFEAT)
        if cue then gs():PlaySound2D(world(), cue, 1.0, 1.0, 0.0, nil, nil) end
    end)
    if not ok then logOnce("som de resultado", err) end
    local dur = now() - (combat.startT or now())
    local sh, hi = combat.shots[1] or 0, combat.hits[1] or 0
    local vets = 0
    for _, m in ipairs(squad) do if rank(m) > 0 then vets = vets + 1 end end
    local line = string.format("RESUMO: %d:%02d | ondas %d | abates %d, perdas %d | precisão %.0f%% | morteiros %d, granadas %d | veteranos vivos %d | pontos %d/%d",
        math.floor(dur / 60), math.floor(dur % 60), combat.wave, combat.kills, combat.losses, sh > 0 and 100 * hi / sh or 0,
        mortar.calls[1] or 0, mortar.grenades[1] or 0, vets, pointsOwned(CFG.FRIENDLY_TEAM), #points)
    notify(line, 25.0)
    pcall(sv.clear)
end

-- Ondas automaticas: espera WAVE_DELAY apos limpar a onda, reforca o esquadrao e manda a proxima.
-- Economia inimiga: cada ponto que o inimigo segura rende AI.rate de mao de obra por s (so com ondas
-- automaticas). Durante uma onda, a cada AI.every s ele gasta AI.cost por soldado em reforcos de 2 a 3 que
-- surgem AI.back cm atras de um ponto dele (do lado oposto ao nosso esquadrao), ate AI.max por onda.
-- Perder pontos endurece as ondas; retoma-los corta a renda dele.
CFG.AI = { rate = 0.6, every = 20.0, cost = 20, max = 6, back = 900.0, cap = 200 }
local ai = { mp = 0, lastT = nil, nextT = 0, sent = 0 }

function ai.reset()
    ai.mp, ai.lastT, ai.nextT, ai.sent = 0, nil, 0, 0
end

-- Ponto inimigo de onde sai o reforco: o mais perto do nosso esquadrao (pressiona onde ha luta).
function ai.source()
    local c = squadCenter() or rts.base()
    local best, bd = nil, math.huge
    for _, pt in ipairs(points) do
        if pt.owner == CFG.ENEMY_TEAM then
            local d = c and flatDist(pt, c) or 0
            if d < bd then best, bd = pt, d end
        end
    end
    return best, c
end

function ai.tick()
    local t = now()
    local dt = ai.lastT and math.min(t - ai.lastT, 1.0) or 0
    ai.lastT = t
    local held = pointsOwned(CFG.ENEMY_TEAM)
    ai.mp = math.min(CFG.AI.cap, ai.mp + held * CFG.AI.rate * dt)
    if #enemies == 0 or held == 0 or ai.sent >= CFG.AI.max or t < ai.nextT then return end
    local n = math.min(math.random(2, 3), CFG.AI.max - ai.sent, math.floor(ai.mp / CFG.AI.cost))
    n = logi.eAfford(n)  -- reforco tambem precisa de camisa + carregamento na frente
    if n < 1 then return end
    local pt, c = ai.source()
    if not pt then return end
    local dx, dy = c and (pt.X - c.X) or 1, c and (pt.Y - c.Y) or 0
    local len = math.max(math.sqrt(dx * dx + dy * dy), 1)
    local at = { X = pt.X + dx / len * CFG.AI.back, Y = pt.Y + dy / len * CFG.AI.back }
    at.Z = groundZ(at.X, at.Y) or pt.Z
    local before = #enemies
    spawnEnemies(at, n, true, true)
    local made = #enemies - before
    ai.nextT = t + CFG.AI.every
    if made > 0 then
        logi.eConsume(made, "reforço")
        ai.mp = ai.mp - made * CFG.AI.cost
        ai.sent = ai.sent + made
        combat.reinforced = (combat.reinforced or 0) + made
        notify(string.format("REFORÇO INIMIGO: %d %s pelo ponto %s (retome os pontos para cortar)", made, made == 1 and "soldado" or "soldados", pt.name), 5.0)
    end
end

local function waveTick()
    if not combat.auto then return end
    pcall(ai.tick)
    if #squad == 0 and economy.manpower < CFG.WEAPONS.rifle.cost then
        combat.auto = false
        combat.nextWaveAt = nil
        endMatch(false); notify(string.format("DERROTA: esquadrao perdido na onda %d (abates %d). Shift+F6 para recomecar", combat.wave, combat.kills))
        return
    end
    local assault = combat.mode == "assault"
    if not assault and #points > 0 and pointsOwned(CFG.ENEMY_TEAM) == #points then
        combat.auto = false
        combat.nextWaveAt = nil
        endMatch(false); notify(string.format("DERROTA: o inimigo tomou todos os pontos na onda %d. Shift+F6 para recomecar", combat.wave))
        return
    end
    -- vitoria por dominio: todos os pontos nossos por HOLD_TO_WIN s seguidos (com ondas automaticas)
    if #points > 0 and pointsOwned(CFG.FRIENDLY_TEAM) == #points then
        combat.holdSince = combat.holdSince or now()
        local hold = assault and CFG.ASSAULT.hold or CFG.HOLD_TO_WIN
        if now() - combat.holdSince >= hold or (assault and #enemies == 0) then
            combat.auto, combat.nextWaveAt, combat.won = false, nil, true
            clearEnemies()
            if assault then
                endMatch(true); notify(string.format("VITÓRIA NO ASSALTO: os %d pontos são seus (abates %d, perdas %d). Alt+F6 = outro assalto",
                    #points, combat.kills, combat.losses), 15.0)
                return
            end
            endMatch(true); notify(string.format("VITORIA POR DOMINIO: todos os pontos por %.0f s (onda %d, abates %d). Shift+F6 = nova partida",
                CFG.HOLD_TO_WIN, combat.wave, combat.kills), 15.0)
            return
        end
    else
        combat.holdSince = nil
    end
    if #enemies > 0 or assault then return end  -- assalto: sem ondas; o inimigo so reforca pelos pontos
    if combat.wave >= CFG.WAVES_TO_WIN then
        combat.auto, combat.nextWaveAt, combat.won = false, nil, true
        earn(CFG.WAVE_BOUNTY)
        endMatch(true); notify(string.format("VITORIA: %d ondas vencidas (abates %d, perdas %d). Shift+F6 = nova partida", combat.wave, combat.kills, combat.losses), 15.0)
        return
    end
    local t = now()
    if not combat.nextWaveAt then
        if combat.wave > 0 then earn(CFG.WAVE_BOUNTY) end
        -- onda quebrada: o inimigo se reagrupa (sem isso o contador de ondas subia mais rapido que a nossa economia)
        local delay = CFG.WAVE_DELAY + (combat.broken and CFG.MORALE.regroup or 0)
        combat.nextWaveAt = t + delay
        notify(string.format("proxima onda em %.0f s%s (esquadrao %d, mao de obra %.0f)", delay,
            combat.broken and " (o inimigo se reagrupa)" or "", #squad, economy.manpower))
    elseif t >= combat.nextWaveAt then
        combat.nextWaveAt = nil
        ai.sent = 0
        local p = waveSpawnPoint()
        if not p then log("sem ponto livre para a onda; tentando de novo"); return end
        local n = math.min(CFG.WAVE_MAX, CFG.ENEMY_SQUAD_SIZE + math.floor(combat.wave * CFG.WAVE_GROWTH)
            + math.floor(#squad * CFG.WAVE_SQUAD_SCALE))
        n = logi.waveCut(n)
        -- a partir da onda FLANK_WAVE, metade das vezes a onda chega em pinca (dois grupos, angulos diferentes)
        local q = (combat.wave + 1 >= CFG.FLANK_WAVE and n >= CFG.FLANK_MIN and math.random() < CFG.FLANK_CHANCE) and flankPoint(p) or nil
        if q then
            local n1 = math.ceil(n / 2)
            spawnEnemies(p, n1)
            spawnEnemies(q, n - n1, true)
            combat.flanks = (combat.flanks or 0) + 1
            notify(string.format("onda %d em PINÇA: dois grupos", combat.wave), 5.0)
        else
            spawnEnemies(p, n)
        end
        logi.eCommit(combat.waveSize or 0)
    end
end

local function toggleWaves()
    combat.auto = not combat.auto
    combat.nextWaveAt = nil
    if combat.auto and combat.won then combat.wave, combat.won = 0, false end  -- nova campanha apos vitoria
    combat.holdSince = nil
    if combat.auto then combat.startT = now() end
    if combat.auto and #points == 0 then
        local ok, err = pcall(setupPoints)
        if not ok then logOnce("setupPoints", err) end
    end
    notify("ondas automaticas: " .. tostring(combat.auto))
end


local function clearSquad()
    for _, m in ipairs(squad) do
        pcall(destroyMarker, m)
        if valid(m.pawn) then m.pawn:K2_DestroyActor() end
        releaseController(m.hpc)
    end
    squad = {}
    clearEnemies()
    for _, c in ipairs(corpses) do if valid(c.pawn) then c.pawn:K2_DestroyActor() end end
    corpses = {}
    clearStructures()
    clearPoints()
    clearStrikes()
    clearCrates()
    clearTrenches()
    fort.clearExtras()
    pcall(logi.reset)
    ai.reset()
    S.crateReadyAt = nil
    mortar.readyAt, mortar.enemyNext = 0, nil
    combat.auto, combat.nextWaveAt, combat.wave, combat.kills, combat.losses, combat.won = false, nil, 0, 0, 0, false
    combat.holdSince, combat.mode = nil, nil
    for _, k in ipairs({ "shots", "hits", "dmg", "covered" }) do combat[k] = { [0] = 0, [1] = 0 } end
    combat.coverMoves, combat.bounds, combat.dryOut, combat.resupplied = 0, 0, 0, 0
    for _, k in ipairs({ "dmg", "calls", "grenades", "gdmg" }) do mortar[k] = { [0] = 0, [1] = 0 } end
    economy.manpower, economy.lastT = CFG.MANPOWER_START, nil
    log("esquadrao, inimigos e corpos removidos")
end

-- Dificuldade (Shift+F5 alterna): sobrescreve os valores de CFG usados pelas ondas e pela economia.
-- "normal" = valores calibrados com o jogador-robo (3 vitorias, 3 derrotas).
CFG.DIFFICULTIES = {
    { name = "fácil",   ENEMY_ACCURACY = 0.55, WAVE_GROWTH = 0.6, WAVE_SQUAD_SCALE = 0.25, MANPOWER_RATE = 1.2, FLANK_CHANCE = 0.25 },
    { name = "normal",  ENEMY_ACCURACY = 0.70, WAVE_GROWTH = 0.8, WAVE_SQUAD_SCALE = 0.40, MANPOWER_RATE = 1.0, FLANK_CHANCE = 0.40 },
    { name = "difícil", ENEMY_ACCURACY = 0.85, WAVE_GROWTH = 1.0, WAVE_SQUAD_SCALE = 0.50, MANPOWER_RATE = 0.9, FLANK_CHANCE = 0.55 },
}
S.difficulty = 2
-- Preferencias que sobrevivem ao reinicio do jogo ("chave=valor" por linha).
CFG.SETTINGS_FILE = "ue4ss/Mods/FoxholeRTS/settings.txt"

local function setDifficulty(i, quiet)
    S.difficulty = ((i - 1) % #CFG.DIFFICULTIES) + 1
    for k, v in pairs(CFG.DIFFICULTIES[S.difficulty]) do if k ~= "name" then CFG[k] = v end end
    if not quiet then
        notify("dificuldade: " .. CFG.DIFFICULTIES[S.difficulty].name, 4.0)
        pcall(function()
            local f = io.open(CFG.SETTINGS_FILE, "w")
            if f then f:write("difficulty=" .. S.difficulty .. "\n"); f:close() end
        end)
    end
    return CFG.DIFFICULTIES[S.difficulty].name
end

pcall(function()
    local f = io.open(CFG.SETTINGS_FILE, "r")
    if not f then return end
    local txt = f:read("*a") or ""
    f:close()
    local d = tonumber(txt:match("difficulty=(%d+)"))
    if d and d ~= S.difficulty then
        setDifficulty(d, true)
        log("dificuldade salva: " .. CFG.DIFFICULTIES[S.difficulty].name)
    end
end)

-- Nova partida (Shift+F6): limpa tudo, esquadrao inicial de START_SQUAD e ondas automaticas (que criam
-- os tres pontos de controle). Antes eram F11, F6 e Shift+F4.
CFG.START_SQUAD = 6
local function newGame()
    if not isLocalAuthority() then return false end
    local setup = logi.ready()
    if not setup then return false end
    clearSquad()
    if spawnSquad(CFG.START_SQUAD) < 1 then return false end
    selectGroup(0)
    if not logi.start(setup) then return false end
    combat.auto = false
    toggleWaves()
    notify(string.format("NOVA PARTIDA (%s): vença %d ondas ou segure todos os pontos por %.0f s (F5 = teclas)",
        CFG.DIFFICULTIES[S.difficulty].name, CFG.WAVES_TO_WIN, CFG.HOLD_TO_WIN), 8.0)
    return true
end

-- Assalto (Alt+F6): o inimigo comeca dono dos tres pontos, mais longe (ASSAULT.dist), cada um com trincheira,
-- arame do nosso lado e ASSAULT.garrison soldados; nos com ASSAULT.squad e ASSAULT.mp de mao de obra. Sem
-- ondas: o inimigo so reforca pela economia dos pontos (cada captura nossa libera um contra-ataque em
-- ASSAULT.counter s). Vitoria: todos os pontos nossos sem inimigo vivo, ou segura-los ASSAULT.hold s.
-- Derrota: sem soldados e sem mao de obra para um fuzileiro.
CFG.ASSAULT = { squad = 8, mp = 120, garrison = 4, hold = 60.0, counter = 8.0, aimp = 60, leash = 300.0,
                dist = { 3000.0, 2600.0, 3600.0 } }
-- Ponto tomado no assalto: o inimigo volta a poder mandar reforcos em ASSAULT.counter s.
function rts.counter()
    ai.sent, ai.nextT = 0, now() + CFG.ASSAULT.counter
end

function rts.newAssault()
    if not isLocalAuthority() then return false end
    local setup = logi.ready()
    if not setup then return false end
    clearSquad()
    if spawnSquad(CFG.ASSAULT.squad) < 1 then return false end
    selectGroup(0)
    if not logi.start(setup) then return false end
    local keep = CFG.POINT_SETUP_DIST
    CFG.POINT_SETUP_DIST = CFG.ASSAULT.dist
    local ok, err = pcall(setupPoints)
    CFG.POINT_SETUP_DIST = keep
    if not ok then logOnce("assalto: pontos", err) end
    if #points == 0 then notify("assalto: sem lugar para os pontos aqui", 4.0); return false end
    for _, pt in ipairs(points) do
        pt.owner, pt.prog = CFG.ENEMY_TEAM, -1.0
        pcall(pointVisual, pt)
        if fort.place({ X = pt.X, Y = pt.Y }) then pt.dug = true end
        pcall(fort.enemyWire, pt)
        -- guarnicao em circulo de 1,5 m no chao do ponto (a formacao das ondas se espalhava e caia em telhados)
        local G = CFG.ASSAULT.garrison
        for k = 1, G do
            local ang = 2 * math.pi * k / G
            local x, y = pt.X + math.cos(ang) * 150, pt.Y + math.sin(ang) * 150
            local z = groundZ(x, y)
            if not z or math.abs(z - pt.Z) > 120 then x, y, z = pt.X, pt.Y, pt.Z end
            local role = (k == 1 and pt == points[1]) and "officer" or roleFor(k)  -- oficial no ponto da frente
            local e = spawnSoldier(x, y, z + 90, slotFor(k), CFG.ENEMY_TEAM, role)
            if e then e.post = pt; table.insert(enemies, e) end
        end
    end
    combat.wave = 0
    economy.manpower, economy.lastT = CFG.ASSAULT.mp, nil
    ai.reset()
    ai.mp, ai.nextT = CFG.ASSAULT.aimp, now() + 2 * CFG.AI.every  -- sem reforco logo de cara
    combat.mode, combat.auto, combat.won, combat.nextWaveAt, combat.holdSince = "assault", true, false, nil, nil
    combat.startT = now()
    notify(string.format("ASSALTO (%s): o inimigo tem os %d pontos, entrincheirado e com arame. Tome todos (ou segure-os %.0f s). Cada ponto tomado provoca contra-ataque",
        CFG.DIFFICULTIES[S.difficulty].name, #points, CFG.ASSAULT.hold), 10.0)
    log(string.format("assalto: %d pontos, %d inimigos, %d soldados", #points, #enemies, #squad))
    return true
end

-- Salvar e continuar (Ctrl+F6). Com ondas automaticas, a partida e gravada a cada SAVE_EVERY s em SAVE_FILE
-- (Lua "return {...}", lido com load num ambiente vazio): onda, placar, mao de obra, dificuldade, pontos e
-- donos, barreiras, trincheiras e cada soldado vivo dos dois lados (classe, posicao, vida, abates, municao).
-- Vitoria ou derrota apagam o save. Caixas, morteiros e alvos nao sao gravados (duram segundos).
CFG.SAVE_FILE = "ue4ss/Mods/FoxholeRTS/save.txt"
CFG.SAVE_EVERY = 30.0

function sv.ser(v)
    local t = type(v)
    if t == "number" then
        if v ~= v or v == math.huge or v == -math.huge then return "0" end
        return (math.type and math.type(v) == "integer") and tostring(v) or string.format("%.3f", v)
    elseif t == "string" then return string.format("%q", v)
    elseif t == "boolean" then return tostring(v)
    elseif t == "table" then
        local out = {}
        for k, x in pairs(v) do
            local key = type(k) == "number" and ("[" .. k .. "]") or ("[" .. string.format("%q", k) .. "]")
            out[#out + 1] = key .. "=" .. sv.ser(x)
        end
        return "{" .. table.concat(out, ",") .. "}"
    end
    return "nil"
end

function sv.parse(txt)
    local chunk = load(txt or "", "save", "t", {})
    if not chunk then return nil end
    local ok, d = pcall(chunk)
    if ok and type(d) == "table" and d.v == 1 then return d end
    return nil
end

function sv.map()
    local ok, n = pcall(function() return world():GetFullName() end)
    return ok and n and (tostring(n):match("([%w_]+)$") or tostring(n)) or nil
end

local function unitData(m)
    local l = loc(m)
    local post
    for i, pt in ipairs(points) do if m.post == pt then post = i end end
    return { role = m.role or "rifle", x = l.X, y = l.Y, z = l.Z, hp = m.pawn.Health, kills = m.kills or 0,
             ammo = m.ammo, group = m.group, post = post }
end

function sv.collect()
    local t = now()
    local d = { v = 1, map = sv.map(), diff = S.difficulty, wave = combat.wave, kills = combat.kills,
        losses = combat.losses, elapsed = t - (combat.startT or t), mp = economy.manpower, aimp = ai.mp,
        shots = combat.shots and combat.shots[1] or 0, hits = combat.hits and combat.hits[1] or 0,
        nextIn = combat.nextWaveAt and math.max(0, combat.nextWaveAt - t) or nil, mode = combat.mode,
        points = {}, squad = {}, enemies = {}, walls = {}, trenches = {}, tents = {}, wires = {}, logi = logi.snapshot(), elogi = logi.eSnapshot() }
    -- dono: 1 nosso, 0 inimigo, -1 neutro
    for _, pt in ipairs(points) do d.points[#d.points + 1] = { x = pt.X, y = pt.Y, owner = pt.owner or -1, prog = pt.prog or 0 } end
    for _, m in ipairs(squad) do if alive(m) then d.squad[#d.squad + 1] = unitData(m) end end
    for _, m in ipairs(enemies) do if alive(m) then d.enemies[#d.enemies + 1] = unitData(m) end end
    for _, a in ipairs(structures) do
        if valid(a) then
            local l, r = a:K2_GetActorLocation(), a:K2_GetActorRotation()
            d.walls[#d.walls + 1] = { x = l.X, y = l.Y, yaw = r.Yaw }
        end
    end
    for _, tr in ipairs(S.trenches) do d.trenches[#d.trenches + 1] = { x = tr.X, y = tr.Y } end
    for _, tn in ipairs(S.tents) do d.tents[#d.tents + 1] = { x = tn.X, y = tn.Y, yaw = tn.yaw } end
    for _, w in ipairs(S.wires) do d.wires[#d.wires + 1] = { x = w.X, y = w.Y, yaw = w.yaw } end
    for i, pt in ipairs(points) do
        local q = d.points[i]
        q.dug, q.wired = pt.dug or nil, pt.wired or nil
    end
    return d
end

function sv.save()
    if not combat.auto or combat.won or #squad == 0 then return false end
    local f = io.open(CFG.SAVE_FILE, "w")
    if not f then return false end
    f:write("return " .. sv.ser(sv.collect()) .. "\n")
    f:close()
    return true
end

function sv.read()
    local f = io.open(CFG.SAVE_FILE, "r")
    if not f then return nil end
    local txt = f:read("*a")
    f:close()
    return sv.parse(txt)
end

function sv.clear() os.remove(CFG.SAVE_FILE) end

-- Recria a partida de d (tabela de sv.collect) sobre um campo limpo.
function sv.restore(d)
    clearSquad()
    setDifficulty(d.diff or S.difficulty, true)
    for _, q in ipairs(d.points or {}) do
        local pt = addPoint(q.x, q.y)
        if pt then
            pt.owner = (q.owner ~= -1) and q.owner or nil
            pt.prog = q.prog or 0
            pt.dug, pt.wired = q.dug, q.wired
            pcall(pointVisual, pt)
        end
    end
    for _, w in ipairs(d.walls or {}) do
        local z = groundZ(w.x, w.y)
        local a = z and fort.wall(w.x, w.y, z, w.yaw or 0)
        if a then structures[#structures + 1] = a end
    end
    for _, tr in ipairs(d.trenches or {}) do fort.place({ X = tr.x, Y = tr.y }) end
    for _, tn in ipairs(d.tents or {}) do fort.tentAt(tn.x, tn.y, tn.yaw or 0) end
    for _, w in ipairs(d.wires or {}) do fort.wireAt(w.x, w.y, w.yaw or 0) end
    local function unit(u, i, team)
        local z = groundZ(u.x, u.y) or u.z or 0
        local m = spawnSoldier(u.x, u.y, z + 90, slotFor(i), team, u.role)
        if not m then return nil end
        m.kills, m.ammo = u.kills, u.ammo
        if u.hp then pcall(function() m.pawn.Health = math.max(1, u.hp); m.pawn:OnRep_Health() end) end
        return m
    end
    for i, u in ipairs(d.squad or {}) do
        local m = unit(u, i, CFG.FRIENDLY_TEAM)
        if m then m.group = u.group or ((i % 2) + 1); m.sel = true; squad[#squad + 1] = m end
    end
    for i, u in ipairs(d.enemies or {}) do
        local m = unit(u, i, CFG.ENEMY_TEAM)
        if m then m.post = u.post and points[u.post] or nil; enemies[#enemies + 1] = m end
    end
    pcall(syncMarkers)
    local t = now()
    combat.wave, combat.kills, combat.losses = d.wave or 0, d.kills or 0, d.losses or 0
    combat.shots[1], combat.hits[1] = d.shots or 0, d.hits or 0
    economy.manpower, economy.lastT = d.mp or CFG.MANPOWER_START, nil
    ai.mp, ai.nextT = d.aimp or 0, now() + CFG.AI.every  -- sem reforco no instante do carregamento
    combat.auto, combat.won, combat.holdSince, combat.mode = true, false, nil, d.mode
    combat.startT = t - (d.elapsed or 0)
    combat.nextWaveAt = d.nextIn and (t + math.max(d.nextIn, 10.0)) or nil
    sv.nextT = t + CFG.SAVE_EVERY
    return #squad
end

function sv.load()
    if not isLocalAuthority() then return false end
    local d = sv.read()
    if not d then notify("nenhuma partida salva", 3.0); return false end
    local here = sv.map()
    if d.map and here and d.map ~= here then notify("a partida salva é de outro mapa (" .. d.map .. ")", 4.0); return false end
    if d.logi and not logi.ready() then return false end
    local n = sv.restore(d)
    if d.logi then pcall(logi.restore, d.logi); pcall(logi.eRestore, d.elogi) end
    local where = combat.mode == "assault" and string.format("assalto, pontos inimigos %d/%d", pointsOwned(CFG.ENEMY_TEAM), #points)
        or string.format("onda %d/%d", combat.wave, CFG.WAVES_TO_WIN)
    notify(string.format("PARTIDA CONTINUADA (%s): %s, %d soldados, %d inimigos, mão de obra %.0f",
        CFG.DIFFICULTIES[S.difficulty].name, where, n, #enemies, economy.manpower), 8.0)
    log(string.format("save carregado: onda %d, %d soldados, %d inimigos, %d pontos, %d barreiras, %d trincheiras, %d postos, %d arames",
        combat.wave, n, #enemies, #points, #structures, #S.trenches, #S.tents, #S.wires))
    return true
end

-- Por quadro: grava a cada SAVE_EVERY s durante a partida; sem partida, avisa uma vez que ha save.
function sv.tick()
    if not rts.active then return end
    local t = now()
    if combat.auto and not combat.won then
        if t >= (sv.nextT or 0) then
            sv.nextT = t + CFG.SAVE_EVERY
            if t - (combat.startT or t) > 5.0 then pcall(sv.save) end
        end
    elseif not sv.hinted and #squad == 0 then
        sv.hinted = true
        local d = sv.read()
        if d then
            local what = d.mode == "assault" and "assalto" or string.format("onda %d", d.wave or 0)
            notify(string.format("há uma partida salva (%s, %d soldados): Ctrl+F6 continua, Shift+F6 começa outra",
                what, #(d.squad or {})), 10.0)
        end
    end
end

-- Erros repetidos a cada frame inundam o log do UE4SS; registra cada mensagem distinta uma vez.
S.loggedErrors = {}
function logOnce(tag, err)
    local k = tag .. tostring(err)
    if S.loggedErrors[k] then return end
    S.loggedErrors[k] = true
    log(tag .. ": " .. tostring(err))
end

-- Painel fixo de status. O HUD do Foxhole e Slate nativo (sem TextBlock acessivel); o unico UMG vivo
-- e o CrosshairWidget_C (cursor, fora do viewport). Criamos outra instancia dessa classe, escondemos a
-- imagem, penduramos um TextBlock no CanvasPanel raiz e adicionamos ao viewport (validado por captura).
CFG.HUD_POS = { X = 24, Y = 150 }
CFG.HUD_COLOR = { SpecifiedColor = { R = 1.0, G = 0.75, B = 0.2, A = 1.0 }, ColorUseRule = 0 }
CFG.HUD_PERIOD = 0.25
CFG.HUD_FONT_SIZE = 16
CFG.HELP_SECS = 40.0         -- ajuda visivel ao ligar o RTS; F5 alterna
CFG.HELP_FONT_SIZE = 13
CFG.HELP_TEXT = table.concat({
    "Botão esq.: selecionar (arrastar = caixa, Shift soma)   1-5: grupo (2 toques = ir até ele)   0: todos   Alt+1-5: pôr no grupo",
    "Espaço: ir ao último alerta (de novo = anteriores)   Q/E: ponto anterior/próximo",
    "Logística: Alt+L = implantar cenário nos locais nativos   L: depósito   Shift+L: prioridade   Ctrl+L: ver cadeia",
    "Botão dir./F7: mover (sobre inimigo = atacar; Shift = fila; Ctrl = fogo de supressão em área)   Home: recuar   End: segurar",
    "Ctrl+1/2/3/4/0: recrutar fuzileiro/metralhador/atirador/médico/oficial (cursor num ponto seu = nasce lá)",
    "Pontos seus curam e recarregam; a base (F2) recarrega   Ctrl+6: caixa de munição sob o cursor (−25)",
    "Ctrl+5: morteiro   Ctrl+7: trincheira (-20)   Ctrl+8: posto de socorro (-30)   Ctrl+9: arame (-10)   K: barreira   J: ponto",
    "Vitória: 10 ondas ou todos os pontos por 90 s",
    "Shift+F6: NOVA PARTIDA   Alt+F6: ASSALTO   Ctrl+F6: continuar salva   F6: esquadrão grátis   F4: onda   Shift+F4: ondas automáticas   F11: limpar",
    "Pause ou Ctrl+Espaço: pausa tática   Insert: velocidade 1x/2x/3x",
    "WASD/setas/F3: câmera   roda do mouse ou PageUp/PageDown: zoom   F2: centralizar   F5: esta ajuda   Shift+F5: dificuldade",
}, "\n")
local hud = { w = nil, tb = nil, help = nil, text = nil, nextT = 0, helpOn = nil }

local function hudCreate()
    local base = FindFirstOf("CrosshairWidget_C")
    if not (base and base:IsValid()) then return false end
    local w = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary"):Create(world(), base:GetClass(), playerController())
    if not valid(w) then return false end
    local root = w.WidgetTree.RootWidget
    for i = 0, root:GetChildrenCount() - 1 do root:GetChildAt(i):SetVisibility(1) end  -- Collapsed
    local tb = StaticConstructObject(StaticFindObject("/Script/UMG.TextBlock"), w.WidgetTree)
    local slot = root:AddChildToCanvas(tb)
    slot:SetAutoSize(true)
    slot:SetPosition(CFG.HUD_POS)
    tb.Font.Size = CFG.HUD_FONT_SIZE  -- Roboto da engine, 24 por padrao; acentos renderizam (validado)
    tb:SetColorAndOpacity(CFG.HUD_COLOR)
    tb:SetShadowOffset({ X = 1.5, Y = 1.5 })
    tb:SetShadowColorAndOpacity({ R = 0, G = 0, B = 0, A = 0.85 })
    local help = StaticConstructObject(StaticFindObject("/Script/UMG.TextBlock"), w.WidgetTree)
    local hs = root:AddChildToCanvas(help)
    hs:SetAutoSize(true)
    -- canto inferior esquerdo (ancora e alinhamento em (0, 1)): a esquerda, abaixo do painel, ficam os
    -- alertas do jogo, que a ajuda cobria (captura gr1.png)
    hs:SetAnchors({ Minimum = { X = 0, Y = 1 }, Maximum = { X = 0, Y = 1 } })
    hs:SetAlignment({ X = 0, Y = 1 })
    hs:SetPosition({ X = CFG.HUD_POS.X, Y = -90 })
    help.Font.Size = CFG.HELP_FONT_SIZE
    help:SetColorAndOpacity({ SpecifiedColor = { R = 0.95, G = 0.95, B = 0.9, A = 1.0 }, ColorUseRule = 0 })
    help:SetShadowOffset({ X = 1.5, Y = 1.5 })
    help:SetShadowColorAndOpacity({ R = 0, G = 0, B = 0, A = 0.85 })
    help:SetText(FText(CFG.HELP_TEXT))
    w:AddToViewport(50)
    hud.w, hud.tb, hud.help, hud.text, hud.helpOn = w, tb, help, nil, nil
    return true
end

local function hudLine()
    local parts = {
        string.format("mão de obra %.0f", economy.manpower),
        string.format("esquadrão %d (sel. %d%s)", #squad, countSelected(),
            veterans(squad, true) > 0 and string.format(", %d vet.", veterans(squad, true)) or ""),
    }
    local low, dry = 0, 0
    for _, m in ipairs(squad) do
        if m.ammo and m.ammo < 1 then dry = dry + 1 elseif ammoFrac(m) < CFG.AMMO_LOW then low = low + 1 end
    end
    if dry > 0 then parts[#parts + 1] = string.format("SEM MUNIÇÃO %d", dry) end
    if low > 0 then parts[#parts + 1] = string.format("munição baixa %d", low) end
    if #structures > 0 then parts[#parts + 1] = string.format("barreiras %d", #structures) end
    if #S.crates > 0 then parts[#parts + 1] = string.format("caixas %d", #S.crates) end
    if #S.trenches > 0 then parts[#parts + 1] = string.format("trincheiras %d", #S.trenches) end
    if #S.tents > 0 then parts[#parts + 1] = string.format("postos %d", #S.tents) end
    if #S.wires > 0 then parts[#parts + 1] = string.format("arame %d", #S.wires) end
    if combat.auto and pointsOwned(CFG.ENEMY_TEAM) > 0 then parts[#parts + 1] = string.format("reforço inimigo %.0f", ai.mp) end
    if #points > 0 then
        local marks = {}
        for _, pt in ipairs(points) do
            local tag = (pt.owner == CFG.FRIENDLY_TEAM and "+") or (pt.owner == CFG.ENEMY_TEAM and "x") or "o"  -- nosso/inimigo/neutro
            local open = (pt.owner == CFG.FRIENDLY_TEAM and pt.prog < 0.999) or (pt.owner == CFG.ENEMY_TEAM and pt.prog > -0.999)
                or (pt.owner == nil and math.abs(pt.prog) > 0.001)
            marks[#marks + 1] = pt.name .. tag .. (open and string.format("%d%%", math.floor(pt.prog * 100 + 0.5)) or "")
        end
        parts[#parts + 1] = string.format("pontos %d/%d [%s]", pointsOwned(CFG.FRIENDLY_TEAM), #points, table.concat(marks, " "))
    end
    if combat.wave > 0 or #enemies > 0 then
        local wave = combat.auto and string.format("onda %d/%d", combat.wave, CFG.WAVES_TO_WIN) or string.format("onda %d", combat.wave)
        if combat.mode == "assault" then wave = string.format("ASSALTO: pontos inimigos %d/%d", pointsOwned(CFG.ENEMY_TEAM), #points) end
        parts[#parts + 1] = string.format("%s: %d inimigos | abates %d perdas %d", wave, #enemies, combat.kills, combat.losses)
    end
    local mleft = mortar.readyAt - now()
    parts[#parts + 1] = mleft > 0 and string.format("morteiro %.0f s", mleft) or "morteiro pronto"
    if combat.auto and combat.holdSince then
        local hold = combat.mode == "assault" and CFG.ASSAULT.hold or CFG.HOLD_TO_WIN
        parts[#parts + 1] = string.format("domínio %.0f s", math.max(0, hold - (now() - combat.holdSince)))
    end
    if combat.won then parts[#parts + 1] = "VITÓRIA" end
    if combat.auto and combat.nextWaveAt then
        parts[#parts + 1] = string.format("próxima onda em %.0f s", math.max(0, combat.nextWaveAt - now()))
    end
    local clockTag = S.paused and "PAUSADO | " or (S.speedI > 1 and string.format("%.0fx | ", CFG.SPEEDS[S.speedI]) or "")
    if S.alertNew > 0 then clockTag = string.format("! %d alerta%s (Espaço) | ", S.alertNew, S.alertNew > 1 and "s" or "") .. clockTag end
    local logiLine = ""
    if logi.on then
        local ok, l2 = pcall(logi.hudLine)
        if ok then logiLine = "\n" .. l2 end
    end
    return clockTag .. "RTS (" .. CFG.DIFFICULTIES[S.difficulty].name .. ") | " .. table.concat(parts, " | ") .. logiLine
end

local function hudTick()
    local t = now()
    local rt = gs():GetRealTimeSeconds(world())  -- periodo em tempo real: o painel atualiza com o jogo pausado
    if rt < hud.nextT then return end
    hud.nextT = rt + CFG.HUD_PERIOD
    if not rts.active then
        if valid(hud.w) and hud.w:IsInViewport() then hud.w:RemoveFromParent() end
        return
    end
    if not (valid(hud.w) and valid(hud.tb)) then
        if not hudCreate() then return end
    elseif not hud.w:IsInViewport() then
        hud.w:AddToViewport(50)
    end
    local showHelp = rts.help == true or (rts.help == nil and t < (rts.helpUntil or 0))
    if valid(hud.help) and showHelp ~= hud.helpOn then
        hud.help:SetVisibility(showHelp and 4 or 1)  -- SelfHitTestInvisible / Collapsed
        hud.helpOn = showHelp
    end
    local line = hudLine()
    if line ~= hud.text then
        hud.tb:SetText(FText(line))
        hud.text = line
    end
end

-- Loop por frame no game thread (UE4SS 3: hook de UEngine::Tick). Substitui LoopAsync +
-- ExecuteInGameThread, que enfileirava do thread assincrono e crashou o UE4SS no teste v0.2.
-- Etapas por quadro, cada uma isolada em pcall e cronometrada (os.clock no Windows = tempo de parede):
-- prof[nome] acumula ms; prof.frames conta quadros. Ver profile() no canal / F5.
local prof = { frames = 0 }
-- Leva o olho (comandante invisivel) ao soldado vivo mais perto do foco da camera; sem soldados, a base.
function rts.eyeTick()
    local t = now()
    if t < (rts.eyeT or 0) or not rts.focus then return end
    rts.eyeT = t + CFG.EYE_EVERY
    local pp = playerPawn()
    if not valid(pp) then return end
    local best, bd = nil, math.huge
    for _, m in ipairs(squad) do
        if alive(m) then
            local d = flatDist(loc(m), rts.focus)
            if d < bd then best, bd = loc(m), d end
        end
    end
    local at = best or rts.home
    if not at then return end
    pp:K2_SetActorLocation({ X = at.X, Y = at.Y, Z = at.Z + 10 }, false, {}, true)
    rts.eyeAt = at
end

local function step(name, f)
    local t0 = os.clock()
    local ok, err = pcall(f)
    if not ok then logOnce(name, err) end
    prof[name] = (prof[name] or 0) + (os.clock() - t0) * 1000
end

local function frameBody()
    if not isLocalAuthority() then return end
    step("hudTick", hudTick)
    if not rts.active and #squad == 0 and #enemies == 0 and #corpses == 0 and not combat.auto and #points == 0 then return end
    prof.frames = prof.frames + 1
    step("cameraTick", cameraTick)
    step("postureTick", anim.postureTick)
    step("saveTick", sv.tick)
    step("hpTick", rts.hpTick)
    if S.eye then step("eyeTick", rts.eyeTick) end
    step("mouseTick", mouseTick)
    step("pathTick", pathTick)
    if rts.markersOn ~= rts.active then step("syncMarkers", syncMarkers) end
    step("squadTick", squadTick)
    step("enemyTick", enemyTick)
    step("corpseTick", corpseTick)
    step("waveTick", waveTick)
    step("economyTick", economyTick)
    step("pointsTick", pointsTick)
    step("logiTick", logi.tick)
    step("mortarTick", mortarTick)
    step("stratTick", rts.stratTick)
end

LoopInGameThreadAfterFrames(1, function()
    tick.n = tick.n + 1
    tick.inFrame = true
    local ok, err = pcall(frameBody)
    tick.inFrame = false
    if not ok then logOnce("frame", err) end
end)

-- Media por quadro (ms) de cada etapa desde a ultima chamada; zera os acumuladores.
local function profile()
    local names, total = {}, 0
    for k, v in pairs(prof) do if k ~= "frames" then names[#names + 1] = k; total = total + v end end
    table.sort(names, function(x, y) return prof[x] > prof[y] end)
    local n = math.max(prof.frames, 1)
    local parts = {}
    for _, k in ipairs(names) do parts[#parts + 1] = string.format("%s %.2f", k, prof[k] / n) end
    local line = string.format("mod: %.2f ms/quadro em %d quadros | %s", total / n, prof.frames, table.concat(parts, ", "))
    prof = { frames = 0 }
    return line
end

local function status()
    local w = world()
    log("world=" .. (valid(w) and w:GetFullName() or "nil"))
    if valid(w) then
        log("IsServer=" .. tostring(ksl():IsServer(w)) .. " IsDedicated=" .. tostring(ksl():IsDedicatedServer(w)))
        local gm = gs():GetGameMode(w)
        log("GameMode=" .. (valid(gm) and gm:GetFullName() or "nil (cliente ou sem autoridade)"))
    end
    local p = playerPawn()
    if p then
        local l = p:K2_GetActorLocation()
        log(string.format("comandante=%s @ (%.0f, %.0f, %.0f) hp=%s", p:GetClass():GetFName():ToString(), l.X, l.Y, l.Z, tostring(p.Health)))
    end
    log(string.format("esquadrao: %s | inimigos: %s | mao de obra %.0f", composition(squad), composition(enemies), economy.manpower))
    local vr = {}
    for i, m in ipairs(squad) do if (m.kills or 0) > 0 then vr[#vr + 1] = string.format("%d:%s %d abates nv%d", i, m.role or "rifle", m.kills, rank(m)) end end
    if #vr > 0 then log("veterania: " .. table.concat(vr, ", ")) end
    log(string.format("rts=%s squad=%d inimigos=%d onda=%d abates=%d perdas=%d", tostring(rts.active), #squad, #enemies,
        combat.wave, combat.kills, combat.losses))
    log(string.format("tiros/acertos/dano: aliados %d/%d/%.0f inimigos %d/%d/%.0f", combat.shots[1], combat.hits[1], combat.dmg[1],
        combat.shots[0], combat.hits[0], combat.dmg[0]))
    log(string.format("tiros barrados por cobertura: aliados %d inimigos %d | idas a cobertura %d (lances inimigos %d) | rotas A* aliados %d inimigos %d",
        combat.covered[1], combat.covered[0], combat.coverMoves or 0, combat.bounds or 0, S.routeStats.squad, S.routeStats.enemy))
    log(string.format("HP curado por medicos: aliados %.0f inimigos %.0f", S.healStats[1], S.healStats[0]))
    for _, pt in ipairs(points) do log(string.format("ponto %s: dono %s prog %.2f", pt.name, tostring(pt.owner), pt.prog)) end
    log(string.format("morteiro: pedidos aliados %d inimigos %d | dano aliados %.0f inimigos %.0f", mortar.calls[1], mortar.calls[0],
        mortar.dmg[1], mortar.dmg[0]))
    log(string.format("granadas: aliados %d (dano %.0f) inimigos %d (dano %.0f)", mortar.grenades[1], mortar.gdmg[1],
        mortar.grenades[0], mortar.gdmg[0]))
    log(profile())
    log(string.format("controladores: %d criados, %d reaproveitados, %d no pool", S.poolStats.created, S.poolStats.reused, #S.hpcPool))
end

------------------------------------------------------------------------------------------------
-- Correcao de listen server: ClientStartRespawnTimer (impl 0x140b97950) arma timers e, se
-- Role == ROLE_Authority (byte +0xf0 == 3), chama a propria Client RPC. Num listen server o
-- controller do host e local E autoridade, a RPC executa aqui mesmo e recursa ate
-- EXCEPTION_STACK_OVERFLOW. Na entrada aninhada rebaixamos Role para AutonomousProxy durante a
-- chamada: ela executa o ramo de cliente sem reenviar a RPC; depois Role volta a Authority.
------------------------------------------------------------------------------------------------
CFG.ROLE_AUTONOMOUS = 2
CFG.ROLE_AUTHORITY = 3
S.respawnDepth = 0
S.respawnHookTargets = {
    "/Script/War.SimPlayerController:ClientStartRespawnTimer",
    "/Script/War.WarPlayerController:ClientStartRespawnTimer",
}

for _, fn in ipairs(S.respawnHookTargets) do
    if valid(StaticFindObject(fn)) then
        RegisterHook(fn, function(ctx)
            S.respawnDepth = S.respawnDepth + 1
            if S.respawnDepth < 2 then return end
            pcall(function()
                local pc = ctx:get()
                if valid(pc) then pc.Role = CFG.ROLE_AUTONOMOUS end
            end)
        end, function(ctx)
            if S.respawnDepth >= 2 then
                pcall(function()
                    local pc = ctx:get()
                    if valid(pc) then pc.Role = CFG.ROLE_AUTHORITY end
                end)
            end
            S.respawnDepth = math.max(0, S.respawnDepth - 1)
        end)
        log("hook de recursao instalado em " .. fn)
    end
end

-- Mesma doenca em RPCs de servidor: num servidor que tambem e o cliente, a acao local (ex.: pegar
-- item, 0x140b10e50) aplica o efeito e chama a RPC de servidor, cuja implementacao chama a acao local
-- de novo -> stack overflow. Nas aninhadas (profundidade >= 2) o parametro vira nil.
-- Isto evita o crash, mas NAO comprova aquisicao: o inventario continuou vazio nos testes.
S.serverRpcBreakers = {
    "/Script/War.SimCharacter:ServerTakePickup",
}
S.rpcDepth = {}
for _, fn in ipairs(S.serverRpcBreakers) do
    if valid(StaticFindObject(fn)) then
        S.rpcDepth[fn] = 0
        RegisterHook(fn, function(ctx, arg1)
            S.rpcDepth[fn] = S.rpcDepth[fn] + 1
            if S.rpcDepth[fn] >= 2 and arg1 then pcall(function() arg1:set(nil) end) end
        end, function()
            S.rpcDepth[fn] = math.max(0, S.rpcDepth[fn] - 1)
        end)
        log("quebra-recursao instalado em " .. fn)
    end
end

-- Builds Shipping ignoram o mapa da linha de comando (UGameInstance::StartGameInstance usa
-- Tmp = "" em 0x142576600), entao a sessao local e aberta daqui, no menu: OpenLevel com "listen".
-- Mapa do laboratorio: HomeRegionW, ou o caminho na 1a linha de Mods/FoxholeRTS/map.txt (ex.: /Game/Maps/HomeRegionC).
CFG.LAB_MAP = "/Game/Maps/HomeRegionW"
pcall(function()
    local f = io.open("ue4ss/Mods/FoxholeRTS/map.txt", "r")
    if not f then return end
    local line = (f:read("*l") or ""):gsub("^%s+", ""):gsub("%s+$", "")
    f:close()
    if line:find("^/Game/") then CFG.LAB_MAP = line end
end)
CFG.LAB_MAP_NAME = CFG.LAB_MAP:match("[^/]+$")

-- FName resolve o pacote sem diferenciar maiusculas; GetFullName devolve a grafia do asset
-- (DeadlandsHex do indice -> DeadLandsHex ao vivo). Comparar o caminho, nao um pedaço do nome.
function rts.isLabMap(name)
    return name:lower():find(CFG.LAB_MAP:lower() .. ".", 1, true) ~= nil
end

local function openLabSession()
    local w = world()
    if not valid(w) then log("sem world"); return end
    log("abrindo " .. CFG.LAB_MAP .. "?listen")
    gs():OpenLevel(w, FName(CFG.LAB_MAP), true, "listen")
end

------------------------------------------------------------------------------------------------
-- Laboratorio: autostart e canal de comandos (so com Mods/FoxholeRTS/autostart.txt).
------------------------------------------------------------------------------------------------
CFG.AUTOSTART_FILE = "ue4ss/Mods/FoxholeRTS/autostart.txt"
CFG.AUTOSTART_DELAY_S = 2   -- era 8; menos tempo com o aviso de servidor na tela
S.menuSeenAt = nil

local function fileExists(p)
    local f = io.open(p, "r")
    if f then f:close(); return true end
    return false
end

-- Executa CMD_FILE no game thread e grava o que for impresso com out() em CMD_OUT.
CFG.CMD_FILE = "D:/tools/foxhole-lab/cmd.lua"
CFG.CMD_OUT = "D:/tools/foxhole-lab/cmd.out"

local function runCommandFile()
    local f = io.open(CFG.CMD_FILE, "r")
    if not f then return end
    local src = f:read("*a")
    f:close()
    os.remove(CFG.CMD_FILE)
    local lines = {}
    local env = setmetatable({
        out = function(...)
            local parts = {}
            for i = 1, select("#", ...) do parts[#parts + 1] = tostring(select(i, ...)) end
            lines[#lines + 1] = table.concat(parts, "\t")
        end,
        world = world, gs = gs, ksl = ksl, valid = valid, playerController = playerController,
        playerPawn = playerPawn, squad = function() return squad end, rts = rts, status = status, log = log,
        enableRTS = enableRTS, disableRTS = disableRTS, spawnSquad = spawnSquad, clearSquad = clearSquad,
        orderMoveTo = function(x, y, z) return issueMove({ X = x, Y = y, Z = z }) end,
        selectGroup = selectGroup, stopSelected = stopSelected, recruit = recruit, economy = economy,
        selectAt = selectAt, selectBox = selectBox, countSelected = countSelected,
        attack = function(i) return issueAttack(enemies[i]) end, enemyAt = enemyAt,
        planPath = function(a, b, nav) return planPath(a, b, soldierPawns(), nav) end, routeStats = S.routeStats,
        build = function(x, y) return buildAt({ X = x, Y = y, Z = 0 }) end, structures = function() return structures end,
        healStats = S.healStats,
        points = function() return points end, addPoint = addPoint, setupPoints = setupPoints, clearPoints = clearPoints,
        pointStep = pointStep, retreat = retreatSelected, setDifficulty = setDifficulty,
        queueMoveTo = function(x, y, z) return queueMove({ X = x, Y = y, Z = z }) end, newGame = newGame, poolStats = S.poolStats,
        hpcPool = function() return S.hpcPool end, profile = function() return profile() end,
        throwGrenade = function(i, j) return throwGrenade(squad[i], enemies[j]) end,
        callMortar = function(x, y, team) return callMortar({ X = x, Y = y }, team) end, mortar = mortar,
        dropCrate = function(x, y) return dropCrate({ X = x, Y = y }) end, crates = function() return S.crates end, CFG = CFG,
        digTrench = function(x, y) return digTrench({ X = x, Y = y }) end, trenches = function() return S.trenches end,
        ai = ai, sv = sv, fort = fort, S = S, logi = logi, anim = anim,
        strikes = function() return strikes end,
        zoom = zoom, centerOnCommander = centerOnCommander,
        enemies = function() return enemies end, combat = combat, spawnEnemies = spawnEnemies,
        clearEnemies = clearEnemies, setTeam = setTeam, focusOn = focusOn, toggleWaves = toggleWaves,
    }, { __index = _G })
    local chunk, err = load(src, "cmd.lua", "t", env)
    if not chunk then
        lines[#lines + 1] = "ERRO de sintaxe: " .. tostring(err)
    else
        local ok, rerr = pcall(chunk)
        if not ok then lines[#lines + 1] = "ERRO: " .. tostring(rerr) end
    end
    local o = io.open(CFG.CMD_OUT, "w")
    if o then o:write(table.concat(lines, "\n"), "\n"); o:close() end
    log("cmd.lua executado (" .. #lines .. " linhas)")
end

-- Aviso do menu "Falha ao baixar informacoes do servidor [Erro: 1]": popup Slate nativo do WarAPIClient (a copia
-- de laboratorio e bloqueada no firewall de proposito). Nao e UserWidget (no menu so existe a mira), nao ha
-- UFunction para fecha-lo e liberar a rede iria contra o modo offline; por isso o autostart sai do menu rapido.
-- Um unico loop de laboratorio no game thread (1 s): canal de comandos + maquina do autostart.
-- autostart: "menu" -> espera AUTOSTART_DELAY_S -> OpenLevel -> "loading" -> liga o modo RTS -> "done"
if fileExists(CFG.AUTOSTART_FILE) then
    log("canal de comandos ativo: " .. CFG.CMD_FILE)
    log("autostart ativo: " .. CFG.LAB_MAP)
    local phase = "menu"
    local loadingTicks = 0
    LoopInGameThreadWithDelay(1000, function()
        local ok, err = pcall(runCommandFile)
        if not ok then logOnce("canal de comandos", err) end
        if phase == "done" then return end
        local w = world()
        if not valid(w) then return end
        local name = w:GetFullName()
        if phase == "menu" then
            if not string.find(name, "MainMenu", 1, true) then S.menuSeenAt = nil; return end
            if S.menuSeenAt == nil then
                S.menuSeenAt = os.time()
                log("menu detectado: " .. name)
            elseif os.time() - S.menuSeenAt >= CFG.AUTOSTART_DELAY_S then
                openLabSession()
                phase = "loading"
            end
        elseif phase == "loading" then
            loadingTicks = loadingTicks + 1
            if loadingTicks > 120 then log("autostart: mapa nao carregou"); phase = "done"; return end
            if rts.isLabMap(name) and isLocalAuthority() and valid(playerController()) then
                local ok2, err2 = pcall(enableRTS)
                if not ok2 then log("enableRTS: " .. tostring(err2)) end
                -- Carregar o pacote nao garante pawn/ponto de spawn pronto. So conclui quando ligou.
                if rts.active then pcall(status); phase = "done" end
            end
        end
    end)
end

local function onGame(f) return function() ExecuteInGameThread(function()
    local ok, err = pcall(f)
    if not ok then log("erro: " .. tostring(err)) end
end) end end

-- Teclas com e sem modificador (1/Ctrl+1, F4/Shift+F4, F6/Shift+F6, F7/Shift+F7, botao direito/Shift+botao
-- direito): nao sabemos se o UE4SS dispara so a combinacao ou as duas (sem teste com entrada real). A versao
-- sem modificador ignora o disparo com Shift/Ctrl/Alt seguro, o que serve aos dois casos.
S.MOD_KEYS = { "LeftShift", "RightShift", "LeftControl", "RightControl", "LeftAlt", "RightAlt" }
local function plain(f)
    return function(...)
        local pc = playerController()
        if valid(pc) then
            for _, k in ipairs(S.MOD_KEYS) do if keyDown(pc, k) then return end end
        end
        return f(...)
    end
end

RegisterKeyBind(Key.F9, onGame(openLabSession))
RegisterKeyBind(Key.F10, onGame(function() if rts.active then disableRTS() else enableRTS() end end))
RegisterKeyBind(Key.F5, onGame(plain(function()
    -- alterna a ajuda (nil = automatica nos primeiros HELP_SECS) e registra o status no log
    local shown = rts.help == true or (rts.help == nil and now() < (rts.helpUntil or 0))
    rts.help = not shown
    status()
end)))
RegisterKeyBind(Key.F6, onGame(plain(spawnSquad)))
RegisterKeyBind(Key.F5, { ModifierKey.SHIFT }, onGame(function() setDifficulty(S.difficulty + 1) end))
RegisterKeyBind(Key.F6, { ModifierKey.SHIFT }, onGame(newGame))
RegisterKeyBind(Key.F6, { ModifierKey.CONTROL }, onGame(function() if rts.active then sv.load() end end))
RegisterKeyBind(Key.F6, { ModifierKey.ALT }, onGame(function() if rts.active then rts.newAssault() end end))
RegisterKeyBind(Key.F7, onGame(plain(orderMove)))
RegisterKeyBind(Key.RIGHT_MOUSE_BUTTON, onGame(plain(function() if rts.active then orderMove() end end)))
RegisterKeyBind(Key.RIGHT_MOUSE_BUTTON, { ModifierKey.SHIFT }, onGame(function() if rts.active then orderMove(true) end end))
RegisterKeyBind(Key.F7, { ModifierKey.SHIFT }, onGame(function() if rts.active then orderMove(true) end end))
RegisterKeyBind(Key.RIGHT_MOUSE_BUTTON, { ModifierKey.CONTROL }, onGame(function() if rts.active then rts.areaOrder(cursorPoint()) end end))
RegisterKeyBind(Key.F7, { ModifierKey.CONTROL }, onGame(function() if rts.active then rts.areaOrder(cursorPoint()) end end))
RegisterKeyBind(Key.F11, onGame(clearSquad))
RegisterKeyBind(Key.F4, onGame(plain(function() spawnEnemies(rts.active and cursorPoint() or nil) end)))
RegisterKeyBind(Key.F4, { ModifierKey.SHIFT }, onGame(toggleWaves))
for g, key in ipairs({ Key.ONE, Key.TWO, Key.THREE, Key.FOUR, Key.FIVE }) do
    RegisterKeyBind(key, onGame(plain(function() if rts.active then selectGroup(g) end end)))
    RegisterKeyBind(key, { ModifierKey.ALT }, onGame(function() if rts.active then rts.assignGroup(g) end end))
end
RegisterKeyBind(Key.ZERO, onGame(plain(function() if rts.active then selectGroup(0) end end)))
RegisterKeyBind(Key.SPACE, onGame(plain(function() if rts.active then rts.jumpAlert() end end)))
RegisterKeyBind(Key.Q, onGame(plain(function() if rts.active then rts.cyclePoint(-1) end end)))
RegisterKeyBind(Key.L, onGame(plain(function() if rts.active then logi.sendTo(cursorPoint()) end end)))
RegisterKeyBind(Key.L, { ModifierKey.SHIFT }, onGame(function() if rts.active then logi.cyclePrio() end end))
RegisterKeyBind(Key.L, { ModifierKey.CONTROL }, onGame(function() if rts.active then logi.cycleView() end end))
RegisterKeyBind(Key.L, { ModifierKey.ALT }, onGame(logi.deploy))
RegisterKeyBind(Key.E, onGame(plain(function() if rts.active then rts.cyclePoint(1) end end)))
RegisterKeyBind(Key.ONE, { ModifierKey.CONTROL }, onGame(function() if rts.active then recruit("rifle") end end))
RegisterKeyBind(Key.TWO, { ModifierKey.CONTROL }, onGame(function() if rts.active then recruit("mg") end end))
RegisterKeyBind(Key.THREE, { ModifierKey.CONTROL }, onGame(function() if rts.active then recruit("sniper") end end))
RegisterKeyBind(Key.FOUR, { ModifierKey.CONTROL }, onGame(function() if rts.active then recruit("medic") end end))
RegisterKeyBind(Key.ZERO, { ModifierKey.CONTROL }, onGame(function() if rts.active then recruit("officer") end end))
RegisterKeyBind(Key.J, onGame(function()
    if rts.active then local c = cursorPoint(); if c then addPoint(c.X, c.Y) end end
end))
RegisterKeyBind(Key.FIVE, { ModifierKey.CONTROL }, onGame(function() if rts.active then callMortar(cursorPoint()) end end))
RegisterKeyBind(Key.SIX, { ModifierKey.CONTROL }, onGame(function() if rts.active then dropCrate(cursorPoint()) end end))
RegisterKeyBind(Key.SEVEN, { ModifierKey.CONTROL }, onGame(function() if rts.active then digTrench(cursorPoint()) end end))
RegisterKeyBind(Key.EIGHT, { ModifierKey.CONTROL }, onGame(function() if rts.active then fort.tent(cursorPoint()) end end))
RegisterKeyBind(Key.NINE, { ModifierKey.CONTROL }, onGame(function() if rts.active then fort.wire(cursorPoint()) end end))
RegisterKeyBind(Key.K, onGame(function() if rts.active then buildAt(cursorPoint()) end end))
RegisterKeyBind(Key.HOME, onGame(function() if rts.active then retreatSelected() end end))
RegisterKeyBind(Key.END, onGame(function() if rts.active then stopSelected() end end))
RegisterKeyBind(Key.F2, onGame(centerOnCommander))
RegisterKeyBind(Key.PAUSE, onGame(function() if rts.active then rts.togglePause() end end))
RegisterKeyBind(Key.SPACE, { ModifierKey.CONTROL }, onGame(function() if rts.active then rts.togglePause() end end))
RegisterKeyBind(Key.INS, onGame(function() if rts.active then rts.cycleSpeed() end end))
RegisterKeyBind(Key.F3, onGame(function() rts.edgePan = not rts.edgePan; log("pan pela borda: " .. tostring(rts.edgePan)) end))
RegisterKeyBind(Key.PAGE_UP, onGame(function() zoom(0.8) end))
RegisterKeyBind(Key.PAGE_DOWN, onGame(function() zoom(1.25) end))

log("v0.9 carregado (Pause/Ctrl+Espaco pausa, Insert velocidade, Ctrl+0 oficial, Alt+F6 assalto, Ctrl+F6 continuar partida salva, Ctrl+botao direito/Ctrl+F7 fogo em area, Ctrl+8 posto de socorro, Ctrl+9 arame, Shift+F5 dificuldade, Ctrl+6 caixa de munição, F9 sessao, F10 RTS, F6 esquadrao, Shift+F6 nova partida, F4 onda, Shift+F4 ondas auto, 1-5 grupos (Alt atribui) 0 todos, Espaco alerta, Q/E pontos, Alt+L implantar, L/Shift+L/Ctrl+L logistica, Ctrl+1/2/3/4 recrutar, Ctrl+5 morteiro, K barreira, J ponto, Home recuar, End segurar, botao direito/F7 mover, F11 limpar, F2 centralizar)")
