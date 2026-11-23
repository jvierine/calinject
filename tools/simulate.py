"""Reproducible circuit and system simulations; no measured hardware data.
Passive values are taken from cad/design.json. Active/RF IC behavior is not
represented by vendor transistor models. Provenance stays in code/HDF5.
"""
from pathlib import Path
import json, subprocess, sys
import numpy as np
import h5py

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'validation/simulation'
OUT.mkdir(exist_ok=True)
sys.path[:0] = [str(ROOT/'firmware'), str(ROOT/'host')]
from protocol import Servo
from calibration import tone_frequency, fit_clock

parts = {p['ref']: p for p in json.loads((ROOT/'cad/design.json').read_text())['parts']}

def value(ref):
    s = parts[ref]['value'].split()[0]
    for unit, scale in [('R',1),('k',1e3),('u',1e-6),('n',1e-9),('p',1e-12)]:
        if unit in s:
            a,b = s.split(unit)
            return float(a+'.'+b if b else a)*scale
    return float(s)

def spice(name, body, analysis, signals):
    path = OUT/(name+'.cir')
    path.write_text(f'Calinject {name}\n{body}\n.control\nset wr_singlescale\nset wr_vecnames\n{analysis}\nwrdata {OUT/(name+".txt")} {signals}\nquit\n.endc\n.end\n')
    run = subprocess.run(['ngspice','-b',str(path)],capture_output=True,text=True)
    (OUT/(name+'.log')).write_text(run.stdout+run.stderr)
    if run.returncode or 'Error:' in run.stderr: raise RuntimeError(run.stdout+run.stderr)
    data = np.loadtxt(OUT/(name+'.txt'),skiprows=1)
    (OUT/(name+'.txt')).unlink()  # Durable numeric products are HDF5.
    return data

