"""Verifica rastro integrado sem converter observacoes/falhas em aprovacao."""
from pathlib import Path
import sys

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'dados/rastro_batch_nativo_integrado.txt'
lines = [line.split('\t') for line in path.read_text(encoding='utf-8-sig').splitlines()]
results = {row[1]: dict(zip(row[2::2], row[3::2])) for row in lines if row[0] == 'RESULT'}
expected = {'native_refusals', 'W_collision_on', 'W_collision_off', 'C_collision_on',
            'reset_flight', 'infantry_hostile', 'infantry_friendly', 'launcher_removed',
            'mixed_classes', 'borrowed_context', 'external_swap', 'truck_loss', 'gc_in_flight'}
assert set(results) == expected, 'batch incompleto ou casos duplicados/inesperados'
assert sum(row[0] == 'RESULT' for row in lines) == len(expected), 'resultado duplicado'
assert all(r['LEASE'] == 'false' for r in results.values()), 'lease vazando'
assert ['REPORT_CLEANUP', 'PASS'] in lines and not any(row[0] == 'ERROR' for row in lines), 'erro/cleanup ausente'
for name in ('W_collision_on', 'C_collision_on', 'gc_in_flight'):
    assert 0 <= float(results[name]['HP']) < 900, f'sem dano nativo: {name}'
assert float(results['W_collision_off']['HP']) == 900, 'comparacao de colisao mudou'
assert float(results['reset_flight']['HP']) == 900, 'reset nao cancelou dano'
assert float(results['infantry_hostile']['HP']) < 100, 'sem dano em soldado'
assert ['GC_IN_FLIGHT', 'PASS'] in lines, 'sem GC integrado'
assert sum(row[:2] == ['CONTEXT_IDENTITY', 'PASS'] for row in lines) == 2, 'identidades nao preservadas'
for tag in ('REFUSALS', 'COOLDOWN', 'RESET', 'LAUNCHER_REMOVED'):
    assert [tag, 'PASS'] in lines, f'gate ausente: {tag}'
print('VERIFICADO: arremesso/dano por faccao, recusas, colisao A/B, reset, remocao, contexto e GC')
print('FRIENDLYFIRE observado: HP', results['infantry_friendly']['HP'])
failed = [name for name, result in results.items() if result['GATE'] == 'FAIL']
logi_gate = [row for row in lines if row[0] == 'LOGI_GATE']
assert len(logi_gate) == 1, 'gate logistico ausente'
if logi_gate[0][1] != 'PASS' and 'truck_loss' not in failed:
    failed.append('truck_loss')
print('GATES NAO APROVADOS:', ', '.join(failed) or 'nenhum declarado no rastro')
print('NAO prova: morte por combate do lancador/soldado, equilibrio, rifle ou estrada')
sys.exit(1 if failed else 0)
