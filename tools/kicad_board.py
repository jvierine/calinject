import os
"""KiCad SWIG helper; executed by KiCad's bundled Python, not macOS system Python.
The orchestration and design source run in base conda Python. KiCad 10 embeds 3.9.
"""
import pcbnew as k, json, pathlib, math, sys, uuid
root=pathlib.Path(os.environ.get('CALINJECT_ROOT',pathlib.Path(__file__).resolve().parents[1]))
d=json.loads((root/'cad/design.json').read_text());b=k.BOARD();b.SetCopperLayerCount(4)
mm=k.FromMM
v=lambda x,y:k.VECTOR2I(mm(x),mm(y))
nets={}
for name in sorted({q['net'] for p in d['parts'] for q in p['pads'] if q['net']}):
 n=k.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
for p in d['parts']:
 f=k.FOOTPRINT(b);f.SetReference(p['ref']);f.SetValue(p['value']);f.SetFPID(k.LIB_ID('Calinject',p['fp']));f.SetPosition(v(p['x'],p['y']));f.SetOrientationDegrees(p['rot'])
 f.SetPath(k.KIID_PATH('/'+str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/jvierine/calinject/schematic'))+'/'+str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/jvierine/calinject/sheet/'+p['section']))+'/'+str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/jvierine/calinject/inst/'+p['ref']))))
 f.SetAttributes(k.FP_SMD if p['assembly']=='SMT' else k.FP_THROUGH_HOLE)
 f.Reference().SetTextSize(v(.8,.8));f.Reference().SetTextThickness(mm(.12));f.Reference().SetPosition(v(p['x'],p['y']-p['body'][1]/2-1.));f.Reference().SetLayer(k.F_Fab)
 f.Value().SetVisible(False)
 for q in p['pads']:
  a=k.PAD(f);a.SetNumber(q['n']);a.SetSize(v(q['w'],q['h']));a.SetOrientationDegrees(p['rot']);a.SetShape(k.PAD_SHAPE_RECT if q['kind']=='smd' or q['n']=='1' else k.PAD_SHAPE_CIRCLE)
  t=math.radians(p['rot']);x=p['x']+q['x']*math.cos(t)+q['y']*math.sin(t);y=p['y']-q['x']*math.sin(t)+q['y']*math.cos(t);a.SetPosition(v(x,y))
  if q['kind']=='smd':
   a.SetAttribute(k.PAD_ATTRIB_SMD);ls=k.LSET()
   for layer in ([k.F_Cu,k.F_Mask] if p['assembly']=='PCB' else [k.F_Cu,k.F_Mask,k.F_Paste]):ls.AddLayer(layer)
   a.SetLayerSet(ls)
  else:
   a.SetAttribute(k.PAD_ATTRIB_NPTH if q['kind']=='np_thru_hole' else k.PAD_ATTRIB_PTH);a.SetDrillSize(v(q['drill'],q['drill']));a.SetLayerSet(k.LSET.AllCuMask());ls=a.GetLayerSet();ls.AddLayer(k.F_Mask);ls.AddLayer(k.B_Mask);a.SetLayerSet(ls)
  if q['net']:a.SetNet(nets[q['net']])
  f.Add(a)
 # Body on fabrication, courtyard with 0.25 mm margin.
 for layer,margin,width in [(k.F_Fab,0,.1),(k.F_CrtYd,.35,.05)]:
  pts=[(-p['body'][0]/2-margin,-p['body'][1]/2-margin),(p['body'][0]/2+margin,-p['body'][1]/2-margin),(p['body'][0]/2+margin,p['body'][1]/2+margin),(-p['body'][0]/2-margin,p['body'][1]/2+margin)]
  # Include pad bounding extent in courtyard.
  if layer==k.F_CrtYd:
   xx=max(p['body'][0]/2,max(abs(q['x'])+q['w']/2 for q in p['pads']))+.25;yy=max(p['body'][1]/2,max(abs(q['y'])+q['h']/2 for q in p['pads']))+.25;pts=[(-xx,-yy),(xx,-yy),(xx,yy),(-xx,yy)]
  for i in range(4):
   t=math.radians(p['rot'])
   transform=lambda pt:v(p['x']+pt[0]*math.cos(t)+pt[1]*math.sin(t),p['y']-pt[0]*math.sin(t)+pt[1]*math.cos(t))
   s=k.PCB_SHAPE(f);s.SetShape(k.SHAPE_T_SEGMENT);s.SetLayer(layer);s.SetWidth(mm(width));s.SetStart(transform(pts[i]));s.SetEnd(transform(pts[(i+1)%4]));f.Add(s)
 b.Add(f)
