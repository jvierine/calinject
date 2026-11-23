"""Calinject Rev C circuit and mechanical source of truth. Units: mm.
Pad geometries must remain tied to the named manufacturer package drawings.
"""
from pathlib import Path
import json, math, os
ROOT=Path(os.environ.get('CALINJECT_ROOT',Path(__file__).resolve().parents[1]))
parts=[]
def pad(n,x,y,w,h,net=None,kind='smd',drill=None):
 return dict(n=str(n),x=x,y=y,w=w,h=h,net=net,kind=kind,drill=drill)
def add(ref,value,fp,x,y,pins,mpn,maker,section,cost=0.04,rot=0,body=(2,1),note='',assembly='SMT'):
 parts.append(dict(ref=ref,value=value,fp=fp,x=x,y=y,rot=rot,pads=pins,mpn=mpn,maker=maker,section=section,cost=cost,body=body,note=note,assembly=assembly))
def chip(ref,val,a,b,x,y,section,typ='R',rot=0,size='0603',mpn=None):
 geom={'0402':(.5,.55,.6),'0603':(.8,.9,.95),'0805':(1.,1.,1.4),'1206':(1.5,1.2,1.8)}[size]
 dx,w,h=geom
 add(ref,val,f'{typ}_{size}',x,y,[pad(1,-dx,0,w,h,a),pad(2,dx,0,w,h,b)],mpn or (('RC0603FR-07'+val+'L') if typ=='R' else 'SPECIFIED_IN_BOM'), 'Yageo' if typ=='R' else 'Murata',section,rot=rot,body=(2*dx,.8 if size=='0603' else 1.25))
def sot(ref,val,nets,x,y,section,mpn,cost=0.2,rot=0):
 count=len(nets);coords=[(-1.,-.95),(-1.,0),(-1.,.95),(1.,.95),(1.,0),(1.,-.95)] if count==6 else [(-1.,-.95),(-1.,0),(-1.,.95),(1.,.95),(1.,-.95)]
 add(ref,val,'SOT23_'+str(count),x,y,[pad(i+1,*p,1.2,.6,nets[i]) for i,p in enumerate(coords)],mpn,'Texas Instruments',section,cost,rot,(1.6,2.9))
def cap(ref,net,x,y,section,val='100n',rot=0):chip(ref,val,net,'GND',x,y,section,'C',rot,mpn='GRM188R71C104KA01D' if val=='100n' else {'4u7':'GRM188R61A475KE15D','1n':'GRM1885C1H102JA01D','22p':'GRM1885C1H220JA01D'}[val])
# Board: 90 x 65 mm; four M3 mounting holes. USB points north.
for n,(x,y) in enumerate([(4,4),(86,4),(4,61),(86,61)],1):
 add('H'+str(n),'M3','Mount_M3',x,y,[pad('',0,0,3.2,3.2,None,'np_thru_hole',3.2)],'M3 screw','Mechanical','Mechanical',0,body=(6,6),assembly='MECHANICAL')
