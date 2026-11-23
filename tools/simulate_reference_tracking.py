"""Offline reference-frequency observer using only simulated telemetry/design.
Truth is used for scoring, never for the frequency estimate. The calibrated
DAC/VCO gain and RC model are assumptions; gain-error sensitivity is included.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import h5py
from scipy.linalg import expm
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from end_to_end import Plant,F0
OUT=ROOT/'validation/end-to-end'

class ReferenceObserver:
 def __init__(self,counts,codes,valid,gain=100):
  self.gain=gain;self.codes=np.asarray(codes);self.valid=np.r_[True,valid];self.epochs=np.arange(len(counts),dtype=float)
  # Captures are consecutive seconds here. For missing telemetry, unwrap must
  # use explicit epoch differences to resolve extra whole counter rollovers.
  delta=(np.diff(np.asarray(counts,dtype=np.int64))%2**32).astype(float)
  observed=np.r_[0,np.cumsum(delta)]-F0*self.epochs
  r=1000.;c=4.7e-6;load=500e3
  self.A=np.array([[-2/(r*c),1/(r*c)],[1/(r*c),-(1/r+1/load)/c]])
  self.B=np.array([1/(r*c),0]);self.inv=np.linalg.inv(self.A);self.E=expm(self.A);self.eigen=np.sort(np.linalg.eigvals(self.A))
  state=-self.inv@self.B*(self.codes[0]*3.3/4096);states=[];area=[0.]
  for code in self.codes:
   states.append(state.copy());steady=-self.inv@self.B*(code*3.3/4096)
   integral=steady+self.inv@(self.E-np.eye(2))@(state-steady)
   area.append(area[-1]+integral[1]);state=steady+self.E@(state-steady)
  self.states=np.array(states);self.area=np.array(area)
  self.residual=observed-gain*self.area
 def control(self,t):
  i=int(np.floor(t));dt=t-i;state=self.states[i];steady=-self.inv@self.B*(self.codes[i]*3.3/4096)
  l1,l2=self.eigen;z=state[1]-steady[1];d=(self.A@state+self.B*(self.codes[i]*3.3/4096))[1]
  c1=(d-l2*z)/(l1-l2);c2=z-c1
  return steady[1]+c1*np.exp(l1*dt)+c2*np.exp(l2*dt)
 def estimate(self,t,window=64):
  use=(abs(self.epochs-t)<=window/2)&self.valid
  if np.sum(use)<24:raise ValueError('insufficient valid GPS captures')
  x=self.epochs[use]-t;y=self.residual[use];y=y-y[0]
  coeff=np.polynomial.polynomial.polyfit(x,y,2)
  return float(coeff[1]+self.gain*self.control(t))

def main():
 plant=Plant();source=OUT/'results.h5';summary=json.loads((OUT/'summary.json').read_text())
 with h5py.File(source) as h:np.testing.assert_allclose(h['plant/dac_code'][:],plant.codes,atol=0)
 cases=[]
 with h5py.File(OUT/'reference-tracking.h5','w') as h:
  h.attrs['generator']='tools/simulate_reference_tracking.py';h.attrs['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
  h['counter_capture_uint32']=np.array(plant.captures,dtype=np.uint32);h['counter_valid']=np.r_[True,plant.valid]
  for gain_error in [0.,-.1,.1]:
   observer=ReferenceObserver(plant.captures,plant.codes,plant.valid,gain=100*(1+gain_error))
   for row in summary['cases']:
    if row['fault'] is not None or row['edge_jitter_assumed_ps']!=20 or row['phase_noise_margin_db']!=0:continue
    name='%s_%sus_%sdb'%(row['profile'],row['width_us'],row['attenuation_db'])
    with h5py.File(source) as src:
     epochs=src[name+'/utc_s'][:]+row['width_us']*1e-6/2
     harmonic={'HF25':1,'HF50':4,'meteor':7}[row['profile']]
     truth=src[name+'/reference_frequency_error_hz'][:]/harmonic
     uncorrected=src[name+'/science_frequency_error_hz'][:]
    estimated=np.array([observer.estimate(t) for t in epochs]);corrected=uncorrected+harmonic*estimated
    case=dict(profile=row['profile'],width_us=row['width_us'],attenuation_db=row['attenuation_db'],gain_error_fraction=gain_error,reference_estimate_error_rms_hz=float(np.sqrt(np.mean((estimated-truth)**2))),science_error_before_rms_hz=float(np.sqrt(np.mean(uncorrected**2))),science_error_after_rms_hz=float(np.sqrt(np.mean(corrected**2))))
    cases.append(case);g=h.create_group('gain_%s/'%gain_error+name);g['utc_s']=epochs;g['reference_estimate_hz']=estimated;g['reference_truth_hz']=truth;g['corrected_science_error_hz']=corrected
  result=dict(method='64s centered quadratic phase fit after subtracting reconstructed DAC phase; offline/noncausal',gain_sensitivity=[-.1,0,.1],truth_used_for_estimation=False,assumptions='Calibrated VCO slope and known loaded RC dynamics; ADC/UBX model as in parent run. No tracking across unresolved UTC labels. Supply-to-frequency noise and unmodeled tuning nonlinearity are excluded.',cases=cases)
  h.attrs['summary_json']=json.dumps(result)
 (OUT/'reference-tracking-summary.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps([c for c in cases if c['profile']=='meteor' and c['width_us']==10000 and c['attenuation_db']==20],indent=2))
if __name__=='__main__':main()
