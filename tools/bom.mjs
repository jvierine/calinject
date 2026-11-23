// Assembly workbooks, generated from the circuit manifest. Coordinates are KiCad
// absolute origin: X right, Y up, viewed from top; all components top side.
import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
const root=process.env.CALINJECT_ROOT ? new URL('file://'+process.env.CALINJECT_ROOT.replace(/\/$/,'')+'/') : new URL('../',import.meta.url);
const data=JSON.parse(await fs.readFile(new URL('cad/design.json',root),'utf8'));
const sourcing=JSON.parse(await fs.readFile(new URL('manufacturing/sourcing.json',root),'utf8'));
const jlc=process.argv.includes('--jlc');
const out=jlc?'manufacturing/jlc-turnkey':'manufacturing';
await fs.mkdir(new URL(out+'/',root),{recursive:true});
let parts=data.parts.filter(p=>!['PCB','MECHANICAL'].includes(p.assembly));
if(jlc){
 parts=parts.filter(p=>p.ref!=='JP1');
 const add=(ref,value,mpn,maker,x,y,rot,fp)=>parts.push({ref,value,mpn,maker,x,y,rot,fp,assembly:'MANUAL ASSEMBLY'});
 const mat=(ref,key,value,x,y,rot,fp)=>{const m=sourcing.materials[key];add(ref,value,m.mpn,m.maker,x,y,rot,fp);parts.at(-1).lcsc=m.lcsc;};
 mat('U1_HL','header9','U1 left 1x9 header',9.38,12,90,'Header_1x9_P2.54');
 mat('U1_HR','header9','U1 right 1x9 header',24.62,12,90,'Header_1x9_P2.54');
 mat('U1_HB','header5','U1 bottom 1x5 header',17,22.16,0,'Header_1x5_P2.54');
 for(const [ref,y] of [['JP1_A',45.73],['JP1_B',48.27]])mat(ref,'header3','JP1 1x3 header',64,y,0,'Header_1x3_P2.54');
 for(const [ref,y] of [['JP1_S1',45.73],['JP1_S2',48.27]])mat(ref,'shunt','Closed-top 2.54mm shunt',62.73,y,0,'Shunt_P2.54');
}
const groups=new Map();
for(const p of parts){const key=p.mpn+'|'+p.value;const a=groups.get(key)||[];a.push(p);groups.set(key,a);}
const bom=[['Designator','Comment','Footprint','Manufacturer','Manufacturer Part','Quantity','Assembly','LCSC Part #']];
for(const g of groups.values()){let p=g[0];const selected=sourcing.parts[p.ref];if(selected&&selected.mpn!==p.mpn)throw Error('Sourcing/manifest mismatch '+p.ref);bom.push([g.map(x=>x.ref).join(','),p.value,p.fp.replace(/_[A-Z]+\d+$/,''),p.maker,p.ref==='JP1'?sourcing.materials.header3.mpn:p.mpn,p.ref==='JP1'?2:g.length,p.assembly,p.lcsc||selected?.lcsc||(p.mpn==='BWSMA-KE-Z001'?'C496549':'')]);}
const cpl=[['Designator','Mid X (mm)','Mid Y (mm)','Layer','Rotation']];
// JLC matches Comment and its own part column; use exact MPNs rather than
// engineering shorthand such as "249", which its matcher interpreted as 2.49k.
if(jlc){
 bom[0][4]='Manufacturer Part Number';
 bom[0][7]='JLCPCB Part #';
 for(const row of bom.slice(1))row[1]=row[4];
}
for(const p of parts.filter(p=>jlc||p.assembly==='SMT'))cpl.push([p.ref,p.x,-p.y,'Top',p.rot]);
if(jlc){
 const refs=bom.slice(1).flatMap(r=>r[0].split(','));
 if(refs.length!==95||new Set(refs).size!==95||cpl.length!==96||refs.some(r=>!cpl.some(c=>c[0]===r)))throw Error('Incomplete turnkey assembly mapping');
}
for(const [name,rows,widths] of [['BOM',bom,[60,25,28,25,42,12,20,15]],['CPL',cpl,[15,18,18,12,14]]]){
 const wb=Workbook.create(),sh=wb.worksheets.add(name);sh.showGridLines=false;
 sh.getRangeByIndexes(0,0,rows.length,rows[0].length).values=rows;
 sh.getUsedRange().format.font={name:'Arial',size:10};sh.getUsedRange().format.rowHeight=20;
 sh.getRangeByIndexes(0,0,1,rows[0].length).format={fill:'#254559',font:{bold:true,color:'#FFFFFF'},rowHeight:26};
 widths.forEach((w,i)=>sh.getRangeByIndexes(0,i,rows.length,1).format.columnWidth=w);sh.freezePanes.freezeRows(1);
 if(name==='BOM'&&!jlc){
  const extra=[['Used with','Assembly material','Manufacturer / part','Quantity per board'],['U1','1x9 male header,2.5mm spacer','FG '+sourcing.materials.header9.mpn,2],['U1','1x5 male header,2.5mm spacer','FG '+sourcing.materials.header5.mpn,1],['JP1','2.54mm shorting shunt','BOOMELE '+sourcing.materials.shunt.mpn,2]];
  const a=wb.worksheets.add('Assembly materials');a.getRange('A1:D4').values=extra;
  a.getUsedRange().format.font={name:'Arial',size:10};a.getUsedRange().format.rowHeight=24;
  a.getRange('A1:D1').format={fill:'#254559',font:{bold:true,color:'#FFFFFF'}};
  [18,48,60,24].forEach((w,i)=>a.getRangeByIndexes(0,i,4,1).format.columnWidth=w);a.freezePanes.freezeRows(1);
 }
 if(name==='CPL')sh.getRange(`B2:C${rows.length}`).setNumberFormat('0.000');
 wb.recalculate();console.log((await wb.inspect({kind:'table',range:`${name}!A1:H5`,tableMaxRows:5,tableMaxCols:8,maxChars:2000})).ndjson);
 console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#VALUE!|#DIV/0!',options:{useRegex:true,maxResults:20}})).ndjson);
 const preview=await wb.render({sheetName:name,range:name==='BOM'?'A1:H13':'A1:E15',scale:1,format:'png'});
 await fs.writeFile(new URL(`validation/${jlc?'jlc-':''}${name.toLowerCase()}-preview.png`,root),new Uint8Array(await preview.arrayBuffer()));
 await (await SpreadsheetFile.exportXlsx(wb)).save(new URL(`${out}/${name}.xlsx`,root).pathname);
 await fs.writeFile(new URL(`${out}/${name}.json`,root),JSON.stringify(rows,null,2)+'\n');
}
