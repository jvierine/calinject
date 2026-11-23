# Firmware

Target: genuine Waveshare RP2040-Zero, MicroPython RP2, 125 MHz system clock. Factory assembler performs initial programming. No soldering is needed to update firmware later.

1. With the lid removed, hold BOOT and connect USB-C. Load the stable UF2 for [WAVESHARE_RP2040_ZERO](https://micropython.org/download/WAVESHARE_RP2040_ZERO/). Version 1.29.0 is the selected baseline; the firmware still needs an on-device first-article test.
2. Install `mpremote` in the host Python environment. Copy `firmware/protocol.py`, `firmware/telemetry.py`, `firmware/settings.py` and `firmware/main.py` to the device filesystem using `mpremote connect PORT fs cp ... :protocol.py` and `:main.py`, then reset.
3. Connect an active 3.3 V GPS antenna with a clear sky view. Check USB `status` and the GNSS configuration ACK. The frequency servo takes several minutes to establish TRACKING.
4. Run the first-article procedure in `docs/acceptance.md`. Save the firmware version and board serial number with the results.

Factory example, from repository root:

```bash
conda run -n base python -m pip install mpremote
conda run -n base python -m mpremote connect PORT fs cp firmware/protocol.py :protocol.py
conda run -n base python -m mpremote connect PORT fs cp firmware/telemetry.py :telemetry.py
conda run -n base python -m mpremote connect PORT fs cp firmware/settings.py :settings.py
conda run -n base python -m mpremote connect PORT fs cp firmware/main.py :main.py
conda run -n base python -m mpremote connect PORT reset
```

## USB protocol

115200 baud nominal, newline-delimited JSON. USB CDC ignores the physical baud-rate setting. Commands and status share one port. Settings are RAM-only until `{"cmd":"save"}` is sent. Saving atomically writes a validated settings file; a valid file restores width, mode, attenuation, trimmer/servo settings, tuning slope/DAC and reference enables at boot. Without a valid file the safe defaults are 100 µs bursts, 31.5 dB attenuation, enabled servo and disabled references. A saved continuous mode intentionally resumes continuous injection after reset. The physical range shunts determine the extra 20 dB pad. Default assembly is LOW.

| JSON command | Effect |
|---|---|
| `{"cmd":"status"}` | Current state and GNSS validity |
| `{"cmd":"save"}` | Persist current settings; use between recordings |
| `{"cmd":"width","us":100}` | 1–900000 µs hardware-timed burst |
| `{"cmd":"atten","db":31.5}` | 0–31.5 dB in 0.5 dB steps; disables trimmer control |
| `{"cmd":"manual","enabled":true}` | Enables the LEVEL trimmer |
| `{"cmd":"mode","value":"burst"}` | One burst per valid UTC PPS |
| `{"cmd":"mode","value":"mute"}` | Forces gate low |
| `{"cmd":"mode","value":"continuous"}` | Explicit continuous RF, including without GNSS lock |
| `{"cmd":"ref10","enabled":true}` | Enables dedicated 10 MHz SMA square-wave output |
| `{"cmd":"refpps","enabled":true}` | Enables dedicated GNSS PPS SMA output |
| `{"cmd":"servo","enabled":false}` | Stops DAC correction; continues monitoring |
| `{"cmd":"slope","hz_per_code":0.0806}` | Set the measured tuning slope |
| `{"cmd":"dac","code":1862}` | Manual DAC, range700–3000; disables servo |

Commands interrupt any queued burst when changing width or mode. A short gap in calibration is intentional. Settings should normally be changed between recordings. Manual attenuation changes can happen during bursts, so disable manual mode for precision amplitude work.

Hardware pullups disable the reference buffers during reset. Startup restores explicitly saved enables, otherwise both remain disabled. Set `enabled:false` to disable either output. While enabled, they follow the source clock directly; GPS validity does not automatically suppress them. Status reports `ref10_enabled` and `refpps_enabled`. Enable before starting acquisition because enabling/disabling can shorten a pulse. The 10 MHz is frequency disciplined but has no fixed phase relationship to PPS.

## Timing and failure behavior

A PIO state machine counts the comparator's 10 MHz edges and captures the count at PPS, with up to one 10 MHz cycle of count quantization. A separate PIO state machine controls the burst gate directly from PPS. USB and Python scheduling do not time the gate edge.

Each queued descriptor authorizes one burst; firmware starvation cannot cause a free-running sequence of bursts. USB telemetry uses an eight-record bounded queue, at most 2048 ASCII bytes per record. Each control-loop pass writes at most 64 single bytes, each only after a writable poll. A slow host causes whole unsent records to be dropped, with cumulative `telemetry_dropped` reporting; no full-record blocking print or flush is used. Readable command input is also bounded per pass. A watchdog remains as a fallback for other processor stalls. Loss of valid UTC time mutes burst mode, while continuous mode remains under explicit user control. A descriptor already waiting for the next PPS can produce one final burst after a software stall or late loss-of-lock notification. Reject that event if its log record is invalid or missing.

After a PPS timeout the firmware reissues RAM configuration, allowing recovery if a GNSS power fault cleared its settings. Failed configuration is retried at two-second intervals initially, then every 30 seconds; it does not silently assume the receiver retained its configuration.

TIM-TP describes the next pulse. The firmware checks UTC availability, time-grid/lock flags, quantization-error validity, integer seconds, sequential epochs and message arrival between observed PPS edges. Initial pulses are deliberately not armed until association is established. NAV-PVT is logged as context; it is not the timestamp of the RF burst. Leap-second/discontinuity intervals are conservatively rejected.

`boot_id` changes on restart. Never join count sequences across boot IDs, capture overruns, timeout events or missing records. `burst_armed` records software authorization; it is not an independent electrical measurement that the burst appeared at the SMA.

The default frequency servo uses 64 one-second count intervals and a conservative half-gain correction. DAC resolution and oscillator pull slope set a frequency floor. TRACKING means three successive frequency windows within 0.15 Hz at10MHz; it does not assert a specific Allan deviation, absolute phase or timing error. `reference_hz` describes the last completed window, including its previous DAC setting; it is not an instantaneous post-correction frequency.

The transport/settings tests exercise stopped readers, partial writes, queue overflow, reconnect-style draining, corrupt settings and interrupted-save recovery. `tests/test_core.py` includes instruction-level PIO timing/count simulations and protocol/servo tests. These omit metastability, analogue thresholds, oscillator phase noise and USB runtime behavior; real RP2040 tests remain required.

The bounded writer relies on the stock RP2 MicroPython 1.29.0 CDC poll/write implementation and a single stdout writer. Do not add direct `print()` calls or competing stdout writers to the control loop. An incomplete first line on USB reconnect can be discarded by the host JSON parser. The source-level contract is checked against the [MicroPython CDC implementation](https://github.com/micropython/micropython/blob/v1.29.0/shared/tinyusb/mp_usbd_cdc.c).

The pinned release uses the [MicroPython TinyUSB fork at b549ac1](https://github.com/micropython/tinyusb/blob/b549ac1d84cbbe550c9590951e2290098b3fb16c/src/class/cdc/cdc_device.c): disconnected CDC transmit data can overwrite old FIFO data; with DTR asserted the writable poll requires FIFO space. This is why individual writable-checked bytes are used instead of a full-record write. Keep the selected runtime version for factory qualification.

The USB `width` command controls the RF injection burst (1–900000 µs); the dedicated 1 PPS SMA remains the configured GNSS 10 ms pulse. `atten` controls the PE4312 in 0.5 dB steps over 0–31.5 dB. The physical range jumper supplies a separate 20 dB range change. DAC updates steer frequency through the RC filter without an intentional phase reset; no configurable firmware slew-rate limiter is implemented. See the end-to-end phase/steering model for assumptions and measured-test requirements.
