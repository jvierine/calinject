import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'firmware'))
from status_led import StatusLED,GREEN,RED,OFF,AMBER

def diff(a,b):return ((a-b+(1<<29))%(1<<30))-(1<<29)
class IndicatorTest(unittest.TestCase):
 def test_fault_overrides_locked_flash_and_recovers(self):
  writes=[];led=StatusLED(writes.append,diff)
  self.assertEqual(led.update(10000,0,True,10000,10000,'TRACKING'),'LOCKED')
  self.assertEqual(writes[-1],GREEN)
  self.assertEqual(led.update(10000,0,True,10000,10000,'TRACKING',True),'FAULT')
  self.assertEqual(writes[-1],RED)
  led.update(10250,0,True,10000,10000,'DAC_LIMIT');self.assertEqual(writes[-1],OFF)
  led.update(11000,0,True,11000,11000,'TRACKING');self.assertEqual(writes[-1],GREEN)
 def test_pps_flash_and_loss_across_tick_wrap(self):
  writes=[];led=StatusLED(writes.append,diff);wrap=1<<30;pps=wrap-50
  led.update(0,wrap-1000,True,pps,pps,'TRACKING');self.assertEqual(writes[-1],GREEN)
  led.update(60,wrap-1000,True,pps,pps,'TRACKING');self.assertEqual(writes[-1],OFF)
  self.assertEqual(led.update(1600,wrap-1000,True,pps,pps,'TRACKING'),'FAULT')
 def test_no_fast_led_rewrites_while_acquiring(self):
  writes=[];led=StatusLED(writes.append,diff)
  for ms in range(0,1000,2):led.update(ms,0,False,None,None,'ACQUIRE')
  self.assertEqual(writes,[GREEN])
  for ms in range(1000,2000,2):led.update(ms,0,True,None,None,'ACQUIRE')
  self.assertEqual(writes,[GREEN,AMBER])