# USB-C controller module. Pin numbering is perimeter anticlockwise from USB-left.
module_nets=['USB5','GND','3V3D','LEVEL_ADC',None,None,None,None,None,None,None,'TCXO_COUNT','PPS',None,'BURST_GATE','ATT_LE','ATT_CLK','ATT_DATA','I2C_SCL','I2C_SDA',None,'GPS_TX','GPS_RX']
module_names=['5V','GND','3V3','GP29','GP28','GP27','GP26','GP15','GP14','GP13','GP12','GP11','GP10','GP9','GP8','GP7','GP6','GP5','GP4','GP3','GP2','GP1','GP0']
# I2C1 uses GP2 SDA and GP3 SCL.
module_nets[18]=None;module_nets[19]='I2C_SCL';module_nets[20]='I2C_SDA'
module_nets[18]='REF10_OE_N';module_nets[13]='REFPPS_OE_N'
coords=[(-7.62,-10.16+2.54*i) for i in range(9)]+[(-5.08+2.54*i,10.16) for i in range(5)]+[(7.62,10.16-2.54*i) for i in range(9)]
add('U1','RP2040-Zero','RP2040_Zero',17,12,[pad(i+1,*p,1.7,1.7,module_nets[i],'thru_hole',1.) for i,p in enumerate(coords)],'RP2040-Zero','Waveshare','Controller',4.0,body=(18,23.5),note='Genuine module. Factory fits 2.54-mm headers and solders module; USB-C faces north.',assembly='FACTORY MODULE')
# Onboard CC resistors / USB termination / 12 MHz crystal / Flash belong to U1.
# Three linear regulators isolate GNSS and timing RF from the MCU's onboard rail.
sot('U2','AP2112K-3.3',['USB5F','GND','USB5F',None,'3V3A'],34,9,'Power','AP2112K-3.3TRG1',.3)
sot('U3','AP2112K-3.3',['USB5F','GND','USB5F',None,'3V3G'],47,9,'Power','AP2112K-3.3TRG1',.3)
chip('F1','500mA','USB5','USB5F',29,5,'Power','F',size='1206',mpn='1206L050/15YR')
cap('C1','USB5F',34,5,'Power','4u7');cap('C2','3V3A',34,13,'Power','4u7')
cap('C3','USB5F',47,5,'Power','4u7');cap('C4','3V3G',50.6,8.05,'Power','4u7')
# GNSS MAX-M10S. 18 lands, pitch 1.1 mm. Body 9.7 x 10.1.
gn=['GND','GPS_TX','GPS_RX','PPS',None,'3V3G','3V3G','3V3G',None,'GND','GNSS_RF','GND',None,None,None,None,None,None]
gp=[(-4.5,-4.4+1.1*i) for i in range(9)]+[(4.5,4.4-1.1*i) for i in range(9)]
add('U4','MAX-M10S','MAX_M10S',68,15,[pad(i+1,*p,1.5,.8,gn[i]) for i,p in enumerate(gp)],'MAX-M10S-00B','u-blox','GNSS',11.42,body=(9.7,10.1),note='TIMEPULSE must not be pulled low at startup; VIO_SEL floating selects 3.3V.')
cap('C5','3V3G',59,15,'GNSS');cap('C6','3V3G',59,19,'GNSS','4u7')
# Commodity right-angle SMA, Lian Xin SMA-KWE C7498154. Barrel points local +X.
def sma(ref,name,x,y,net,section):
 positions={'J1':(86.4,15,0),'J2':(12,61.4,270),'J3':(78,61.4,270),'J4':(86.4,43,0),'J5':(3.6,44,180)}
 x,y,rot=positions[ref]
 p=[pad(1,0,0,1.9,1.9,net,'thru_hole',1.2)]+[pad(2,dx,dy,2.,2.,'GND','thru_hole',1.4) for dx in [-2.1,2.1] for dy in [-2.1,2.1]]
 add(ref,name,'SMA_KWE_RA',x,y,p,'SMA-KWE','Lian Xin Technology',section,.8,rot=rot,body=(6.,6.),note='C7498154. Female SMA, horizontal barrel local+X; 4.2mm square legs,0.9mm pins. Tip11.6mm from signal-pin center, thread4mm. Axis6mm above PCB. Match exact drawing, not just SMA-KWE name.',assembly='THT')
