"""Confere apenas o ciclo observado no hex; não certifica estrada, equilíbrio ou vitória."""
from pathlib import Path
import sys

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'dados/rastro_mvp_ciclo.txt'
lines = path.read_text(encoding='utf-8-sig').splitlines()
rows = []
for line in lines:
    parts = line.split('\t')
    if parts[0] == 'MVP':
        assert len(parts) % 2 == 0, 'amostra truncada'
        rows.append(dict(zip(parts[2::2], parts[3::2])))
assert rows and any('CallumsCapeHex' in s for s in lines), 'sem ciclo no hex'
assert all(r['E_AUDIT'] == r['C_AUDIT'] == 'true' for r in rows), 'conservação falhou'
assert all(float(r['LOST']) == 0 for r in rows), 'perda na coleta'
assert max(float(r['DELIVERED']) for r in rows) >= 120, 'coleta sem entrega'
assert max(float(r['E_DELIVERED']) for r in rows) > 0, 'sem entrega inimiga'
assert max(float(r['E_USED_SHIRTS']) for r in rows) > 0, 'sem consumo inimigo'
assert max(float(r['RESUPPLIED']) for r in rows) > 0, 'sem reabastecimento em combate'
assert max(float(r['WAVE']) for r in rows) >= 4, 'combate insuficiente'
assert rows[-1]['AUTO'] == rows[-1]['WON'] == 'false', 'sem derrota terminal observada'
assert float(rows[-1]['LOSSES']) > 0 and float(rows[-1]['KILLS']) > 0, 'sem combate real'
assert any(s.startswith('FACTORY\tammo\t') for s in lines), 'sem estoque da fábrica'
survivors = [s.split('\t') for s in lines if s.startswith('SURVIVOR\t')]
assert survivors and all(s[2:] == ['worker', 'true'] for s in survivors), 'derrota não isolou trabalhadores vivos'
print('PASS: coleta/refino, abastecimento, consumo inimigo, combate e derrota no hex')
print('NÃO prova: estrada/colisão, corte de comboio, vitória, equilíbrio ou ausência de crashes gerais')
