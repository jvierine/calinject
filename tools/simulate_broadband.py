"""Native-rate quantized broadband snapshots with assumed anti-alias filters.
The filters are stress-test examples, not RTL-SDR/RX888 hardware models.
"""
from pathlib import Path
import sys,json
import numpy as np
import h5py
from scipy.signal import butter,freqs
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from end_to_end import nominal_level,phase_noise,F0
OUT=ROOT/'validation/end-to-end';rng=np.random.default_rng(433)
profiles=[dict(name='HF25',fs=64e6,fc=25e6,center=0,bits=16),dict(name='HF50',fs=128e6,fc=50e6,center=0,bits=16),dict(name='meteor',fs=2e6,fc=.8e6,center=69.97e6,bits=8)]
rows=[]
with h5py.File(OUT/'broadband.h5','w') as h:
 h.attrs['generator']='tools/simulate_broadband.py';h.attrs['filter_assumption']='6th-order Butterworth carrier response; gated transients of the analogue filter not modeled. Not a measured receiver response.'
 for profile in profiles:
  fs=profile['fs'];t=np.arange(round(fs*.0004))/(fs*(1+3e-6));gate=(t>=.0001)&(t<.0002)
  pn_t=np.arange(402)/1e6;pn=phase_noise(len(pn_t),1e6,edge_ps=20,rng=rng);phase=np.interp(t,pn_t,pn)
  x=np.zeros(len(t),dtype=complex if profile['center'] else float);aliases=[]
  b,a=butter(6,2*np.pi*profile['fc'],analog=True)
  for n in range(1,21):
   rf=n*F0;bb=rf-profile['center'];_,response=freqs(b,a,[2*np.pi*abs(bb if profile['center'] else rf)])
   level=nominal_level(n,20);amplitude=np.sqrt(50*1e-3*10**(level/10));theta=2*np.pi*bb*t+n*phase-n*np.pi*.1
   if profile['center']:component=amplitude*response[0]*np.exp(1j*theta)
   else:component=np.sqrt(2)*amplitude*abs(response[0])*np.cos(theta+np.angle(response[0]))
   x+=gate*component
   alias=(bb+fs/2)%fs-fs/2
   if not profile['center']:alias=abs(alias)
   aliases.append(dict(harmonic=n,rf_hz=rf,observed_alias_hz=alias,assumed_filter_loss_db=float(-20*np.log10(abs(response[0]))),line_before_filter_dbm=float(level)))
  science=profile['center']+180e3 if profile['center'] else 2.5e6
  science_amp=np.sqrt(50*1e-3*10**(-86/10))
  sigma=np.sqrt(50*1e-3*10**(-96/10))
  if profile['center']:
   x+=science_amp*np.exp(2j*np.pi*(science-profile['center'])*t)
   x+=sigma/np.sqrt(2)*(rng.normal(size=len(t))+1j*rng.normal(size=len(t)))
  else:
   x+=np.sqrt(2)*science_amp*np.cos(2*np.pi*science*t)
   # A flat noise spectral density over the full real ADC Nyquist band.
   x+=sigma*np.sqrt(fs/2e6)*rng.normal(size=len(t))
  fullscale=(4 if profile['center'] else 10)*np.sqrt(50*1e-3*10**(nominal_level(7 if profile['center'] else 1,20)/10))
  step=2*fullscale/2**profile['bits']
  quant=lambda y:np.clip(np.round(y/step),-2**(profile['bits']-1),2**(profile['bits']-1)-1)*step
  y=quant(x.real)+1j*quant(x.imag) if profile['center'] else quant(x)
  clipped=float(np.mean(abs(x)>fullscale))
  if profile['center']:
   spec=np.fft.fftshift(np.fft.fft(y));freq=np.fft.fftshift(np.fft.fftfreq(len(y),1/fs));p=abs(spec/len(y))**2/50
  else:
   spec=np.fft.rfft(y);freq=np.fft.rfftfreq(len(y),1/fs);p=2*abs(spec/len(y))**2/50
  g=h.create_group(profile['name']);g['sample_time_s']=t;g['quantized_samples_v']=y;g['frequency_hz']=freq;g['power_dbm_per_fft_bin']=10*np.log10(np.maximum(p,1e-30)/1e-3)
  rows.append(dict(**profile,aliases=aliases,clipped_fraction=clipped,fullscale_v=fullscale))
 result=dict(profiles=rows,limitations='Quantized native-rate demonstrations, generic filters and assumed gain. Noise flatness, ADC ENOB/DNL/INL, actual front-end gain/filtering and intermodulation require measured receiver models. Harmonics truncated at 200MHz; higher harmonics remain unmodeled.')
 h.attrs['summary_json']=json.dumps(result)
(OUT/'broadband-summary.json').write_text(json.dumps(result,indent=2)+'\n')
print('Native-rate broadband snapshots complete')
