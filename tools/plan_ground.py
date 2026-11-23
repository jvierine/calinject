from design import ROOT,parts,world
import json,math
from shapely.geometry import box,Point,LineString
from shapely.affinity import rotate
j=json.loads((ROOT/'cad/design.json').read_text());pads=[];holes=[];vias=[]
for p in parts:
 for q in p['pads']:
  x,y=world(p,q);shape=rotate(box(x-q['w']/2,y-q['h']/2,x+q['w']/2,y+q['h']/2),-p['rot'],origin=(x,y))
  pads.append((p,q,x,y,shape))
  if q['drill']:holes.append((x,y,q['drill']))
for p,q,x,y,shape in pads:
 if q['net']!='GND' or q['kind']!='smd':continue
 found=False
 for r in [.75,1.,1.25,1.5,2.]:
  for ang in range(0,360,30):
   a=math.radians(ang);vx=round(x+r*math.cos(a),4);vy=round(y+r*math.sin(a),4)
   copper=Point(vx,vy).buffer(.3).union(LineString([(x,y),(vx,vy)]).buffer(.075 if p['ref']=='Y1' else .125))
   if copper.intersects(box(63,32.75,65,35.25)):continue
   if not box(.5,.5,89.5,64.5).contains(copper):continue
   if any(copper.distance(other)<.2 for op,oq,ox,oy,other in pads if oq['net']!='GND'):continue
   if any(math.hypot(vx-hx,vy-hy)<.15+hd/2+.26 for hx,hy,hd in holes):continue
   if any(math.hypot(vx-v['x'],vy-v['y'])<.56 for v in vias):continue
   vias.append(dict(ref=p['ref'],pin=q['n'],x=vx,y=vy));found=True;break
  if found:break
 if not found:print('No ground via escape:',p['ref'],q['n'])
# Ground stitching between the clock/pulse area and the receiver signal path.
for vx in range(28,75,3):
 vy=51.;copper=Point(vx,vy).buffer(.3)
 if any(copper.distance(shape)<.2 for p,q,x,y,shape in pads if q['net']!='GND'):continue
 if any(math.hypot(vx-hx,vy-hy)<.15+hd/2+.26 for hx,hy,hd in holes):continue
 if any(math.hypot(vx-v['x'],vy-v['y'])<.65 for v in vias):continue
 vias.append(dict(x=vx,y=vy))
j['ground_vias']=vias;(ROOT/'cad/design.json').write_text(json.dumps(j,indent=2)+'\n');print('Ground vias',len(vias))
