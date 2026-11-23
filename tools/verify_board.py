"""Manufacturing consistency audit; run with KiCad bundled Python after exports."""
from pathlib import Path
import json,math,hashlib
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1];board=ROOT/'cad/calinject.kicad_pcb';b=k.LoadBoard(str(board))
d=json.loads((ROOT/'cad/design.json').read_text());expected={p['ref']:p for p in d['parts']};actual={f.GetReference():f for f in b.GetFootprints()}
errors=[]
if set(expected)!=set(actual):errors.append('Footprint references differ from manifest')
for ref,p in expected.items():
 f=actual[ref]
 if abs(k.ToMM(f.GetPosition().x)-p['x'])>1e-5 or abs(k.ToMM(f.GetPosition().y)-p['y'])>1e-5:errors.append(ref+' placement')
 if (f.GetOrientationDegrees()-p['rot'])%360>1e-5:errors.append(ref+' rotation')
 if f.GetValue()!=p['value']:errors.append(ref+' value')
 expected_pads=[]
 for q in p['pads']:
  angle=math.radians(p['rot']);x=p['x']+q['x']*math.cos(angle)+q['y']*math.sin(angle);y=p['y']-q['x']*math.sin(angle)+q['y']*math.cos(angle)
  expected_pads.append((q['n'],round(x,4),round(y,4),round(q['w'],4),round(q['h'],4),round(q['drill'] or 0,4)))
 actual_pads=[(a.GetNumber(),round(k.ToMM(a.GetPosition().x),4),round(k.ToMM(a.GetPosition().y),4),round(k.ToMM(a.GetSize().x),4),round(k.ToMM(a.GetSize().y),4),round(k.ToMM(a.GetDrillSize().x),4)) for a in f.Pads()]
 if sorted(expected_pads)!=sorted(actual_pads):errors.append(ref+' pad geometry')
 for pad in f.Pads():
  q=next(q for q in p['pads'] if q['n']==pad.GetNumber())
  if q['kind']=='smd':
   layers={layer for layer in range(k.PCB_LAYER_ID_COUNT) if pad.IsOnLayer(layer)}
   allowed={k.F_Cu,k.F_Mask} if p['assembly']=='PCB' else {k.F_Cu,k.F_Mask,k.F_Paste}
   if layers!=allowed:errors.append(ref+'/'+q['n']+' layers')
  if q['net'] and pad.GetNetname()!=q['net']:errors.append(ref+'/'+q['n']+' net')
t1={p.GetNumber():p.GetNetname() for p in actual['T1'].Pads()}
if t1!={'1':'RF_TO_SDR','2':'T1_LINK','3':'RF_FROM_ANT','4':'COUPLED','5':'T1_LINK','6':'GND'}:errors.append('Combiner pin map')
tracks=list(b.GetTracks());vias=[v for v in tracks if isinstance(v,k.PCB_VIA)]
if any(v.GetViaType()!=k.VIATYPE_THROUGH for v in vias):errors.append('Non-through via')
if b.GetCopperLayerCount()!=4:errors.append('Copper layer count')
if min(k.ToMM(t.GetWidth()) for t in tracks if not isinstance(t,k.PCB_VIA))<.14999:errors.append('Track narrower than0.15mm')
cpl=json.loads((ROOT/'manufacturing/CPL.json').read_text());placed={row[0]:row for row in cpl[1:]};smd={p['ref']:p for p in d['parts'] if p['assembly']=='SMT'}
if set(placed)!=set(smd):errors.append('CPL component set')
for ref,p in smd.items():
 row=placed[ref]
 if abs(row[1]-p['x'])>1e-5 or abs(row[2]+p['y'])>1e-5 or row[4]!=p['rot']:errors.append(ref+' CPL placement')
for name in ['drc','erc']:
 report=json.loads((ROOT/('validation/'+name+'.json')).read_text())
 findings=sum(len(s['violations']) for s in report['sheets']) if name=='erc' else sum(len(report[x]) for x in ['violations','unconnected_items','schematic_parity'])
 if findings:errors.append(name+' findings')
result=dict(revision='C',board_sha256=hashlib.sha256(board.read_bytes()).hexdigest(),components=len(actual),smt_placements=len(placed),through_vias=len(vias),
 checks=['manifest placement/value/net consistency','SMT pad copper/mask/paste layers','testpoint no-paste layers','ADP-2-1+ pin map','four-layer/all-through-via rules','minimum track width','CPL consistency','zero ERC/DRC/connectivity/parity findings'],errors=errors)
(ROOT/'validation/manufacturing-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));assert not errors,errors
