# Using the markers in SDR data

For wiring, dependency installation and USB control examples, see [connections and host control](../docs/operation.md).

Keep the USB HDF5 status log alongside the receiver recording. USB arrival timestamps are only useful for diagnostics; scheduling and buffering make them unsuitable as absolute sample timestamps.

1. Record at least one in-band 10 MHz harmonic. A narrow RTL-SDR capture must include a harmonic inside its usable passband, away from DC spurs and the filter edge. A real-sampled RX888 capture must put the selected harmonic below Nyquist. Other comb harmonics can alias through imperfect anti-alias filtering.
2. Turn off AGC and choose a calibration level that yields reliable detection without clipping or intermodulation. Acquire a high-SNR burst template with the same receiver settings and filter chain.
3. Use complex matched correlation against the measured template to estimate burst location. `match_template` accepts bounded real or complex snippets and is invariant to constant complex phase. Its fractional-sample parabolic interpolation is an approximation. Receiver filtering can move the apparent envelope edge; establish the offset experimentally.
4. Associate each detected marker with a valid logged `boot_id`, `seq`, and TIM-TP UTC epoch. **A periodic 1 Hz RF marker does not encode its integer-second label.** Resolve that association using a recording start time known to better than0.5s, a deliberately commanded identifiable gap, or an independent timestamp. Never silently guess from USB arrival time. A starting epoch or explicit correspondence must be supplied.
5. Subtract the measured fixed antenna/cable, GNSS user delay, board gate, receiver and template delays with a documented sign convention. A marker that arrives `delay_s` after the target UTC epoch should map to `epoch + delay_s` before correcting the whole recording.
6. Fit marker sample indices against their explicit UTC seconds. The slope gives samples per second. Missing markers are permitted if the correct UTC seconds are retained. Inspect residuals to find dropped sample blocks and clock changes; split the recording at discontinuities. Fit successive shorter windows to track drift.
7. Isolate a pilot harmonic and fit phase *within* the interior of each burst, with filter transients removed. Convert phase slope using the corrected sample rate. For conventional complex IQ, `f_RF = f_pilot_RF + f_BB - f_pilot_BB`. The true pilot frequency depends on the disciplined oscillator's residual error. `tone_frequency` and `rf_frequency` implement these steps.

Do not unwrap carrier phase blindly between bursts: a1s gap leaves integer-Hz ambiguity, and servo DAC updates alter the phase slope. A100µs burst provides only a short frequency observation; improve precision by averaging many bursts, increasing the width or using continuous mode. PPS spacing measures sample-rate error independently of the receiver LO, so it can separate sample-clock drift from LO drift.

For real RX888 samples, bandpass one harmonic and form its analytic signal (for example with `scipy.signal.hilbert`) before calling `tone_frequency`. Keep the selected band away from DC/Nyquist and establish the frequency sign/alias convention explicitly. The helper does not infer the Nyquist zone or resolve aliased harmonics automatically.

`calibration.py` fits an HDF5 file containing equally sized one-dimensional `/sample_index` and `/utc_seconds` datasets:

```bash
conda run -n base python host/calibration.py markers.h5 --nominal-fs 64000000 --output clock-fit.h5
```

The result stores a local sample/UTC anchor, fitted rate, rate error in ppm and residual samples. This is an analysis utility, not an RTL-SDR/RX888 capture driver or an automatic end-to-end timing solution. Preserve native receiver files and their discontinuity metadata. Full-band long recordings need a streaming extraction stage around these bounded-snippet helpers.
