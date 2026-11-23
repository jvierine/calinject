"""Calinject Rev C firmware for MicroPython RP2040 (Waveshare RP2040-Zero).
PIO owns edge counting and gate timing; Python/USB latency cannot move the gate.
Prototype firmware: execute the documented logic-analyzer acceptance tests.
"""
from machine import Pin,UART,I2C,ADC,freq,WDT
import rp2,sys,select,time,json,os
import neopixel
from status_led import StatusLED,RED,OFF,GREEN
pixel=neopixel.NeoPixel(Pin(16),1)
def led_write(color):
    pixel[0]=color;pixel.write()
led=StatusLED(led_write,time.ticks_diff)
boot_ms=time.ticks_ms();led.set(GREEN)
from protocol import Parser,packet,valset,CONFIG,timepulse,Servo
from telemetry import Telemetry
import settings
try:
    freq(125000000)
    CLK=11;PPS=10;GATE=8
    # Never enable pull-down on PPS: MAX-M10S shares it with SAFEBOOT_N.
    Pin(PPS,Pin.IN);Pin(CLK,Pin.IN);Pin(GATE,Pin.OUT,value=0)
    # Dedicated reference buffers default disabled. Pullups also disable them while
    # the processor is reset. Inputs are direct hardware clocks, not Python toggles.
    ref10_oe=Pin(4,Pin.OUT,value=1);refpps_oe=Pin(9,Pin.OUT,value=1)

    @rp2.asm_pio()
    def counter():
        mov(x,invert(null))
        label('low')
        wait(0,gpio,11)
        wait(1,gpio,11)
        jmp(x_dec,'check_low')
        label('check_low')
        jmp(pin,'capture')
        jmp('low')
        label('capture')
        mov(isr,invert(x))
        push(noblock)
        label('high')
        wait(0,gpio,11)
        wait(1,gpio,11)
        jmp(x_dec,'check_high')
        label('check_high')
        jmp(pin,'high')
        jmp('low')

    @rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
    def burst():
        pull(block)
        mov(x,osr)
        wait(0,gpio,10)
        wait(1,gpio,10)
        set(pins,1)
        label('delay')
        jmp(x_dec,'delay')
        set(pins,0)
        # One descriptor authorizes one burst. Starvation fails muted.
        wrap()

    smc=rp2.StateMachine(0,counter,freq=125000000,jmp_pin=Pin(PPS))
    smg=rp2.StateMachine(1,burst,freq=125000000,set_base=Pin(GATE))
    smc.active(1);smg.active(1)
    uart=UART(0,baudrate=9600,tx=Pin(0),rx=Pin(1),rxbuf=4096)
    i2c=I2C(1,sda=Pin(2),scl=Pin(3),freq=100000)
    le=Pin(7,Pin.OUT,value=0);clk=Pin(6,Pin.OUT,value=0);dat=Pin(5,Pin.OUT,value=0)
    adc=ADC(29);parser=Parser();servo=Servo();width_us=100;mode='burst';att=63
    manual=False;pending=None;last_pps=None;seq=0;config_ok=False;nav=None
    last_count=None;last_valid_ms=None;fault_ms=None;cmd='';armed_seq=None;last_tp_key=None
    poll=select.poll();poll.register(sys.stdin,select.POLLIN)
    outpoll=select.poll();outpoll.register(sys.stdout.buffer,select.POLLOUT)
    def writable():
        return any(event[1]&select.POLLOUT for event in outpoll.poll(0))
    telemetry=Telemetry(sys.stdout.buffer,writable,binary=True)

    def emit(x):
        x['firmware']='C-0.4.1'
        x['telemetry_dropped']=telemetry.dropped
        telemetry.enqueue(json.dumps(x))

    def attenuation(code):
        global att
        att=max(0,min(63,int(code)));le(0)
        for bit in range(5,-1,-1):
            clk(0);dat((att>>bit)&1);time.sleep_us(2);clk(1);time.sleep_us(2)
        clk(0);le(1);time.sleep_us(2);le(0)

    def dac():i2c.writeto(0x60,bytes(((servo.code>>8)&15,servo.code&255)))

    def mute_gate():
        global pending,armed_seq
        smg.active(0);Pin(GATE,Pin.OUT,value=0)
        smg.init(burst,freq=125000000,set_base=Pin(GATE));smg.active(1)
        pending=None;armed_seq=None

    boot_id=''.join('%02x'%x for x in os.urandom(8))
    saved,settings_loaded=settings.load()
    width_us=saved['width_us'];mode=saved['mode'];manual=saved['manual']
    servo.slope=saved['slope'];servo.code=saved['dac'];servo.enabled=saved['servo']
    attenuation(saved['atten_code']);dac()
    ref10_oe(0 if saved['ref10'] else 1);refpps_oe(0 if saved['refpps'] else 1)
    if mode=='continuous':smg.active(0);Pin(GATE,Pin.OUT,value=1)
    uart.write(valset(CONFIG))
    config_sent=time.ticks_ms();retries=0;wdt=WDT(timeout=8000)
    while True:
        now=time.ticks_ms();wdt.feed()
        # Drain captures before UART: a TIM-TP arriving just after a pulse describes
        # the following pulse and must not be assigned retrospectively.
        fifo=smc.rx_fifo()
        if fifo>1:
            fault_ms=now
            while smc.rx_fifo():smc.get()
            servo.reset_window()
            if mode!='continuous':mute_gate()
            last_pps=None
            led.update(now,boot_ms,config_ok,last_pps,last_valid_ms,servo.state,True)
            emit({'event':'capture_overrun','boot_id':boot_id});continue
        if fifo:
            count=smc.get();seq+=1;interval=None if last_pps is None else time.ticks_diff(now,last_pps)
            valid=(pending is not None and pending['valid'] and interval is not None and 900<interval<1100 and time.ticks_diff(now,pending['received_ms'])<950)
            if valid:last_valid_ms=now
            if servo.step(count,valid):dac()
            emit(dict(event='pps',boot_id=boot_id,seq=seq,count=count,valid=valid,
                      tp=pending,burst_us=width_us,mode=mode,burst_armed=(armed_seq is not None),attenuation_db=att*.5,
                      servo=servo.state,dac=servo.code,reference_hz=servo.hz,
                      reference_estimate_window_s=64,gnss=nav,
                      ref10_enabled=not ref10_oe(),refpps_enabled=not refpps_oe(),led_state=led.state))
            pending=None;armed_seq=None;last_pps=now;last_count=count
        raw=uart.read()
        if raw:
            for cls,ident,p in parser.feed(raw):
                if cls==5 and p==b'\x06\x8a':
                    config_ok=(ident==1)
                    emit({'event':'gnss_config_ack','ok':config_ok})
                elif (cls,ident)==(1,7) and len(p)>=92:
                    import struct
                    nav=dict(year=struct.unpack_from('<H',p,4)[0],month=p[6],day=p[7],hour=p[8],minute=p[9],second=p[10],valid=p[11],tacc_ns=struct.unpack_from('<I',p,12)[0],fix=p[20],flags=p[21],satellites=p[23])
                elif (cls,ident)==(13,1):
                    tp=timepulse(p)
                    if tp:
                        # First pulse establishes phase. Accept messages only well
                        # between observed pulses, not near an ambiguous boundary.
                        age=9999 if last_pps is None else time.ticks_diff(now,last_pps)
                        key=(tp['week'],tp['tow_ms'])
                        if 20<age<900 and key!=last_tp_key and config_ok:
                            sequential=(last_tp_key is not None and (key[0]*604800000+key[1])-(last_tp_key[0]*604800000+last_tp_key[1])==1000)
                            tp['valid']=tp['valid'] and sequential and (nav is not None and (nav['valid']&7)==7 and nav['second']<60)
                            tp['received_ms']=now;pending=tp;last_tp_key=key
                            if tp['valid'] and mode=='burst':
                                if smg.tx_fifo()==0:
                                    smg.put(int(width_us*125)-2);armed_seq=key
                            elif not tp['valid'] and mode!='continuous':mute_gate()
        if not config_ok and time.ticks_diff(now,config_sent)>(2000 if retries<5 else 30000):
            uart.write(valset(CONFIG));config_sent=now;retries+=1
        if last_pps is not None and time.ticks_diff(now,last_pps)>1500:
            servo.state='NO_PPS';servo.reset_window()
            if mode!='continuous':mute_gate()
            # RAM configuration can be lost after a GNSS rail fault. Retry without
            # a permanent cutoff, at a slower rate after the initial attempts.
            config_ok=False;retries=0;config_sent=now;uart.write(valset(CONFIG))
            last_pps=None;emit({'event':'pps_timeout','boot_id':boot_id})
        for _ in range(128):
            if not any(event[1]&select.POLLIN for event in poll.poll(0)):break
            c=sys.stdin.read(1)
            if not c:break
            if c in '\r\n':
                if not cmd:continue
                try:
                    obj=json.loads(cmd);op=obj.get('cmd')
                    if op=='status':emit(dict(event='status',boot_id=boot_id,mode=mode,width_us=width_us,attenuation_db=att*.5,servo=servo.state,dac=servo.code,reference_hz=servo.hz,config_ok=config_ok,gnss=nav,parser_errors=parser.bad,manual_level=manual,ref10_enabled=not ref10_oe(),refpps_enabled=not refpps_oe(),led_state=led.state))
                    elif op in ['ref10','refpps']:
                        enabled=obj['enabled']
                        if not isinstance(enabled,bool):raise ValueError('enabled must be boolean')
                        (ref10_oe if op=='ref10' else refpps_oe)(0 if enabled else 1)
                        emit({'ok':True,op+'_enabled':enabled})
                    elif op=='width':
                        x=int(obj['us'])
                        if not 1<=x<=900000:raise ValueError('width must be 1..900000 us')
                        mute_gate();width_us=x
                        if mode=='continuous':smg.active(0);Pin(GATE,Pin.OUT,value=1)
                        emit({'ok':True,'width_us':x})
                    elif op=='atten':
                        x=float(obj['db'])
                        if not 0<=x<=31.5:raise ValueError('attenuation must be 0..31.5 dB')
                        manual=False;attenuation(round(2*x));emit({'ok':True,'attenuation_db':att*.5})
                    elif op=='manual':manual=bool(obj['enabled']);emit({'ok':True,'manual_level':manual})
                    elif op=='mode':
                        x=obj['value']
                        if x not in ['burst','mute','continuous']:raise ValueError('invalid mode')
                        mute_gate();mode=x
                        if x=='continuous':smg.active(0);Pin(GATE,Pin.OUT,value=1)
                        emit({'ok':True,'mode':mode})
                    elif op=='servo':servo.enabled=bool(obj['enabled']);emit({'ok':True})
                    elif op=='slope':
                        x=float(obj['hz_per_code'])
                        if not .01<x<.5:raise ValueError('slope outside expected range')
                        servo.slope=x;servo.reset_window();emit({'ok':True})
                    elif op=='dac':
                        x=int(obj['code'])
                        if not 700<=x<=3000:raise ValueError('DAC must be700..3000')
                        servo.enabled=False;servo.code=x;servo.reset_window();dac();emit({'ok':True})
                    elif op=='save':
                        # Deliberately omit the next burst while flash is written.
                        # PIO still counts clocks; control loop resumes after save.
                        if mode!='continuous':mute_gate()
                        settings.save(dict(width_us=width_us,mode=mode,atten_code=att,
                            manual=manual,servo=servo.enabled,slope=servo.slope,dac=servo.code,
                            ref10=not ref10_oe(),refpps=not refpps_oe()))
                        emit({'ok':True,'settings_saved':True})
                    else:raise ValueError('unknown command')
                except Exception as e:emit({'error':str(e)})
                cmd=''
            elif len(cmd)<255:cmd+=c
            else:cmd=''
        if manual:
            new=round(adc.read_u16()*63/65535)
            if abs(new-att)>=2:attenuation(new)
        led.update(now,boot_ms,config_ok,last_pps,last_valid_ms,servo.state,
                   fault_ms is not None and time.ticks_diff(now,fault_ms)<2000)
        telemetry.pump(64)
        time.sleep_ms(2)
except Exception:
    led.state='FAULT'
    # A fatal control-loop error leaves the gate muted and cable drivers off.
    # Keep a visible fault until power cycle/reset; USB commands cannot recover it.
    for pin,value in ((8,0),(4,1),(9,1)):
        Pin(pin,Pin.OUT,value=value)
    try:smg.active(0)
    except Exception:pass
    while True:
        if 'wdt' in globals():wdt.feed()
        led.set(RED if (time.ticks_diff(time.ticks_ms(),boot_ms)//250)%2==0 else OFF)
        time.sleep_ms(10)
