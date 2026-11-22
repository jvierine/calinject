import os
"""Non-routing finishing: no-connect nets, assembly fiducials/polarity, paste."""
import pcbnew as k,json,pathlib
root=pathlib.Path(os.environ.get('CALINJECT_ROOT',pathlib.Path(__file__).resolve().parents[1]))
b=k.LoadBoard(str(root/'cad/calinject.kicad_pcb'));d=json.loads((root/'cad/design.json').read_text());parts={p['ref']:p for p in d['parts']};mm=k.FromMM
for f in b.GetFootprints():
 p=parts[f.GetReference()]
 if p['section']=='Mechanical':f.SetAttributes(f.GetAttributes()|k.FP_BOARD_ONLY|k.FP_EXCLUDE_FROM_BOM|k.FP_EXCLUDE_FROM_POS_FILES)
 for a in f.Pads():
  q=next(q for q in p['pads'] if q['n']==a.GetNumber())
  if not q['net'] and q['n']:
   net=k.NETINFO_ITEM(b,'unconnected-(%s-%s-Pad%s)'%(p['ref'],q['label'],q['n']));b.Add(net);a.SetNet(net)
  # Reduced EP paste; via holes must be tented from bottom, normal prototype
  # process may wick some solder. No filled/capped-via cost assumed.
  if p['ref']=='U9' and q['n']=='21':a.SetLocalSolderPasteMargin(mm(-.35))
 # Pin-1 fabrication marker; readable assembly drawing defines package angle.
 if p['ref'] in ['U1','U2','U3','U4','U5','U6','U7','U8','U9','U10','U11','Y1','T1','D1']:
  a=next(a for a in f.Pads() if a.GetNumber()=='1')
  text=k.PCB_TEXT(f);text.SetText('1');text.SetTextSize(k.VECTOR2I(mm(.6),mm(.6)));text.SetTextThickness(mm(.1));text.SetLayer(k.F_Fab);text.SetPosition(a.GetPosition()+k.VECTOR2I(mm(-.6),mm(-.8)));f.Add(text)
k.SaveBoard(str(root/'cad/calinject.kicad_pcb'),b)
plugin=k.PCB_IO_MGR.FindPlugin(k.PCB_IO_MGR.KICAD_SEXP)
for f in b.GetFootprints():
 c=k.Cast_to_FOOTPRINT(f.Duplicate(False));c.SetOrientationDegrees(0);c.SetPosition(k.VECTOR2I(0,0));plugin.FootprintSave(str(root/'cad/Calinject.pretty'),c)
