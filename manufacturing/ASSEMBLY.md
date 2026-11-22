# Full turnkey assembly specification

Quote five complete functional PCBAs. The customer prints and fits the case. The supplier performs all electrical assembly and initial programming, including the purchased controller module, headers, five SMA jacks, trimmer and range shunts. No winding or customer soldering is required.

## PCB and stack

90 × 65 mm, four copper layers, 1.6 mm finished thickness, FR-4, nominal 1 oz (35 µm) copper on all layers, lead-free HASL or ENIG. The native nominal stack has 0.20 mm outer dielectrics, a 1.04 mm central dielectric and 0.01 mm masks. Confirm actual pressed stack and finished thickness before fabrication.

All vias are plated through holes. Minimum track is 0.15 mm, typical clearance 0.20 mm, and minimum via drill 0.30 mm with 0.60 mm pad. Provide solder mask both sides and front silkscreen. Inner1 and Inner2 are ground reference planes. The panel assembler may add panel fiducials and tooling outside the board outline; return the panel drawing for review.

Trim through-hole leads to no more than 2 mm below the PCB's bottom face. The case provides 3 mm clearance below that face.

RF width 0.36 mm targets approximately 50 Ω with the stated outer dielectric. Confirm the impedance calculation using the actual stack; the 1.575 GHz GPS trace is especially sensitive. Any width/stack change must update the native PCB and rerun DRC. Total thickness alone does not establish RF impedance.

Use the Gerber ZIP, separate PTH/NPTH Excellon drills and IPC-D-356 netlist. Do not mirror top-side placement. Native `.pos` and CPL use absolute KiCad origin at the upper-left: X right, Y up, so on-board Y values are negative. All SMT parts are on top. Verify package pin 1 against the assembly drawing and local footprint, rather than assuming a distributor's zero angle.

## Parts

No substitutions for U4 GNSS, Y1 tunable clipped-sine TCXO, U6 comparator, U7/U8 comb logic, U9 attenuator, U10/U11 output buffers or T1 coupler without review. A fixed-frequency TCXO or CMOS-output oscillator is not a substitute for Y1. Preserve the PDC-20-3+ lower-band specification starting at 200 kHz.

Follow u-blox reflow/MSL instructions for U4. Keep its unused startup/control pins unconnected as drawn. Pin 1 is at the top-left in the local assembly drawing; RF pin 11 is on the opposite side. U9 has an exposed ground pad with reduced paste opening. Review solder-mask tenting and paste; inspect for solder loss into nearby through vias. Filled/capped vias are not assumed in the prototype cost.

U1 is a **genuine Waveshare RP2040-Zero USB-C module**, supplied without headers. Fit 23 male pins at 2.54 mm pitch: two 1×9 rows and one 1×5 row. The plastic spacer between carrier and module PCBs is 2.54 mm tall. Supplementary items are 2× Harwin M20-9990946 and 1× M20-9990546, subject to lead-length/stack verification. Solder the module permanently, with USB facing north. Install after mainboard SMT reflow unless Waveshare permits reflow of the finished module.

JP1 comprises two 1×3 rows at 2.54 mm pitch, with 2.54 mm between rows. The BOM requests two Amphenol 68000-103HLF headers for this compound footprint. Supply two matching 2.54 mm shorting shunts. Default LOW shorts 1–2 and 4–5; HIGH shorts 2–3 and 5–6. Fit both shunts in the same range. The BOM's Assembly materials sheet lists supplementary U1 headers and JP1 shunts; these are required even though they have no separate SMT placement rows.

The five SMA jacks use BAT WIRELESS BWSMA-KE-Z001, LCSC C496549: female center contact, ordinary SMA, 5.08 mm square ground-pin spacing. Vendor text contains inconsistent male/female wording, so the mechanical drawing and incoming contact inspection control. No reverse-polarity SMA. Amphenol 132134 is a compatible higher-cost option. Verify mating depth through the 12 mm case holes.

J4 is 10 MHz OUT and J5 is 1 PPS OUT. Separate buffers default disabled in firmware and are included in functional acceptance. The LEVEL trimmer adjusts a DC ADC input. Ship with both JP1 shunts LOW and electronic attenuation at 31.5 dB.

## Programming, test and quote scope

Follow `firmware/README.md` and `docs/acceptance.md`. Program and qualify one first article before completing the other four boards. Confirm factory test capability and cost in the quotation. Continuity testing alone does not qualify RF directionality or absolute timing.

Provide proposed final BOM, availability, actual stackup, placement orientation preview, programming plan, test plan and itemized price before an order is placed. This package does not authorize procurement or manufacture. Initial programming and all assembly must be included; the end user receives complete electrically assembled units.
