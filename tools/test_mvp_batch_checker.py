"""Rastros sinteticos testam o gate; nao sao novas partidas nem prova de MVP."""
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
baseline = (root / 'dados/rastro_batch_mvp_integrado.txt').read_text(encoding='utf-8')
synthetic = baseline.replace('DELIVERED\t0\t', 'DELIVERED\t120\t').replace('BMAT\t40.0\t', 'BMAT\t100.0\t')
dead = 'PLAYER_TRUCK\tres\tdead\t0\tPAWN\tfalse'
live = 'PLAYER_TRUCK\tres\ttoField\t900\tPAWN\ttrue'

with tempfile.TemporaryDirectory(prefix='foxhole-mvp-check-') as directory:
    path = Path(directory) / 'synthetic.txt'
    for name, trace, passed in [
        ('real_negativo', baseline, False),
        ('sintetico_completo', synthetic.replace(dead, live), True),
        ('sem_registro', synthetic.replace(dead + '\n', ''), False),
        ('morto', synthetic, False),
        ('sem_ator', synthetic.replace(dead, live.replace('true', 'false')), False),
        ('HP_zero', synthetic.replace(dead, live.replace('900', '0')), False),
        ('HP_infinito', synthetic.replace(dead, live.replace('900', 'inf')), False),
        ('estado_desconhecido', synthetic.replace(dead, live.replace('toField', 'fantasma')), False),
        ('duplicado', synthetic.replace(dead, live + '\n' + live), False),
        ('sem_cleanup', synthetic.replace(dead, live).replace('SCENE_CLEANUP\tPASS', ''), False),
    ]:
        path.write_text(trace, encoding='utf-8')
        result = subprocess.run([sys.executable, str(root / 'tools/check_mvp_batch_trace.py'), str(path)], capture_output=True, text=True)
        assert (result.returncode == 0) == passed, (name, result.stdout, result.stderr)
        if name not in {'sintetico_completo', 'sem_cleanup'}:
            assert 'FAIL: reconstrucao_recurso' in result.stdout, name
print('PASS: gate exige registro unico de recurso vivo; ausencia/HP0/estado/ator/duplicacao/cleanup recusados')
