# First-article and production acceptance

Status: **not yet performed**. This procedure is part of the factory quotation, not evidence that a board has passed. Request a first article before producing the rest of the batch. No RF test result may be replaced by an ideal circuit simulation.

## Before applying power

Inspect MPNs, pin-1 orientation, QFN soldering and the GNSS module. Check SMA center-to-ground resistance: the external ports have DC-blocking capacitors and 1 MΩ bleeders. The coupler may have an internal DC path to ground behind those capacitors. Inspect module/header soldering, both range shunts and case clearance. X-ray U9's exposed-pad solder joint if available.

## Power and USB

Use a current-limited 5 V USB supply initially. Verify no rail short; check3V3A,3V3G and3V3D are3.3V within5%. Measure current with the GPS antenna disconnected and attached. First-article target is under250mA; investigate higher draw before release. USB-C operation must be checked with both C-to-C and A-to-C cables and both plug orientations.

At GPS ANT, measure bias voltage at no load and with a representative active antenna load. F2 is a 50 mA hold-current resettable fuse, not a precision current limiter. Select an antenna drawing at most 20 mA in normal operation; verify the voltage remaining after the fuse and choke meets its specification. The feed can lose about 0.4 V at 20 mA using the fuse's 20 Ω post-trip maximum resistance, before temperature/inductor effects. R1 is a zero-ohm link. Test a brief current-limited antenna short and recovery without damaging the receiver or resetting USB; verify GNSS reconfiguration/reacquisition if its rail momentarily collapses.

Load the specified MicroPython UF2 and the two firmware files. Confirm a USB status response and successful GNSS RAM-configuration ACK. Package the board with both JP1 shunts in LOW and maximum electronic attenuation.

## Oscillator and comb

Use a high-impedance probe on TP2; avoid loading the raw clipped-sine oscillator. Confirm10MHz counts, correct comparator logic levels and no double transitions. Sweep DAC700,1862,3000 with the servo disabled. Record oscillator frequency and tuning slope. Confirm monotonic positive pull, tuning coverage around10MHz, and control voltage inside0.5–2.5V. Enter the measured Hz/code slope for this serial number.

Measure COMB_RAW with an appropriate low-capacitance high-bandwidth probe. Check the pulse is approximately7–12ns. Verify no missing even harmonics and no near-null at70MHz. R10/C17 set the comb pulse shape; their values must be revised and requalified if the first article does not give usable10–70MHz lines. The user must not be expected to tune hardware.

Measure each10MHz harmonic with a spectrum analyzer at0,15.5,31.5dB settings, in both physical ranges. Use continuous mode for level characterization, then verify burst-on levels agree. Record actual dBm, setting error, frequency and linewidth. Measure muted-mode leakage with USB attached and active; supply/PCB coupling can bypass the logical gate and attenuator. Accept leakage only when below the stated application noise/spur requirement; a default target is at least40dB below the corresponding enabled line, and below the receiver's scientific interference threshold.

Check aggregate comb peak level and out-of-band harmonics. The comb intentionally extends above70MHz; it is not a70MHz-low-pass output. Receiver front-end/anti-alias filtering remains necessary.

## Coupler and receiver isolation

Use a calibrated VNA with all unused ports terminated in50Ω. Measure RF IN→TO SDR insertion loss/return loss over the quoted operating band. Measure calibration-to-SDR and calibration-to-antenna transfer at10,20,30,40,50,60,70MHz using an RF fixture at the injection port. Directional difference is the difference of these two measured transfers, not just a component catalogue number.

Proposed first-article acceptance: mainline insertion loss≤1dB, input/output return loss≥15dB, and injection directivity≥20dB at all used harmonics. These are release criteria to measure, not established guarantees. Document any narrower qualified band rather than accepting a failing sample silently.

Repeat with the actual SDR powered and configured. Measure calibration energy returning toward the antenna. Receiver return loss can dominate this measurement even if the coupler alone passes. If unacceptable, qualify a matching pad, buffer or different receiver interface and include its loss in the system budget.

## Dedicated reference outputs

Verify both SMA reference buffers are disabled at startup and after watchdog reset. Enable each separately with `ref10`/`refpps`; confirm their behavior is independent of injection width, mute/continuous modes and electronic attenuation. Check status reflects the requested enables. Do not require an untruncated pulse at an asynchronous enable transition.

Measure 10 MHz OUT and 1 PPS OUT with high-impedance and 50 Ω inputs. Record high/low voltage, rise/fall time, ringing and source impedance; nominal high levels are 3.3 V high impedance and approximately 1.65 V into 50 Ω. Verify both buffer channels share current through their separate resistors and there is no thermal problem. Verify the 10 MHz frequency, duty cycle and jitter meet the intended instrument's input specification. PPS should be about 10 ms wide; measure rising-edge delay/jitter relative to GNSS PPS. Its width is independent of the 100 µs injection burst.

Repeat oscillator/servo and injection leakage measurements with both outputs enabled and terminated through representative cables. Confirm a loaded reference output does not upset counting or create comparator double transitions. Check the GNSS-invalid/holdover status remains truthful while manually enabled outputs continue. No claim of fixed 10 MHz phase relative to PPS is permitted.

## GPS timing and servo

Use clear-sky GNSS reception and a time-interval counter or oscilloscope referenced to an independent calibrated GPS source. A signal generator locked to the same oscillator being tested is not an independent timing standard.

Check100µs default burst width and1,10,1000,10000,900000µs settings. Confirm one burst per valid second, including after USB disconnect/reconnect, slow host reading, power cycle and GNSS antenna loss. Verify mute and continuous modes, no unintended startup bursts, and at most the documented one already-armed burst during a late fault.

Record PPS-to-gate delay and jitter. Record PPS-to-RF-envelope delay using a specified filter/template. The first comb pulse is phase-quantized by up to one100ns reference cycle. Confirm there are no extra-edge or whole-second association errors. Exercise corrupted/truncated UBX messages, delayed processing and count FIFO overflow if possible.

Allow30minutes of operation. Record servo convergence,64s frequency estimates, DAC setting and temperature. Verify tuning range at expected enclosure temperatures. Loss of GNSS must leave a truthful HOLDOVER/NO_PPS state; do not label holdover frequency accurate without a measured stability bound.

## SDR end-to-end test

Use each intended receiver configuration: RX888 real direct sampling and RTL-SDR complex tuned sampling. Inject a separately referenced test tone and the calibration comb. Recover sample rate from PPS marker spacing, then correct the test tone frequency. Test for sample loss under full intended USB/disk throughput.

Calibrate constant path delay using known pulses. Test repeatability after receiver restart, retune, gain/filter change, USB restart and cable replacement. Report distributions and maximum observed error, not just an average. Acceptance against the0.1–1µs goal requires the actual receiver bandwidth, SNR and delay correction. A narrowband record may not support0.1µs precision.

## Files returned by assembler

For each serial number return inspection results, power measurements, firmware identifier, measured tuning slope and level table. Return first-article VNA Touchstone files, oscilloscope captures and timing/servo logs. Use HDF5 for numeric measurement datasets, JSON for configuration and PDFs for signed inspection reports. Do not ship with failed or missing first-article qualification represented as passed.
