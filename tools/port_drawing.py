"""Case plan / connector guide. Geometry comes from the shared circuit manifest."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'cad/design.json').read_text());parts={p['ref']:p for p in d['parts']}
c=canvas.Canvas(str(ROOT/'docs/port-guide.pdf'),pagesize=(210*mm,297*mm))
c.setTitle('Calinject connector guide');c.setFont('Helvetica-Bold',18);c.drawString(20*mm,273*mm,'Calinject connector guide')
c.setFont('Helvetica',10);c.drawString(20*mm,264*mm,'Top view, USB at north; dimensions in mm. Prototype fit requires checking.')
ox=35;oy=145;scale=1.35
def xy(x,y):return ((ox+scale*(7+x))*mm,(oy+scale*(79-7-y))*mm)
c.setStrokeColor(HexColor('#254559'));c.setLineWidth(1.2);c.roundRect(ox*mm,oy*mm,104*scale*mm,79*scale*mm,1.5*mm)
c.setDash(3,2);a,b=xy(0,65);c.rect(a,b,90*scale*mm,65*scale*mm);c.setDash()
for ref in ['J1','J2','J3','J4','J5']:
 p=parts[ref];x,y=xy(p['x'],p['y']);c.circle(x,y,6*scale*mm);c.setFont('Helvetica-Bold',9)
 c.drawCentredString(x,y+10*mm,p['value']);c.setFont('Helvetica',8);c.drawCentredString(x,y-2*mm,ref)
x,y=xy(17,-7);c.setLineWidth(3);c.line(x-6*mm,y,x+6*mm,y);c.setFont('Helvetica-Bold',9);c.drawCentredString(x,y+4*mm,'USB-C')
x,y=xy(12,34);c.setLineWidth(1);c.circle(x,y,2.4*scale*mm);c.setFont('Helvetica',8);c.drawString(x+4*mm,y-2*mm,'LEVEL')
c.setFont('Helvetica',10)
lines=[
'GPS ANT: active 3.3 V antenna, normally up to 20 mA.',
'RF IN: from the existing antenna bias board; DC blocked.',
'TO SDR: injected receiver signal; DC blocked.',
'10 MHz OUT: continuous square wave, separately USB enabled.',
'1 PPS OUT: GNSS rising edge, 10 ms high, separately USB enabled.',
'Reference outputs: nominal 3.3 V high impedance / 1.65 V into 50 ohm.',
'Reference clock phase is not locked to PPS. Read USB validity/servo status.',
'LOW/HIGH range shunts and initial BOOT programming are inside the case.',
]
for i,line in enumerate(lines):c.drawString(20*mm,(124-i*8)*mm,line)
c.showPage();c.save()
