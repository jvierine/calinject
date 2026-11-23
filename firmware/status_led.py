"""Visible state only: the LED is never a precision timing output.
The module's WS2812 is latched between writes, so no LED PWM timer or PIO
state machine competes with the PPS counter/gate. Brightness is deliberately low.
"""
OFF=(0,0,0);GREEN=(0,12,0);AMBER=(10,4,0);RED=(12,0,0)
class StatusLED:
    def __init__(self,write,ticks_diff):
        self.write=write;self.diff=ticks_diff;self.color=None;self.state='STARTUP'
    def set(self,color):
        if color!=self.color:self.write(color);self.color=color
    def update(self,now,boot_ms,configured,last_pps,last_valid,servo,fault=False):
        # Faults take precedence over startup and green PPS flashes.
        lost=last_valid is not None and self.diff(now,last_valid)>1500
        fault=fault or lost or servo in ('COUNT_FAULT','DAC_LIMIT','NO_PPS')
        if not configured and self.diff(now,boot_ms)>30000:fault=True
        if fault:
            self.state='FAULT';color=RED if (self.diff(now,boot_ms)//250)%2==0 else OFF
        elif not configured:self.state='STARTUP';color=GREEN
        elif servo=='TRACKING' and last_valid is not None and last_pps==last_valid:
            self.state='LOCKED';color=GREEN if 0<=self.diff(now,last_pps)<100 else OFF
        else:self.state='ACQUIRING';color=AMBER
        self.set(color)
        return self.state
