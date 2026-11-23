"""Parametric, watertight Calinject enclosure using Manifold solid booleans.
Provenance remains here; exported parts contain only functional markings.
All geometry is mm. Board coordinates are the same top view as cad/design.json.
"""
from pathlib import Path
import json,math
import numpy as np
import manifold3d as m
import trimesh
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical';W=98;D=73;H=20;wall=2.4;floor=2.4
OX=4;OY=4;pcb_top=7.;lid_bottom=13.

def box(x,y,z,dx,dy,dz):return m.Manifold.cube((dx,dy,dz)).translate((x,y,z))
def cyl(x,y,z,r,h):return m.Manifold.cylinder(h,r,r,48).translate((x,y,z))
# Open tray, four separate lid screw towers outside the PCB footprint.
base=box(0,0,0,W,D,lid_bottom)-box(wall,wall,floor,W-2*wall,D-2*wall,H)
corners=[(2.5,2.5),(W-2.5,2.5),(2.5,D-2.5),(W-2.5,D-2.5)]
for x,y in corners:
 base+=cyl(x,y,floor,1.8,lid_bottom-floor)
 # M2 lid screws; towers sit beyond the square PCB corners.
 base-=cyl(x,y,3,.8,H)
for x,y in [(4,4),(86,4),(4,61),(86,61)]:
 base+=cyl(OX+x,OY+y,floor,3,3.)
 base-=cyl(OX+x,OY+y,.8,1.25,6.)
# USB-C opening is generous enough for the genuine RP2040-Zero on 2.54mm headers.
# PCB module USB points north. Connector face near boardy=0.25; cable plug can enter cavity.
base-=box(OX+17-7,-1,8.0,14,OY+2,8.5)
# Tongue locates the lid; outer lip fits inside walls with0.3mm radial clearance.
lid=box(0,0,lid_bottom,W,D,H-lid_bottom)-box(wall,wall,lid_bottom-.1,W-2*wall,D-2*wall,H-wall-lid_bottom+.1)
lip=box(wall+.3,wall+.3,lid_bottom-1.4,W-2*(wall+.3),D-2*(wall+.3),1.4)
lip-=box(wall+1.6,wall+1.6,lid_bottom-1.5,W-2*(wall+1.6),D-2*(wall+1.6),2)
# Clear the base screw towers from the locating tongue.
for x,y in corners:lip-=cyl(x,y,lid_bottom-2,2.1,4)
lid+=lip
for x,y in corners:
 # Corner columns support the screw heads without bridging the hollow lid.
 lid+=cyl(x,y,lid_bottom,1.8,H-lid_bottom)
 lid-=cyl(x,y,lid_bottom-1,1.1,H-lid_bottom+2)
 lid-=cyl(x,y,H-1.3,1.8,2.)
# SMA-KWE axis is6mm above PCB. Split at that height: the PCB with
# soldered connectors drops into U-shaped notches, then the lid closes them.
ports=[('J1','right',15),('J4','right',43),('J5','left',44),('J2','bottom',12),('J3','bottom',78)]
for ref,side,p in ports:
 hole=m.Manifold.cylinder(wall+3,3.6,3.6,64)
 if side=='right':hole=hole.rotate((0,90,0)).translate((W-wall-2,OY+p,13))
 elif side=='left':hole=hole.rotate((0,90,0)).translate((-1,OY+p,13))
 else:hole=hole.rotate((-90,0,0)).translate((OX+p,D-wall-2,13))
 base-=hole;lid-=hole
 # Outside nut relief makes the whole4mm thread accessible despite the case
 # wall and PCB's0.5mm copper-to-edge clearance.
 relief=m.Manifold.cylinder(1.,5.5,5.5,64)
 if side=='right':relief=relief.rotate((0,90,0)).translate((W-.9,OY+p,13))
 elif side=='left':relief=relief.rotate((0,90,0)).translate((-.1,OY+p,13))
 else:relief=relief.rotate((-90,0,0)).translate((OX+p,D-.9,13))
 base-=relief;lid-=relief
lid-=box(OX+17-7,-1,8.0,14,OY+2,8.5)
# Trimmer and controller BOOT/RESET access. These are tool holes, not decorative vents.
lid-=cyl(OX+12,OY+34,lid_bottom-2,2.4,H)
# RGB LED is between BOOT and RESET on the USB-facing module surface.
# A 7.2mm viewing aperture accommodates the approximate package-center position
# from the manufacturer's front-view drawing; inspect first article alignment.
led_x=OX+17;led_y=OY+15.8
lid-=cyl(led_x,led_y,H-wall-.1,3.6,wall+.2)
lid-=cyl(led_x,led_y,H-wall-.1,4.6,.9)
# Optional translucent PETG/PLA cap, inserted from inside, retained with a tiny
# dot of adhesive at the flange. Geometry has clearance; it is not a press fit.
diffuser=cyl(led_x,led_y,H-wall+.1,4.5,.7)+cyl(led_x,led_y,H-wall+.7,3.5,1.7)
assert (lid ^ diffuser).volume()<1e-5,'Diffuser/lid collision'
diffuser_print=diffuser.translate((-led_x,-led_y,-(H-wall+.1)))
# Initial BOOT programming is done with lid removed.
# Both pieces export in print orientation: external broad face flat on the bed.
# Lid is inverted for support-free printing, with alignment lip pointing upward.
lid_print=lid.rotate((180,0,0)).translate((0,D,H))

