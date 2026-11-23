"""Bounded USB telemetry. One-byte writes only after a writable poll.
No waiting for host space and no print/flush calls in the control loop.
"""
class Telemetry:
    def __init__(self,stream,writable,max_frames=8,max_frame=2048):
        self.stream=stream;self.writable=writable;self.max_frames=max_frames
        self.max_frame=max_frame;self.frames=[];self.offset=0;self.dropped=0
    def enqueue(self,line):
        frame=line+'\n'
        if len(frame)>self.max_frame or any(ord(c)>127 for c in frame):
            self.dropped+=1;return False
        if len(self.frames)>=self.max_frames:
            # Never truncate a frame already partly sent. Drop the oldest whole
            # unsent frame, keeping newer telemetry and explicit loss accounting.
            index=1 if self.offset else 0
            if index>=len(self.frames):self.dropped+=1;return False
            self.frames.pop(index);self.dropped+=1
        self.frames.append(frame);return True
    def pump(self,budget=64):
        sent=0
        while self.frames and sent<budget and self.writable():
            # RP2 CDC POLLOUT guarantees at least one free byte, not enough for
            # a whole JSON record. A single writer uses that space immediately.
            try:n=self.stream.write(self.frames[0][self.offset:self.offset+1])
            except OSError:break
            if not n:break
            self.offset+=1;sent+=1
            if self.offset==len(self.frames[0]):self.frames.pop(0);self.offset=0
        return sent
