"""Execute the delivered main.py with deterministic peripheral models.
This is CPython execution of the control loop, not ARM/USB silicon emulation.
PIO models consume the real firmware descriptors; their instructions are checked
separately by verify_firmware.py. No-host USB models include the selected MicroPython CDC overwrite behavior
and a zero-progress/uninitialized transport, exposing host dependencies. Arrays and traces are stored in HDF5.
"""
from pathlib import Path
import sys,types,tempfile,os,json,struct,hashlib
from unittest.mock import patch
import numpy as np
import h5py
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'firmware'))
from protocol import packet
import settings
from status_led import GREEN,RED,AMBER,OFF
class StopSimulation(BaseException):pass

def simulate(name,duration_s=260,saved=None,usb='absent',fault=None):
    env={};pins={};sms={};events=[];led_trace=[];bursts=[];dac=[];feed=[];frames=[]
    class Clock:
        us=0
        def ticks_ms(self):return (self.us//1000)%(1<<30)
        def ticks_diff(self,a,b):return ((a-b+(1<<29))%(1<<30))-(1<<29)
        def advance(self,us):
            end=self.us+us
            for second in range(self.us//1000000+1,end//1000000+1):
                if not(fault=='pps_loss' and 210<=second<215):
                    if 0 in sms:sms[0].rx.append((second*10000000+(max(0,second-200)*100 if fault=='i2c' else 0))&0xffffffff)
                    if 1 in sms and sms[1].enabled and sms[1].tx:
                        descriptor=sms[1].tx.pop(0)
                        bursts.append((second,(descriptor+2)/125))
            self.us=end
            if self.us>=duration_s*1000000:raise StopSimulation()
        def sleep_ms(self,x):self.advance(x*1000)
        def sleep_us(self,x):self.advance(x)
    clock=Clock()
    class Pin:
        IN=0;OUT=1
        def __init__(self,n,mode=None,value=None):
            self.n=n
            if value is not None:self(value)
        def __call__(self,v=None):
            if v is not None:pins[self.n]=v
            return pins.get(self.n,0)
    class SM:
        def __init__(self,n,program,**kw):self.n=n;self.rx=[];self.tx=[];self.enabled=False;sms[n]=self
        def active(self,v=None):
            if v is not None:self.enabled=bool(v)
            return self.enabled
        def init(self,*a,**kw):self.tx=[]
        def rx_fifo(self):return len(self.rx)
        def tx_fifo(self):return len(self.tx)
        def get(self):return self.rx.pop(0)
        def put(self,x):self.tx.append(x)
    class UART:
        def __init__(self,*a,**kw):self.configs=0;self.acked=False;self.last=-1;self.sent_us=0
        def write(self,b):self.configs+=1;self.acked=False;self.sent_us=clock.us;return len(b)
        def read(self):
            ms=clock.us//1000;out=b''
            if self.configs and not self.acked and clock.us-self.sent_us>=100000 and fault!='no_ack':
                out+=packet(5,1,b'\x06\x8a');self.acked=True
            second=ms//1000
            if ms%1000>=100 and second!=self.last:
                self.last=second;valid=ms>=2000 and fault!='no_fix' and not(fault in ('gnss_loss','pps_loss') and 210<=second<215)
                nav=bytearray(92);struct.pack_into('<H',nav,4,2026);nav[6:11]=bytes((11,23,0,0,second%60));nav[11]=7 if valid else 0
                nav[20]=3 if valid else 0;nav[21]=1 if valid else 0;nav[23]=10
                out+=packet(1,7,nav)+packet(13,1,struct.pack('<IIiHBB',(second+1)*1000,0,0,2400,3 if valid else 0,0))
            return out or None
    class I2C:
        def __init__(self,*a,**kw):pass
        def scan(self):return [0x62]
        def writeto(self,address,b):
            assert address==0x62, 'Current build uses MCP4725A1'
            if fault=='i2c' and clock.us>=210000000:raise OSError('modeled I2C failure')
            dac.append((clock.us,int.from_bytes(b,'big')));return len(b)
    class ADC:
        def __init__(self,*a):pass
        def read_u16(self):return 32768
    class WDT:
        def __init__(self,timeout):self.timeout=timeout
        def feed(self):feed.append(clock.us)
    class Pixel:
        def __init__(self,*a):self.color=OFF
        def __setitem__(self,i,c):self.color=c
        def write(self):
            led_trace.append((clock.us,*self.color))
            # Conservative CPU occupancy for 24 bits plus reset. PIO advances
            # independently even if a WS2812 write straddles a PPS boundary.
            clock.advance(100)
    class Output:
        writes=0
        def __init__(self):self.buffer=self;self.retained=b''
        def write(self,s):
            self.writes+=1
            connected=usb=='connected' or (usb=='reconnect' and clock.us>=220000000) or (usb=='disconnect' and clock.us<220000000)
            assert isinstance(s,bytes) and len(s)==1,'Use uncooked binary one-byte writes'
            if usb=='uninitialized':return 0
            if connected:frames.append(s.decode('ascii'))
            else:self.retained=(self.retained+s)[-256:]
            return len(s)
    class Input:
        def read(self,n):raise AssertionError('Read without POLLIN')
    output=Output();input_=Input()
    class Poll:
        def register(self,stream,event):self.stream=stream
        def poll(self,timeout):
            assert timeout==0
            connected=usb=='connected' or (usb=='reconnect' and clock.us>=220000000) or (usb=='disconnect' and clock.us<220000000)
            ready=connected or usb in ('absent','uninitialized','disconnect','reconnect')
            return [(1,4)] if self.stream is output and ready else []
    modules={
        'machine':types.SimpleNamespace(Pin=Pin,UART=UART,I2C=I2C,ADC=ADC,WDT=WDT,freq=lambda x:None),
        'rp2':types.SimpleNamespace(asm_pio=lambda **k:lambda f:f,PIO=types.SimpleNamespace(OUT_LOW=0),StateMachine=SM),
        'neopixel':types.SimpleNamespace(NeoPixel=Pixel),
        'time':clock,'sys':types.SimpleNamespace(stdin=input_,stdout=output),
        'select':types.SimpleNamespace(poll=Poll,POLLIN=1,POLLOUT=4),
    }
    with tempfile.TemporaryDirectory() as d:
        previous=os.getcwd();os.chdir(d)
        try:
            if saved=='corrupt':Path('settings.json').write_text('{partial')
            elif saved is not None:settings.save(saved)
            with patch.dict(sys.modules,modules):
                try:exec(compile((ROOT/'firmware/main.py').read_text(),'main.py','exec'),env)
                except StopSimulation:pass
        finally:os.chdir(previous)
    trace=np.array(led_trace,dtype=np.int64);gaps=np.diff(feed)
    locked=env['servo'].state=='TRACKING'
    row=dict(name=name,duration_s=duration_s,usb=usb,fault=fault,settings_loaded=env.get('settings_loaded'),
             burst_count=len(bursts),width_us=env.get('width_us'),max_telemetry_frames=len(env['telemetry'].frames),
             telemetry_dropped=env['telemetry'].dropped,stdout_write_calls=output.writes,
             final_servo=env['servo'].state,final_led=env['led'].state,
             max_watchdog_feed_gap_ms=float(max(gaps)/1000) if len(gaps) else None,
             ref10_enabled=not pins.get(4,1),refpps_enabled=not pins.get(9,1),
             led_writes=len(trace),fatal_muted=pins.get(8)==0 and not sms[1].enabled)
    checks={'startup_green':tuple(trace[0,1:])==GREEN,'bounded_usb_queue':row['max_telemetry_frames']<=8,
            'watchdog_fed':row['max_watchdog_feed_gap_ms']<8000}
    if usb in ('absent','uninitialized'):checks['bounded_transport_retention']=len(output.retained)<=256
    if fault is None:
        checks.update(servo_tracks=locked,correct_burst_width=all(abs(w-env['width_us'])<.001 for _,w in bursts),
                      autonomous_bursts=len(bursts)>duration_s-10,
                      green_pps_when_locked=tuple(trace[-2,1:])==GREEN and tuple(trace[-1,1:])==OFF)
        if isinstance(saved,dict):checks['saved_settings_restored']=row['settings_loaded'] and row['width_us']==saved['width_us'] and row['ref10_enabled']==saved['ref10'] and row['refpps_enabled']==saved['refpps']
    elif fault=='no_fix':checks.update(acquisition_amber=tuple(trace[-1,1:])==AMBER,no_bursts=not bursts)
    elif fault=='no_ack':checks.update(fault_red=any(tuple(x[1:])==RED for x in trace),no_bursts=not bursts)
    elif fault=='i2c':checks.update(fatal_muted=row['fatal_muted'],fault_red=any(tuple(x[1:])==RED for x in trace))
    else:
        checks.update(fault_red=any(tuple(x[1:])==RED for x in trace),loss_suppresses_bursts=not any(212<=t<216 for t,_ in bursts),reacquires=env['config_ok'])
    if row['fatal_muted']:row['final_led']='FAULT'
    row['checks']=checks;row['all_pass']=all(checks.values())
    return row,dict(led=trace,bursts=np.array(bursts),dac=np.array(dac),watchdog_feed_us=np.array(feed))

def main():
    out=ROOT/'validation/end-to-end';out.mkdir(exist_ok=True);rows=[]
    persisted=dict(settings.DEFAULTS,width_us=1000,atten_code=40,ref10=True,refpps=True)
    cases=[dict(name='power_only_defaults'),dict(name='usb_uninitialized',usb='uninitialized'),dict(name='host_stalled',usb='stalled'),dict(name='power_only_saved',saved=persisted),
           dict(name='power_only_long_pulse',saved=dict(persisted,width_us=900000)),
           dict(name='corrupt_settings_fallback',saved='corrupt'),
           dict(name='host_disconnect',usb='disconnect'),
           dict(name='no_gps_fix',fault='no_fix',duration_s=40),
           dict(name='host_connected',usb='connected'),dict(name='host_reconnect',usb='reconnect'),
           dict(name='gnss_loss_recovery',fault='gnss_loss'),dict(name='pps_loss_recovery',fault='pps_loss'),
           dict(name='config_failure',fault='no_ack',duration_s=40),dict(name='fatal_i2c',fault='i2c')]
    with h5py.File(out/'standalone.h5','w') as h:
        h.attrs['scope']='Actual main.py control-loop execution; modeled peripherals; no hardware measurement'
        for case in cases:
            row,arrays=simulate(**case);rows.append(row);g=h.create_group(row['name'])
            for k,v in arrays.items():g[k]=v
            g.attrs['summary_json']=json.dumps(row);print(json.dumps(row),flush=True)
        h.attrs['source_sha256']=json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'firmware').glob('*.py')})
    result=dict(cases=rows,all_pass=all(r['all_pass'] for r in rows),hardware_tested=False)
    (out/'standalone-summary.json').write_text(json.dumps(result,indent=2)+'\n')
    assert result['all_pass'],result
if __name__=='__main__':main()