result = {'models': 'Passive SPICE and synthetic system models; not hardware measurements', 'checks': {}}
with h5py.File(OUT/'results.h5','w') as f:
    f.attrs['generator'] = 'tools/simulate.py'
    f.attrs['model_limits'] = result['models']
    # 1 V Thevenin stimulus: a matched through connection gives 0.5 V.
    for label, refs in [('fixed',('R13','R14','R15')),('range',('R19','R20','R23'))]:
        a,b,c = map(value, refs)
        d = spice(label+'_pad',f'V1 src 0 AC 1\nRs src in 50\nC1 in a {value("C20")}\nRa a 0 {a}\nRb a out {b}\nRc out 0 {c}\nRl out 0 50',
                  'ac dec 100 500k 70meg','v(a) v(out)')
        hz=d[:,0]; vin=d[:,1]+1j*d[:,2]; vo=d[:,3]+1j*d[:,4]
        loss=-20*np.log10(abs(2*vo))
        # Include blocking capacitor in the impedance seen at the input port.
        zin=vin/((1-vin)/(50+1/(2j*np.pi*hz*value('C20'))))+1/(2j*np.pi*hz*value('C20'))
        rl=-20*np.log10(abs((zin-50)/(zin+50)))
        # 25dB is the passive subnetwork target; full-board criterion is 15dB.
        # The 100nF series capacitor limits the low-end return loss to ~30dB.
        result['checks'][label+'_pad']={'loss_db_min':float(loss.min()),'loss_db_max':float(loss.max()),'return_loss_db_min':float(rl.min()),'return_loss_target_db':25,'pass':bool(np.all((loss>19.8)&(loss<20.2)) and rl.min()>25)}
        g=f.create_group(label+'_pad');g['frequency_hz']=hz;g['loss_db']=loss;g['return_loss_db']=rl
    d=spice('dac_filter',f'V1 src 0 PULSE(0 1 1m 1n 1n 1 2)\nR1 src mid {value("R4")}\nC1 mid 0 {value("C11")}\nR2 mid out {value("R5")}\nC2 out 0 {value("C12")}\nRload out 0 500k', 'tran 50u 150m','v(out)')
    t,y=d[:,0],d[:,1];dc_gain=1/(1+(value("R4")+value("R5"))/500000);settling=float(t[np.flatnonzero(abs(y-dc_gain)>.001*dc_gain)[-1]]-.001)
    result['checks']['dac_filter']={'control_input_load_ohm':500000,'dc_gain':dc_gain,'settling_to_0_1_percent_s':settling,'servo_update_s':64,'pass':bool(settling<.2)}
    g=f.create_group('dac_filter');g['time_s']=t;g['voltage_v']=y
    # Ballasted dual output buffers driving a lossless 2m/50ohm cable. Driver
    # resistance is a sensitivity sweep, not an IBIS/transistor chip model.
    cables=[]
    for load in [50,1e6]:
        for driver in [0,5,15]:
            name='cable_%s_%s'%(int(load),driver)
            d=spice(name,f'V1 a 0 PULSE(0 3.3 20n 1n 1n 100n 250n)\nV2 b 0 PULSE(0 3.3 21n 1n 1n 100n 250n)\nR1 a sum {value("R24")+driver}\nR2 b sum {value("R25")+driver}\nR3 sum tx {max(value("R26"),.001)}\nT1 tx 0 rx 0 Z0=50 TD=10n\nRl rx 0 {load}', 'tran .1n 250n','v(rx) i(V1) i(V2)')
            high=d[(d[:,0]>70e-9)&(d[:,0]<100e-9),1]
            row=dict(load_ohm=load,assumed_driver_resistance_ohm=driver,steady_high_v=float(np.mean(high)),peak_v=float(max(d[:,1])),min_v=float(min(d[:,1])),peak_per_channel_current_ma=float(np.max(abs(d[:,2:]))*1e3))
            cables.append(row);g=f.create_group(name);g['time_s']=d[:,0];g['received_v']=d[:,1];g['channel_current_a']=d[:,2:]
    result['checks']['reference_cables']={'cable_delay_ns':10,'channel_skew_ns':1,'cases':cables,'qualification':'Source-terminated, DC-coupled outputs. Ideal lossless line and resistive drivers; ringing with real cables/ICs needs measurement.'}
    # RC threshold timing, before unknown Schmitt propagation delay/loading.
    d=spice('pulse_rc',f'V1 src 0 PULSE(0 3.3 10n .2n .2n 50n 100n)\nR1 src out {value("R10")}\nC1 out 0 {value("C17")}', 'tran .05n 300n','v(src) v(out)')
    g=f.create_group('pulse_rc');g['time_s']=d[:,0];g['input_v']=d[:,1];g['rc_v']=d[:,2]
    delays=[]
    for threshold in np.linspace(.3,.7,41):
        rising=np.flatnonzero((d[:-1,2]<3.3*threshold)&(d[1:,2]>=3.3*threshold))[0]+1
        delays.append(float((d[rising,0]-10e-9)*1e9))
    result['checks']['pulse_rc']={'threshold_fraction_sweep':[.3,.7],'rc_delay_ns_min':min(delays),'rc_delay_ns_max':max(delays),'qualification':'Not a pulse-width guarantee: gate propagation, input capacitance and actual thresholds excluded'}
    # True firmware servo, edge quantization, independent PPS jitter, temperature
    # random walk and initially inaccurate pull-slope calibration.
    rng=np.random.default_rng(20261123);tails=[];tracking=[];limits=0
    for trial in range(100):
        actual_slope=rng.uniform(80,150)*(3.3/4096)/(1+(value("R4")+value("R5"))/500000);zero=rng.uniform(1400,2300)
        s=Servo();phase=float(2**32-100);s.step(int(phase)&0xffffffff,True)
        jitter_prev=0.;thermal=0.;err=[]
        for second in range(7200):
            thermal+=rng.normal(0,.001)
            hz=1e7+(s.code-zero)*actual_slope+thermal
            jitter=rng.normal(0,20e-9)
            phase+=hz*(1+jitter-jitter_prev);jitter_prev=jitter
            s.step(int(phase)&0xffffffff,True)
            err.append(hz-1e7)
            limits+=s.state=='DAC_LIMIT'
        tails.append(np.sqrt(np.mean(np.square(err[-1800:]))));tracking.append(s.state=='TRACKING')
    result['checks']['servo']={'tuning_hz_per_volt_sweep':[80,150],'control_input_ohm':500000,'trials':100,'duration_s_each':7200,'pps_jitter_rms_ns':20,'tail_frequency_rms_hz_worst':float(max(tails)),'tracking_at_end':int(sum(tracking)),'dac_limit_samples':limits,'pass':bool(max(tails)<.15 and all(tracking) and limits==0)}
    f['servo_tail_rms_hz']=tails
    # 100us isolated complex pilot, white Gaussian noise, known sample rate.
    # This intentionally excludes receiver filter/group delay and pilot drift.
    fs=2e6;t=np.arange(200)/fs;errors=[]
    for snr in [10,20,30,40]:
        e=[]
        for _ in range(500):
            x=np.exp(2j*np.pi*12345.67*t)+10**(-snr/20)/np.sqrt(2)*(rng.normal(size=len(t))+1j*rng.normal(size=len(t)))
            e.append(tone_frequency(x,fs)['baseband_hz']-12345.67)
        errors.append(float(np.sqrt(np.mean(np.square(e)))))
    result['checks']['single_burst_frequency']={'burst_us':100,'sample_rate_hz':fs,'snr_db':[10,20,30,40],'frequency_error_rms_hz':errors,'qualification':'Finite precision per burst; average independent bursts or increase width for finer LO tracking'}
    f['single_burst_frequency_rms_hz']=errors
    # PPS markers with 100ns RMS timing error; missing markers are explicit.
    t=np.delete(np.arange(120,dtype=float),[7,19,20,83]);actual_fs=64e6*(1+2.5e-6)
    n=123.25+actual_fs*t+rng.normal(0,100e-9*actual_fs,len(t));fit=fit_clock(n,t+1780000000,64e6)
    result['checks']['sample_clock']={'marker_jitter_rms_ns':100,'seconds':120,'sample_rate_error_ppm_injected':2.5,'sample_rate_error_ppm_recovered':fit['sample_rate_error_ppm'],'anchor_error_ns':float((fit['anchor_sample']-123.25)/actual_fs*1e9),'pass':bool(abs(fit['sample_rate_error_ppm']-2.5)<.005)}
    f['clock_residual_samples']=fit['residual_samples']
result['all_asserted_checks_pass']=all(v.get('pass',True) for v in result['checks'].values())
(OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
if not result['all_asserted_checks_pass']: raise SystemExit(1)
