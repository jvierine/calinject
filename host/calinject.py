"""Calinject USB control and HDF5 status logging. No serial arrival time is PPS time."""
import argparse,json,time
import h5py,numpy as np,serial

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('port');ap.add_argument('--send',help='one JSON command');ap.add_argument('--log',help='new HDF5 status file');ap.add_argument('--seconds',type=float,default=0)
    a=ap.parse_args()
    if not a.send and not a.log:ap.error('use --send or --log')
    f=h5py.File(a.log,'x') if a.log else None
    if f:
        f.attrs['schema']='calinject-status-v1';f.attrs['host_time_note']='USB arrival time only; use UBX TIM-TP for pulse epoch'
        rows=f.create_dataset('records',shape=(0,),maxshape=(None,),dtype=h5py.string_dtype('utf-8'),chunks=(128,))
        ts=f.create_dataset('host_arrival_unix_ns',shape=(0,),maxshape=(None,),dtype='i8',chunks=(128,))
    try:
        with serial.Serial(a.port,115200,timeout=1) as s:
            if a.send:s.write((json.dumps(json.loads(a.send))+'\n').encode())
            else:s.write(b'{"cmd":"status"}\n')
            start=time.monotonic()
            while not a.seconds or time.monotonic()-start<a.seconds:
                line=s.readline();stamp=time.time_ns()
                if not line:continue
                try:obj=json.loads(line)
                except (ValueError,UnicodeDecodeError):continue
                print(json.dumps(obj),flush=True)
                if f:
                    n=len(rows);rows.resize(n+1,axis=0);ts.resize(n+1,axis=0);rows[n]=json.dumps(obj);ts[n]=stamp;f.flush()
                if a.send and not a.log and (obj.get('event')=='status' or 'ok' in obj or 'error' in obj):break
    except KeyboardInterrupt:pass
    finally:
        if f:f.close()
if __name__=='__main__':main()
