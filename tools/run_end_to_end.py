"""Run the complete behavioral simulation/report chain with the active Python."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
for name in ['simulate.py','simulate_standalone.py','end_to_end.py','simulate_reference_tracking.py','simulate_broadband.py','validate_end_to_end.py','report_end_to_end.py']:
 print('Running',name,flush=True)
 subprocess.run([sys.executable,str(ROOT/'tools'/name)],cwd=ROOT,check=True)
