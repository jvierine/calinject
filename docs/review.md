# Rev B readiness review — 2026-11-23

**Disposition: design package ready for a factory first-article build and quotation.** Known source/CAD issues identified in the Rev A review have been addressed. This is not a claim of measured hardware qualification; no physical board has yet been built. The factory test procedure is part of the first-article scope, followed by the remaining four boards after acceptance.

| Rev A finding | Rev B action and evidence |
|---|---|
| Cost change not implemented | ADP-2-1+ SMT combiner is in native CAD/BOM/CPL/routing. Parts estimate is $59.97. Operating band/loss/levels are updated. |
| Clock leakage/layout risk | Oscillator/comparator area compacted; comb/attenuator bypass capacitors moved closer; 16 additional ground-stitching vias separate the clock area and receiver path. Fixed pad increased to 20 dB for weak markers. Actual muted leakage remains a first-article measurement. |
| Nonstandard pad layers | SMD pads now use only F.Cu/F.Mask/F.Paste. Rotated footprint body/courtyard geometry corrected. Native DRC/parity checks and fabrication exports regenerated. |
| Blocking USB logging | Bounded telemetry queue, per-byte writable checks, bounded output/input work per control-loop pass; tests exercise stopped/slow readers, partial frames and overflow. No blocking print/flush remains in the loop. |
| Settings lost at reset | Explicit save command writes validated settings atomically. Tests cover corrupt/invalid files and interrupted-save recovery. No automatic recurring flash writes. |
| Pulse envelope not measured | Physical pulse-shaping circuit compacted; every intended harmonic and width is specified in the first-article acceptance test. Ideal model regenerated for Rev B losses; no measured result is claimed. |

The current reports establish zero KiCad ERC/DRC/connectivity/parity findings, correct SMT pad-layer sets, consistent manifest/BOM/placement, and passing protocol/servo/PIO/transport/settings tests. Application bytecode compiles with MicroPython 1.29; its upstream PIO assembler accepts both actual PIO functions. The enclosure mesh is watertight; board outline, mounting holes and SMA locations are unchanged, and the USB cable opening is enlarged for housing clearance.

Normal first-article qualification still includes measured harmonic levels, muted spurs, antenna leakage, RF path loss/match, reference-output levels, timing/delay, GPS/servo operation and USB stress on the selected MicroPython build. Identical RF markers require explicit UTC epoch association in the receiver analysis; the supplied host tools describe that workflow and cannot infer an unknown integer second from an identical pulse train.

Historical details are retained in [Rev A review](review-rev-a.md). Current electrical assumptions are in [design](design.md), build steps in [build](build.md), and factory acceptance in [acceptance](acceptance.md). The distinction between a manufacturable first article and measured qualification is intentional.
