# Connections and host control

These instructions apply to the current Rev A coupler board. The proposed lower-cost combiner board has not been implemented.

## Inline connection

```text
Receiving antenna → existing bias board → RF IN [Calinject] TO SDR → receiver
                                             GPS ANT ← active GPS antenna
                                             USB-C   ← computer
```

Both receiver-path ports block DC. Keep the existing antenna bias board on the antenna side and disable the SDR's bias tee. GPS ANT has a separate protected 3.3 V bias supply; use a compatible active antenna normally drawing at most 20 mA, and verify its minimum supply voltage against the measured feed voltage.

## External combiner connection

```text
50 Ω terminator → RF IN [Calinject] TO SDR → combiner calibration input
Receiving antenna / bias board ────────────→ combiner antenna input → SDR
```

Terminate RF IN in 50 Ω rather than leaving it open. Account for the external combiner's loss when setting the actual calibration level. Neither the current coupler nor an isolated hybrid combiner guarantees zero antenna leakage; their finite isolation and the actual receiver match matter.

## USB control

Run these examples from the repository root, replacing PORT with the actual serial device (`/dev/cu.usbmodem...` on macOS, often `/dev/ttyACM0` on Linux). Only one application can own the serial port at a time.

```bash
conda run -n base python -m pip install -r requirements.txt
conda run -n base python host/calinject.py PORT --send '{"cmd":"status"}'
conda run -n base python host/calinject.py PORT --send '{"cmd":"atten","db":31.5}'
conda run -n base python host/calinject.py PORT --send '{"cmd":"width","us":100}'
conda run -n base python host/calinject.py PORT --send '{"cmd":"ref10","enabled":true}'
conda run -n base python host/calinject.py PORT --send '{"cmd":"refpps","enabled":true}'
conda run -n base python host/calinject.py PORT --log status.h5
```

USB CDC carries newline-delimited JSON. Settings are RAM-only; restart restores default 100 µs bursts, maximum electronic attenuation, enabled servo and disabled reference outputs. The two internal range shunts provide an additional 20 dB pad and ship in LOW. See the [complete command list and programming instructions](../firmware/README.md).

Separate 10 MHz OUT and 1 PPS OUT connectors have nominal 50 Ω source impedance, with approximately 3.3 V into high impedance or 1.65 V into 50 Ω. The 10 MHz output is a square wave with no fixed phase relationship to PPS; PPS is a separate 10 ms GNSS pulse. Verify the external instrument's allowed voltage, waveform and termination before connection. See [reference output details](design.md#reference-outputs).

Record the USB status log with the SDR data, but do not use USB arrival time as a precision sample timestamp. Follow the [SDR calibration workflow](../host/README.md) for explicit epoch association, fixed-delay calibration, sample-rate fitting and frequency estimation. The 0.1–1 µs timing target requires receiver-specific measurements and a recording without unaccounted dropped samples.
