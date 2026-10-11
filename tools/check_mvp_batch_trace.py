"""Gate de cadeia fresca; nao depende de perder/ganhar para aprovar logistica."""
from pathlib import Path
import sys
import math

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'data/trace_batch_mvp_integrated.txt'
lines = [line.split('\t') for line in path.read_text(encoding='utf-8-sig').splitlines()]
rows = [dict(zip(row[2::2], row[3::2])) for row in lines if row[0] == 'MVP']
assert rows and any('CallumsCapeHex' in '\t'.join(row) for row in lines), 'sem ciclo no hex'
assert all(row['E_AUDIT'] == row['C_AUDIT'] == 'true' for row in rows), 'conservacao falhou'
assert ['SCENE_CLEANUP', 'PASS'] in lines, 'sem cleanup terminal'
assert not any(row[0] == 'ERROR' for row in lines), 'erro no ensaio'
maxval = lambda key: max(float(row[key]) for row in rows)
resource = [row for row in lines if row[:2] == ['PLAYER_TRUCK', 'res']]
resource_alive = (len(resource) == 1 and len(resource[0]) == 6
                  and resource[0][2] in {'idle', 'toField', 'loading', 'toRef'}
                  and math.isfinite(float(resource[0][3])) and float(resource[0][3]) > 0
                  and resource[0][4:] == ['PAWN', 'true'])
gates = {
    'coleta_entrega': maxval('DELIVERED') >= 120,
    'refino_producao_jogador': maxval('BMAT') > 40,
    'reconstrucao_recurso': resource_alive,
    'entrega_inimiga': maxval('E_DELIVERED') > 0,
    'consumo_inimigo': maxval('E_USED_SHIRTS') > 0,
    'reabastecimento_combate': maxval('RESUPPLIED') > 0 and maxval('KILLS') > 0,
}
for name, passed in gates.items():
    print(('PASS' if passed else 'FAIL') + ': ' + name)
print('VERIFICADO: conservacao em', len(rows), 'amostras; perda de coleta', maxval('LOST'))
print('NAO prova: estrada, vitoria, equilibrio nem causa da falha de coleta')
sys.exit(0 if all(gates.values()) else 1)
