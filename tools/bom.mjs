// Assembly workbooks, generated from the circuit manifest. Coordinates are KiCad
// absolute origin: X right, Y up, viewed from top; all components top side.
import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
const root=process.env.CALINJECT_ROOT ? new URL('file://'+process.env.CALINJECT_ROOT.replace(/\/$/,'')+'/') : new URL('../',import.meta.url);
const data=JSON.parse(await fs.readFile(new URL('cad/design.json',root),'utf8'));
const parts=data.parts.filter(p=>!['PCB','MECHANICAL'].includes(p.assembly));
const groups=new Map();
for(const p of parts){const key=p.mpn+'|'+p.value;const a=groups.get(key)||[];a.push(p);groups.set(key,a);}
const bom=[['Designator','Comment','Footprint','Manufacturer','Manufacturer Part','Quantity','Assembly','LCSC Part #']];
for(const g of groups.values()){let p=g[0];bom.push([g.map(x=>x.ref).join(','),p.value,p.fp.replace(/_[A-Z]+\d+$/,''),p.maker,p.ref==='JP1'?'68000-103HLF':p.mpn,p.ref==='JP1'?2:g.length,p.assembly,p.ref.startsWith('J')&&p.ref!='JP1'?'C496549':'']);}
const cpl=[['Designator','Mid X (mm)','Mid Y (mm)','Layer','Rotation']];
for(const p of parts.filter(p=>p.assembly==='SMT'))cpl.push([p.ref,p.x,-p.y,'Top',p.rot]);
for(const [name,rows,widths] of [['BOM',bom,[60,25,28,25,42,12,20,15]],['CPL',cpl,[15,18,18,12,14]]]){
 const wb=Workbook.create(),sh=wb.worksheets.add(name);sh.showGridLines=false;
 sh.getRangeByIndexes(0,0,rows.length,rows[0].length).values=rows;
 sh.getUsedRange().format.font={name:'Arial',size:10};sh.getUsedRange().format.rowHeight=20;
 sh.getRangeByIndexes(0,0,1,rows[0].length).format={fill:'#254559',font:{bold:true,color:'#FFFFFF'},rowHeight:26};
 widths.forEach((w,i)=>sh.getRangeByIndexes(0,i,rows.length,1).format.columnWidth=w);sh.freezePanes.freezeRows(1);
 if(name==='BOM'){
  const extra=[['Used with','Assembly material','Manufacturer / part','Quantity per board'],['U1','1x9 male header,2.54mm spacer','Harwin M20-9990946',2],['U1','1x5 male header,2.54mm spacer','Harwin M20-9990546',1],['JP1','2.54mm shorting shunt','Assembler to propose matching closed-top shunt',2]];
  const a=wb.worksheets.add('Assembly materials');a.getRange('A1:D4').values=extra;
  a.getUsedRange().format.font={name:'Arial',size:10};a.getUsedRange().format.rowHeight=24;
  a.getRange('A1:D1').format={fill:'#254559',font:{bold:true,color:'#FFFFFF'}};
  [18,48,60,24].forEach((w,i)=>a.getRangeByIndexes(0,i,4,1).format.columnWidth=w);a.freezePanes.freezeRows(1);
 }
 if(name==='CPL')sh.getRange(`B2:C${rows.length}`).setNumberFormat('0.000');
 wb.recalculate();console.log((await wb.inspect({kind:'table',range:`${name}!A1:H5`,tableMaxRows:5,tableMaxCols:8,maxChars:2000})).ndjson);
 console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#VALUE!|#DIV/0!',options:{useRegex:true,maxResults:20}})).ndjson);
 const preview=await wb.render({sheetName:name,range:name==='BOM'?'A1:H13':'A1:E15',scale:1,format:'png'});
 await fs.writeFile(new URL(`validation/${name.toLowerCase()}-preview.png`,root),new Uint8Array(await preview.arrayBuffer()));
 await (await SpreadsheetFile.exportXlsx(wb)).save(new URL(`manufacturing/${name}.xlsx`,root).pathname);
 await fs.writeFile(new URL(`manufacturing/${name}.json`,root),JSON.stringify(rows,null,2)+'\n');
}
