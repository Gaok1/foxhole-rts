import json
from pathlib import Path
from build_snapshot import parse, components
p=Path(__file__).parent
d=json.loads((p/'home-region-snapshot.json').read_text(encoding='utf-8'))
assert len(d['control_points'])==127 and len(d['segments'])==122
assert d['world'].endswith('HomeRegionW.HomeRegionW') and not d['physical_validation']
assert all(not e['validated'] for ls in d['edges'].values() for e in ls)
editor=[s for s in d['segments'].values() if any('SplineEditorMesh' in a for a in s['assets'])]
assert editor and all(not s['road_asset'] for s in editor)
assert len(components(d,True))>=len(components(d,False))
try: parse('EXPORT_WORLD\tHomeRegionW')
except ValueError: pass
else: raise AssertionError('snapshot incompleto aceito')
assert all(len(s['endpoints'])==2 for s in d['segments'].values() if not s['rejected'])
assert all(e['to'] in d['nodes'] for ls in d['edges'].values() for e in ls)
print('OK snapshot real: incidencia, curvas, editor excluido, incompleto recusado, fisica nao presumida')

hexdata=json.loads((p/'callums-cape-snapshot.json').read_text(encoding='utf-8'))
assert hexdata['world'].endswith('CallumsCapeHex.CallumsCapeHex')
assert len(hexdata['control_points'])==405 and len(hexdata['segments'])==431
assert len(hexdata['nodes'])==4013 and not hexdata['physical_validation']
assert sum(s['road_asset'] for s in hexdata['segments'].values())==391
assert all(not e['validated'] for edges in hexdata['edges'].values() for e in edges)
assert hexdata['epoch']!=d['epoch']
assert all(e['blocked'] for edges in hexdata['edges'].values() for e in edges if not e['road_asset'])
assert all(e['to'] in hexdata['nodes'] for edges in hexdata['edges'].values() for e in edges)
print('OK Callums: 405 controles, 431 segmentos, 4013 nos; epoch proprio e zero autorizacao fisica')
