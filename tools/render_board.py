"""Render the actual frozen KiCad PCB as a readable two-layer layout illustration.
Copper planes/masks/bodies are hidden for clarity; routing is not synthesized.
Run with base conda Python; extraction uses KiCad's matching bundled interpreter.
"""
from pathlib import Path
import argparse,json,subprocess,sys,os
ROOT=Path(__file__).resolve().parents[1]

def extract():
 import pcbnew as k
 b=k.LoadBoard(str(ROOT/'cad/calinject.kicad_pcb'))
 xy=lambda p:[k.ToMM(p.x),k.ToMM(p.y)]
 data=dict(tracks=[],vias=[],pads=[],labels=[])
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA):
   data['vias'].append(dict(p=xy(t.GetPosition()),diameter=k.ToMM(t.GetWidth(k.F_Cu)),drill=k.ToMM(t.GetDrillValue())))
  else:
   if t.GetLayer() not in [k.F_Cu,k.B_Cu]:continue
   if isinstance(t,k.PCB_ARC):raise RuntimeError('Arc rendering needs explicit tessellation')
   data['tracks'].append(dict(a=xy(t.GetStart()),b=xy(t.GetEnd()),width=k.ToMM(t.GetWidth()),top=t.GetLayer()==k.F_Cu))
 for f in b.GetFootprints():
  for p in f.Pads():
   data['pads'].append(dict(p=xy(p.GetPosition()),size=xy(p.GetSize()),drill=xy(p.GetDrillSize()),angle=p.GetOrientationDegrees(),circle=p.GetShape()==k.PAD_SHAPE_CIRCLE,npth=p.GetAttribute()==k.PAD_ATTRIB_NPTH))
  if not f.GetReference().startswith('H'):
   data['labels'].append(dict(text=f.GetReference(),p=xy(f.Reference().GetPosition())))
 print(json.dumps(data))

def render():
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 import matplotlib.patheffects as pe
 from matplotlib.patches import Rectangle,Circle,Ellipse
 from matplotlib.collections import LineCollection
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--kicad-python',default=os.environ.get('KICAD_PYTHON'))
 args=parser.parse_args()
 candidates=[args.kicad_python,'/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9','/Volumes/KiCad/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9']
 interpreter=next((p for p in candidates if p and Path(p).exists()),None)
 if not interpreter:raise SystemExit('Set KICAD_PYTHON or --kicad-python to KiCad bundled Python')
 raw=subprocess.check_output([interpreter,str(Path(__file__)),'--extract'],cwd=ROOT,text=True)
 d=json.loads(raw);pale='#f5f9f7';dark='#203b34';gold='#d9b553';red='#ba2838';blue='#3069b2'
 fig=plt.figure(figsize=(14,10.8),facecolor='white');ax=fig.add_axes([.025,.065,.95,.91])
 ax.set(xlim=(-10,100),ylim=(75,-1));ax.set_aspect('equal');ax.axis('off')
 ax.add_patch(Rectangle((0,0),90,65,facecolor=pale,edgecolor='#405c52',linewidth=1.7,joinstyle='round',zorder=0))
 # Actual right-angle SMA dimensions from the reviewed connector drawing.
 from matplotlib.patches import Polygon
 import math
 manifest=json.loads((ROOT/'cad/design.json').read_text())
 for p in manifest['parts']:
  if p['ref'] not in ['J1','J2','J3','J4','J5']:continue
  angle=math.radians(p['rot'])
  def point(x,y):return (p['x']+x*math.cos(angle)+y*math.sin(angle),p['y']-x*math.sin(angle)+y*math.cos(angle))
  ax.add_patch(Polygon([point(x,y) for x,y in [(3,-3.1),(11.6,-3.1),(11.6,3.1),(3,3.1)]],closed=True,facecolor='#e5cc8a',edgecolor='#b18c32',linewidth=1.,zorder=2))
  for x in [8.,8.7,9.4,10.1,10.8]:
   a,c=point(x,-3.1),point(x,3.1);ax.plot([a[0],c[0]],[a[1],c[1]],color='#b18c32',lw=.6,zorder=3)
 for top,color in [(False,blue),(True,red)]:
  tt=[t for t in d['tracks'] if t['top']==top]
  col=LineCollection([[t['a'],t['b']] for t in tt],colors=color,linewidths=[t['width']*10.5 for t in tt],zorder=1 if not top else 2,capstyle='round',joinstyle='round')
  ax.add_collection(col)
 for v in d['vias']:
  ax.add_patch(Circle(v['p'],v['diameter']/2,facecolor=gold,edgecolor='none',zorder=3))
  ax.add_patch(Circle(v['p'],v['drill']/2,facecolor=pale,edgecolor='none',zorder=4))
 for p in d['pads']:
  x,y=p['p'];w,h=p['size'];dx,dy=p['drill']
  if p['npth']:
   ax.add_patch(Circle((x,y),dx/2,facecolor='white',edgecolor='#58665e',linewidth=.8,zorder=5));continue
  if p['circle']:shape=Ellipse((x,y),w,h,facecolor=gold,edgecolor='none',zorder=5)
  else:
   shape=Rectangle((x-w/2,y-h/2),w,h,angle=-p['angle'],rotation_point='center',facecolor=gold,edgecolor='none',zorder=5)
  ax.add_patch(shape)
  if dx:ax.add_patch(Ellipse((x,y),dx,dy,facecolor=pale,edgecolor='none',zorder=6))
 # Labels come from the native fabrication drawing; a pale halo separates text
 # from crossing tracks without changing any copper geometry.
 for label in d['labels']:
  if label['text'] in ['U1','J1','J2','J3','J4','J5']:continue
  x,y=label['p'];ax.text(x,y,label['text'],color=dark,fontsize=8.5,ha='center',va='center',zorder=8,path_effects=[pe.withStroke(linewidth=2.3,foreground=pale)])
 # Functional port labels lie within the empty connector bodies / module area.
 for text,x,y,size in [('USB-C / RP2040',17,9,9),('GPS ANT',80,9.7,9),('RF IN',12,54.6,9),('TO SDR',78,54.6,9),('10 MHz OUT',78.5,50.4,9),('1 PPS OUT',5,38.5,8),('LEVEL',12,36.8,8),('CALINJECT · REV C · 90 × 65 mm',44,61.8,10)]:
  ax.text(x,y,text,color=dark,fontsize=size,fontweight='bold',ha='center',va='center',zorder=9,path_effects=[pe.withStroke(linewidth=2.6,foreground=pale)])
 fig.text(.50,.035,'Top view  ·  red: top copper  ·  blue: bottom copper  ·  gold: pads and vias',ha='center',color=dark,fontsize=10)
 for suffix in ['png','svg']:
  fig.savefig(ROOT/('docs/board-layout.'+suffix),dpi=180,facecolor='white')
 svg=ROOT/'docs/board-layout.svg'
 svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
 plt.close(fig)
 print('Rendered actual PCB:',len(d['tracks']),'tracks,',len(d['vias']),'vias,',len(d['pads']),'pads')

if __name__=='__main__':
 if '--extract' in sys.argv:extract()
 else:render()
