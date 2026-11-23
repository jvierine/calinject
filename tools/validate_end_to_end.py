"""Paired sensitivities, numerical convergence and applied IQ phase correction."""
from pathlib import Path
import sys,json,copy
import numpy as np
import h5py
from scipy.signal import fftconvolve,firwin
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'host')]
import end_to_end as model
from simulate_reference_tracking import ReferenceObserver
from tracking import FrequencyTrack
from calibration import tone_frequency_robust,fit_clock
OUT=ROOT/'validation/end-to-end'
plant=model.Plant();rows=[];convergence=[]
seed=np.random.default_rng(819).bit_generator.state
observer=ReferenceObserver(plant.captures,plant.codes,plant.valid)
with h5py.File(OUT/'paired-validation.h5','w') as h:
 h.attrs['generator']='tools/validate_end_to_end.py'
 for edge,margin in [(20,0),(100,0),(20,5)]:
  model.RNG.bit_generator.state=copy.deepcopy(seed)
  row,arrays,example=model.receiver_case(plant,model.PROFILES[-1],1000,20,edge_ps=edge,pn_margin=margin)
  epochs=arrays['utc_s'];ref=np.array([observer.estimate(t+.0005) for t in epochs])
  offsets=arrays['pilot_baseband_hz']-30000-7*ref
  track=FrequencyTrack(epochs+.0005,offsets)
  rate=np.interp(epochs[0],arrays['local_clock_epoch_s'],arrays['local_clock_rate_hz'])
  sample_index=example['start_native_index']+2*np.arange(len(example['iq']))
  t_est=epochs[0]+(sample_index-arrays['marker_index'][0])/rate+12.399e-6
  corrected=track.correct(example['iq'],t_est)
  # Science tone is measured outside the calibration pulse in the corrected IQ.
  tail=corrected[1200:];fs=rate/2
  z=tail*np.exp(-2j*np.pi*180000*np.arange(len(tail))/fs)
  z=fftconvolve(z,firwin(129,10000,fs=fs),mode='same')[128:-128]
  corrected_error=tone_frequency_robust(z,fs)['baseband_hz']
  row['applied_phase_correction_science_error_hz']=corrected_error
  rows.append(row);g=h.create_group('edge_%s_margin_%s'%(edge,margin));g['corrected_iq']=corrected;g['estimated_utc_s']=t_est;g['phase_correction_cycles']=track.phase_cycles(t_est)
 # Noiseless paired discretization check, including the equivalent quantizer.
 baseline=None;previous=None
 for oversample in [16,32,64]:
  row,arrays,example=model.receiver_case(plant,model.PROFILES[1],1000,20,epochs=16,noise=False,oversample=oversample)
  error=arrays['marker_timing_error_s']
  if baseline is None:baseline=error
  delta=0. if previous is None else float(np.sqrt(np.mean((error-previous)**2))*1e9)
  convergence.append(dict(oversampling=oversample,marker_rms_ns=row['marker_timing_rms_ns'],difference_from_16x_rms_ns=float(np.sqrt(np.mean((error-baseline)**2))*1e9),difference_from_previous_rms_ns=delta))
  previous=error
  if oversample==64 and delta>25:raise AssertionError('Timing discretization not converged to 25ns')
 a=fit_clock(arrays['marker_index'],arrays['utc_s'],128e6)
 shifted=fit_clock(arrays['marker_index'],arrays['utc_s']+1,128e6)
 ambiguity=dict(assigned_utc_shift_s=1,clock_rate_change_hz=shifted['sample_rate_hz']-a['sample_rate_hz'],anchor_utc_change_s=shifted['anchor_utc_s']-a['anchor_utc_s'])
 assert abs(ambiguity['clock_rate_change_hz'])<1e-6 and ambiguity['anchor_utc_change_s']==1
 result=dict(paired_noise_sensitivity=rows,convergence=convergence,integer_second_ambiguity=ambiguity,limits='Paired sensitivity uses identical stochastic draws. Noiseless convergence includes deterministic first-pulse delay and quantization. Phase correction is offline and uses estimated sample times plus explicitly assigned UTC epochs.')
 h.attrs['summary_json']=json.dumps(result)
(OUT/'paired-validation-summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(applied_phase_errors_hz=[r['applied_phase_correction_science_error_hz'] for r in rows],convergence=convergence),indent=2))
