import sys
from pathlib import Path
sys.path.insert(0,str(Path('dados/paralel/economia').resolve()))
from build_patch import build
s=Path('tools/test_orders.py').read_text(encoding='utf-8')
s=s.replace('source = (Path(__file__).resolve().parents[1] / "mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")','source = build(Path("mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8"))')
try: exec(compile(s,'tools/test_orders.py','exec'),{'__file__':str(Path('tools/test_orders.py').resolve()),'build':build,'Path':Path})
except Exception as e: print('EXISTING SUITE CANDIDATE:',type(e).__name__,str(e));raise
