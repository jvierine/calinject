import os
"""Import autorouting, add ground planes and export fabrication using KiCad APIs."""
import pcbnew as k,pathlib,sys
root=pathlib.Path(os.environ.get('CALINJECT_ROOT',pathlib.Path(__file__).resolve().parents[1]));b=k.LoadBoard(str(root/'cad/calinject.kicad_pcb'));mm=k.FromMM;v=lambda x,y:k.VECTOR2I(mm(x),mm(y))
if '--import' in sys.argv:print('SES import',k.ImportSpecctraSES(b,str(root/'cad/calinject.ses')))
for track in b.GetTracks():
 if isinstance(track,k.PCB_VIA):track.SetViaType(k.VIATYPE_THROUGH);track.SetLayerPair(k.F_Cu,k.B_Cu)
for layer in [k.In1_Cu,k.In2_Cu]:
 z=k.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('GND'));z.SetLocalClearance(mm(.2));z.SetThermalReliefGap(mm(.25));z.SetThermalReliefSpokeWidth(mm(.3));z.SetPadConnection(k.ZONE_CONNECTION_FULL)
 o=z.Outline();o.NewOutline()
 for x,y in [(0.4,.4),(89.6,.4),(89.6,64.6),(.4,64.6)]:o.Append(int(mm(x)),int(mm(y)))
 b.Add(z)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(root/'cad/calinject.kicad_pcb'),b)
print('Tracks',len(list(b.GetTracks())))
