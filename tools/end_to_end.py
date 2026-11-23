"""Multirate behavioral Calinject/SDR simulation, not a hardware qualification.
Source references and assumptions are saved as HDF5 metadata/JSON. The model
uses the actual firmware servo/UBX and delivered host recovery functions.
"""
from pathlib import Path
import json,sys,math,struct
import numpy as np
import h5py
from scipy.linalg import expm
from scipy.signal import firwin,fftconvolve,welch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'host'),str(ROOT/'firmware')]
from calibration import match_template,fit_clock,tone_frequency,tone_frequency_robust,rf_frequency
from tracking import FrequencyTrack
from protocol import Servo,Parser,packet,timepulse
OUT=ROOT/'validation/end-to-end';OUT.mkdir(exist_ok=True)
RNG=np.random.default_rng(20261125)
F0=10e6
OFFSETS=np.array([10,100,1000,10000,100000.])
TYP=np.array([-90,-120,-140,-145,-148.])
SOURCE='https://ecsxtal.com/store/pdf/ECS-TXO32-S3.pdf'
ASSUMPTIONS=dict(source=SOURCE,phase_noise_typ_dbc_hz=TYP.tolist(),phase_noise_max_dbc_hz=(TYP+5).tolist(),offset_hz=OFFSETS.tolist(),phase_noise_below_10hz='Not specified: replaced by explicit slow FM/temperature stress model',above_100khz='Flat extrapolation to analysis Nyquist; not a specification',edge_jitter_rms_ps=[20,100],edge_jitter_note='Assumed independent timing error per 10MHz edge; not a comparator or board guarantee',adc_aperture_jitter_ps=10,pps_jitter_rms_ns=20,gate_sync_quantization_ns=8,first_pulse_delay_ns=[0,100],fixed_delay_us=12.345,noise_dbm_per_analysis_sample=-96,receiver_filters='Generic linear-phase 350kHz channel, NOT measured RTL/RX888 responses',rtl_lo_phase_noise_dbc_hz=[-65,-90,-110,-125,-130],rtl_lo_phase_noise_note='Illustrative sensitivity model, not an RTL-SDR specification',clock_ppm_initial=3,clock_drift_ppm_per_s=.002,rtl_lo_error_hz=100,rtl_lo_drift_hz_per_s=.02,oversampling=32,analysis_sample_rate_hz=1e6,burst_epochs=64)

def phase_psd(freq,mask=TYP,edge_ps=0,low=10):
    """One-sided rad^2/Hz: S_phi = 2 * 10**(L/10)."""
    f=np.asarray(freq);safe=np.maximum(f,10)
    s=2*10**(np.interp(np.log10(safe),np.log10(OFFSETS),mask)/10)
    s+=2*(2*np.pi*F0*edge_ps*1e-12)**2/F0
    return np.where(f>=low,s,0.)

def phase_noise(size,fs,mask=TYP,edge_ps=0,rng=RNG):
    # At least 0.25s gives <=4Hz bin spacing for close-in noise. Independent
    # segments model different PPS bursts; this is not inter-burst phase data.
    n=2**int(np.ceil(np.log2(max(size,int(fs*.25)))))
    freq=np.fft.rfftfreq(n,1/fs);s=phase_psd(freq,mask,edge_ps)
    coeff=(rng.normal(size=len(freq))+1j*rng.normal(size=len(freq)))*np.sqrt(n*fs*s/4)
    coeff[0]=0;coeff[-1]=coeff[-1].real*np.sqrt(2)
    return np.fft.irfft(coeff,n)[:size]

