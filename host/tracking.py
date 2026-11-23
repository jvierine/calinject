"""Offline phase-continuous correction from timestamped frequency estimates.
This does not recover ambiguous inter-burst carrier phase or improve the
reference's absolute accuracy. Estimate frequencies within individual bursts.
"""
import numpy as np

class FrequencyTrack:
    """Piecewise-linear frequency, analytically integrated to continuous phase.
    Knots refer to burst/window midpoints. Uses future knots: offline, not a
    causal live predictor. Outside the knot span the endpoint frequency is held.
    Frequencies are Hz offsets to remove, times are relative seconds.
    """
    def __init__(self,seconds,offset_hz):
        self.t=np.asarray(seconds,dtype=float);self.f=np.asarray(offset_hz,dtype=float)
        if self.t.ndim!=1 or self.t.shape!=self.f.shape or len(self.t)<2 or not np.isfinite(self.t).all() or not np.isfinite(self.f).all() or np.any(np.diff(self.t)<=0):
            raise ValueError('need >=2 finite ordered frequency knots')
        self.slope=np.diff(self.f)/np.diff(self.t)
        self.area=np.r_[0,np.cumsum((self.f[:-1]+self.f[1:])*.5*np.diff(self.t))]
    def phase_cycles(self,seconds):
        x=np.asarray(seconds,dtype=float)
        if not np.isfinite(x).all():raise ValueError('nonfinite time')
        i=np.clip(np.searchsorted(self.t,x,side='right')-1,0,len(self.t)-2)
        dt=x-self.t[i];out=self.area[i]+self.f[i]*dt+.5*self.slope[i]*dt**2
        out=np.where(x<self.t[0],self.f[0]*(x-self.t[0]),out)
        return np.where(x>self.t[-1],self.area[-1]+self.f[-1]*(x-self.t[-1]),out)
    def correct(self,iq,seconds):
        x=np.asarray(iq);t=np.asarray(seconds)
        if x.shape!=t.shape:raise ValueError('sample/time shapes differ')
        return x*np.exp(-2j*np.pi*self.phase_cycles(t))
