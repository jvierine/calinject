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
OUT=ROOT/'mechanical';W=104;D=79;H=20;wall=2.4;floor=2.4
OX=7;OY=7;pcb_top=7.;lid_bottom=17.6

def box(x,y,z,dx,dy,dz):return m.Manifold.cube((dx,dy,dz)).translate((x,y,z))
def cyl(x,y,z,r,h):return m.Manifold.cylinder(h,r,r,48).translate((x,y,z))
# Open tray, four separate lid screw towers outside the PCB footprint.
base=box(0,0,0,W,D,lid_bottom)-box(wall,wall,floor,W-2*wall,D-2*wall,H)
for x,y in [(4.3,4.3),(W-4.3,4.3),(4.3,D-4.3),(W-4.3,D-4.3)]:
 base+=cyl(x,y,floor,3.1,lid_bottom-floor)
 # 2.5-mm pilot for M3 plastic-thread or tapped machine screw; no heat insert required.
 base-=cyl(x,y,5,1.25,H)
for x,y in [(4,4),(86,4),(4,61),(86,61)]:
 base+=cyl(OX+x,OY+y,floor,3,3.)
 base-=cyl(OX+x,OY+y,.8,1.25,6.)
# USB-C opening is generous enough for the genuine RP2040-Zero on 2.54mm headers.
# PCB module USB points north. Connector face near boardy=0.25; cable plug can enter cavity.
base-=box(OX+17-6,-1,10.0,12,OY+2,6.5)
# Tongue locates the lid; outer lip fits inside walls with0.3mm radial clearance.
lid=box(0,0,lid_bottom,W,D,H-lid_bottom)
lip=box(wall+.3,wall+.3,lid_bottom-1.4,W-2*(wall+.3),D-2*(wall+.3),1.4)
lip-=box(wall+1.6,wall+1.6,lid_bottom-1.5,W-2*(wall+1.6),D-2*(wall+1.6),2)
# Clear the base screw towers from the locating tongue.
for x,y in [(4.3,4.3),(W-4.3,4.3),(4.3,D-4.3),(W-4.3,D-4.3)]:lip-=cyl(x,y,15,3.4,5)
lid+=lip
for x,y in [(4.3,4.3),(W-4.3,4.3),(4.3,D-4.3),(W-4.3,D-4.3)]:
 lid-=cyl(x,y,15,1.7,7)
 lid-=cyl(x,y,H-1.3,3.,2.)
# Recessed SMA ports: 12-mm access holes allow the mating nut to reach the PCB jack.
for x,y in [(82,15),(12,56),(78,56),(84,43),(7,44)]:lid-=cyl(OX+x,OY+y,15,6,8)
# Trimmer and controller BOOT/RESET access. These are tool holes, not decorative vents.
lid-=cyl(OX+12,OY+34,15,2.4,8)
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
res=[export(base,'base'),export(lid_print,'lid')]
res.append(dict(assembled_intersection_mm3=(base ^ lid).volume()))
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