sma('J1','GPS ANT',82,15,'ANT_RF','GNSS')
chip('C7','100p','GNSS_RF','ANT_RF',76,15,'GNSS','C',size='0402',mpn='GRM1555C1H101JA01D')
chip('L1','27n','ANT_BIAS','ANT_RF',82,21,'GNSS','L',rot=90,size='0402',mpn='LQW15AN27NG80D')
chip('F2','50mA','3V3G','ANT_FUSED',70,25,'GNSS','F',size='1206',mpn='1206L005/60WR')
# Fuse resistance already provides filtering; avoid wasting antenna headroom in
# a 10-ohm resistor and avoid resistor overload during a sustained antenna short.
chip('R1','0','ANT_FUSED','ANT_BIAS',77,25,'GNSS',mpn='RC0603FR-070RL')
cap('C8','ANT_BIAS',82,27,'GNSS');cap('C9','ANT_BIAS',86,27,'GNSS','1n')
# RF ESD diode, 0201 package.
add('D1','PESD5V0F1BL','DFN1006_2',78,21,[pad(1,-.35,0,.45,.6,'ANT_RF'),pad(2,.35,0,.45,.6,'GND')],'PESD5V0F1BL,315','Nexperia','GNSS',.12,body=(1.,.6))
# Reference: DAC -> two RC poles -> tunable oscillator.
sot('U5','MCP4725A1',['DAC_OUT','GND','3V3A','I2C_SDA','I2C_SCL','GND'],38,24,'Reference','MCP4725A1T-E/CH',1.1)
parts[-1]['maker']='Microchip';parts[-1]['note']='C61423; A1 option, A0 pin grounded: I2C 0x62.'
cap('C10','3V3A',38,20,'Reference')
chip('R2','4k7','I2C_SDA','3V3D',29,25,'Controller',rot=90,mpn='RC0603FR-074K7L')
chip('R3','4k7','I2C_SCL','3V3D',32,25,'Controller',rot=90,mpn='RC0603FR-074K7L')
chip('R4','1k','DAC_OUT','DAC_FILT',43,24,'Reference',mpn='RC0603FR-071KL')
cap('C11','DAC_FILT',46,27,'Reference','4u7',90)
chip('R5','1k','DAC_FILT','VCTRL',49,24,'Reference',mpn='RC0603FR-071KL')
cap('C12','VCTRL',52,27,'Reference','4u7',90)
add('Y1','10MHz VCTCXO','KDS_DSA321SDN',57,33,[pad(1,-1.12,.7,.78,.9,'VCTRL'),pad(2,1.12,.7,.78,.9,'GND'),pad(3,1.12,-.7,.78,.9,'OSC_SINE'),pad(4,-1.12,-.7,.78,.9,'3V3A')],'1XTV10000MDA','KDS Daishinku','Reference',1.067,body=(3.2,2.5),note='C253701. Clipped sine; Vc 0.5..2.5V, nominal1.5V. Positive pull +/-8..15ppm. Control input >=500k. Respect KDS bottom copper keepout; calibrate tuning slope.')
cap('C13','3V3A',53,31,'Reference')
chip('C14','1n','OSC_SINE','SINE_BIASED',62,32,'Reference','C',mpn='GRM1885C1H102JA01D')
chip('R6','10k','3V3A','VREF_HALF',62,28,'Reference',mpn='RC0603FR-0710KL')
chip('R7','10k','VREF_HALF','GND',66,28,'Reference',mpn='RC0603FR-0710KL')
cap('C15','VREF_HALF',65,25,'Reference')
chip('R8','10k','SINE_BIASED','VREF_HALF',66,32,'Reference',rot=90,mpn='RC0603FR-0710KL')
sot('U6','TLV3501',['VREF_HALF','GND','SINE_BIASED','3V3A','CLK10','GND'],71,32,'Reference','TLV3501AIDBVR',2.2)
cap('C16','3V3A',73.5,34.8,'Reference')
chip('R9','330','CLK10','TCXO_COUNT',41,35,'Controller',mpn='RC0603FR-07330RL')
# Pulse width approx 7..12ns with 220R / 22pF and Schmitt inverter. Measure prototype.
chip('R10','220','CLK10','DELAY_RC',66.5,36.5,'Comb',mpn='RC0603FR-07220RL')
cap('C17','DELAY_RC',66.5,38.5,'Comb','22p')
sot('U7','SN74LVC1G14',[None,'DELAY_RC','GND','DELAY_N','3V3A'],68,41,'Comb','SN74LVC1G14DBVR',.12)
cap('C18','3V3A',71,37.8,'Comb')
# DCU VSSOP8 pitch0.5: pins 1..4 down left,5..8 up right.
np=['CLK10','DELAY_N','COMB_GATED','GND','COMB_RAW','BURST_GATE','COMB_RAW','3V3A']
coords=[(-1.4,-.75+.5*i) for i in range(4)]+[(1.4,.75-.5*i) for i in range(4)]
add('U8','74LVC2G08','VSSOP8_DCU',58,41,[pad(i+1,*p,1.,.3,np[i]) for i,p in enumerate(coords)],'74LVC2G08DC,125','Nexperia','Comb',.2,body=(2.3,2.))
cap('C19','3V3A',60.6,39,'Comb')
chip('R11','100k','BURST_GATE','GND',53,38,'Comb',rot=90,mpn='RC0603FR-07100KL')
chip('R12','49R9','COMB_GATED','DRIVE50',52,42,'Comb',mpn='RC0603FR-0749R9L')
chip('C20','100n','DRIVE50','PAD_IN',48,42,'Comb','C',mpn='GRM188R71H104KA93D')
# 20 dB 50-ohm PI pad: shunts61.9,series249. Keeps PE input benign at all harmonics.
chip('R13','61R9','PAD_IN','GND',45,39,'Attenuator',rot=90,mpn='RC0603FR-0761R9L')
chip('R14','249','PAD_IN','ATT_IN',43,42,'Attenuator',mpn='RC0603FR-07249RL')
chip('R15','61R9','ATT_IN','GND',40,39,'Attenuator',rot=90,mpn='RC0603FR-0761R9L')
# PE4312 QFN20 4x4, 0.5 pitch, exposed2.6mm pad. Pins anticlockwise.
pe=['ATT_C16','ATT_IN','ATT_DATA_R','ATT_CLK','ATT_LE','3V3A','GND','GND','3V3A','GND','GND','GND','3V3A','ATT_OUT','3V3A','3V3A','3V3A','GND','3V3A','3V3A']
coords=[(-1.95,-1+.5*i,.8,.28) for i in range(5)]+[(-1+.5*i,1.95,.28,.8) for i in range(5)]+[(1.95,1-.5*i,.8,.28) for i in range(5)]+[(1-.5*i,-1.95,.28,.8) for i in range(5)]
add('U9','PE4312','QFN20_4x4_EP',33,43,[pad(i+1,*p,pe[i]) for i,p in enumerate(coords)]+[pad(21,0,0,2.6,2.6,'GND')],'PE4312C-Z','pSemi','Attenuator',4.40,body=(4,4),note='Serial mode, parallel bits pulled high = 31.5 dB startup. 10k series on pins1,3.')
cap('C21','3V3A',33.2,46.8,'Attenuator');cap('C22','3V3A',29,48,'Attenuator','1n')
chip('R16','10k','3V3A','ATT_C16',28,40,'Attenuator',mpn='RC0603FR-0710KL')
chip('R17','10k','ATT_DATA','ATT_DATA_R',28,43,'Attenuator',mpn='RC0603FR-0710KL')
chip('R18','100k','ATT_LE','GND',28,46,'Attenuator',mpn='RC0603FR-07100KL')
# Isolated transformer combiner. Sum to SDR; separate antenna/cal branches.
chip('C23','100n','ATT_OUT','ATT_AC',40,48,'RF path','C',mpn='GRM188R71H104KA93D')
chip('R19','61R9','PAD20_IN','GND',46,47,'RF path',rot=90,mpn='RC0603FR-0761R9L')
chip('R20','249','PAD20_IN','PAD20_OUT',51,48,'RF path',mpn='RC0603FR-07249RL')
chip('R23','61R9','PAD20_OUT','GND',56,47,'RF path',rot=90,mpn='RC0603FR-0761R9L')
add('JP1','LEVEL RANGE','Range_2x3',64,47,[pad(1,-2.54,-1.27,1.8,1.8,'PAD20_IN','thru_hole',1.),pad(2,0,-1.27,1.8,1.8,'ATT_AC','thru_hole',1.),pad(3,2.54,-1.27,1.8,1.8,'PAD_BYPASS','thru_hole',1.),pad(4,-2.54,1.27,1.8,1.8,'PAD20_OUT','thru_hole',1.),pad(5,0,1.27,1.8,1.8,'COUPLED','thru_hole',1.),pad(6,2.54,1.27,1.8,1.8,'PAD_BYPASS','thru_hole',1.)],'2x FG-PZ2.54-1-03P + 2x C100114','FG / BOOMELE','RF path',.2,body=(7.62,5.08),assembly='THT',note='Two shunts: LOW1-2 and4-5; HIGH2-3 and5-6. Never mix. LOW default. No pad branch attached in HIGH.')
cpnets=['RF_TO_SDR','T1_LINK','RF_FROM_ANT','COUPLED','T1_LINK','GND']
cpcoords=[(-2.54,2.54),(0,2.54),(2.54,2.54),(2.54,-2.54),(0,-2.54),(-2.54,-2.54)]
add('T1','ADP-2-1+','MiniCircuits_CD636',48,57,[pad(i+1,*pt,1.65,2.54,cpnets[i]) for i,pt in enumerate(cpcoords)],'ADP-2-1+','Mini-Circuits','RF path',12.04,rot=180,body=(7.87,5.59),note='JLC C2683460. Sum1 to SDR; branch3 antenna; branch4 cal. Join2/5 and isolate from ground. Specified0.5..400MHz.')
sma('J2','RF IN',12,56,'RF_IN','RF path');sma('J3','TO SDR',78,56,'RF_OUT','RF path')
chip('C24','1u 50V','RF_IN','RF_FROM_ANT',23,56,'RF path','C',size='0805',mpn='GRM21BR71H105KA12L')
chip('C25','1u 50V','RF_TO_SDR','RF_OUT',67,56,'RF path','C',size='0805',mpn='GRM21BR71H105KA12L')
chip('R21','1M','RF_IN','GND',18,57.5,'RF path',mpn='RC0603FR-071ML')
chip('R22','1M','RF_OUT','GND',72,60,'RF path',mpn='RC0603FR-071ML')
# Manual level knob, read as DC only. All RF attenuation is inside PE4312.
add('RV1','10k LEVEL','Bourns_3362P',12,34,[pad(1,-2.54,0,1.8,1.8,'3V3D','thru_hole',.9),pad(2,0,2.54,1.8,1.8,'LEVEL_ADC','thru_hole',.9),pad(3,2.54,0,1.8,1.8,'GND','thru_hole',.9)],'3362P-1-103LF','Bourns','Controller',.6,body=(6.6,6.6),assembly='THT')
cap('C26','LEVEL_ADC',18,36,'Controller')
# Dedicated reference outputs. Two equal, independently ballasted buffer outputs
# share each load: 100 || 100 + 0 = 50 ohm nominal source resistance.
# This keeps each gate near 16.5mA with a 50-ohm load at 3.3V. Never tie CMOS
# outputs directly together. Disabled output is high impedance (1M bleed).
for r,name,x,y,source,oe in [('U10','10 MHz',83,34,'CLK10','REF10_OE_N'),('U11','1 PPS',18,44,'PPS','REFPPS_OE_N')]:
 ns=[oe,source,r+'_B','GND',source,r+'_A',oe,'3V3A']
 coords=[(-1.7,-.975+.65*i) for i in range(4)]+[(1.7,.975-.65*i) for i in range(4)]
 add(r,'SN74LVC2G125','SSOP8_DCT',x,y,[pad(i+1,*pt,1.6,.3,ns[i]) for i,pt in enumerate(coords)],'SN74LVC2G125DCTR','Texas Instruments','Reference outputs',.35,body=(2.8,2.95),note='Parallel channels through individual100ohm resistors. OE high disables both. DC-coupled. Active DCT package; do not fit obsolete DCU3 variant.')
