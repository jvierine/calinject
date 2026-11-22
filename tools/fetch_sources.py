# Developer reference downloads, excluded from redistributable design package.
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request
root=Path(__file__).resolve().parents[1]/'references'
urls={
'ecs-vctcxo.pdf':'https://ecsxtal.com/store/pdf/ECS-TXO32-S3.pdf',
'tlv3501.pdf':'https://www.ti.com/lit/ds/symlink/tlv3501.pdf',
'lvc14.pdf':'https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf',
'lvc2g08.pdf':'https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf',
'rpzero.pdf':'https://files.waveshare.com/upload/4/4c/RP2040_Zero.pdf',
'mcp4725.pdf':'https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP4725-12-Bit-Digital-to-Analog-Converter-with-EEPROM-Memory-DS20002039.pdf'}
def f(item):
 name,url=item
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  data=urllib.request.urlopen(req,timeout=90).read()
  if not data.startswith(b'%PDF'):raise ValueError('not PDF')
  (root/name).write_bytes(data);print(name,len(data),flush=True)
 except Exception as e:print(name,type(e).__name__,flush=True)
with ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(f,urls.items()))
