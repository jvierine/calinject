"""Synthetic pilot-frequency recovery using the delivered host estimator.
Independent random burst phases; average frequency estimates, never unwrap
phase between PPS epochs. No hardware performance is implied.
"""
from pathlib import Path
import sys,json
import numpy as np
import h5py
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'host'))
from calibration import tone_frequency
OUT=ROOT/'validation/simulation';OUT.mkdir(exist_ok=True)
rng=np.random.default_rng(20261124)
widths=[100,1000,10000];snrs=[10,20,30];counts=[1,10,60]
trials=1200;fs=2e6;f0=12345.67
rows=[]
with h5py.File(OUT/'averaging.h5','w') as h:
 h.attrs['generator']='tools/simulate_averaging.py'
 h.attrs['model']='Isolated complex tone, independent white Gaussian noise and burst phase, known sample rate; no hardware measurements'
 h.attrs['sample_rate_hz']=fs;h.attrs['trials_per_case']=trials
 for width in widths:
  t=np.arange(round(width*1e-6*fs))/fs
  for snr in snrs:
   error=[]
   for _ in range(trials):
    x=np.exp(2j*np.pi*f0*t+1j*rng.uniform(-np.pi,np.pi))
    x+=10**(-snr/20)/np.sqrt(2)*(rng.normal(size=len(t))+1j*rng.normal(size=len(t)))
    error.append(tone_frequency(x,fs)['baseband_hz']-f0)
   error=np.asarray(error);h[f'width_{width}_snr_{snr}/frequency_error_hz']=error
   for n in counts:
    grouped=error.reshape(-1,n).mean(axis=1)
    row=dict(width_us=width,snr_db=snr,bursts_averaged=n,independent_groups=len(grouped),rms_error_hz=float(np.sqrt(np.mean(grouped**2))),bias_hz=float(grouped.mean()),single_burst_error_over_one_fft_bin_fraction=float(np.mean(abs(error)>fs/len(t))))
    rows.append(row)
 # Evaluate causal tracking at PPS cadence using actual simulated estimator
 # errors. Linear drift is specified at burst midpoint; within-burst curvature
 # is negligible for these widths. All windows use independent errors.
 drift=[];rate=.2
 for width in widths:
  err=h[f'width_{width}_snr_30/frequency_error_hz'][:]
  epoch=np.arange(trials,dtype=float);truth=rate*epoch
  observed=truth+err
  for n in counts:
   average=np.convolve(observed,np.ones(n)/n,mode='valid')
   newest=truth[n-1:];midpoint=(truth[:len(average)]+newest)/2
   drift.append(dict(width_us=width,bursts_averaged=n,drift_hz_per_s=rate,age_of_estimate_s=(n-1)/2,current_time_rms_hz=float(np.sqrt(np.mean((average-newest)**2))),midpoint_time_rms_hz=float(np.sqrt(np.mean((average-midpoint)**2))),expected_current_time_bias_hz=-rate*(n-1)/2))
 result=dict(sample_rate_hz=fs,trials_per_case=trials,burst_period_s=1,rows=rows,linear_drift=drift,limits='Ideal isolated tone; excludes receiver filtering, sample-rate error, reference error, interference and oscillator phase noise. 60-burst static results have only 20 independent groups.')
 h.attrs['summary_json']=json.dumps(result)
(OUT/'averaging-summary.json').write_text(json.dumps(result,indent=2)+'\n')
lines=['# Longer bursts and averaging','','Synthetic results using the supplied frequency estimator at 2 MS/s. Each case contains 1,200 independent noisy bursts with random initial phase. Noise power per sample and burst-on signal amplitude stay fixed. Averaging combines separately estimated frequencies; phase is never connected across the one-second gaps.','','## At 30 dB per-sample SNR','','| Burst width | Duty at 1 PPS | One burst RMS | 10 bursts RMS | 60 bursts RMS |','|---|---:|---:|---:|---:|']
for width in widths:
 vals=[next(r['rms_error_hz'] for r in rows if r['width_us']==width and r['snr_db']==30 and r['bursts_averaged']==n) for n in counts]
 lines.append(f'| {width/1000:g} ms | {width/10000:g}% | '+ ' | '.join(f'{v:.4g} Hz' for v in vals)+' |')
lines+=['','The first-to-last burst-midpoint spans are 9 s for 10 bursts and 59 s for 60 bursts. Their causal averages represent times 4.5 s and 29.5 s behind the newest burst. The 60-burst numbers use 20 non-overlapping groups and therefore have appreciable Monte Carlo uncertainty. These are frequency errors, not PPS arrival-time uncertainties.','','## While the receiver drifts','','For a receiver frequency ramp of 0.2 Hz/s, a trailing average of 10 bursts lags the newest frequency by 0.9 Hz; 60 bursts lag by 5.9 Hz. Assigning each estimate to the midpoint of its window removes this bias for a linear ramp, but does not produce a current-time estimate. A drift fit/predictor would need separate validation.','','Longer bursts improve immediate tracking without this multi-second averaging delay. A 1 ms burst at 30 dB SNR is a useful starting point in this model; 10 ms improves precision further while occupying 1% of each second. The firmware already supports both widths over USB. The default remains 100 µs.','','## Low-SNR failure mode','','At 10 dB SNR, 10 ms bursts produced occasional large estimator errors (3 of 1,200 exceeded one 100 Hz FFT bin), raising single-burst RMS error to about 7 Hz. The phase-slope estimator is sensitive to phase-unwrapping failures in weak samples. Longer duration alone is insufficient in this regime: require an adequate isolated pilot and validate an outlier-rejection or more robust estimator before relying on these values. At 20 dB SNR, the 10 ms single-burst RMS error was about 0.028 Hz.','','## Limits','','These simulations assume a single isolated pilot, independent complex white Gaussian noise, known sample rate, and no reference-frequency error. They exclude filtering, interference, oscillator phase noise and sample loss. The same per-sample SNR means a longer burst contains more calibration energy and contaminates more science samples. Noise-only improvement is roughly duration to the power −3/2 and averaging-count to the power −1/2 in this regime. It does not reduce correlated pilot/reference errors or calibration biases. For example, a 0.064 Hz reference error at 10 MHz becomes 0.448 Hz at 70 MHz; that illustrative scale can dominate the long-burst noise figures.','','The complete 10/20/30 dB sweep and linear-drift results are stored as HDF5 and JSON alongside the other simulations. Reproduce with:','','```sh','conda run -n base python tools/simulate_averaging.py','```','']
(ROOT/'docs/averaging.md').write_text('\n'.join(lines))
print('\n'.join(lines[:12]))
