"""Offline timing/frequency utilities for Calinject recordings.
Fits use explicit PPS correspondences. Burst phase is fitted within each burst,
never unwrapped across seconds. This avoids unobservable integer-cycle aliases.
"""
import argparse,json
import numpy as np
import h5py
from scipy.signal import fftconvolve,find_peaks

def match_template(samples,template,min_spacing,threshold=.6):
    """Find a measured/calibrated burst template. Returns its start sample indices.
    IQ samples/template must have matching center frequency, rate, and filtering.
    A constant complex phase is allowed. Threshold is normalized correlation.
    Fractional interpolation is approximate; calibrate its bias with the SDR.
    Intended for bounded in-memory snippets, not full-band day-long recordings.
    """
    x=np.asarray(samples);h=np.asarray(template)
    if x.ndim!=1 or h.ndim!=1 or len(h)<8 or len(x)<len(h):raise ValueError('invalid sample/template arrays')
    if not np.isfinite(x).all() or not np.isfinite(h).all():raise ValueError('nonfinite samples')
    energy=float(np.vdot(h,h).real)
    if energy<=0:raise ValueError('empty template')
    numerator=abs(fftconvolve(x,np.conj(h[::-1]),mode='valid'))
    denominator=np.sqrt(np.maximum(fftconvolve(abs(x)**2,np.ones(len(h)),mode='valid'),0)*energy)
    score=numerator/np.maximum(denominator,np.finfo(float).tiny)
    peaks,_=find_peaks(score,height=threshold,distance=int(min_spacing))
    frac=[]
    for p in peaks:
        a,b,c=score[p-1:p+2];den=a-2*b+c;frac.append(0 if den==0 else float(np.clip(.5*(a-c)/den,-.5,.5)))
    return peaks+frac,score[peaks]

def fit_clock(sample_index,utc_seconds,nominal_fs):
    """Affine sample clock over a short interval. Reject missing/dropped samples
    by inspecting residuals; piecewise fit only within continuous capture spans.
    utc_seconds may be large Unix seconds, so subtract origin before fitting.
    """
    n=np.asarray(sample_index,dtype=float);t=np.asarray(utc_seconds,dtype=float)
    if len(n)<3 or n.shape!=t.shape or np.any(np.diff(n)<=0) or np.any(np.diff(t)<=0):raise ValueError('need >=3 ordered explicit PPS correspondences')
    if not np.isfinite(n).all() or not np.isfinite(t).all() or nominal_fs<=0:raise ValueError('invalid clock inputs')
    dt=t-t[0];dn=n-n[0];slope,offset=np.linalg.lstsq(np.column_stack((dt,np.ones(len(dt)))),dn,rcond=None)[0]
    residual=n-(n[0]+offset+slope*dt)
    return dict(sample_rate_hz=float(slope),sample_rate_error_ppm=float((slope/nominal_fs-1)*1e6),anchor_utc_s=float(t[0]),anchor_sample=float(n[0]+offset),residual_samples=residual)

def tone_frequency(iq,fs):
    """Local unwrapped phase slope in high-SNR complex tone, one burst interior.
    Caller must isolate a single harmonic and trim filter/gate transients.
    Negative frequencies and IQ sign convention are preserved.
    """
    x=np.asarray(iq)
    if len(x)<8 or not np.iscomplexobj(x) or fs<=0:raise ValueError('complex burst with >=8 samples required')
    phase=np.unwrap(np.angle(x));t=np.arange(len(x))/fs
    a,b=np.polyfit(t,phase,1);res=phase-(a*t+b)
    return dict(baseband_hz=float(a/(2*np.pi)),phase_residual_rms_rad=float(np.sqrt(np.mean(res**2))))

def rf_frequency(baseband_hz,measured_pilot_baseband_hz,pilot_rf_hz):
    """f_RF = f_pilot_RF + (f_BB - f_pilot_BB), after sample-rate correction.
    Assumes conventional positive-frequency IQ; test polarity on each receiver.
    """
    return pilot_rf_hz+baseband_hz-measured_pilot_baseband_hz

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('markers',help='HDF5 /sample_index and /utc_seconds, explicitly associated');p.add_argument('--nominal-fs',type=float,required=True);p.add_argument('--output',required=True)
    a=p.parse_args()
    with h5py.File(a.markers,'r') as f:r=fit_clock(f['sample_index'][:],f['utc_seconds'][:],a.nominal_fs)
    with h5py.File(a.output,'x') as f:
        f.attrs['schema']='calinject-clock-fit-v1'
        for k,v in r.items():
            if isinstance(v,np.ndarray):f.create_dataset(k,data=v)
            else:f.attrs[k]=v
    print(json.dumps({k:v for k,v in r.items() if not isinstance(v,np.ndarray)},indent=2))
if __name__=='__main__':main()
