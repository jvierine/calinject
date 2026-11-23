"""Compile application bytecode and assemble PIO with upstream MicroPython 1.29.
This is source/compiler verification, not execution on physical RP2040 hardware.
"""
from pathlib import Path
import ast,hashlib,importlib.util,json,subprocess,sys,tempfile,types,urllib.request
ROOT=Path(__file__).resolve().parents[1]
URL='https://raw.githubusercontent.com/micropython/micropython/v1.29.0/ports/rp2/modules/rp2.py'
raw=urllib.request.urlopen(URL,timeout=30).read()
assert hashlib.sha256(raw).hexdigest()=='5a9dc4e48ce272395768ac7273cf5e5ee48b36af5323f457c0d0c99e1ebcaf68','Upstream assembler changed'
native=types.ModuleType('_rp2')
native.PIO=type('PIO',(),dict(SHIFT_LEFT=0,SHIFT_RIGHT=1,JOIN_NONE=0,OUT_LOW=0))
micro=types.ModuleType('micropython');micro.const=lambda n:n
sys.modules['_rp2']=native;sys.modules['micropython']=micro
rp2=types.ModuleType('verified_rp2_assembler');exec(compile(raw,URL,'exec'),rp2.__dict__)
tree=ast.parse((ROOT/'firmware/main.py').read_text());functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['counter','burst']]
env={'rp2':rp2};exec(compile(ast.Module(body=functions,type_ignores=[]),'<actual-firmware-pio>','exec'),env)
programs={name:[int(x) for x in env[name][0]] for name in ['counter','burst']}
assert sum(map(len,programs.values()))<=32
out=ROOT/'validation/firmware-mpy';out.mkdir(exist_ok=True)
compiler_version=subprocess.check_output([sys.executable,'-m','mpy_cross','--version'],text=True).strip()
for name in ['main','protocol','telemetry','settings']:
 subprocess.run([sys.executable,'-m','mpy_cross','-o',str(out/(name+'.mpy')),str(ROOT/'firmware'/(name+'.py'))],check=True)
report=dict(compiler=compiler_version,pio_assembler_url=URL,pio_assembler_sha256=hashlib.sha256(raw).hexdigest(),
 programs=programs,total_pio_words=sum(map(len,programs.values())),on_device_execution=False,
 sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'firmware').glob('*.py'))},
 compiled={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.mpy'))})
(ROOT/'validation/firmware-compile.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