chip('R24','100','U10_A','REF10_SUM',79,37,'Reference outputs',mpn='RC0603FR-07100RL')
chip('R25','100','U10_B','REF10_SUM',84,36.6,'Reference outputs',mpn='RC0603FR-07100RL')
chip('R26','0','REF10_SUM','REF10_OUT',84,38.2,'Reference outputs',mpn='RC0603FR-070RL')
chip('R27','10k','REF10_OE_N','3V3A',78.4,33,'Reference outputs',mpn='RC0603FR-0710KL')
cap('C27','3V3A',87,31.4,'Reference outputs')
chip('R28','100','U11_A','REFPPS_SUM',23,44,'Reference outputs',mpn='RC0603FR-07100RL')
chip('R29','100','U11_B','REFPPS_SUM',18,47,'Reference outputs',mpn='RC0603FR-07100RL')
chip('R30','0','REFPPS_SUM','REFPPS_OUT',14,47,'Reference outputs',mpn='RC0603FR-070RL')
chip('R31','10k','REFPPS_OE_N','3V3A',23,41,'Reference outputs',mpn='RC0603FR-0710KL')
cap('C28','3V3A',16.2,39.8,'Reference outputs')
sma('J4','10 MHz OUT',84,43,'REF10_OUT','Reference outputs')
sma('J5','1 PPS OUT',7,44,'REFPPS_OUT','Reference outputs')
chip('R32','1M','REF10_OUT','GND',84,49,'Reference outputs',mpn='RC0603FR-071ML')
chip('R33','1M','REFPPS_OUT','GND',8,50,'Reference outputs',mpn='RC0603FR-071ML')
# Test pads at accessible positions; no connector capacitance on oscillator sine output.
for i,(name,net,x,y) in enumerate([('PPS','PPS',52,17),('10M','TCXO_COUNT',44,32),('GATE','BURST_GATE',47,35),('VC','VCTRL',56,27),('GND','GND',49,17),('3V3','3V3A',38,16)],1):
 add('TP'+str(i),name,'TestPoint',x,y,[pad(1,0,0,1.4,1.4,net)],'TESTPOINT','PCB','Test',0,body=(1.4,1.4),assembly='PCB')
