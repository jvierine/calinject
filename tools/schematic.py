"""Generate editable hierarchical KiCad schematics from the circuit manifest."""
from pathlib import Path
import json,uuid,math
from design import parts,ROOT
uid=lambda s:str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/jvierine/calinject/'+s))
q=lambda s:json.dumps(str(s))
effect='(effects (font (size 1.0 1.0)))'
rootid=uid('schematic')
def typ(p,pd):
 r,n,label=p['ref'],pd['n'],pd['label']
 if not pd['net']:return 'no_connect'
 if r.startswith('#FLG'):return 'power_out'
 if r in ['U2','U3'] and n=='5':return 'power_out'
 if r=='U1' and n in ['1','3']:return 'power_out'
 if label in ['GND','VSS','VDD','VCC','V+','V-','V_BCKP','V_IO','EP','IN'] and r.startswith('U'):return 'power_in'
 if r=='Y1':return {'1':'input','2':'power_in','3':'output','4':'power_in'}[n]
 if r=='U4' and n in ['2','4','13','14']:return 'output'
 if r=='U4' and n in ['3','5','9','15','17','18']:return 'input'
 if r=='U5':return {'1':'output','2':'power_in','3':'power_in','4':'bidirectional','5':'input','6':'input'}[n]
 if r=='U6':return {'1':'input','2':'power_in','3':'input','4':'power_in','5':'output','6':'input'}[n]
 if r=='U7':return {'1':'no_connect','2':'input','3':'power_in','4':'output','5':'power_in'}[n]
 if r=='U8':return 'output' if n in ['3','7'] else ('power_in' if n in ['4','8'] else 'input')
 if r in ['U10','U11']:return 'output' if n in ['3','6'] else ('power_in' if n in ['4','8'] else 'input')
 if r=='U1':return 'bidirectional'
 return 'passive'
def geometry(p):
 ps=[];pd=p['pads'];n=len(pd)
 if n==2:return [(-7.62,0,0),(7.62,0,180)],3.81
 rows=math.ceil(n/2);h=max(5.08,(rows+1)*2.54/2)
 for i in range(n):
  left=i<rows;j=i if left else i-rows
  ps.append((-15.24 if left else 15.24,h-2.54-j*2.54,0 if left else 180))
 return ps,h
def library_symbol(p):
 name=p['ref'];ps,h=geometry(p)
 s=f'(symbol "{name}" (pin_names (offset 0.7)) (in_bom {'no' if name.startswith('#') else 'yes'}) (on_board {'no' if name.startswith('#') else 'yes'})\n'
 s+=f'(property "Reference" "{name[0]}" (at 0 {h+2.54} 0) {effect})\n(property "Value" {q(p["value"])} (at 0 {h+5.08} 0) {effect})\n'
 if len(ps)==2:
  if p['ref'].startswith('C'):
   s+=f'(symbol "{name}_0_1" (polyline (pts (xy -1 -2) (xy -1 2)) (stroke (width 0.25) (type default)) (fill (type none))) (polyline (pts (xy 1 -2) (xy 1 2)) (stroke (width 0.25) (type default)) (fill (type none))))\n'
  else:s+=f'(symbol "{name}_0_1" (rectangle (start -3.81 -1.27) (end 3.81 1.27) (stroke (width 0.2) (type default)) (fill (type none))))\n'
 else:s+=f'(symbol "{name}_0_1" (rectangle (start -10.16 {-h}) (end 10.16 {h}) (stroke (width 0.2) (type default)) (fill (type background))))\n'
 s+=f'(symbol "{name}_1_1"\n'
 for pd,(x,y,a) in zip(p['pads'],ps):
  ln=6.62 if len(ps)==2 and p['ref'].startswith('C') else (3.81 if len(ps)==2 else 5.08)
  s+=f'(pin {typ(p,pd)} line (at {x} {y} {a}) (length {ln}) (name {q(pd["label"])} (effects (font (size .9 .9)))) (number {q(pd["n"])} (effects (font (size .9 .9)))))\n'
 return s+'))\n'
def sch_head(id,title,libs):
 return f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{id}") (paper "A3") (title_block (title {q(title)}) (date "2026-11-22") (rev "A"))\n(lib_symbols {libs})\n'
