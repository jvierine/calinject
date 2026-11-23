"""Create reproducible-scope prototype source and factory quotation archives."""
from pathlib import Path
import subprocess,json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist';OUT.mkdir(exist_ok=True)
# Use Git's ignore rules to exclude downloaded vendor PDFs, caches and alternatives.
paths=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
paths=sorted({p for p in paths if p and (ROOT/p).is_file()})
assert not any(p.endswith('.csv') for p in paths)
factory_prefixes=('cad/','manufacturing/','firmware/','host/','mechanical/','docs/','validation/')
for name,selected in [
 ('calinject-revC-complete-design',paths),
 ('calinject-revC-JLC-turnkey-build',[p for p in paths if p in ['README.md','LICENSE','requirements.txt'] or p.startswith(factory_prefixes)]),
]:
 manifest={'package':name,'revision':'C','status':'Design package ready for factory first-article build; hardware qualification not yet performed','quantity':5,'files':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in selected}}
 archive=OUT/(name+'.zip')
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in selected:z.write(ROOT/p,p)
  z.writestr('MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
 print(archive.name,archive.stat().st_size,'bytes',len(selected),'files')
checksums={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('calinject-revC-*.zip')) if p.name in ['calinject-revC-complete-design.zip','calinject-revC-JLC-turnkey-build.zip']}
(OUT/'SHA256SUMS.json').write_text(json.dumps(checksums,indent=2)+'\n')
