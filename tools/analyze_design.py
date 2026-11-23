"""Ideal rectangular-pulse model; not an RF circuit simulation or measurement.
Source provenance is kept in this script and HDF5 metadata only.
"""
from pathlib import Path
import json
import numpy as np
import h5py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
n=np.arange(1,8);width=np.array([7.,10.,12.]);duty=width*1e-2
# Loaded voltage after 49.9ohm source with ideal 3.3V logic source.
vpeak=1.65
p=2*(vpeak*duty[:,None]*np.sinc(duty[:,None]*n))**2/50
high=10*np.log10(p/1e-3)-20-1.3-3.2
low=high-20
with h5py.File(ROOT/'validation/ideal-levels.h5','w') as f:
 f.attrs['schema']='calinject-ideal-level-model-v1'
 f.attrs['model']='Ideal rectangular pulses into 50ohm; no measured hardware data'
 f.attrs['generator']='tools/analyze_design.py'
 f.attrs['loaded_pulse_peak_v']=vpeak
 f.attrs['fixed_pad_db']=20.;f.attrs['attenuator_insertion_db']=1.3;f.attrs['combiner_loss_db']=3.2
 f.create_dataset('frequency_hz',data=n*1e7)
 f.create_dataset('comb_pulse_width_ns',data=width)
 f.create_dataset('high_range_on_dbm',data=high)
 f.create_dataset('low_range_on_dbm',data=low)
fig,ax=plt.subplots(figsize=(7.2,4.4))
for i,w in enumerate(width):ax.plot(n*10,low[i],marker='o',label=f'{w:g} ns comb pulse')
ax.set(xlabel='Harmonic frequency (MHz)',ylabel='Burst-on harmonic power (dBm)',title='Ideal LOW-range output, 0 dB electronic attenuation',xticks=n*10)
ax.grid(alpha=.25);ax.legend();fig.tight_layout();fig.savefig(ROOT/'docs/ideal-levels.png',dpi=180);plt.close(fig)
print(json.dumps(dict(nominal_low_10mhz_dbm=float(low[1,0]),nominal_low_70mhz_dbm=float(low[1,-1])),indent=2))