class Plant:
    """Actual Servo code plus exact two-pole loaded DAC filter/VCO plant.
    The 100k control input is the datasheet minimum; tune slope is assumed.
    Counter captures include quantization, rollover and PPS time jitter.
    """
    def __init__(self,seconds=2400):
        self.r=1000.;self.c=4.7e-6;self.load=100e3;self.kv=100.
        self.A=np.array([[-2/(self.r*self.c),1/(self.r*self.c)],[1/(self.r*self.c),-(1/self.r+1/self.load)/self.c]])
        self.B=np.array([1/(self.r*self.c),0.]);self.E=expm(self.A)
        self.inv=np.linalg.inv(self.A);self.eig=np.sort(np.linalg.eigvals(self.A))
        self.servo=Servo();v=1862*3.3/4096;self.state=-self.inv@self.B*v
        self.captures=[(2**32-100)&0xffffffff]
        self.zero=1.50;self.phase=[0.];self.states=[];self.codes=[];self.err=[];self.valid=[];self.modes=[]
        self.thermal=.25*np.sin(2*np.pi*np.arange(seconds+1)/900)+np.cumsum(RNG.normal(0,.0008,seconds+1))
        self.servo.step((2**32-100)&0xffffffff,True)
        for second in range(seconds):
            self.states.append(self.state.copy());self.codes.append(self.servo.code)
            u=self.servo.code*3.3/4096;steady=-self.inv@self.B*u
            integral=steady+self.inv@(self.E-np.eye(2))@(self.state-steady)
            dphase=self.kv*(integral[1]-self.zero)+.5*(self.thermal[second]+self.thermal[second+1])
            self.phase.append(self.phase[-1]+dphase)
            self.state=steady+self.E@(self.state-steady)
            self.err.append(self.kv*(self.state[1]-self.zero)+self.thermal[second+1])
            valid=not (1000<=second<1060 or 1820<=second<1826)
            jitter=RNG.normal(0,20e-9)
            count=int(2**32-100+(second+1)*F0+self.phase[-1]+F0*jitter)&0xffffffff
            self.captures.append(count)
            self.servo.step(count,valid);self.valid.append(valid);self.modes.append(self.servo.state)
        self.phase=np.array(self.phase);self.codes=np.array(self.codes);self.states=np.array(self.states);self.err=np.array(self.err)
    def at(self,t):
        t=np.asarray(t);i=np.clip(np.floor(t).astype(int),0,len(self.codes)-1);dt=t-i
        state=self.states[i];steady=(-self.inv@self.B)[None,:]*(self.codes[i]*3.3/4096)[...,None]
        z=state[...,1]-steady[...,1];d=(state@self.A.T)[...,1]+(self.codes[i]*3.3/4096)*self.B[1]
        l1,l2=self.eig;c1=(d-l2*z)/(l1-l2);c2=z-c1
        integral=steady[...,1]*dt+c1*np.expm1(l1*dt)/l1+c2*np.expm1(l2*dt)/l2
        thermal=self.thermal[i]*dt+.5*(self.thermal[i+1]-self.thermal[i])*dt**2
        phase=self.phase[i]+self.kv*(integral-self.zero*dt)+thermal
        hz=self.kv*(steady[...,1]+c1*np.exp(l1*dt)+c2*np.exp(l2*dt)-self.zero)+self.thermal[i]+(self.thermal[i+1]-self.thermal[i])*dt
        return np.squeeze(phase),np.squeeze(hz)

def nominal_level(harmonic,attenuation,width_ns=10):
    duty=width_ns*.01
    p=2*(1.65*duty*np.sinc(harmonic*duty))**2/50
    return 10*np.log10(p/1e-3)-20-1.3-20-3.2-attenuation

def native_index(t,fs):
    return 123.25+fs*((1+3e-6)*t+.5*.002e-6*t*t)

def index_time(n,fs):
    a=.5*fs*.002e-6;b=fs*(1+3e-6);c=n-123.25
    return 2*c/(b+np.sqrt(b*b+4*a*c))

PROFILES=[dict(name='HF25',native_fs=64e6,harmonic=1,kind='direct'),dict(name='HF50',native_fs=128e6,harmonic=4,kind='direct'),dict(name='meteor',native_fs=2e6,harmonic=7,kind='tuner')]

