"""Case plan / connector guide. Geometry comes from the shared circuit manifest."""
from pathlib import Path
import json,math
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'cad/design.json').read_text());parts={p['ref']:p for p in d['parts']}
c=canvas.Canvas(str(ROOT/'docs/port-guide.pdf'),pagesize=(210*mm,297*mm))
c.setTitle('Calinject connector guide');c.setFont('Helvetica-Bold',18);c.drawString(20*mm,273*mm,'Calinject connector guide')
c.setFont('Helvetica',10);c.drawString(20*mm,264*mm,'Top view, USB at north; dimensions in mm. Prototype fit requires checking.')
ox=35;oy=145;scale=1.35
def xy(x,y):return ((ox+scale*(4+x))*mm,(oy+scale*(73-4-y))*mm)
c.setStrokeColor(HexColor('#254559'));c.setLineWidth(1.2);c.roundRect(ox*mm,oy*mm,98*scale*mm,73*scale*mm,1.5*mm)
c.setDash(3,2);a,b=xy(0,65);c.rect(a,b,90*scale*mm,65*scale*mm);c.setDash()
for ref in ['J1','J2','J3','J4','J5']:
 p=parts[ref];angle=math.radians(p['rot']);path=c.beginPath()
 for i,(a,b) in enumerate([(-3,-3),(11.6,-3),(11.6,3),(-3,3)]):
  x,y=xy(p['x']+a*math.cos(angle)+b*math.sin(angle),p['y']-a*math.sin(angle)+b*math.cos(angle))
  (path.moveTo if i==0 else path.lineTo)(x,y)
 path.close();c.drawPath(path)
 x,y=xy(p['x']-5 if ref in ['J1','J4'] else p['x']+4 if ref=='J5' else p['x'],p['y']-7)
 c.setFont('Helvetica-Bold',9);c.drawCentredString(x,y,p['value']);c.setFont('Helvetica',8);c.drawCentredString(x,y-3*mm,ref)
x,y=xy(17,-4);c.setLineWidth(3);c.line(x-6*mm,y,x+6*mm,y);c.setFont('Helvetica-Bold',9);c.drawCentredString(x,y+4*mm,'USB-C')
x,y=xy(12,34);c.setLineWidth(1);c.circle(x,y,2.4*scale*mm);c.setFont('Helvetica',8);c.drawString(x+4*mm,y-2*mm,'LEVEL')
x,y=xy(17,15.8);c.circle(x,y,3.6*scale*mm);c.setFont('Helvetica-Bold',8);c.drawString(x+6*mm,y,'STATUS')
c.setFont('Helvetica',10)
lines=[
'USB-C: 5 V power; works with a wall supply and no computer.',
'STATUS: green startup; amber acquiring; green PPS tracking; red fault.',
'GPS ANT: active 3.3 V antenna, normally up to 20 mA.',
'RF IN: from the existing antenna bias board; DC blocked.',
'TO SDR: injected receiver signal; DC blocked.',
'10 MHz OUT: continuous square wave, separately USB enabled.',
'1 PPS OUT: GNSS rising edge, 10 ms high, separately USB enabled.',
'Reference outputs: nominal 3.3 V high impedance / 1.65 V into 50 ohm.',
'Reference clock phase is not locked to PPS. Read USB validity/servo status.',
'LOW/HIGH range shunts and initial BOOT programming are inside the case.',
]
for i,line in enumerate(lines):c.drawString(20*mm,(124-i*7)*mm,line)
c.showPage();c.save()