flags=[dict(ref='#FLG0'+str(i+1),value='PWR_FLAG',fp='',section='Power',pads=[dict(n='1',net=net,label='POWER')]) for i,net in enumerate(['GND','USB5F'])]
parts=parts+flags
sections=['Controller','Power','GNSS','Reference','Comb','Attenuator','RF path','Test','Reference outputs']
parent=sch_head(rootid,'CALINJECT - GPS-timed 10 MHz comb','')
parent+='(text "USB-C  ->  GNSS + TCXO servo  ->  10 MHz pulse comb  ->  attenuator  ->  directional injection" (at 30 20 0) (effects (font (size 2 2)) (justify left)) (uuid "'+uid('title')+'"))\n'
for si,sec in enumerate(sections):
 pp=[p for p in parts if p['section']==sec];sid=uid('sheet/'+sec);file=sec.lower().replace(' ','_')+'.kicad_sch';content=sch_head(sid,'CALINJECT / '+sec,''.join(library_symbol(p).replace('(symbol "'+p['ref']+'"','(symbol "Calinject:'+p['ref']+'"',1) for p in pp))
 # 4 columns, large ICs use upper row with sufficient room for pin labels.
 for i,p in enumerate(pp):
  x=50.8+96.52*(i%4);y=55.88+58.42*(i//4);ps,h=geometry(p);inst=uid('inst/'+p['ref'])
  content+=f'(symbol (lib_id "Calinject:{p["ref"]}") (at {x} {y} 0) (unit 1) (in_bom {'no' if p['ref'].startswith('#') else 'yes'}) (on_board {'no' if p['ref'].startswith('#') else 'yes'}) (dnp no) (uuid "{inst}")\n'
  for pn,pv,dy in [('Reference',p['ref'],-h-4.5),('Value',p['value'],-h-2),('Footprint',('Calinject:'+p['fp'] if p['fp'] else ''),h+2)]:
   content+=f'(property "{pn}" {q(pv)} (at {x} {y+dy} 0) (effects (font (size 1 1))'+(' (hide yes)' if pn=='Footprint' else '')+'))\n'
  for pd in p['pads']:content+=f'(pin {q(pd["n"])} (uuid "{uid(inst+pd["n"])}"))\n'
  content+=f'(instances (project "calinject" (path "/{rootid}/{sid}" (reference "{p["ref"]}") (unit 1)))))\n'
  for pd,(px,py,ang) in zip(p['pads'],ps):
   xx=x+px;yy=y-py
   if pd['net']:
    end=xx+(-3.81 if ang==0 else 3.81)
    content+=f'(wire (pts (xy {xx} {yy}) (xy {end} {yy})) (stroke (width 0) (type default)) (uuid "{uid(inst+pd["n"]+"w")}"))\n'
    # global label anchor at wire tip, text extends away from component
    la=0 if ang==0 else 180
    content+=f'(global_label {q(pd["net"])} (shape passive) (at {end} {yy} {la}) (effects (font (size .85 .85)) (justify '+('right' if la==0 else 'left')+f')) (uuid "{uid(inst+pd["n"]+"label")}"))\n'
   else:content+=f'(no_connect (at {xx} {yy}) (uuid "{uid(inst+pd["n"]+"nc")}"))\n'
 content+=')\n';(ROOT/'cad'/file).write_text(content)
 x=25+(si%4)*96;y=45+(si//4)*60
 parent+=f'(sheet (at {x} {y}) (size 80 40) (stroke (width .2) (type default)) (fill (color 0 0 0 0)) (uuid "{sid}") (property "Sheetname" {q(sec)} (at {x} {y-2} 0) (effects (font (size 1.5 1.5)) (justify left))) (property "Sheetfile" {q(file)} (at {x} {y+42} 0) (effects (font (size 1 1)) (justify left))) (instances (project "calinject" (path "/{rootid}" (page "{si+2}")))))\n'
parent+=')\n';(ROOT/'cad/calinject.kicad_sch').write_text(parent)
(ROOT/'cad/Calinject.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")\n'+''.join(library_symbol(p) for p in parts if p['section'] in sections)+')\n')
(ROOT/'cad/sym-lib-table').write_text('(sym_lib_table (lib (name "Calinject")(type "KiCad")(uri "${KIPRJMOD}/Calinject.kicad_sym")(options "")(descr "Calinject circuit symbols")))\n')
(ROOT/'cad/fp-lib-table').write_text('(fp_lib_table (lib (name "Calinject")(type "KiCad")(uri "${KIPRJMOD}/Calinject.pretty")(options "")(descr "Calinject footprints")))\n')
print('Schematic generated:',len(sections)+1,'sheets')
