import unittest,sys,struct,pathlib,ast
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'firmware'),str(ROOT/'host')]
from protocol import Parser,packet,timepulse,Servo,CONFIG,valset
from calibration import fit_clock,tone_frequency,rf_frequency,match_template

class ProtocolTest(unittest.TestCase):
 def test_chunked_noise_and_corruption(self):
  p=Parser();good=packet(13,1,bytes(range(16)));bad=bytearray(good);bad[-1]^=1
  stream=b'noise'+bad+good+packet(1,7,b'abc');out=[]
  for c in stream:out+=p.feed(bytes([c]))
  self.assertEqual(out,[(13,1,bytes(range(16))),(1,7,b'abc')]);self.assertEqual(p.bad,1)
 def test_bounded_oversize(self):
  p=Parser();p.feed(b'\xb5\x62\x01\x01\xff\xff00'+b'x'*4096);self.assertLess(len(p.buf),8)
 def test_utc_flags(self):
  def tp(flags=3,tow=1000):return timepulse(struct.pack('<IIiHBB',tow,0,-100,2446,flags,0))
  self.assertTrue(tp()['valid'])
  for f in [0,1,2,0x13,0x23,0x33]:self.assertFalse(tp(f)['valid'])
  self.assertFalse(tp(tow=1001)['valid'])
 def test_config_frame(self):
  self.assertEqual(Parser().feed(valset(CONFIG))[0][:2],(6,0x8a))
 def test_servo_simulated_convergence_and_loss(self):
  s=Servo(code=1900);phase=2**32-10;c=int(phase);s.step(c,True)
  for second in range(1024):
   phase+=1e7+(s.code-1800)*s.slope;s.step(int(phase)&0xffffffff,True)
  self.assertLess(abs(s.code-1800),3);self.assertEqual(s.state,'TRACKING')
  s.step(0,False);self.assertEqual(s.state,'HOLDOVER');self.assertIsNone(s.prev)
 def test_servo_count_fault(self):
  s=Servo();s.step(0,True);s.step(12345,True);self.assertEqual(s.state,'COUNT_FAULT')

class AnalysisTest(unittest.TestCase):
 def test_clock_missing_seconds_and_drift(self):
  rng=np.random.default_rng(123);t=np.arange(120,dtype=float);t=np.delete(t,[2,21,22]);fs=64e6*(1+2.5e-6)
  n=123.25+fs*t+rng.normal(0,.05,len(t));r=fit_clock(n,t+1780000000,64e6)
  self.assertLess(abs(r['sample_rate_error_ppm']-2.5),.00001)
  self.assertLess(abs(r['anchor_sample']-123.25),.02)
 def test_drop_is_visible(self):
  t=np.arange(20.);n=t*2e6;n[10:]-=4096;r=fit_clock(n,t,2e6)
  self.assertGreater(max(abs(r['residual_samples'])),1000)
 def test_short_burst_lo_correction(self):
  fs=2e6;t=np.arange(160)/fs;f=-12345.67;r=tone_frequency(np.exp(2j*np.pi*f*t),fs)
  self.assertAlmostEqual(r['baseband_hz'],f,places=6);self.assertAlmostEqual(rf_frequency(20000,r['baseband_hz'],40e6),40032345.67)
 def test_measured_template_phase_invariance(self):
  rng=np.random.default_rng(4);h=np.hanning(128)*np.exp(2j*np.pi*.13*np.arange(128));x=.005*(rng.normal(size=4096)+1j*rng.normal(size=4096))
  for p in [200,1600,3000]:x[p:p+len(h)]+=h*np.exp(.7j)
  n,score=match_template(x,h,1000,.8);np.testing.assert_allclose(n,[200,1600,3000],atol=.15)

# Instruction-level simulator obtains the actual PIO program bodies from source.
# GPIO synchronization delays/metastability and analogue edges require bench tests.
def program(name):
 tree=ast.parse((ROOT/'firmware/main.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
 inst=[];labels={}
 env={n:n for n in ['x','null','isr','osr','pins','gpio','pin','x_dec','block','noblock']}
 for op in ['mov','wait','jmp','push','pull','set']:
  env[op]=(lambda op:lambda *args:inst.append((op,args)))(op)
 env['invert']=lambda x:('invert',x);env['label']=lambda n:labels.update({n:len(inst)});env['wrap']=lambda:None
 exec(compile(ast.Module(body=fn.body,type_ignores=[]),'<pio>','exec'),env)
 return inst,labels

def simulate(name,cycles,clk_phase=0,pps_period=12500,pps_width=1250,descriptor=12498):
 inst,labels=program(name);pc=0;x=0;isr=0;osr=0;tx=[descriptor];out=[];edges=[];gate=0
 for tick in range(cycles):
  op,a=inst[pc];nextpc=pc+1
  # 125MHz logic clock, asynchronous10MHz reference represented on sample grid.
  clk=int(((tick+clk_phase)*8)%100>=50);pps=int(tick%pps_period<pps_width and tick>=pps_period)
  def val(a):
   if isinstance(a,tuple):return (~val(a[1]))&0xffffffff
   return {'x':x,'null':0,'isr':isr,'osr':osr}[a]
  if op=='wait':
   if (clk if a[2]==11 else pps)!=a[0]:nextpc=pc
  elif op=='jmp':
   if len(a)==1:nextpc=labels[a[0]]
   elif a[0]=='pin':
    if pps:nextpc=labels[a[1]]
   elif a[0]=='x_dec':
    take=x!=0;x=(x-1)&0xffffffff
    if take:nextpc=labels[a[1]]
  elif op=='mov':
   v=val(a[1])
   if a[0]=='x':x=v
   elif a[0]=='isr':isr=v
  elif op=='push':out.append((tick,isr))
  elif op=='pull':
   if tx:osr=tx.pop(0)
   else:nextpc=pc
  elif op=='set':
   if gate!=a[1]:gate=a[1];edges.append((tick,gate))
  pc=nextpc%len(inst)
 return out,edges

class PIOTest(unittest.TestCase):
 def test_memory_capacity(self):self.assertLessEqual(sum(len(program(n)[0]) for n in ['counter','burst']),32)
 def test_no_clock_edges_lost(self):
  for phase in range(13):
   out,_=simulate('counter',90000,clk_phase=phase)
   self.assertEqual(len(out),7)
   self.assertTrue(all(b[1]-a[1]==1000 for a,b in zip(out,out[1:])))
 def test_burst_width_and_starvation(self):
  _,edges=simulate('burst',90000)
  self.assertEqual(len(edges),2);self.assertEqual(edges[1][0]-edges[0][0],12500)
  self.assertLessEqual(edges[0][0]-12500,1)
if __name__=='__main__':unittest.main(verbosity=2)
