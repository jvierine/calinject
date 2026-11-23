import sys,pathlib,unittest
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'host'))
from tracking import FrequencyTrack
from calibration import tone_frequency,tone_frequency_robust

class TrackingTest(unittest.TestCase):
 def test_chirp_correction_and_no_knot_phase_steps(self):
  t=np.linspace(0,20,20001);track=FrequencyTrack([0,5,10,20],[3,4,5,7])
  phase=3*t+.1*t*t
  np.testing.assert_allclose(track.phase_cycles(t),phase,atol=1e-12)
  np.testing.assert_allclose(track.correct(np.exp(2j*np.pi*phase),t),1,atol=1e-10)
  for knot in [5,10]:
   p=track.phase_cycles([knot-1e-9,knot+1e-9]);self.assertLess(abs(p[1]-p[0]),2e-8)
 def test_endpoint_hold_and_invalid_inputs(self):
  track=FrequencyTrack([0,1],[1,3]);np.testing.assert_allclose(track.phase_cycles([-1,1,2]),[-1,2,5])
  for t,f in [([0,0],[1,2]),([0,1],[1,np.nan]),([0],[1])]:
   with self.assertRaises(ValueError):FrequencyTrack(t,f)
 def test_coherent_estimator_with_phase_outlier(self):
  t=np.arange(2000)/1e6
  for f in [12345.67,-12345.67]:
   x=np.exp(2j*np.pi*f*t+.7j);x[1000]*=-1
   recovered=tone_frequency_robust(x,1e6)
   self.assertLess(abs(recovered['baseband_hz']-f),.02)
   self.assertGreater(recovered['coherence'],.99)
   self.assertGreater(abs(tone_frequency(x,1e6)['baseband_hz']-f),100)
 def test_reference_observer_across_counter_rollover(self):
  sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
  from end_to_end import Plant
  from simulate_reference_tracking import ReferenceObserver
  plant=Plant(seconds=600)
  observer=ReferenceObserver(plant.captures,plant.codes,plant.valid)
  self.assertTrue(np.any(np.diff(np.asarray(plant.captures,dtype=np.int64))<0))
  for t in [128.3,256.3,480.3,560.3]:
   self.assertLess(abs(observer.estimate(t)-plant.at(t)[1]),.03)
if __name__=='__main__':unittest.main()
