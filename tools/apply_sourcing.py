"""Patch frozen sourcing footprints with native S-expressions, then run KiCad.
Run in base conda. Avoids the KiCad 10 macOS SWIG iterator defect.
"""
from pathlib import Path
import json, copy, uuid, subprocess, math
import sexpdata as sx
ROOT=Path(__file__).resolve().parents[1];S=sx.Symbol
def nodes(n,key):return [v for v in n if isinstance(v,list) and v and v[0]==S(key)]
def one(n,key):return nodes(n,key)[0]
def uid():return [S('uuid'),str(uuid.uuid4())]
def main():
 path=ROOT/'cad/calinject.kicad_pcb';b=sx.loads(path.read_text())
 parts={p['ref']:p for p in json.loads((ROOT/'cad/design.json').read_text())['parts']};moved=[]
 for f in nodes(b,'footprint'):
  ref=next(q[2] for q in nodes(f,'property') if q[1]=='Reference');p=parts[ref]
  next(q for q in nodes(f,'property') if q[1]=='Value')[2]=p['value'];f[1]='Calinject:'+p['fp']
  if ref not in ['Y1','U10','U11']:continue
  assert not p['rot']
  for a in nodes(f,'pad'):
   q=next(q for q in p['pads'] if q['n']==a[1]);at=one(a,'at');old=(p['x']+at[1],p['y']+at[2]);new=(p['x']+q['x'],p['y']+q['y'])
   if old!=new:moved.append((one(a,'net')[1],old,new))
   at[1:3]=[q['x'],q['y']];one(a,'size')[1:3]=[q['w'],q['h']]
  f[:]=[n for n in f if not (isinstance(n,list) and n and n[0]==S('fp_line') and one(n,'layer')[1] in ['F.Fab','F.CrtYd'])]
  for layer in ['F.Fab','F.CrtYd']:
   x=p['body'][0]/2;y=p['body'][1]/2
   if layer=='F.CrtYd':x=max(x,max(abs(q['x'])+q['w']/2 for q in p['pads']))+.25;y=max(y,max(abs(q['y'])+q['h']/2 for q in p['pads']))+.25
   pts=[(-x,-y),(x,-y),(x,y),(-x,y)]
   for a,c in zip(pts,pts[1:]+pts[:1]):f.append([S('fp_line'),[S('start'),*a],[S('end'),*c],[S('stroke'),[S('width'),.1 if layer=='F.Fab' else .05],[S('type'),S('default')]],[S('layer'),layer],uid()])
  lib=copy.deepcopy(f);lib[1]=p['fp'];lib[:]=[n for n in lib if not(isinstance(n,list) and n and n[0] in [S('at'),S('path'),S('uuid')])];lib[2:2]=[[S('version'),20260206],[S('generator'),S('pcbnew')]]
  for pad in nodes(lib,'pad'):pad[:]=[n for n in pad if not(isinstance(n,list) and n and n[0]==S('net'))]
  (ROOT/'cad/Calinject.pretty'/f"{p['fp']}.kicad_mod").write_text(sx.dumps(lib)+'\n')
 for t in nodes(b,'segment'):
  for key in ['start','end']:
   pt=one(t,key)
   for net,a,c in moved:
    if one(t,'net')[1]==net and abs(pt[1]-a[0])<1e-5 and abs(pt[2]-a[1])<1e-5:pt[1:3]=list(c);break
 b[:]=[n for n in b if not (isinstance(n,list) and n and n[0]==S('zone') and nodes(n,'name') and one(n,'name')[1]=='KDS bottom copper clearance')]
 # KDS page6: no tracks/pours/vias in the central2x2.5mm bottom area.
 # In1 is only0.2mm below top; In2/B.Cu are more than0.5mm below the device.
 for layer in ['F.Cu','In1.Cu']:
  b.append([S('zone'),[S('net'),0],[S('net_name'),''],[S('layer'),layer],uid(),[S('name'),'KDS bottom copper clearance'],[S('hatch'),S('edge'),.5],[S('keepout'),[S('tracks'),S('not_allowed')],[S('vias'),S('not_allowed')],[S('pads'),S('allowed')],[S('copperpour'),S('not_allowed')],[S('footprints'),S('allowed')]],[S('polygon'),[S('pts'),*[[S('xy'),x,y] for x,y in [(63,32.75),(65,32.75),(65,35.25),(63,35.25)]]]]])
 # Short bleeder branch joins the 50ohm main line without crossing SMA legs.
 a=(17.2,57.5);c=(17.2,56.)
 if not any(tuple(one(t,'start')[1:3])==a and tuple(one(t,'end')[1:3])==c for t in nodes(b,'segment')):
  b.append([S('segment'),[S('start'),*a],[S('end'),*c],[S('width'),.2],[S('layer'),'F.Cu'],[S('net'),'RF_IN'],uid()])
 path.write_text(sx.dumps(b)+'\n')
 cli=next(p for p in [Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'),Path('/Volumes/KiCad/KiCad/KiCad.app/Contents/MacOS/kicad-cli')] if p.exists())
 subprocess.run([str(cli),'pcb','drc','--refill-zones','--save-board','--schematic-parity','--format','json','-o',str(ROOT/'validation/drc.json'),str(path)],cwd=ROOT,check=True)
 print('Updated sourcing footprints; inspect DRC before export')
if __name__=='__main__':main()
