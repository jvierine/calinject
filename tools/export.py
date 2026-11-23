"""Export frozen, reviewed PCB. Does not reroute or regenerate the design."""
from pathlib import Path
import subprocess,os,shutil,json,zipfile
ROOT=Path(os.environ.get('CALINJECT_ROOT',Path(__file__).resolve().parents[1]))
CLI=os.environ.get('KICAD_CLI') or shutil.which('kicad-cli')
if not CLI:
 for candidate in ['/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli','/Volumes/KiCad/KiCad/KiCad.app/Contents/MacOS/kicad-cli']:
  if Path(candidate).exists():CLI=candidate;break
if not CLI:raise SystemExit('Set KICAD_CLI to KiCad10 kicad-cli')
def run(*args):
 r=subprocess.run([CLI,*args],cwd=ROOT,capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stderr+r.stdout)
 print(r.stdout.strip())
board='cad/calinject.kicad_pcb';sch='cad/calinject.kicad_sch'
run('sch','erc','--format','json','--output','validation/erc.json',sch)
run('pcb','drc','--schematic-parity','--format','json','--output','validation/drc.json',board)
j=json.loads((ROOT/'validation/drc.json').read_text());assert not any(j[k] for k in ['violations','unconnected_items','schematic_parity']),j
j=json.loads((ROOT/'validation/erc.json').read_text());assert not any(s['violations'] for s in j['sheets']),j
run('sch','export','pdf','-o','docs/schematic.pdf',sch)
run('pcb','export','gerbers','-o','manufacturing/gerbers/','-l','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,Edge.Cuts','--subtract-soldermask',board)
run('pcb','export','drill','-o','manufacturing/gerbers/','--excellon-separate-th','--generate-map','--generate-report',board)
run('pcb','export','pos','-o','manufacturing/calinject-top.pos','--side','front','--format','ascii','--units','mm','--smd-only',board)
run('pcb','export','ipcd356','-o','manufacturing/calinject.d356',board)
run('pcb','export','pdf','--mode-single','--black-and-white','--scale','3','-o','docs/assembly-top.pdf','-l','F.Fab,Edge.Cuts','--sketch-pads-on-fab-layers',board)
run('pcb','export','pdf','--mode-multipage','--scale','3','-o','docs/copper-layers.pdf','-l','F.Cu,In1.Cu,In2.Cu,B.Cu','--cl','Edge.Cuts',board)
run('pcb','export','step','--board-only','--force','-o','mechanical/pcb-only.step',board)
with zipfile.ZipFile(ROOT/'manufacturing/calinject-revB-gerbers.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((ROOT/'manufacturing/gerbers').iterdir()):z.write(p,p.name)
