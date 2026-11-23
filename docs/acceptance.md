# First-article and production acceptance

Status: **first-article measurements not yet performed**. The customer performs this procedure after receipt and USB-C programming; custom factory qualification is excluded from the assembly quote. Qualify one board before relying on the batch for measurements. No RF test result may be replaced by an ideal circuit simulation.

## Before applying power

Inspect MPNs, pin-1 orientation, QFN soldering and the GNSS module. Check SMA center-to-ground resistance: the external ports have DC-blocking capacitors and 1 MΩ bleeders. The transformer combiner has internal DC paths behind those capacitors. Inspect module/header soldering, both range shunts and case clearance. X-ray U9's exposed-pad solder joint if available.

## Power and USB

Use a current-limited 5 V USB supply initially. Verify no rail short; check3V3A,3V3G and3V3D are3.3V within5%. Measure current with the GPS antenna disconnected and attached. First-article target is under250mA; investigate higher draw before release. USB-C operation must be checked with both C-to-C and A-to-C cables and both plug orientations.

At GPS ANT, measure bias voltage at no load and with a representative active antenna load. F2 is a 50 mA hold-current resettable fuse, not a precision current limiter. Select an antenna drawing at most 20 mA in normal operation; verify the voltage remaining after the fuse and choke meets its specification. The feed can lose about 0.4 V at 20 mA using the fuse's 20 Ω post-trip maximum resistance, before temperature/inductor effects. R1 is a zero-ohm link. Test a brief current-limited antenna short and recovery without damaging the receiver or resetting USB; verify GNSS reconfiguration/reacquisition if its rail momentarily collapses.

Load the specified MicroPython UF2 and all five firmware files (main.py, protocol.py, telemetry.py, settings.py, status_led.py). Remove any old settings.json for the default factory test; save the measured slope only after commissioning. Confirm a USB status response and successful GNSS RAM-configuration ACK. Package the board with both JP1 shunts in LOW and maximum electronic attenuation.

## Oscillator and comb

Use a high-impedance probe on TP2; avoid loading the raw clipped-sine oscillator. Confirm10MHz counts, correct comparator logic levels and no double transitions. Sweep DAC700,1862,3000 with the servo disabled. Record oscillator frequency and tuning slope. Confirm monotonic positive pull, tuning coverage around10MHz, and control voltage inside0.5–2.5V. Enter the measured Hz/code slope for this serial number.

Measure COMB_RAW with an appropriate low-capacitance high-bandwidth probe. Check the pulse is approximately7–12ns. Verify no missing even harmonics and no near-null at70MHz. R10/C17 set the comb pulse shape; their values must be revised and requalified if the first article does not give usable10–70MHz lines. The user must not be expected to tune hardware.

Measure each10MHz harmonic with a spectrum analyzer at0,15.5,31.5dB settings, in both physical ranges. Use continuous mode for level characterization, then verify burst-on levels agree. Record actual dBm, setting error, frequency and linewidth. Measure muted-mode leakage with USB attached and active; supply/PCB coupling can bypass the logical gate and attenuator. Accept leakage only when below the stated application noise/spur requirement; a default target is at least40dB below the corresponding enabled line, and below the receiver's scientific interference threshold.

Check aggregate comb peak level and out-of-band harmonics. The comb intentionally extends above70MHz; it is not a70MHz-low-pass output. Receiver front-end/anti-alias filtering remains necessary.

## Combiner and receiver isolation

Use a calibrated VNA with all unused ports terminated in50Ω. Measure RF IN→TO SDR insertion loss/return loss over the quoted operating band. Measure calibration-to-SDR and calibration-to-antenna transfer at10,20,30,40,50,60,70MHz using an RF fixture at the calibration branch. Branch isolation must be measured with the sum port matched, not inferred from the drawing.

Proposed first-article acceptance: antenna-to-SDR loss no greater than 4 dB over 0.5–70 MHz, input/output return loss at least 15 dB, and calibration-to-antenna branch isolation at least 20 dB at all used harmonics. Record the actual (approximately 3.2 dB) calibration-to-SDR loss separately. These are release criteria to measure, not established guarantees. Document any narrower qualified band rather than accepting a failing sample silently.

Repeat with the actual SDR powered and configured. Measure calibration energy returning toward the antenna. Receiver return loss can dominate this measurement even if the combiner alone passes. If unacceptable, qualify a matching pad, buffer or different receiver interface and include its loss in the system budget.

## Dedicated reference outputs

With settings.json absent, verify both SMA reference buffers are disabled at startup and after watchdog reset. Then explicitly save enabled reference settings and verify they restore after a power cycle; finally return to the safe factory defaults. Enable each separately with `ref10`/`refpps`; confirm their behavior is independent of injection width, mute/continuous modes and electronic attenuation. Check status reflects the requested enables. Do not require an untruncated pulse at an asynchronous enable transition.

Measure 10 MHz OUT and 1 PPS OUT with high-impedance and 50 Ω inputs. Record high/low voltage, rise/fall time, ringing and source impedance; nominal high levels are 3.3 V high impedance and approximately 1.65 V into 50 Ω. Verify both buffer channels share current through their separate resistors and there is no thermal problem. Verify the 10 MHz frequency, duty cycle and jitter meet the intended instrument's input specification. PPS should be about 10 ms wide; measure rising-edge delay/jitter relative to GNSS PPS. Its width is independent of the 100 µs injection burst.