# Additional local IC bypassing after layout audit.
cap('C29','3V3A',37.600000,8.050000,'Power',rot=0)
cap('C31','3V3G',61.700000,16.400000,'Power',rot=90)
cap('C32','3V3A',34.461300,24.484100,'Power',rot=180)
cap('C33','3V3A',19.6,41.2,'Power',rot=0)
# Pin labels are explicit in schematics and independent of footprint orientation.
labels={
'U1':module_names,'U2':['IN','GND','EN','NC','OUT'],'U3':['IN','GND','EN','NC','OUT'],
'U4':['GND','TXD','RXD','TIMEPULSE','EXTINT','V_BCKP','V_IO','VCC','RESET_N','GND','RF_IN','GND','LNA_EN','VCC_RF','VIO_SEL','SDA','SCL','SAFEBOOT_N'],
'U5':['VOUT','VSS','VDD','SDA','SCL','A0'],'Y1':['VC','GND','OUT','VDD'],
'U6':['IN-','V-','IN+','V+','OUT','SHDN'],'U7':['NC','A','GND','Y','VCC'],
'U8':['1A','1B','2Y','GND','2A','2B','1Y','VCC'],
'U10':['1OE_N','1A','2Y','GND','2A','1Y','2OE_N','VCC'],
'U11':['1OE_N','1A','2Y','GND','2A','1Y','2OE_N','VCC'],
'T1':['SUM_TO_SDR','LINK','ANT_BRANCH','CAL_BRANCH','LINK','GND'],
'U9':['C16','RF1','DATA','CLK','LE','VDD','PUP1','PUP2','VDD','GND','GND','VSS_EXT','P/S','RF2','C8','C4','C2','GND','C1','C0.5','EP']}
for p in parts:
 p['fp'] += '_'+p['ref']
 if p['ref'] in ['U2','U3']:p['maker']='Diodes Incorporated'
 if p['ref']=='U5':p['maker']='Microchip'
 if p['ref'].startswith('F'):p['maker']='Littelfuse';p['cost']=.5
 if p['ref']=='L1':p['cost']=.12
 for i,pd in enumerate(p['pads']): pd['label']=labels.get(p['ref'],[str(q['n']) for q in p['pads']])[i]
for p in parts:
 if p['ref']=='C17':p['mpn']='CL10C220JB8NNNC';p['maker']='Samsung Electro-Mechanics'
 if p['ref']=='Y1':p['x'],p['y']=64,34
 if p['ref']=='C13':p['x'],p['y']=64,31.2
 if p['ref']=='C14':p['x'],p['y']=67.6,34
 if p['ref']=='R8':p['x'],p['y']=68.3,30
def world(p,q):
 t=math.radians(p['rot']);return p['x']+q['x']*math.cos(t)+q['y']*math.sin(t),p['y']-q['x']*math.sin(t)+q['y']*math.cos(t)
if __name__=='__main__':
 (ROOT/'cad/design.json').write_text(json.dumps(dict(revision='C',width_mm=90,height_mm=65,parts=parts),indent=2)+'\n')
 print(len(parts),'components; estimated component sum',sum(p['cost'] for p in parts))
