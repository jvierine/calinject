# Rev A engineering review — 2026-11-23

Reviewed the native circuit/PCB generators, current PCB geometry, firmware and host utilities at commit 0500140. This is a document/source review, not an independent laboratory qualification. No electrical or mechanical design changes were made as part of this review.

**Disposition: suitable for continued prototype development; not ready to order the five-board batch.** The timing/servo architecture is plausible, but RF leakage, comb pulse shape and actual firmware behavior on hardware remain unqualified. Existing zero-finding ERC/DRC reports and software tests have a narrower scope than these requirements.

## 1. The agreed cost change is not implemented

`tools/design.py` still specifies T1 PDC-20-3+ at a $39.02 allowance. Its eight-pin footprint and routed connections remain in the PCB, fabrication files and v0.1.0-prototype release. The color illustration changes presentation only. Replacing T1 requires a schematic/footprint/routing revision, new BOM/CPL/exports, revised level/loss/isolation estimates and updated acceptance criteria.

The discussed ADP-2-1+ combiner is an SMT, factory-built option listed by JLCPCB as C2683460. Its specified lower limit is 500 kHz, compared with 200 kHz for the present coupler; it also introduces about 3.2 dB of antenna-path loss. Its 20 dB minimum branch isolation is not a guarantee of zero antenna leakage. A matched SDR removes the output-reflection mechanism but does not remove direct finite branch leakage. These are design choices still to resolve, not properties of the currently fabricated files.

Sources: [ADP-2-1+ datasheet](https://www.minicircuits.com/pdfs/ADP-2-1%2B.pdf), [JLC catalogue](https://jlcpcb.com/parts/2nd/RF_and_Wireless/RF_Power_Splitters__Combiners_2559), [combiner mismatch discussion](https://www.minicircuits.com/appdoc/AN10-006.html).

## 2. Weak calibration needs RF leakage qualification

The oscillator/comparator and the pre-gate comb continue to run while the injection gate is muted. The route drawing shows their nets and the digital/reference circuits on the same board as the sensitive RF path. Parasitic coupling can bypass logical gating and attenuation. This is a risk to measure, not a measured failure.

Before layout freeze, compact the clock/pulse-generation area, keep its supply/return loops local, inspect proximity to the RF input/output and attenuator output, and review decoupling placement. In particular C16 is placed several millimetres from U6, and C21/C22 several millimetres from U9; review actual routed supply/ground paths rather than assuming their shared net names make ideal bypasses. The two inner ground planes are useful; they are not a substitute for local bypass geometry or isolation testing.

Measure muted spectra at the SDR output and antenna port at the actual intended weak settings, including USB activity and reference-output loads. Measure absolute dBm as well as on/off difference. An illustrative 40 dB suppression target alone does not establish that residual spurs are below the receiver's scientific noise/interference threshold.

## 3. Comb flatness depends on an unmeasured logic pulse

R10/C17 and U7/U8 generate a nominal 7–12 ns pulse. RC tolerance, Schmitt thresholds, propagation delays, loading and PCB parasitics affect the pulse shape. The existing ideal rectangular-pulse model already shows appreciable 70 MHz level variation across that width range. Measure the waveform and every used harmonic before accepting the chosen values; qualify any factory value changes before the other four boards are built.

The 10 MHz reference is frequency disciplined over 64-second count windows; its phase is not locked to PPS. Its exact instantaneous frequency and the requested 0.1–1 µs end-to-end timing accuracy are not established by simulation.

Sources: [Schmitt inverter](https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf), [AND gate](https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf), [oscillator](https://ecsxtal.com/store/pdf/ECS-TXO32-S3.pdf).

## 4. USB availability must not accidentally determine reference uptime

`firmware/main.py` uses blocking `print()` for status and feeds an eight-second watchdog in the main loop. Its own comments acknowledge that USB backpressure can stall execution. A watchdog reset restores both reference enables to disabled and resets acquisition/servo state. This needs a hardware test with the actual MicroPython build, no host reader, a slow reader and USB reconnects. If these conditions cause resets, use bounded/nonblocking telemetry that drops reports without blocking timing/control work.

Current settings are RAM-only, including reference enables. Power-cycle persistence has not been implemented. That is acceptable for a host-controlled prototype, but should be made an explicit operating decision before using the board as a standalone reference.

## 5. Clean up custom pad layer assignments

`tools/kicad_board.py` assigns SMD pads with `k.LSET.FrontMask()`. The resulting native pads include F.SilkS, F.Adhes, F.CrtYd and F.Fab as well as F.Cu/F.Mask/F.Paste. Standard SMD pads should normally use only copper, mask and paste layers. The existing exporter subtracts solder mask from silkscreen, which reduces the immediate silk-over-pad issue, but these unusually broad assignments should be corrected in the generator, PCB and local library before the next fabrication export. Inspect the actual Gerbers after correction; do not merely suppress checks.

This was observed in the native PCB layer lists. It is not an assertion that the current copper netlist is shorted or that the existing silkscreen export necessarily deposits ink on the lands.

## 6. Absolute timing needs an explicit epoch association

The RF bursts repeat identically each second. They identify a second boundary but do not encode its UTC label. The host utilities require explicit sample-index/UTC correspondences; they are not a complete automatic RTL-SDR/RX888 capture-and-calibration pipeline. Resolve the starting second with suitable capture metadata, an identifiable commanded gap or an independent timestamp, then measure receiver/filter/cable delays and inspect clock-fit residuals for sample loss.

The UBX time-pulse configuration keys, next-pulse message semantics and relevant UTC/quantization/lock flags were checked against the [M10 SPG 5.10 interface description](https://content.u-blox.com/sites/default/files/u-blox-M10-SPG-5.10_InterfaceDescription_UBX-21035062.pdf). That source check does not replace a real receiver/PIO timing test.

## Positive findings and review limits

- The tunable clipped-sine oscillator, comparator, DAC and frequency-counting approach form a coherent architecture. The selected main pin mappings checked in this review are consistent with their manufacturer descriptions.
- Independent PIO gate timing is preferable to timing the burst from USB or Python scheduling; descriptor starvation limits uncontrolled repeat bursts.
- Fixed pads plus the PE4312 provide a practical adjustable-level chain. Separate buffers isolate the external reference loads.
- Full-turnkey assembly instructions explicitly include module/header/THT work, programming and first-article tests; the user is not assigned winding or soldering.
- Existing reports contain zero ERC/DRC/connectivity/parity findings. The current circuit is an unbuilt prototype; all hardware performance findings remain conditional until measured.

This review does not certify every custom land pattern, SMA mechanical substitution, pressed PCB stack, regulator fault behavior, EMC performance or printed-case fit. The documented first-article acceptance procedure remains required.
