"""Add through-ground stitching to the frozen board, avoiding existing copper.
Run with KiCad Python. No signal routing or footprint placement is changed.
"""
from pathlib import Path
import math,json
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'cad/calinject.kicad_pcb'
b=k.LoadBoard(str(path));mm=k.FromMM
xy=lambda p:(k.ToMM(p.x),k.ToMM(p.y))
distance=lambda a,c:math.hypot(a[0]-c[0],a[1]-c[1])
tracks=list(b.GetTracks());pads=[p for f in b.GetFootprints() for p in f.Pads()]
vias=[v for v in tracks if isinstance(v,k.PCB_VIA)]
ground=[xy(v.GetPosition()) for v in vias if v.GetNetname()=='GND']
ground += [xy(p.GetPosition()) for p in pads if p.GetNetname()=='GND' and p.GetAttribute()==k.PAD_ATTRIB_PTH]
def segment_distance(p,a,c):
 dx,dy=c[0]-a[0],c[1]-a[1];den=dx*dx+dy*dy
 t=0 if not den else max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den))
 return distance(p,(a[0]+t*dx,a[1]+t*dy))
def clear(p):
 if not (1<p[0]<89 and 1<p[1]<64):return False
 for q in pads:
  center=xy(q.GetPosition())
  if q.GetNetname()=='GND':
   if q.GetDrillSize().x and distance(p,center)<.55+k.ToMM(q.GetDrillSize().x)/2:return False
   continue
  box=q.GetBoundingBox();lo=xy(box.GetOrigin());hi=xy(box.GetEnd())
  dx=max(lo[0]-p[0],0,p[0]-hi[0]);dy=max(lo[1]-p[1],0,p[1]-hi[1])
  if math.hypot(dx,dy)<.52:return False
 for t in tracks:
  if t.GetNetname()=='GND':continue
  if isinstance(t,k.PCB_VIA):
   if distance(p,xy(t.GetPosition()))<.52+k.ToMM(t.GetWidth(k.F_Cu))/2:return False
  elif segment_distance(p,xy(t.GetStart()),xy(t.GetEnd()))<.52+k.ToMM(t.GetWidth())/2:return False
 return all(distance(p,g)>.65 for g in ground)
added=[]
def add(p,reason):
 v=k.PCB_VIA(b);v.SetPosition(k.VECTOR2I(mm(p[0]),mm(p[1])));v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet('GND'));b.Add(v);ground.append(p);added.append(dict(position_mm=p,reason=reason))
missing=[]
for v in vias:
 if v.GetNetname()=='GND':continue
 p=xy(v.GetPosition())
 if min(distance(p,g) for g in ground)<=1.5:continue
 found=False
 for radius in [.85,1.,1.2,1.4,1.5]:
  for deg in range(0,360,10):
   angle=math.radians(deg);candidate=(round(p[0]+radius*math.cos(angle),4),round(p[1]+radius*math.sin(angle),4))
   if clear(candidate):add(candidate,'return for '+v.GetNetname());found=True;break
  if found:break
 if not found:missing.append(dict(net=v.GetNetname(),position_mm=p))
# Dense perimeter stitching ties the two reference planes together. These vias
# are not a metal enclosure and do not prove radiated-emissions shielding.
for x in range(2,89,2):
 for y in [1.5,63.5]:
  p=(x,y)
  if clear(p):add(p,'perimeter stitch')
for y in range(3,64,2):
 for x in [1.5,88.5]:
  p=(x,y)
  if clear(p):add(p,'perimeter stitch')
# Stitch around the GNSS region where clear; do not move the RF geometry.
for x in range(58,89,2):
 for y in [5.,23.]:
  p=(x,y)
  if clear(p):add(p,'GNSS boundary stitch')
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(path),b)
(ROOT/'validation/return-improvements.json').write_text(json.dumps(dict(added=added,unresolved=missing),indent=2)+'\n')
print('Added',len(added),'ground vias; unresolved',missing)