def receiver_case(plant,profile,width_us,attenuation,edge_ps=20,pn_margin=0,epochs=64,noise=True,oversample=32,fault=None):
    fs=1e6;ratio=int(profile['native_fs']/fs);n=profile['harmonic'];pilot=n*F0;center=pilot-30000
    duration=width_us*1e-6;pad=.00015;highfs=fs*oversample
    taps=firwin(16*oversample+1,350e3,fs=highfs)
    # Independent noiseless training template at nominal sample rate, as would
    # be measured with the same receiver settings before science acquisition.
    th=np.arange(round((duration+32e-6)*highfs))/highfs
    template=fftconvolve((th<duration)*np.exp(2j*np.pi*30000*th),taps)[:len(th)][::oversample]
    template_energy=np.vdot(template,template).real
    indexes=[];times=[];offsets=[];reference=[];measured_pilot=[];legacy_pilot=[];measured_science=[];clipped=[];scores=[];missed=[]
    start_epoch=1800
    parser=Parser();first=None
    for epoch in range(start_epoch,start_epoch+epochs):
        # Actual UBX framing/parser and UTC-validity helper are exercised here;
        # this is a GNSS event model, not emulation of the firmware main loop.
        utc_valid=bool(plant.valid[epoch] and plant.valid[epoch-1]) and not (fault=='gnss_loss' and 1820<=epoch<1828)
        payload=struct.pack('<IIiHBB',epoch*1000,0,0,2446,3 if utc_valid else 0,0)
        frame=packet(13,1,payload);messages=parser.feed(frame[:9])+parser.feed(frame[9:]);tp=timepulse(messages[0][2])
        if not tp['valid']:missed.append(epoch);continue
        initial=int(np.floor(native_index(epoch-pad,profile['native_fs'])/ratio))
        t0=index_time(initial*ratio,profile['native_fs']);localfs=fs*(1+3e-6+.002e-6*epoch)
        count=int(np.ceil((duration+2*pad+.01)*localfs));u=np.arange(count*oversample)/(localfs*oversample);t=t0+u
        gps_jitter=RNG.normal(0,20e-9) if noise else 0
        sync=RNG.uniform(0,8e-9) if noise else 4e-9
        gate=epoch+12.345e-6+gps_jitter+sync
        refphase,_=plant.at(gate)
        first_pulse=((-(F0*(gate-epoch)+refphase))%1)/F0
        arrival=gate+first_pulse
        phase_ref,refhz=plant.at(t)
        if profile['kind']=='direct':
            # Digital downconverter phase is tied to ADC sample-clock phase.
            ctrphase=center*((1+3e-6)*t+.5*.002e-6*t*t)
            ctrhz=center*(1+3e-6+.002e-6*epoch)
        else:
            ctrphase=center*t+100*t+.5*.02*t*t;ctrhz=center+100+.02*epoch
        lo_phase=2*np.pi*np.remainder(ctrphase,1)
        pilot_phase=2*np.pi*np.remainder(pilot*t+n*phase_ref,1)-lo_phase
        science_rf=pilot+150000.
        science_phase=2*np.pi*np.remainder(science_rf*t,1)-lo_phase
        pn=phase_noise(count,fs,TYP+pn_margin,edge_ps) if noise else np.zeros(count)
        rxpn=phase_noise(count,fs,np.array(ASSUMPTIONS['rtl_lo_phase_noise_dbc_hz'])) if noise and profile['kind']=='tuner' else np.zeros(count)
        # ADC time jitter changes all RF phases coherently. Independent white
        # aperture errors are assumed at the native ADC clock then bandlimited
        # to this equivalent analysis channel.
        jitter=RNG.normal(0,10e-12/np.sqrt(ratio),count) if noise else np.zeros(count)
        hp=np.interp(u,np.arange(count)/localfs,n*pn-rxpn+2*np.pi*pilot*jitter)
        hs=np.interp(u,np.arange(count)/localfs,-rxpn+2*np.pi*science_rf*jitter)
        level=nominal_level(n,attenuation);amp=np.sqrt(50*1e-3*10**(level/10))
        envelope=(t>=arrival)&(t<arrival+duration)
        cal=amp*envelope*np.exp(1j*(pilot_phase+hp))
        # Persistent science tone 150kHz above the reference, -86dBm at SDR.
        # It is recovered from a separate, calibration-free 10ms observation.
        science_amp=np.sqrt(50*1e-3*10**(-86/10))
        science=science_amp*np.exp(1j*(science_phase+hs))
        # Noise is specified at the equivalent analysis rate before filtering.
        # Oversampling increases total white power so spectral density stays fixed.
        sigma=np.sqrt(50*1e-3*10**(-96/10))
        noise_hi=sigma*np.sqrt(oversample/2)*(RNG.normal(size=len(t))+1j*RNG.normal(size=len(t))) if noise else np.zeros(len(t))
        signal=cal+science+noise_hi
        fullscale=amp*.6 if fault=='clipping' else amp*4
        clip=np.mean((abs(signal.real)>fullscale)|(abs(signal.imag)>fullscale)) if fault=='clipping' else 0.
        if fault=='clipping':signal=np.clip(signal.real,-fullscale,fullscale)+1j*np.clip(signal.imag,-fullscale,fullscale)
        y=fftconvolve(signal,taps)[:len(signal)][::oversample]
        # Equivalent in-band quantization: 8-bit tuner IQ or 16-bit direct
        # ADC, with white quantization-noise reduction from decimation. This
        # does not model ADC DNL/INL or actual receiver gain. Native-rate
        # quantized broadband examples are generated separately.
        bits=8 if profile['kind']=='tuner' else 16
        adc_fullscale=(4 if bits==8 else 20)*np.sqrt(50*1e-3*10**(nominal_level(n,20)/10))
        step=2*adc_fullscale/(2**bits*np.sqrt(ratio))
        y=step*(np.round(y.real/step)+1j*np.round(y.imag/step))
        # Correct the template's carrier using a coarse, known acquisition
        # frequency: direct DDC clock error or tuner's initial LO offset. Only
        # acquisition is assisted; no true arrival or fine frequency enters recovery.
        acquisition_center=center*(1+3e-6+.002e-6*start_epoch) if profile['kind']=='direct' else center+100+.02*start_epoch
        coarse=(pilot-acquisition_center)-30000
        # Estimate the persistent science tone from the known calibration-free
        # trailing 10ms. Its frequency is recovered, not supplied as truth.
        tail_start=int(np.ceil((duration+pad+40e-6)*fs))
        tail=y[tail_start:];coarse_science=180000+coarse
        demod=tail*np.exp(-2j*np.pi*coarse_science*np.arange(len(tail))/fs)
        channel=fftconvolve(demod,firwin(129,10000,fs=fs),mode='same')[128:-128]
        science_est=tone_frequency_robust(channel,fs)['baseband_hz']+coarse_science
        basis=np.exp(2j*np.pi*science_est*np.arange(len(y))/fs)
        science_coefficient=np.vdot(basis[tail_start:],tail)/len(tail)
        ypilot=y-science_coefficient*basis
        h=template*np.exp(2j*np.pi*coarse*np.arange(len(template))/fs)
        peaks,score=match_template(ypilot,h,max(8,len(h)//2),.7)
        if not len(peaks):missed.append(epoch);continue
        best=int(np.argmax(score));p=peaks[best];scores.append(float(score[best]))
        idx=(initial+p)*ratio
        # Model a real 4096-native-sample discontinuity in the recording index.
        if fault=='sample_drop' and epoch>=start_epoch+epochs//2:idx-=4096
        indexes.append(idx);times.append(float(epoch));clipped.append(float(clip))
        # Cut the burst interior; filter guard is 16us at either end. Isolate
        # each tone further by mixing and a 20kHz lowpass when duration allows.
        # For the short-burst case, the stronger pilot is estimated first and
        # removed before fitting the weak science tone.
        left=int(np.ceil(p+24e-6*fs));right=int(np.floor(p+(duration-8e-6)*fs))
        if right-left<8:raise RuntimeError('Too little settled burst interior')
        z=ypilot[left:right]
        pilot_est=tone_frequency_robust(z,fs)['baseband_hz']
        legacy_pilot.append(float(tone_frequency(z,fs)['baseband_hz']))
        measured_pilot.append(float(pilot_est));measured_science.append(float(science_est))
        _,rferr=plant.at(epoch+duration/2);reference.append(float(n*rferr));offsets.append(float(arrival-epoch))
        if first is None:first=dict(iq=y,time_relative_s=t[::oversample]-epoch,template=h,detected_sample=p,start_native_index=initial*ratio)
    if len(times)<8:raise RuntimeError('Too few detections')
    times=np.array(times);indexes=np.array(indexes);corrected_index=indexes-profile['native_fs']*(12.345e-6+4e-9+50e-9)
    clock=fit_clock(corrected_index,times,profile['native_fs'])
    center_epoch=(times[0]+times[-1])/2;true_rate=profile['native_fs']*(1+3e-6+.002e-6*center_epoch)
    # Independent short-window fits recover the changing ADC rate. An affine
    # fit across the whole record is retained to expose its quadratic residual.
    local_rates=[];local_epoch=[]
    for j in range(0,len(times)-15,8):
        sl=slice(j,j+16);fit=fit_clock(corrected_index[sl],times[sl],profile['native_fs'])
        local_rates.append(fit['sample_rate_hz']);local_epoch.append(float(np.mean(times[sl])))
    estimated_native=np.interp(times,local_epoch,local_rates)
    measured_pilot=np.array(measured_pilot)*estimated_native/profile['native_fs']
    measured_science=np.array(measured_science)*estimated_native/profile['native_fs']
    science_est=rf_frequency(measured_science,measured_pilot,pilot)
    ferr=science_est-(pilot+150000)
    legacy_ferr=rf_frequency(measured_science,np.array(legacy_pilot)*estimated_native/profile['native_fs'],pilot)-(pilot+150000)
    # With reference error truth removed only for attribution, not recovery.
    residual_frequency=ferr+np.array(reference)
    timing=(corrected_index-native_index(times,profile['native_fs']))/profile['native_fs']
    # Smooth offline software correction based on measured frequency offsets.
    track=FrequencyTrack(times,np.array(measured_pilot)-30000)
    knot_eps=1e-9;phase_step=max(abs(track.phase_cycles(tt+knot_eps)-track.phase_cycles(tt-knot_eps)) for tt in times[1:-1])
    result=dict(profile=profile['name'],width_us=width_us,attenuation_db=attenuation,edge_jitter_assumed_ps=edge_ps,phase_noise_margin_db=pn_margin,fault=fault,detected=len(times),missed=len(missed),nominal_pilot_dbm=level,nominal_pre_filter_snr_db=level+96,clock_average_error_hz=float(clock['sample_rate_hz']-true_rate),clock_average_error_ppm=float((clock['sample_rate_hz']/true_rate-1)*1e6),marker_timing_rms_ns=float(np.sqrt(np.mean(timing**2))*1e9),marker_timing_bias_ns=float(np.mean(timing)*1e9),global_affine_residual_peak_samples=float(max(abs(clock['residual_samples']))),science_frequency_error_rms_hz=float(np.sqrt(np.mean(ferr**2))),science_frequency_error_bias_hz=float(np.mean(ferr)),reference_residual_rms_hz=float(np.sqrt(np.mean(np.array(reference)**2))),frequency_error_after_reference_truth_removed_rms_hz=float(np.sqrt(np.mean(residual_frequency**2))),maximum_template_score=float(max(scores)),minimum_template_score=float(min(scores)),max_clipped_fraction=float(max(clipped)),software_phase_change_across_2ns_cycles=float(phase_step),limits='Behavioral model and assumed receiver/noise parameters; not device specifications')
    result['legacy_phase_slope_frequency_error_rms_hz']=float(np.sqrt(np.mean(legacy_ferr**2)))
    result['capture_discontinuity_flag']=result['global_affine_residual_peak_samples']>512
    result['overload_flag']=result['max_clipped_fraction']>.001
    result['analysis_usable']=not (result['capture_discontinuity_flag'] or result['overload_flag'])
    result['equivalent_adc_bits']=bits
    arrays=dict(utc_s=times,marker_index=indexes,marker_timing_error_s=timing,science_frequency_error_hz=ferr,reference_frequency_error_hz=reference,local_clock_epoch_s=local_epoch,local_clock_rate_hz=local_rates,pilot_baseband_hz=measured_pilot,science_baseband_hz=measured_science)
    return result,arrays,first

def main():
    plant=Plant();results=[]
    with h5py.File(OUT/'results.h5','w') as h:
        h.attrs['generator']='tools/end_to_end.py';h.attrs['assumptions_json']=json.dumps(ASSUMPTIONS)
        h.attrs['hardware_measurement']=False
        g=h.create_group('plant');g['phase_error_cycles']=plant.phase;g['frequency_error_hz']=plant.err;g['dac_code']=plant.codes;g['filter_state_v']=plant.states;g['valid']=plant.valid
        # Dedicated one-second source phase-noise normalization check.
        pn=phase_noise(2**20,1e6,edge_ps=0);freq,ps=welch(pn,fs=1e6,nperseg=2**18)
        expected=np.trapezoid(phase_psd(np.linspace(10,500e3,200000)),np.linspace(10,500e3,200000))
        ratio=float(np.var(pn)/expected)
        if not .5<ratio<2:raise AssertionError('Phase-noise normalization')
        pg=h.create_group('phase_noise');pg['offset_hz']=freq;pg['estimated_ssb_dbc_hz']=10*np.log10(np.maximum(ps/2,1e-30));pg['source_time_phase_rad']=pn
        # Publish the band-limited typical/max intrinsic jitter separately from
        # the assumed additive edge noise, which can dominate the high-offset floor.
        fine=np.geomspace(10,100e3,100000);integrated={}
        for margin in [0,5]:
            var=np.trapezoid(phase_psd(fine,TYP+margin),fine)
            integrated['typ' if margin==0 else 'max_points_interpolated']=float(np.sqrt(var)/(2*np.pi*F0)*1e12)
        for p in PROFILES:
            for width in [100,1000,10000]:
                for att in [20.,31.5]:
                    name='%s_%sus_%sdb'%(p['name'],width,att)
                    row,arrays,example=receiver_case(plant,p,width,att)
                    results.append(row);g=h.create_group(name)
                    for key,value in arrays.items():g[key]=value
                    eg=g.create_group('example')
                    for key,value in example.items():eg[key]=value
                    print(name,json.dumps(row),flush=True)
        for fault in ['gnss_loss','sample_drop','clipping']:
            row,arrays,example=receiver_case(plant,PROFILES[-1],1000,20,fault=fault)
            results.append(row);g=h.create_group(fault)
            for key,value in arrays.items():g[key]=value
        for edge,margin in [(100,0),(20,5)]:
            row,arrays,example=receiver_case(plant,PROFILES[-1],1000,20,edge_ps=edge,pn_margin=margin)
            results.append(row);g=h.create_group('sensitivity_%s_%s'%(edge,margin))
            for key,value in arrays.items():g[key]=value
        # Exact loaded-filter steering response: frequency is continuous at a
        # DAC transition and phase is an integral, not a resettable accumulator.
        change=np.flatnonzero(np.diff(plant.codes)!=0)+1;transition=int(change[-1]);tt=transition+np.r_[[-1e-9],np.linspace(0,.15,1000)]
        phase,hz=plant.at(tt);g=h.create_group('steering');g['time_relative_s']=tt-transition;g['phase_error_cycles']=phase;g['frequency_error_hz']=hz
        phase_jump=float(abs(phase[1]-phase[0]));frequency_jump=float(abs(hz[1]-hz[0]))
        checks=dict(phase_noise_variance_ratio=ratio,servo_phase_change_across_1ns_cycles=phase_jump,servo_frequency_change_across_1ns_hz=frequency_jump,loaded_filter_dc_gain=1/1.02,dac_update_count=len(change),phase_continuity_pass=phase_jump<1e-6 and frequency_jump<.002)
        if not checks['phase_continuity_pass']:raise AssertionError(checks)
        summary=dict(assumptions=ASSUMPTIONS,intrinsic_10hz_to_100khz_jitter_ps=integrated,checks=checks,cases=results,hardware_qualified=False)
        h.attrs['summary_json']=json.dumps(summary)
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Completed',len(results),'cases',flush=True)
if __name__=='__main__':main()
