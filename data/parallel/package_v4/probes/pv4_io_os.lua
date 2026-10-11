-- pv4_io_os.lua - SONDA de io/os do Lua do UE4SS no Windows (PACOTE_V4). Preparada e NAO executada.
-- NAO e so leitura: cria e apaga DOIS arquivos temporarios pv4_io_probe_a.tmp / _b.tmp ao lado do save, nunca toca save.txt*.
-- Uso (sem botloop): copiar para D:/tools/foxhole-lab/ e rodar  sh D:/tools/foxhole-lab/run.sh pv4_io_os.lua
-- Objetivo: registrar o retorno REAL de cada chamada que sv.writeAtomic/sv.readFile/sv.clear usam, que ate hoje so foram vistas
-- no lupa: (1) os.rename sobre destino existente falha? (o codigo assume que sim e remove o destino antes);
-- (2) io.open(p,"wb"):write/flush/close; (3) f:seek("end") devolve o tamanho; (4) os.remove de arquivo inexistente; (5) os.clock.
-- PASS = (1) devolve nil/false com destino existente (o codigo ja trata) OU true (entao o remove previo e inofensivo);
--        (2)-(4) como descrito abaixo; qualquer ERRO de execucao e FAIL.
local dir = (CFG.SAVE_FILE:match("^(.*)[/\\][^/\\]*$")) or "."
local A, B = dir .. "/pv4_io_probe_a.tmp", dir .. "/pv4_io_probe_b.tmp"
local function show(...) out(...) end
local function rd(p) local f = io.open(p, "rb"); if not f then return nil end local t = f:read("*a"); f:close(); return t end
local function wr(p, t)
    local f, e = io.open(p, "wb")
    if not f then return false, e end
    local w, we = f:write(t)
    local fl, fe = f:flush()
    local c, ce = f:close()
    return w ~= nil, tostring(we) .. "|" .. tostring(fl) .. "|" .. tostring(fe) .. "|close=" .. tostring(c) .. "|" .. tostring(ce)
end
local function step(name, fn)
    local ok, a, b, c = pcall(fn)
    show(ok and "OK" or "ERRO", name, tostring(a), tostring(b), tostring(c))
end

show("DIR", dir)
os.remove(A); os.remove(B)
step("escrever A", function() return wr(A, "AAAA") end)
step("escrever B", function() return wr(B, "BBBBBB") end)
step("ler A/B", function() return rd(A), rd(B) end)
step("seek end (tamanho de B, esperado 6)", function()
    local f = io.open(B, "rb"); local size = f:seek("end"); f:seek("set"); local t = f:read("*a"); f:close(); return size, t
end)
step("rename A -> B com B existente (DESTINO EXISTE)", function()
    local ok, err = os.rename(A, B)
    return ok, err, "B agora=" .. tostring(rd(B)) .. " A existe=" .. tostring(rd(A) ~= nil)
end)
step("remove B, rename A -> B (sem destino)", function()
    if rd(A) == nil then wr(A, "AAAA") end
    local r1 = os.remove(B)
    local ok, err = os.rename(A, B)
    return r1, ok, err
end)
step("conteudo final de B (esperado AAAA)", function() return rd(B) end)
step("remove inexistente", function() return os.remove(dir .. "/pv4_io_nao_existe.tmp") end)
step("remove B e A", function() return os.remove(B), os.remove(A) end)
step("os.clock", function() return os.clock(), os.time() end)
step("limpeza conferida (A,B inexistentes)", function() return rd(A) == nil and rd(B) == nil end)
show("FIM: registre cada linha; a resposta de 'rename ... DESTINO EXISTE' decide se o remove previo do sv.writeAtomic e necessario")