# Board outline.
for a,z in [((0,0),(90,0)),((90,0),(90,65)),((90,65),(0,65)),((0,65),(0,0))]:
 s=k.PCB_SHAPE();s.SetShape(k.SHAPE_T_SEGMENT);s.SetLayer(k.Edge_Cuts);s.SetStart(v(*a));s.SetEnd(v(*z));s.SetWidth(mm(.05));b.Add(s)
# Important manually constrained top RF/GNSS routes, filled out by router for digital nets.
fp={f.GetReference():f for f in b.GetFootprints()}
def pos(ref,pin):return next(p.GetPosition() for p in fp[ref].Pads() if p.GetNumber()==str(pin))
def wire(net,points,width=.3,layer=k.F_Cu):
 for a,z in zip(points,points[1:]):
  t=k.PCB_TRACK(b);t.SetStart(a if isinstance(a,k.VECTOR2I) else v(*a));t.SetEnd(z if isinstance(z,k.VECTOR2I) else v(*z));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(nets[net]);b.Add(t)
# 4-layer 1.6mm, outer dielectric0.20mm nominal: width0.36mm ~50ohm; fab must confirm stackup.
wire('GNSS_RF',[pos('U4',11),(73.5,18.3),(75.5,16.3),pos('C7',1)],.36)
wire('ANT_RF',[pos('C7',2),pos('J1',1)],.36)
wire('ATT_DATA_R',[pos('R17',2),pos('U9',3)],.2)
wire('RF_OUT',[pos('R22',1),(71.2,56)],.2)
wire('RF_IN',[pos('J2',1),pos('C24',1)],.36)
wire('RF_FROM_ANT',[pos('C24',2),(32,54.46),pos('T1',3)],.36)
wire('RF_TO_SDR',[pos('T1',1),(62,54.46),pos('C25',1)],.36)
wire('T1_LINK',[pos('T1',2),pos('T1',5)],.3)
wire('RF_OUT',[pos('C25',2),pos('J3',1)],.36)
# Ground vias are validated against all pad and drill clearances by base-Python planner.
for via in d.get('ground_vias',[]):
 pp=pos(via['ref'],via['pin']) if via.get('ref') else None;vx,vy=via['x'],via['y']
 vi=k.PCB_VIA(b);vi.SetPosition(v(vx,vy));vi.SetWidth(mm(.6));vi.SetDrill(mm(.3));vi.SetViaType(k.VIATYPE_THROUGH);vi.SetLayerPair(k.F_Cu,k.B_Cu);vi.SetNet(nets['GND']);b.Add(vi)
 if pp is not None:wire('GND',[pp,v(vx,vy)],.25)
# Export before zones for autorouter. Ground vias allow cross-layer ground stitching.
for txt,x,y,size in [('CALINJECT  REV B',40,63,.9),('GPS ANT 3V3',77,8,.8),('RF IN',12,51,.9),('TO SDR',79,51,.9),('USB-C',17,26,.8),('LEVEL',12,40,.8),('LOW / HIGH',64,51,.8),('10 MHz OUT',80,47.5,.8),('1 PPS OUT',7,39,.8)]:
 t=k.PCB_TEXT(b);t.SetText(txt);t.SetPosition(v(x,y));t.SetTextSize(v(size,size));t.SetTextThickness(mm(.12));t.SetLayer(k.F_SilkS);b.Add(t)
b.SetFileName(str(root/'cad/calinject.kicad_pcb'));k.SaveBoard(b.GetFileName(),b)
print('Saved',len(d['parts']),'components',len(nets),'nets')
# KiCad DSN exporter includes geometry, nets and existing tracks.
b.SetCopperLayerCount(2)
print('DSN',k.ExportSpecctraDSN(b,str(root/'cad/calinject.dsn')))
b.SetCopperLayerCount(4)
# Standalone footprint library extracted from the actual board.
lib=root/'cad/Calinject.pretty';lib.mkdir(exist_ok=True)
for f in b.GetFootprints():
 c=k.Cast_to_FOOTPRINT(f.Duplicate(False));c.SetOrientationDegrees(0);c.SetPosition(v(0,0));k.PCB_IO_MGR.FindPlugin(k.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(lib),c)
