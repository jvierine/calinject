"""KDS pull/load endpoints exercise the actual firmware loop in the RC plant."""
import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from end_to_end import Plant

class KdsPlantTests(unittest.TestCase):
 def test_pull_and_loading_endpoints(self):
  for gain in (80.,150.):
   for load in (500e3,1e12):
    for offset in (-15.,15.):
     with self.subTest(gain=gain,load=load,offset=offset):
      p=Plant(kv=gain,load=load,initial_offset_hz=offset)
      vc=p.states[:,1]
      self.assertTrue(np.all((vc>=.5)&(vc<=2.5)))
      self.assertLess(np.max(abs(p.err[-256:])),.5)
      self.assertFalse(np.any((p.codes==700)|(p.codes==3000)))

if __name__=='__main__':unittest.main()
