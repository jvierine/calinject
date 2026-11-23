"""Check JLC library rotation compensation and actual exported XLSX cells.
SMA copper is rotationally symmetric: four ground pins and a central RF pin.
USB orientation is independently tied to the genuine Waveshare pinout.
"""
from pathlib import Path
import json,math,zipfile,xml.etree.ElementTree as ET,hashlib
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'cad/design.json').read_text());parts={p['ref']:p for p in d['parts']}
rows=json.loads((ROOT/'manufacturing/jlc-turnkey/CPL.json').read_text());cpl={r[0]:r for r in rows[1:]}
offsets=json.loads((ROOT/'manufacturing/jlc-rotation-offsets.json').read_text())['parts']
assert len(cpl)==95 and len(rows)==96
for ref,p in parts.items():
 if ref not in cpl:continue
 row=cpl[ref];offset=offsets.get(ref,{}).get('rotation_offset_deg',0)
 assert row==[ref,p['x'],-p['y'],'Top',(p['rot']+offset)%360],ref
for ref,expected in [('J1',(1,0)),('J2',(0,1)),('J3',(0,1)),('J4',(1,0)),('J5',(-1,0))]:
 p=parts[ref];angle=math.radians(cpl[ref][4])
 # JLC C7498154 zero direction -X; rotations CCW, board coordinates Y down.
 direction=(-round(math.cos(angle)),round(math.sin(angle)))
 assert direction==expected,(ref,direction)
 assert {q['net'] for q in p['pads'][1:]}=={'GND'}
 g={(round(q['x'],4),round(q['y'],4)) for q in p['pads'][1:]}
 assert g=={(-x,-y) for x,y in g}
 tip=(p['x']+11.6*direction[0],p['y']+11.6*direction[1])
 assert tip[0]<0 or tip[0]>90 or tip[1]>65,(ref,tip)
u=parts['U1'];pins={q['label']:q for q in u['pads']}
assert cpl['U1']==['U1',17,-12,'Top',0]
assert pins['5V']['x']<0 and pins['5V']['y']<-10
assert pins['GP0']['x']>0 and pins['GP0']['y']<-10
# Read actual saved workbook cells without modifying it.
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(ROOT/'manufacturing/jlc-turnkey/CPL.xlsx') as z:
 shared=[]
 if 'xl/sharedStrings.xml' in z.namelist():
  shared=[''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
 sheet=ET.fromstring(z.read('xl/worksheets/sheet1.xml'));saved=[]
 for row in sheet.findall('s:sheetData/s:row',ns):
  values=[]
  for c in row.findall('s:c',ns):
   t=c.get('t');v=c.find('s:v',ns)
   if t=='inlineStr':value=''.join(c.find('s:is',ns).itertext())
   elif t=='s':value=shared[int(v.text)]
   elif t=='str':value=v.text
   else:value=float(v.text) if v is not None else ''
   values.append(value)
  saved.append(values)
 assert saved==rows,'Saved workbook differs from placement JSON'
result=dict(revision='C',status='Local file checks pass; confirm live JLC preview separately',
 connectors={r:dict(x_mm=cpl[r][1],y_mm=cpl[r][2],rotation_deg=cpl[r][4],threads=offsets[r]['expected_direction']) for r in offsets},
 usb_c=dict(reference='U1',rotation_deg=0,direction='north',pinout='5V northwest; GP0 northeast'),
 placement_count=95,cpl_sha256=hashlib.sha256((ROOT/'manufacturing/jlc-turnkey/CPL.xlsx').read_bytes()).hexdigest())
(ROOT/'validation/jlc-placement-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
