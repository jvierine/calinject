# Longer bursts and averaging

Synthetic results using the supplied frequency estimator at 2 MS/s. Each case contains 1,200 independent noisy bursts with random initial phase. Noise power per sample and burst-on signal amplitude stay fixed. Averaging combines separately estimated frequencies; phase is never connected across the one-second gaps.

## At 30 dB per-sample SNR

| Burst width | Duty at 1 PPS | One burst RMS | 10 bursts RMS | 60 bursts RMS |
|---|---:|---:|---:|---:|
| 0.1 ms | 0.01% | 8.57 Hz | 2.755 Hz | 1.306 Hz |
| 1 ms | 0.1% | 0.2717 Hz | 0.0953 Hz | 0.03301 Hz |
| 10 ms | 1% | 0.008735 Hz | 0.002774 Hz | 0.001005 Hz |

The first-to-last burst-midpoint spans are 9 s for 10 bursts and 59 s for 60 bursts. Their causal averages represent times 4.5 s and 29.5 s behind the newest burst. The 60-burst numbers use 20 non-overlapping groups and therefore have appreciable Monte Carlo uncertainty. These are frequency errors, not PPS arrival-time uncertainties.

## While the receiver drifts

For a receiver frequency ramp of 0.2 Hz/s, a trailing average of 10 bursts lags the newest frequency by 0.9 Hz; 60 bursts lag by 5.9 Hz. Assigning each estimate to the midpoint of its window removes this bias for a linear ramp, but does not produce a current-time estimate. A drift fit/predictor would need separate validation.

Longer bursts improve immediate tracking without this multi-second averaging delay. A 1 ms burst at 30 dB SNR is a useful starting point in this model; 10 ms improves precision further while occupying 1% of each second. The firmware already supports both widths over USB. The default remains 100 µs.

## Low-SNR failure mode

At 10 dB SNR, 10 ms bursts produced occasional large estimator errors (3 of 1,200 exceeded one 100 Hz FFT bin), raising single-burst RMS error to about 7 Hz. The phase-slope estimator is sensitive to phase-unwrapping failures in weak samples. Longer duration alone is insufficient in this regime: require an adequate isolated pilot and validate an outlier-rejection or more robust estimator before relying on these values. At 20 dB SNR, the 10 ms single-burst RMS error was about 0.028 Hz.

## Limits

These simulations assume a single isolated pilot, independent complex white Gaussian noise, known sample rate, and no reference-frequency error. They exclude filtering, interference, oscillator phase noise and sample loss. The same per-sample SNR means a longer burst contains more calibration energy and contaminates more science samples. Noise-only improvement is roughly duration to the power −3/2 and averaging-count to the power −1/2 in this regime. It does not reduce correlated pilot/reference errors or calibration biases. For example, a 0.064 Hz reference error at 10 MHz becomes 0.448 Hz at 70 MHz; that illustrative scale can dominate the long-burst noise figures.

The complete 10/20/30 dB sweep and linear-drift results are stored as HDF5 and JSON alongside the other simulations. Reproduce with:

```sh
conda run -n base python tools/simulate_averaging.py
```
