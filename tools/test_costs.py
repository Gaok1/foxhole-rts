"""PYTHONPATH=D:/tools/pylibs python tools/test_costs.py — schemas reais, sem jogo."""
from pathlib import Path
from lupa import LuaRuntime

lua = LuaRuntime()
lua.execute('''
local function fname(s) return {ToString=function() return s end} end
local function strict(t) return setmetatable(t,{__index=function(_,k) error("campo errado: "..k) end}) end
local function arr(values)
 return {ForEach=function(_,fn) for i,v in ipairs(values) do fn(i,{get=function() return v end}) end end}
end
local function cost(s,n) return strict({CodeName=fname(s),Quantity=n}) end
local function amounts(s,n) return {Resource=cost(s,n),OtherResources=arr({cost("Wood",5)})} end
local blank={Resource=cost("None",0),OtherResources=arr({})}
local rows={
 BPItemDynamicData={"RifleW",{CostPerCrate=arr({strict({ItemCodeName=fname("Cloth"),Quantity=100})}),QuantityPerCrate=20,CrateProductionTime=70}},
 BPStructureDynamicData={"Factory",{MaxHealth=2000,ResourceAmounts=amounts("Cloth",400),AltResourceAmounts=blank,RepairCost=400,StoredItemCapacity=40}},
 BPVehicleDynamicData={"TruckW",{MaxHealth=900,ResourceAmounts=amounts("Cloth",100),FuelCapacity=100,FuelConsumptionPerSecond=0.025,ItemHolderCapacity=15,EngineForce=25500,TankArmour=0}},
 BPAmmoDynamicData={"Rifle",{Damage=45,Suppression=0.1,ExplosionRadius=0}}
}
function LoadAsset(path)
 local r=assert(rows[path:match("%.([^%.]+)$")])
 return {IsValid=function() return true end,ForEachRow=function(_,fn) fn(r[1],r[2]) end}
end
output=""
io.open=function() return {write=function(_,s) output=output..s end,flush=function() end,close=function() end} end
function out() end
''')
source = Path(__file__).with_name("export_costs.lua").read_text(encoding="utf-8")
lua.execute(source)
result = lua.globals().output
assert "RifleW | custo=Clothx100 qtd=20 tempo=70" in result
assert "Factory | vida=2000 custo=Clothx400+Woodx5 alt= reparo=400" in result
assert "TruckW | vida=900 custo=Clothx100+Woodx5" in result
print("PASS: ProductionResource e CodeNameSmallQuantity distintos; custos primario/secundario e zero real")
