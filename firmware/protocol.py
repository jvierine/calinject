"""Portable UBX framing and Calinject servo. Runs under MicroPython and CPython."""
import struct

class MCP4725:
    """Reviewed A0/A1 address options, with the external A0 pin grounded.

    Microchip DS20002039F sections 6.1.1, 7.2 and ordering information.
    One DAC is required. Missing/ambiguous devices fail before RF is enabled.
    """
    def __init__(self,i2c):
        found=[a for a in i2c.scan() if a in (0x60,0x62)]
        if len(found)!=1:raise ValueError('Expected one MCP4725 at 0x60 or 0x62')
        self.i2c=i2c;self.address=found[0]

    def write(self,code):
        if not isinstance(code,int) or not 0<=code<=4095:
            raise ValueError('DAC code must be an integer in 0..4095')
        # Fast write: normal power, no EEPROM writes or endurance consumption.
        if self.i2c.writeto(self.address,bytes((code>>8,code&255)))!=2:
            raise OSError('Incomplete DAC write')

def packet(cls, ident, payload=b''):
    body=bytes((cls,ident))+struct.pack('<H',len(payload))+payload
    a=b=0
    for c in body:a=(a+c)&255;b=(b+a)&255
    return b'\xb5\x62'+body+bytes((a,b))

class Parser:
    def __init__(self):self.buf=bytearray();self.bad=0
    def feed(self,data):
        self.buf.extend(data);out=[]
        while len(self.buf)>=8:
            p=self.buf.find(b'\xb5\x62')
            if p<0:self.buf=self.buf[-1:];break
            if p:del self.buf[:p]
            if len(self.buf)<8:break
            n=self.buf[4]|(self.buf[5]<<8)
            if n>1024:del self.buf[0];self.bad+=1;continue
            if len(self.buf)<n+8:break
            raw=bytes(self.buf[:n+8]);del self.buf[:n+8]
            if packet(raw[2],raw[3],raw[6:-2])!=raw:self.bad+=1;continue
            out.append((raw[2],raw[3],raw[6:-2]))
        return out

def valset(items):
    # UBX CFG-VALSET, version0, RAM layer only. No flash wear or persistent assumptions.
    buf=bytearray(b'\0\1\0\0')
    for key,value,size in items:
        buf.extend(struct.pack('<I',key));buf.extend(int(value).to_bytes(size,'little'))
    return packet(6,0x8a,buf)

CONFIG=[
    (0x10740001,1,1), # UART1 UBX output
    (0x10740002,0,1), # UART1 NMEA output off
    (0x20910007,1,1), # UBX NAV-PVT
    (0x2091017e,1,1), # UBX TIM-TP (describes NEXT pulse)
    (0x30210001,1000,2), # measurement period ms
    (0x30210002,1,2), # navigation measurement ratio
    (0x20050023,0,1), # pulse definition PERIOD
    (0x20050030,1,1), # pulse length definition LENGTH
    (0x40050002,1000000,4),(0x40050003,1000000,4),
    (0x40050004,10000,4),(0x40050005,10000,4), # GNSS logic PPS width10ms
    (0x10050007,1,1),(0x10050008,1,1),(0x10050009,1,1),
    (0x1005000a,1,1),(0x1005000b,1,1),
    (0x2005000c,0,1), # UTC time grid; require UTC flags before arming
]

def timepulse(payload):
    if len(payload)!=16:return None
    tow,sub,qerr,week,flags,ref=struct.unpack('<IIiHBB',payload)
    # timebase UTC, UTC available, quantization valid, locked to GNSS.
    valid=(flags&3)==3 and not(flags&0x30) and tow%1000==0 and sub==0
    return dict(week=week,tow_ms=tow,sub_ms=sub,qerr_ps=qerr,flags=flags,ref_info=ref,valid=valid)

class Servo:
    """64-second frequency servo. Counts 10MHz edges; never claims phase lock.
    Nominal slope is measured/replaced during commissioning. 12-bit DAC sets a
    few-ppb frequency step; status frequency is an estimate, not exact truth.
    """
    def __init__(self,code=1862,slope_hz_per_code=.0806):
        self.code=code;self.slope=slope_hz_per_code;self.prev=None;self.total=0;self.n=0
        self.hz=None;self.good=0;self.state='ACQUIRE';self.enabled=True
    def reset_window(self):self.prev=None;self.total=0;self.n=0;self.good=0
    def step(self,count,valid):
        if not valid:
            self.reset_window();self.state='HOLDOVER';return False
        if self.prev is None:self.prev=count;self.state='ACQUIRE';return False
        delta=(count-self.prev)&0xffffffff;self.prev=count
        if not 9999000<=delta<=10001000:
            self.reset_window();self.state='COUNT_FAULT';return False
        self.total+=delta;self.n+=1
        if self.n<64:return False
        self.hz=self.total/self.n;err=self.hz-1e7;self.total=0;self.n=0
        if abs(err)<.15:self.good+=1
        else:self.good=0
        self.state='TRACKING' if self.good>=3 else 'ACQUIRE'
        if not self.enabled:self.state='MONITOR';return False
        change=round(-.5*err/self.slope);new=max(700,min(3000,self.code+change))
        if new in (700,3000):self.state='DAC_LIMIT';self.good=0
        changed=new!=self.code;self.code=new
        return changed
