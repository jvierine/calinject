"""Measure actual native-PCB return-via and bypass geometry with KiCad Python.
Distances screen layout risks; they do not certify SI, PI or EMC performance.
"""
from pathlib import Path
import json, math
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1]
b=k.LoadBoard(str(ROOT/'cad/calinject.kicad_pcb'))
xy=lambda v:(k.ToMM(v.x),k.ToMM(v.y))
dist=lambda a,c:math.hypot(a[0]-c[0],a[1]-c[1])
fs={f.GetReference():f for f in b.GetFootprints()}
vias=[t for t in b.GetTracks() if isinstance(t,k.PCB_VIA)]
ground=[xy(v.GetPosition()) for v in vias if v.GetNetname()=='GND']
ground += [xy(p.GetPosition()) for f in fs.values() for p in f.Pads() if p.GetNetname()=='GND' and p.GetAttribute()==k.PAD_ATTRIB_PTH]
signal=[]
for v in vias:
 if v.GetNetname()=='GND':continue
 p=xy(v.GetPosition());signal.append(dict(net=v.GetNetname(),position_mm=p,nearest_ground_transition_mm=min(dist(p,g) for g in ground)))
dec=[]
for ref,cap in [('U2','C2'),('U3','C4'),('U4','C5'),('U5','C10'),('Y1','C13'),('U6','C16'),('U7','C18'),('U8','C19'),('U9','C21'),('U10','C27'),('U11','C28')]:
 cap={'U2':'C29','U4':'C31','U5':'C32','U11':'C33'}.get(ref,cap)
 power=[p for p in fs[ref].Pads() if p.GetNetname() in ['3V3A','3V3G']]
 cp=next(p for p in fs[cap].Pads() if p.GetNetname()!='GND');cg=next(p for p in fs[cap].Pads() if p.GetNetname()=='GND')
 dec.append(dict(ic=ref,capacitor=cap,nearest_supply_pad_mm=min(dist(xy(p.GetPosition()),xy(cp.GetPosition())) for p in power),capacitor_ground_via_mm=min(dist(xy(cg.GetPosition()),g) for g in ground)))
r=dict(copper_layers=b.GetCopperLayerCount(),zones=[dict(layers=[b.GetLayerName(i) for i in range(k.PCB_LAYER_ID_COUNT) if z.IsOnLayer(i)],net=z.GetNetname()) for z in b.Zones()],ground_vias=sum(v.GetNetname()=='GND' for v in vias),signal_vias=sorted(signal,key=lambda x:-x['nearest_ground_transition_mm']),decoupling=dec)
(ROOT/'validation/layout-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
