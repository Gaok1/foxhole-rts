"""Exportação observacional -> grafo conservador. Sem dependências externas."""
import argparse, hashlib, json, math
from pathlib import Path

ROOT=Path(__file__).parent
def distance(a,b):
    return math.dist(a,b)
def parse(source):
    nodes,segments={},{}
    world=None
    def segment(key):
        return segments.setdefault(key,dict(links=[],points={},assets=[]))
    for line in source.splitlines():
        p=line.split('\t')
        if p[0]=='EXPORT_WORLD': world=p[1]
        elif p[0]=='NODE_WORLD': nodes[p[1]]={'position':list(map(float,p[2:5])),'width':float(p[5])}
        elif p[0]=='LINK': segment(p[2])['links'].append({'node':p[1],'end':p[3]=='true'})
        elif p[0]=='SEGMENT': segment(p[1])
        elif p[0]=='CURVE_WORLD': segment(p[1])['points'][int(p[2])]=list(map(float,p[3:6]))
        elif p[0]=='MESH_ASSET': segment(p[1])['assets'].append(p[2])
    if not world or not any(x.startswith('EXPORT_DONE\t'+world) for x in source.splitlines()):
        raise ValueError('exportacao incompleta')
    epoch=world+':'+hashlib.sha256(source.encode()).hexdigest()[:16]
    graph_nodes={key:{'X':v['position'][0],'Y':v['position'][1],'Z':v['position'][2]} for key,v in nodes.items()}
    edges={key:[] for key in nodes}
    for key,s in segments.items():
        pts=[v for _,v in sorted(s['points'].items())]; s['points']=pts
        assets=s['assets']; s['assets']=sorted(set(assets))
        s['road_asset']=bool(assets) and all('/Environment/Roads/' in a for a in assets)
        links=s['links']; why=None
        if len(links)!=2 or len({q['node'] for q in links})!=2 or len({q['end'] for q in links})!=2:
            why='incidencia_parcial_ou_ambigua'
        elif any(q['node'] not in nodes for q in links): why='node_ausente'
        elif len(pts)<2: why='curva_ausente'
        else:
            a,b=links[0]['node'],links[1]['node']
            pa,pb=nodes[a]['position'],nodes[b]['position']
            direct=distance(pa,pts[0])+distance(pb,pts[-1])
            reverse=distance(pa,pts[-1])+distance(pb,pts[0])
            # Orienta somente uma incidencia comprovada; nunca cria ligacao por proximidade.
            if min(direct,reverse)>1: why='curva_endpoints_divergentes'
            else:
                if reverse<direct: pts=list(reversed(pts))
                s['endpoints']=[a,b]
                chain=[a]
                for i,p in enumerate(pts[1:-1],1):
                    nid=key+':curve:'+str(i); chain.append(nid)
                    graph_nodes[nid]=dict(zip(('X','Y','Z'),p)); edges[nid]=[]
                chain.append(b)
                for x,y in zip(chain,chain[1:]):
                    for u,v in ((x,y),(y,x)):
                        edges[u].append({'to':v,'segment':key,'validated':False,'blocked':not s['road_asset'],'road_asset':s['road_asset']})
        s['rejected']=why
    return dict(world=world,epoch=epoch,control_points=nodes,segments=segments,nodes=graph_nodes,edges=edges,
                physical_validation=False)

def components(data,roads_only):
    seen=set(); sizes=[]
    for start in data['nodes']:
        if start in seen: continue
        stack=[start]; seen.add(start); size=0
        while stack:
            cur=stack.pop(); size+=1
            for e in data['edges'][cur]:
                if roads_only and not e['road_asset']: continue
                if e['to'] not in seen: seen.add(e['to']); stack.append(e['to'])
        sizes.append(size)
    return sorted(sizes,reverse=True)

if __name__=='__main__':
    cli=argparse.ArgumentParser(description='Converte exportacao observacional; nao autoriza rotas fisicas.')
    cli.add_argument('--input',type=Path,default=Path('D:/tools/foxhole-lab/roads-export-live.txt'))
    cli.add_argument('--output',type=Path,default=ROOT/'home-region-snapshot.json')
    cli.add_argument('--report',type=Path,default=ROOT/'snapshot-report.json')
    args=cli.parse_args()
    source=args.input.read_text(encoding='utf-8-sig')
    data=parse(source)
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    report={'control_points':len(data['control_points']),'segments':len(data['segments']),
            'road_assets':sum(s['road_asset'] for s in data['segments'].values()),
            'rejected':{k:s['rejected'] for k,s in data['segments'].items() if s['rejected']},
            'native_components':components(data,False),'road_components':components(data,True),
            'graph_nodes':len(data['nodes']),'physical_validation':False}
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='rejected'}))
