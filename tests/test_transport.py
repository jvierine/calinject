import unittest,sys,pathlib,tempfile,json
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'firmware'))
from telemetry import Telemetry
import settings

class Sink:
 def __init__(self):self.capacity=0;self.output='';self.calls=0
 def writable(self):return self.capacity>0
 def write(self,s):
  assert len(s)==1 and ord(s)<128 and self.capacity>0
  self.capacity-=1;self.calls+=1;self.output+=s;return 1

class TransportTest(unittest.TestCase):
 def test_stalled_host_is_bounded_and_does_not_write(self):
  s=Sink();t=Telemetry(s,s.writable)
  for n in range(10000):t.enqueue(json.dumps(dict(seq=n)));self.assertEqual(t.pump(),0)
  self.assertEqual(len(t.frames),8);self.assertEqual(t.dropped,9992);self.assertEqual(s.calls,0)
 def test_partial_frame_survives_overflow_then_reconnect(self):
  s=Sink();t=Telemetry(s,s.writable,max_frames=3)
  t.enqueue('{"seq":0}');s.capacity=3;t.pump()
  for n in range(1,10):t.enqueue(json.dumps(dict(seq=n)))
  s.capacity=1000
  while t.frames:t.pump(4)
  self.assertEqual([json.loads(x)['seq'] for x in s.output.splitlines()],[0,8,9])
  self.assertEqual(t.dropped,7)
 def test_write_checks_capacity_for_every_byte(self):
  s=Sink();t=Telemetry(s,s.writable);t.enqueue('{"ok":true}')
  for n in range(12):s.capacity=1;self.assertEqual(t.pump(64),1)
  self.assertFalse(t.frames);self.assertEqual(json.loads(s.output),{'ok':True})
 def test_oversized_or_multibyte_frames_are_dropped_whole(self):
  s=Sink();t=Telemetry(s,s.writable,max_frame=8)
  self.assertFalse(t.enqueue('x'*8));self.assertFalse(t.enqueue('é'));self.assertFalse(t.frames)

class SettingsTest(unittest.TestCase):
 def test_round_trip_and_atomic_temp_file(self):
  with tempfile.TemporaryDirectory() as d:
   p=str(pathlib.Path(d)/'settings.json');v=dict(settings.DEFAULTS);v.update(width_us=250,ref10=True)
   settings.save(v,p);self.assertEqual(settings.load(p),(v,True))
   pathlib.Path(p+'.tmp').write_text('{partial')
   self.assertEqual(settings.load(p),(v,True))
 def test_corrupt_or_unknown_schema_uses_safe_defaults(self):
  with tempfile.TemporaryDirectory() as d:
   p=str(pathlib.Path(d)/'settings.json')
   for data in ['{',json.dumps({'ref10':True}),json.dumps(dict(settings.DEFAULTS,width_us=-1))]:
    pathlib.Path(p).write_text(data);self.assertEqual(settings.load(p),(settings.DEFAULTS,False))
 def test_invalid_setting_cannot_replace_good_file(self):
  with tempfile.TemporaryDirectory() as d:
   p=str(pathlib.Path(d)/'settings.json');settings.save(settings.DEFAULTS,p)
   with self.assertRaises(ValueError):settings.save(dict(settings.DEFAULTS,slope=float('nan')),p)
   self.assertEqual(settings.load(p),(settings.DEFAULTS,True))

if __name__=='__main__':unittest.main()