Repeat oscillator/servo and injection leakage measurements with both outputs enabled and terminated through representative cables. Confirm a loaded reference output does not upset counting or create comparator double transitions. Check the GNSS-invalid/holdover status remains truthful while manually enabled outputs continue. No claim of fixed 10 MHz phase relative to PPS is permitted.

## GPS timing and servo

Use clear-sky GNSS reception and a time-interval counter or oscilloscope referenced to an independent calibrated GPS source. A signal generator locked to the same oscillator being tested is not an independent timing standard.

Check100µs default burst width and1,10,1000,10000,900000µs settings. Check that no-reader/stalled-reader operation does not reset the MCU or interrupt reference outputs; telemetry loss must be counted without truncating subsequent complete JSON records. Confirm one burst per valid second, including after USB disconnect/reconnect, no reader for at least 30 minutes, a stalled reader, slow host reading, command flooding, power cycle and GNSS antenna loss. Verify mute and continuous modes, no unintended startup bursts, and at most the documented one already-armed burst during a late fault.

Record PPS-to-gate delay and jitter. Record PPS-to-RF-envelope delay using a specified filter/template. The first comb pulse is phase-quantized by up to one100ns reference cycle. Confirm there are no extra-edge or whole-second association errors. Exercise corrupted/truncated UBX messages, delayed processing and count FIFO overflow if possible.

Allow30minutes of operation. Record servo convergence,64s frequency estimates, DAC setting and temperature. Verify tuning range at expected enclosure temperatures. Loss of GNSS must leave a truthful HOLDOVER/NO_PPS state; do not label holdover frequency accurate without a measured stability bound.

## SDR end-to-end test

Use each intended receiver configuration: RX888 real direct sampling and RTL-SDR complex tuned sampling. Inject a separately referenced test tone and the calibration comb. Recover sample rate from PPS marker spacing, then correct the test tone frequency. Test for sample loss under full intended USB/disk throughput.

Calibrate constant path delay using known pulses. Test repeatability after receiver restart, retune, gain/filter change, USB restart and cable replacement. Report distributions and maximum observed error, not just an average. Acceptance against the0.1–1µs goal requires the actual receiver bandwidth, SNR and delay correction. A narrowband record may not support0.1µs precision.

## Files returned by assembler

For each serial number return inspection results, power measurements, firmware identifier, measured tuning slope and level table. Return first-article VNA Touchstone files, oscilloscope captures and timing/servo logs. Use HDF5 for numeric measurement datasets, JSON for configuration and PDFs for signed inspection reports. Do not ship with failed or missing first-article qualification represented as passed.

## Additional power and cable checks

Measure both reference outputs with representative 50 Ω and high-impedance instruments and 0.5–5 m coax cables. Capture edge overshoot/undershoot, channel sharing, and propagation delay. Do not infer actual buffer current from the ideal resistive simulation. Check LDO stability and start-up, GNSS acquisition/transmit load transients, and quiet-rail ripple with both reference outputs loaded and USB active. Record oscillator frequency/jitter and muted receiver spurs under those conditions; a failing result requires a revised filtered supply or shielding solution before the remaining boards are assembled. See the layout review for the shared analog/fast-logic rail and lack of ferrite isolation.

## Phase noise and software reference tracking

Measure the continuous 10 MHz reference and selected injected harmonics against an independent low-noise standard. Record phase-noise density at 10/100 Hz and 1/10/100 kHz offsets, both with the servo active and held at a fixed DAC code. Longer records are needed to examine the 64 s steering cycle and close-in drift. Separate burst-gating sidebands from random phase noise; use continuous mode for the underlying carrier measurement. Repeat with USB traffic, loaded reference outputs and representative supply/temperature changes. The TCXO datasheet curve does not include comparator, logic, buffer or board noise. No board phase-noise limit is established by the assumed 20/100 ps edge-jitter simulations.

Calibrate DAC Hz/code and filter response before applying the simulated counter/DAC reference observer to real recordings. Verify the recovered reference frequency and software-corrected science frequency against independent measurements, including UTC labeling and sample-loss handling. A smooth software correction does not establish absolute carrier-phase coherence between bursts.

## USB-C power-only and indicator acceptance

With a data connection, set/save a 1000 µs width, 20 dB electronic attenuation and both reference outputs enabled. Remove computer power. Boot from a 5 V USB-C wall supply using a USB-C-to-C cable, then repeat with USB-A-to-C. Confirm GNSS startup, saved attenuation/width, the 10 MHz/PPS outputs and calibrated burst timing using instruments. Watch solid green at startup, amber acquisition and 100 ms green PPS flashes after TRACKING. Repeat without a settings file for safe defaults. Run disconnected for at least one hour; check the watchdog does not reset it. A physical power-only cable is a useful additional check.

Disconnect/reconnect the GPS antenna; check red indication after validity/PPS loss, suppression of further invalid bursts, and automatic reacquisition. One previously armed burst can occur before fault information arrives. Test a missing GNSS ACK and injected I2C failure. Check the LED window/diffuser visibility and ensure LED transitions do not introduce unacceptable RF spurs or move the hardware PPS/burst edge. Connect a computer with the serial port closed, stall its reader, unplug/replug data while preserving power, and confirm operation continues. Verify serial JSON has complete newline-terminated records; discard the first partial record after reconnect.
