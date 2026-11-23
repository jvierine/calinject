"""Public summary of recorded behavioral scenarios, not hardware measurements.

Input provenance stays here and in numerical metadata; no source paths on plots.
"""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
timing=json.loads((ROOT/'validation/end-to-end/summary.json').read_text())['cases']
tracking=json.loads((ROOT/'validation/end-to-end/reference-tracking-summary.json').read_text())['cases']
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,2,figsize=(9,3.4),layout='constrained')
for name,label,color in [('HF25','HF, 64 MS/s','#24669a'),('HF50','HF, 128 MS/s','#b45c25'),('meteor','Meteor, 2 MS/s','#357858')]:
    t=sorted([r for r in timing if r['profile']==name and r['fault'] is None and r['attenuation_db']==20 and r['edge_jitter_assumed_ps']==20 and r['phase_noise_margin_db']==0],key=lambda r:r['width_us'])
    f=sorted([r for r in tracking if r['profile']==name and r['attenuation_db']==20 and r['gain_error_fraction']==0],key=lambda r:r['width_us'])
    assert len(t)==len(f)==3
    axs[0].plot([r['width_us']/1000 for r in t],[r['marker_timing_rms_ns'] for r in t],'o-',color=color,label=label)
    axs[1].plot([r['width_us']/1000 for r in f],[r['science_error_after_rms_hz'] for r in f],'o-',color=color,label=label)
for ax in axs:
    ax.set_xscale('log');ax.set_xticks([.1,1,10],['0.1','1','10'])
    ax.set_xlabel('Calibration burst length (ms)');ax.grid(alpha=.18)
axs[0].set_ylabel('Marker timing RMS error (ns)');axs[0].set_ylim(bottom=0)
axs[1].set_ylabel('Science frequency RMS error (Hz)');axs[1].set_yscale('log')
axs[0].legend(frameon=False,fontsize=9)
fig.savefig(ROOT/'docs/burst-recovery.png',dpi=180)
plt.close(fig)
