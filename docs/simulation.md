# Simulation results

The passive circuits and modeled control system pass the checks below. This supports building a first article; it does not establish that every part of the physical board works.

| Check | Result |
|---|---|
| Fixed and selectable 20 dB pads, 0.5–70 MHz | 19.952–19.956 dB attenuation; minimum return loss 29.85 dB |
| DAC two-section RC filter | Settles within 0.1% in 87 ms, well before the 64 s servo update |
| Frequency servo, 100 simulated two-hour runs | All end in TRACKING, no DAC limits; worst final-half-hour RMS error 0.064 Hz at 10 MHz |
| Sample-rate recovery, 120 s with missing markers | Injected +2.5 ppm recovered as +2.500129 ppm |
| Firmware/PIO and USB tests | All 20 pass, including clock-edge counting, burst duration, starvation muting, and stalled USB output |

The pad simulation uses the actual design resistor values, a 100 nF blocking capacitor, ideal components, and matched 50 Ω ports. Its 25 dB return-loss target is a subnetwork check; the full-board acceptance target is 15 dB. No PCB parasitics or active attenuator model is included. The selectable pad has a separate output capacitor in the full circuit; it is outside this isolated pad model.

The servo simulation runs the firmware's actual servo code with count quantization, 20 ns RMS independent PPS jitter, a small oscillator temperature random walk, and actual tuning slopes of 0.064–0.097 Hz/code while the servo assumes 0.0806 Hz/code. These are modeled conditions, not an oscillator stability specification. The sample-rate test assumes correctly identified UTC markers with 100 ns RMS measurement error; it does not demonstrate RF burst arrival-time estimation to 100 ns.

## A short burst gives finite frequency precision

For a 100 µs isolated pilot sampled at 2 MS/s, 500 synthetic trials per SNR give:

| Per-sample SNR | RMS frequency error from one burst |
|---|---:|
| 10 dB | 90 Hz |
| 20 dB | 28 Hz |
| 30 dB | 8.6 Hz |
| 40 dB | 2.7 Hz |

This uses the supplied phase-slope estimator and complex white Gaussian noise. Receiver filtering, interference, pilot uncertainty and sample-rate error are excluded. Average independent frequency estimates or increase burst width for finer tracking. The 10 MHz servo's modeled error also multiplies by harmonic number. Neither sample rate nor RF frequency is known exactly.

See [longer bursts and averaging](averaging.md) for the 0.1/1/10 ms comparison, 10–30 dB SNR sweep, and receiver-drift tradeoff.

## What remains to measure

The 220 Ω/22 pF pulse-shaping network has a simulated RC threshold delay of 1.9–6.0 ns when the threshold is swept from 30% to 70% of supply. This excludes Schmitt input capacitance, actual thresholds, gate propagation and PCB loading. It cannot certify the proposed 7–12 ns output pulse width or the harmonic envelope.

These simulations do not contain vendor models for the combiner, attenuator, comparator, logic ICs, oscillator, GNSS receiver or regulators. They cannot verify transformer pin mapping internally, antenna isolation, supply stability, clock feedthrough, RF emissions, GPS lock, or end-to-end receiver delays. Use the [first-article acceptance procedure](acceptance.md) to establish those results.

## Reproduce

Install ngspice and the project Python requirements, then run:

```sh
conda run -n base python tools/simulate.py
conda run -n base python -m unittest discover -s tests -v
```

The generated SPICE decks, solver logs, JSON summary and HDF5 numeric results are in `validation/simulation/`. Ngspice 47 was used for the recorded run. No hardware changes were made as a result of these checks.

The [cable and layout review](layout-review.md) adds transmission-line simulations of the reference outputs, including channel skew and driver-resistance sensitivity. These use the revised 100 Ω individual ballast resistors and a 1 mΩ model for the zero-ohm common link.