def export(s,name):
 mesh=s.to_mesh();t=trimesh.Trimesh(vertices=mesh.vert_properties[:,:3],faces=mesh.tri_verts,process=True)
 if not t.is_watertight or t.volume<=0:raise RuntimeError('Invalid mesh '+name)
 t.export(OUT/(name+'.stl'))
 (OUT/(name+'.3mf')).write_bytes(trimesh.exchange.threemf.export_3MF(trimesh.Scene(t)))
 return dict(name=name,watertight=bool(t.is_watertight),volume_mm3=float(t.volume),bounds_mm=t.bounds.tolist(),triangles=len(t.faces))
assert (base ^ lid).volume()<1e-5, 'Case halves interfere'
res=[export(base,'base'),export(lid_print,'lid'),export(diffuser_print,'status-diffuser')]
res.append(dict(assembled_intersection_mm3=(base ^ lid).volume()))
# Conservative solid proxies check wall clearance without claiming a full
# component STEP assembly. Connector dimensions come from C7498154's drawing.
pcb=box(OX,OY,pcb_top-1.6,90,65,1.6)
for x,y in [(4,4),(86,4),(4,61),(86,61)]:pcb-=cyl(OX+x,OY+y,pcb_top-2,1.6,3)
case=base+lid;fits=[]
manifest=json.loads((ROOT/'cad/design.json').read_text())
for p in manifest['parts']:
 if p['ref'] not in ['J1','J2','J3','J4','J5']:continue
 proxy=box(-3,-3,0,6,6,9.2)
 proxy+=m.Manifold.cylinder(8.6,3.2,3.2,48).rotate((0,90,0)).translate((3,0,6))
 proxy=proxy.rotate((0,0,-p['rot'])).translate((OX+p['x'],OY+p['y'],pcb_top))
 collision=(case ^ proxy).volume()
 assert collision<.01,(p['ref'],'case collision',collision)
 fits.append(dict(connector=p['ref'],case_intersection_mm3=collision))
collision=(case ^ pcb).volume();assert collision<.01,('PCB case collision',collision)
res.append(dict(pcb_case_intersection_mm3=collision,connector_proxies=fits,scope='Nominal rigid geometry; print tolerances and actual components require first-article fit check'))
# Orthographic depth-buffer preview. Per-pixel depth avoids painter-sort artifacts
# on the large coplanar triangles surrounding the connector openings.
from PIL import Image,ImageDraw,ImageFont
from matplotlib import font_manager
ww,hh=1400,1100;rgb=np.full((hh,ww,3),250,dtype=np.uint8);depth=np.full((hh,ww),-np.inf)
view=np.array([1.,-1.,1.15]);view/=np.linalg.norm(view)
right=np.cross([0,0,1],view);right/=np.linalg.norm(right);up=np.cross(view,right)
light=np.array([-.3,-.5,1.]);light/=np.linalg.norm(light)
for s,color in [(base,[66,100,119]),(lid.translate((0,0,17)),[170,202,211])]:
 a=s.to_mesh();vertices=np.asarray(a.vert_properties[:,:3],dtype=float);faces=a.tri_verts
 rel=vertices-[W/2,D/2,20];screen=np.column_stack((ww/2+9*(rel@right),hh/2-9*(rel@up),rel@view))
 for indices in faces:
  tri=screen[indices];x0=max(0,int(np.floor(tri[:,0].min())));x1=min(ww,int(np.ceil(tri[:,0].max()))+1)
  y0=max(0,int(np.floor(tri[:,1].min())));y1=min(hh,int(np.ceil(tri[:,1].max()))+1)
  if x1<=x0 or y1<=y0:continue
  p,q,r=tri;den=(q[1]-r[1])*(p[0]-r[0])+(r[0]-q[0])*(p[1]-r[1])
  if abs(den)<1e-8:continue
  yy,xx=np.mgrid[y0:y1,x0:x1];xx=xx+.5;yy=yy+.5
  aa=((q[1]-r[1])*(xx-r[0])+(r[0]-q[0])*(yy-r[1]))/den
  bb=((r[1]-p[1])*(xx-r[0])+(p[0]-r[0])*(yy-r[1]))/den;cc=1-aa-bb
  zz=aa*p[2]+bb*q[2]+cc*r[2];patch=depth[y0:y1,x0:x1]
  mask=(aa>=-1e-6)&(bb>=-1e-6)&(cc>=-1e-6)&(zz>patch)
  normal=np.cross(vertices[indices[1]]-vertices[indices[0]],vertices[indices[2]]-vertices[indices[0]])
  length=np.linalg.norm(normal)
  if length<1e-9:continue
  shade=.55+.45*max(0,float(normal@light/length))
  patch[mask]=zz[mask];rgb[y0:y1,x0:x1][mask]=np.asarray(color)*shade
im=Image.fromarray(rgb);draw=ImageDraw.Draw(im)
font=ImageFont.truetype(font_manager.findfont('DejaVu Sans'),28)
draw.text((ww/2,35),'Calinject enclosure — exploded view',fill='#254559',font=font,anchor='mt')
im.save(ROOT/'docs/enclosure.png')
(ROOT/'validation/enclosure.json').write_text(json.dumps(res,indent=2)+'\n');print(res)
