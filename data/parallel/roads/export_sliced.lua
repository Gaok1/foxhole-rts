-- Exportador pronto para canal: arquivo retorna modulo; start(baseIndex) apos oracle v6.
-- baseIndex deve ser o indice confirmado ARRAY_INDEX_CHECK; nao inferir base0/1.
local exporter={}
function exporter.start(baseIndex)
 assert(type(baseIndex)=='number','indice inicial precisa ser confirmado pelo oracle')
 local name=world():GetFullName()
 local components=FindAllOf('LandscapeSplinesComponent') or {}
 if #components~=1 or not valid(components[1]) then out('GATE','exige um spline component confirmado'); return end
 local component=components[1]
 local lib=StaticFindObject('/Script/Engine.Default__KismetMathLibrary')
 if not valid(lib) then out('GATE','math library ausente'); return end
 local cps,segs=FindAllOf('LandscapeSplineControlPoint') or {},FindAllOf('LandscapeSplineSegment') or {}
 local phase,index,sub='cp',1,baseIndex
 local current,id,array,kind
 local function convert(p)
  return lib:TransformLocation(component:K2_GetComponentToWorld(),{X=p.X,Y=p.Y,Z=p.Z})
 end
 out('EXPORT_WORLD',name)
 LoopInGameThreadWithDelay(16,function()
  if world():GetFullName()~=name or not valid(component) then out('EXPORT_CANCEL','mundo/componente invalido'); return true end
  if not current then
   current=(phase=='cp' and cps or segs)[index]; index=index+1
   if not current then
    if phase=='cp' then phase,index='segment',1; return false end
    out('EXPORT_DONE',name); return true
   end
   if not valid(current) then out('EXPORT_INVALID',phase,index-1); current=nil; return false end
   id=current:GetFullName(); sub=baseIndex
   if phase=='cp' then
    local p=convert(current.Location); out('NODE_WORLD',id,p.X,p.Y,p.Z,current.Width)
    array,kind=current.ConnectedSegments,'link'
   else array,kind=current.Points,'point'; out('SEGMENT',id) end
   return false
  end
  if not valid(current) then out('EXPORT_CANCEL','objeto invalidado'); return true end
  if sub>=baseIndex+array:GetArrayNum() then
   if phase=='segment' and kind=='point' then array,kind,sub=current.LocalMeshComponents,'mesh',baseIndex; return false end
   current=nil; return false
  end
  local value=array[sub]; local at=sub; sub=sub+1
  if kind=='link' then out('LINK',id,valid(value.Segment) and value.Segment:GetFullName() or 'invalido',value.End)
  elseif kind=='point' then local p=convert(value.Center); out('CURVE_WORLD',id,at,p.X,p.Y,p.Z)
  else
   if valid(value) then
    local asset=value.StaticMesh; local assetName=valid(asset) and asset:GetFullName() or 'ausente'
    local road=assetName:find('/Environment/Roads/',1,true)~=nil
    out('MESH_ASSET',id,assetName,road and 'asset_estrada' or 'desconhecido','fisica_nao_validada')
   else out('MESH_INVALID',id) end
  end
  return false
 end)
end
return exporter