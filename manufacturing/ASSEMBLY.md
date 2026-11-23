# Full turnkey assembly specification

Quote five fully electrically assembled PCBAs, supplied unprogrammed. The customer prints and fits the case. The supplier performs all electrical assembly, including the purchased controller module, headers, five SMA jacks, trimmer and range shunts. No winding or customer soldering is required.

## PCB and stack

90 × 65 mm, four copper layers, 1.6 mm finished thickness, FR-4, nominal 1 oz (35 µm) copper on all layers, lead-free HASL or ENIG. The native nominal stack has 0.20 mm outer dielectrics, a 1.04 mm central dielectric and 0.01 mm masks. Confirm actual pressed stack and finished thickness before fabrication.

All vias are plated through holes. Minimum track is 0.15 mm, typical clearance 0.20 mm, and minimum via drill 0.30 mm with 0.60 mm pad. Provide solder mask both sides and front silkscreen. Inner1 and Inner2 are ground reference planes. The panel assembler may add panel fiducials and tooling outside the board outline; return the panel drawing for review.

Trim through-hole leads to no more than 2 mm below the PCB's bottom face. The case provides 3 mm clearance below that face.

RF width 0.36 mm targets approximately 50 Ω with the stated outer dielectric. Confirm the impedance calculation using the actual stack; the 1.575 GHz GPS trace is especially sensitive. Any width/stack change must update the native PCB and rerun DRC. Total thickness alone does not establish RF impedance.

Use the Gerber ZIP, separate PTH/NPTH Excellon drills and IPC-D-356 netlist. Do not mirror top-side placement. Native `.pos` and CPL use absolute KiCad origin at the upper-left: X right, Y up, so on-board Y values are negative. All SMT parts are on top. Verify package pin 1 against the assembly drawing and local footprint, rather than assuming a distributor's zero angle.

## Parts

No substitutions for U4 GNSS, Y1 tunable clipped-sine TCXO, U6 comparator, U7/U8 comb logic, U9 attenuator, U10/U11 output buffers or T1 combiner without review. A fixed-frequency TCXO or CMOS-output oscillator is not a substitute for Y1. Use ADP-2-1+, JLC C2683460, specified from 500 kHz. T1 is SMT: sum pin1 goes to SDR, branch3 to antenna and branch4 to calibrator. Join pins2/5 and keep that link isolated from ground. Follow its 180-degree placement in the native PCB/CPL.

Follow u-blox reflow/MSL instructions for U4. Keep its unused startup/control pins unconnected as drawn. Pin 1 is at the top-left in the local assembly drawing; RF pin 11 is on the opposite side. U9 has an exposed ground pad with reduced paste opening. Review solder-mask tenting and paste; inspect for solder loss into nearby through vias. Filled/capped vias are not assumed in the prototype cost.

U1 is a **genuine Waveshare RP2040-Zero USB-C module**, supplied without headers. Fit 23 male pins at 2.54 mm pitch: two FG-PZ2.54-1-09P rows and one FG-PZ2.54-01-05P row. Use 2.5 mm plastic spacers, 0.64 mm square pins, 3 mm solder tails and 6 mm mating pins. Solder the module permanently, with USB facing north. Install after mainboard SMT reflow unless Waveshare permits reflow of the finished module.

JP1 comprises two FG-PZ2.54-1-03P headers, with 2.54 mm between rows. Fit two BOOMELE closed-top 2.54 mm shunts, C100114. Default LOW shorts 1–2 and 4–5; HIGH shorts 2–3 and 5–6. Fit both in the same range. For JLC upload use the **single-sheet full BOM/CPL in jlc-turnkey/**, which includes all headers and shunts as documented assembly aliases. The root CPL remains SMT-only.

The five SMA jacks are **Lian Xin SMA-KWE, C7498154**, female ordinary SMA, right angle, 4.2 mm square ground-pin spacing. Fit the exact reviewed drawing; similar names are not proof of compatibility. No reverse-polarity or vertical jacks. J1/J4 point east, J5 west, J2/J3 south. The thread must project horizontally past the PCB edge. Inspect orientation and mating depth before soldering. Rev B's vertical 5.08 mm jacks do not fit this board.

Y1 is **KDS 1XTV10000MDA / DSA321SDN, C253701**. Respect its central bottom copper keepout on top and Inner1. Vc must stay within 0.5–2.5 V. Measure the positive tuning slope on the first article, set it over USB and save it. Do not apply the old ECS phase-noise table to this oscillator. U10/U11 use the active **SN74LVC2G125DCTR SSOP-8, 0.65 mm pitch**; the old DCU 0.5 mm package is incompatible. U8 is Nexperia 74LVC2G08DC,125.

J4 is 10 MHz OUT and J5 is 1 PPS OUT. Separate buffers default disabled in firmware and are included in functional acceptance. The LEVEL trimmer adjusts a DC ADC input. Ship with both JP1 shunts LOW. Customer firmware initializes electronic attenuation to 31.5 dB.

## Programming, test and quote scope

**Factory scope: assembly only, with normal fabrication/assembly inspection and electrical checks. Do not quote firmware loading, custom functional tests or RF/timing qualification.** The customer will perform initial USB-C programming, commissioning and the acceptance tests after receipt. No soldering or external programming adapter is needed.

Provide proposed final BOM, availability, actual stackup, placement orientation preview, normal inspection scope and itemized price before an order is placed. This package does not authorize procurement or manufacture. Include every SMT/THT part, the genuine controller module, headers and both range shunts; the customer receives complete electrically assembled units.

Firmware and test files are included for the customer's use. Follow `firmware/README.md` to load MicroPython and all five application files, including `status_led.py`. Qualify one received board with `docs/acceptance.md` before relying on the batch for measurements. Normal factory continuity checks do not qualify RF isolation or absolute timing.

Status indication uses the genuine RP2040-Zero's existing GP16 WS2812 RGB LED; do not fit an additional LED or change carrier wiring. The customer tests USB-C power-only operation and the RGB indicator after programming.
