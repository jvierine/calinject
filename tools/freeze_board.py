"""Final native-board edits after SES import: reviewed clearance/labels/stack.
Run with KiCad's bundled Python, once per regenerated board. No rerouting.
"""
from pathlib import Path
import json
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'cad/calinject.kicad_pcb';b=k.LoadBoard(str(p));mm=k.FromMM
parts={v['ref']:v for v in json.loads((ROOT/'cad/design.json').read_text())['parts']}
for f in b.GetFootprints():
 if parts[f.GetReference()]['assembly']=='PCB':
  for pad in f.Pads():
   ls=pad.GetLayerSet();ls.RemoveLayer(k.F_Paste);pad.SetLayerSet(ls)
 if f.GetReference()=='R8':
  target=k.VECTOR2I(mm(parts['R8']['x']),mm(parts['R8']['y']));delta=target-f.GetPosition()
  old=[a.GetPosition() for a in f.Pads()]
  for t in b.GetTracks():
   if isinstance(t,k.PCB_VIA):continue
   if any(t.GetStart()==a for a in old):t.SetStart(t.GetStart()+delta)
   if any(t.GetEnd()==a for a in old):t.SetEnd(t.GetEnd()+delta)
  f.SetPosition(target)
# Open the small output-resistor routing corridor after normalizing neck widths.
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA) or t.GetNetname()!='REFPPS_SUM':continue
 for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
  v=getter()
  if abs(k.ToMM(v.y)-45.0252)<.001:setter(k.VECTOR2I(v.x,mm(45.15)))
# Space the VREF route from the moved R8 input pad. Known frozen-route vertices;
# the bounds no longer match after the shift, so repeating is harmless.
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA) or t.GetNetname()!='VREF_HALF':continue
 for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
  v=getter();x,y=k.ToMM(v.x),k.ToMM(v.y)
  if any(abs(x-a)<.0001 for a in [68.7517,69.0983]) and 29.9<y<31.1:
   setter(k.VECTOR2I(v.x+mm(.1),v.y))
labels={'R25':(87,36.4),'R26':(87,38.2),'R29':(20.8,47),'R18':(25.5,46),'C22':(28.5,50),
        'Y1':(61.5,34.3),'C17':(64.1,38.5),'U7':(68,43.5),'T1':(48,51.8)}
for f in b.GetFootprints():
 if f.GetReference() in labels:
  x,y=labels[f.GetReference()];f.Reference().SetPosition(k.VECTOR2I(mm(x),mm(y)))
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(p),b)
plugin=k.PCB_IO_MGR.FindPlugin(k.PCB_IO_MGR.KICAD_SEXP)
for f in b.GetFootprints():
 c=k.Cast_to_FOOTPRINT(f.Duplicate(False));c.SetOrientationDegrees(0);c.SetPosition(k.VECTOR2I(0,0));plugin.FootprintSave(str(ROOT/'cad/Calinject.pretty'),c)
s=p.read_text()
if '(stackup' not in s:
 stack='''(stackup
 (layer "F.SilkS" (type "Top Silk Screen"))
 (layer "F.Paste" (type "Top Solder Paste"))
 (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
 (layer "F.Cu" (type "copper") (thickness 0.035))
 (layer "dielectric 1" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.2) (loss_tangent 0.02))
 (layer "In1.Cu" (type "copper") (thickness 0.035))
 (layer "dielectric 2" (type "core") (thickness 1.04) (material "FR4") (epsilon_r 4.2) (loss_tangent 0.02))
 (layer "In2.Cu" (type "copper") (thickness 0.035))
 (layer "dielectric 3" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.2) (loss_tangent 0.02))
 (layer "B.Cu" (type "copper") (thickness 0.035))
 (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
 (layer "B.Paste" (type "Bottom Solder Paste"))
 (layer "B.SilkS" (type "Bottom Silk Screen"))
 (copper_finish "HASL lead free") (dielectric_constraints no))
'''
 p.write_text(s.replace('(setup\n','(setup\n'+stack,1))
 b=k.LoadBoard(str(p));k.SaveBoard(str(p),b)
