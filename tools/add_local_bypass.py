"""Find clear local 100nF bypass placements without rerouting existing signals.
Development edit: updates native board, manifest and design source together.
Run once with KiCad Python; existing C29..C34 prevent duplicate application.
"""
from pathlib import Path
import math,json
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'cad/calinject.kicad_pcb';b=k.LoadBoard(str(path));mm=k.FromMM
xy=lambda p:(k.ToMM(p.x),k.ToMM(p.y))
dist=lambda a,c:math.hypot(a[0]-c[0],a[1]-c[1])
def segdist(p,a,c):
 dx,dy=c[0]-a[0],c[1]-a[1];den=dx*dx+dy*dy;t=0 if not den else max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den))
 return dist(p,(a[0]+t*dx,a[1]+t*dy))
def pointclear(p,r,net,all_layers=False):
 for f in b.GetFootprints():
  for q in f.Pads():
   if q.GetNetname()==net:continue
   box=q.GetBoundingBox();lo=xy(box.GetOrigin());hi=xy(box.GetEnd());dx=max(lo[0]-p[0],0,p[0]-hi[0]);dy=max(lo[1]-p[1],0,p[1]-hi[1])
   if math.hypot(dx,dy)<r+.22:return False
 for t in b.GetTracks():
  if t.GetNetname()==net:continue
  if isinstance(t,k.PCB_VIA):
   if dist(p,xy(t.GetPosition()))<r+.22+k.ToMM(t.GetWidth(k.F_Cu))/2:return False
  elif (all_layers or t.GetLayer()==k.F_Cu) and segdist(p,xy(t.GetStart()),xy(t.GetEnd()))<r+.22+k.ToMM(t.GetWidth())/2:return False
 return True
def lineclear(a,c,net):
 n=max(1,int(dist(a,c)/.08))
 return all(pointclear((a[0]+(c[0]-a[0])*i/n,a[1]+(c[1]-a[1])*i/n),.125,net) for i in range(n+1))
def track(a,c,net):
 t=k.PCB_TRACK(b);t.SetStart(k.VECTOR2I(mm(a[0]),mm(a[1])));t.SetEnd(k.VECTOR2I(mm(c[0]),mm(c[1])));t.SetWidth(mm(.25));t.SetLayer(k.F_Cu);t.SetNet(b.FindNet(net));b.Add(t)
manifest=json.loads((ROOT/'cad/design.json').read_text());template=next(p for p in manifest['parts'] if p['ref']=='C13');lines=[];added=[]
for num,ic in enumerate(['U2','U3','U4','U5','U11','U10'],29):
 ref='C'+str(num);fs={f.GetReference():f for f in b.GetFootprints()}
 if ref in fs:raise RuntimeError('Already applied: '+ref)
 powers=[p for p in fs[ic].Pads() if p.GetNetname() in ['3V3A','3V3G']];found=None
 for radius in [1.2,1.5,1.8,2.1,2.4,2.7,3.,3.3,3.6,4.]:
  for pin in powers:
   origin=xy(pin.GetPosition());net=pin.GetNetname()
   for deg in range(0,360,15):
    ang=math.radians(deg);power=(round(origin[0]+radius*math.cos(ang),4),round(origin[1]+radius*math.sin(ang),4))
    if not pointclear(power,.66,net) or not lineclear(origin,power,net):continue
    for rot in [0,90,180,270]:
     ang=math.radians(rot);ground=(power[0]+1.6*math.cos(ang),power[1]-1.6*math.sin(ang));center=((power[0]+ground[0])/2,(power[1]+ground[1])/2)
     # Match actual library courtyard geometry, including pads outside bodies.
     hx,hy=(1.53,.76) if rot in [0,180] else (.76,1.53)
     overlap=False
     for existing in b.GetFootprints():
      vertices=[xy(v) for item in existing.GraphicalItems() if item.GetLayer()==k.F_CrtYd for v in [item.GetStart(),item.GetEnd()]]
      if not vertices:continue
      xs,ys=zip(*vertices)
      if center[0]+hx>min(xs) and center[0]-hx<max(xs) and center[1]+hy>min(ys) and center[1]-hy<max(ys):overlap=True;break
     if overlap:continue
     if not pointclear(ground,.66,'GND'):continue
     for va in range(0,360,30):
      aa=math.radians(va);via=(ground[0]+.8*math.cos(aa),ground[1]+.8*math.sin(aa))
      if (via[0]-ground[0])*(ground[0]-power[0])+(via[1]-ground[1])*(ground[1]-power[1])<0:continue
      if pointclear(via,.3,'GND',True) and lineclear(ground,via,'GND'):
       # Existing drills must stay clear even on the same net.
       if any(dist(via,xy(v.GetPosition()))<.7 for v in b.GetTracks() if isinstance(v,k.PCB_VIA)):continue
       found=(origin,power,ground,center,rot,via,net);break
     if found:break
    if found:break
   if found:break
  if found:break
 if not found:print("No direct-route placement for",ic);continue
 origin,power,ground,center,rot,via,net=found
 f=k.FootprintLoad(str(ROOT/'cad/Calinject.pretty'),template['fp']);f.SetReference(ref);f.SetValue('100n');f.SetPosition(k.VECTOR2I(mm(center[0]),mm(center[1])));f.SetOrientationDegrees(rot);f.SetFPID(k.LIB_ID('Calinject','C_0603_'+ref));f.SetUuid(k.KIID())
 for q in f.Pads():q.SetNet(b.FindNet(net if q.GetNumber()=='1' else 'GND'));q.SetUuid(k.KIID())
 f.Reference().SetPosition(k.VECTOR2I(mm(center[0]),mm(center[1]-1.3)));b.Add(f)
 track(origin,power,net);track(ground,via,'GND')
 v=k.PCB_VIA(b);v.SetPosition(k.VECTOR2I(mm(via[0]),mm(via[1])));v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet('GND'));b.Add(v)
 p=json.loads(json.dumps(template));p.update(ref=ref,fp='C_0603_'+ref,x=center[0],y=center[1],rot=rot);p['pads'][0]['net']=net;p['section']='Power';manifest['parts'].append(p)
 lines.append("cap('%s','%s',%.6f,%.6f,'Power',rot=%d)"%(ref,net,*center,rot));added.append(dict(ic=ic,cap=ref,distance_mm=dist(origin,power)))
 plugin=k.PCB_IO_MGR.FindPlugin(k.PCB_IO_MGR.KICAD_SEXP);copy=k.Cast_to_FOOTPRINT(f.Duplicate(False));copy.SetOrientationDegrees(0);copy.SetPosition(k.VECTOR2I(0,0));plugin.FootprintSave(str(ROOT/'cad/Calinject.pretty'),copy)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(path),b)
(ROOT/'cad/design.json').write_text(json.dumps(manifest,indent=2)+'\n')
source=ROOT/'tools/design.py';s=source.read_text();marker='# Pin labels are explicit';s=s.replace(marker,'# Additional local IC bypassing after layout audit.\n'+'\n'.join(lines)+'\n'+marker);source.write_text(s)
(ROOT/'validation/bypass-improvements.json').write_text(json.dumps(added,indent=2)+'\n');print(added)
