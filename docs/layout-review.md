# Cable drivers, grounding and power review

This review led to four additional local 100 nF capacitors, 177 additional ground vias, and revised reference-output ballast resistors. The native design is four layers; the two inner layers are ground reference planes apart from normal pad/via antipads and the KDS-required 2 × 2.5 mm keepout on In1 under Y1. In2 remains beneath that area at the required greater depth. Ground is not split into analog and digital islands.

## Reference cables and buffers

The 10 MHz and PPS SMAs each have an SN74LVC2G125 dual-channel buffer. Each channel connects through its own **100 Ω** resistor; the common series component is now a **zero-ohm link**. Thus the nominal source impedance is 100 Ω in parallel with 100 Ω, or 50 Ω, plus the buffer's own output impedance. The channels are never directly tied together. This replaces the former 49.9 Ω individual / 24.9 Ω common network and better limits current during channel skew without increasing part count.

Nominal loaded high is 1.65 V into 50 Ω and 3.3 V into high impedance. A receiver needing a guaranteed 2 V TTL high into 50 Ω is incompatible. Short circuits, multiple loads, external DC bias and arbitrary long cables are not supported operating conditions. Outputs are disabled during reset by pullups; saved firmware settings can explicitly enable them after boot.

Ngspice models a lossless 50 Ω cable with 10 ns one-way delay (approximately 2 m), matched and 1 MΩ receivers, 1 ns channel skew, and assumed per-channel driver resistances of 0, 5 and 15 Ω. Predicted matched highs are 1.53–1.65 V, high-impedance highs approximately 3.30 V, and peak channel currents 22.0–24.75 mA. The old network gave peaks up to 41.3 mA in the same simplified model. These are model results at nominal 3.3 V, not corner-qualified output specifications. TI specifies 24 mA drive at 3.3 V and 50 mA absolute maximum continuous output current; an absolute maximum is not a design target. Actual buffer waveforms, skew, current, overshoot and reference timing must be checked on hardware across supply and temperature.

Both outputs use **DC coupling and series source termination**. No parallel RC AC termination is fitted: a source-terminated point-to-point line absorbs the returning reflection, and a 50 Ω receiver already terminates the far end. Series AC coupling is a different operation and would not preserve the PPS DC pulse level. USB D+/D− stay on the genuine Waveshare module; none run on the carrier board.

## Layer changes and stitching

The added return vias connect both internal ground planes near signal layer changes. Rev C has 243 ground vias and 30 non-ground vias. All non-ground via centers are within **1.5 mm** of a ground-plane transition except one slow I2C_SCL control via, at **5.50 mm**. The exception is documented rather than forcing a clearance violation. The clock, comb and RF layer changes meet the 1.5 mm geometric target. These distances are geometric checks, not an extracted inductance or signal-integrity result.

Additional nominal 2 mm-pitch stitching runs around the board perimeter and the GNSS boundary wherever clearance permits. Existing stitching separates the comb/clock region from the receiver path. Gaps remain at connectors, components and traces. The stitching connects reference planes; it is **not a continuous metal wall or an RF shield**, particularly without grounded outer-layer guard copper. The printed enclosure remains unshielded. Antenna isolation, clock feedthrough and emissions still require measurements; shielding cannot be claimed from via count or DRC.

## Decoupling and power

The carrier uses **AP2112K LDOs**, not switching converters: one for the reference/RF circuitry and one for GNSS. The RP2040 module supplies its digital rail with its onboard regulator. The external USB supply may itself be a switching supply. LDOs do not eliminate high-frequency noise or ground coupling.

New local capacitors are C29 at U2, C31 at U4, C32 at U5 and C33 at U11. Their supply-pad distances are 1.8–2.04 mm, with short top-layer connections and local ground vias. Existing regulator bulk capacitors remain. The GNSS regulator's output capacitor C4 has moved to 1.80 mm from its output pin. U10's C27 is 2.21 mm from its supply pin. Oscillator, comparator, comb and attenuator bypasses remain local. The machine-readable audit records each measured distance; proximity alone does not establish the complete supply-current loop impedance.

**No ferrite beads separate the existing 3.3 V loads.** The reference/RF rail is separate from the module's digital rail, but it also powers the fast comb and reference-output buffers. Consequently it must not be described as a fully isolated AVDD supply. The RP2040's internal AVDD/DVDD implementation is on the purchased module. Adding a generic bead without a load/impedance model can introduce resonant peaking; if supply-induced oscillator jitter or muted spurs fail acceptance, a damped filtered oscillator/comparator branch or separate quiet LDO requires a circuit/layout revision and requalification. This release does not claim that rail-noise isolation has been measured or solved by the added bypasses.

## Verification and remaining checks

The revised CAD must pass ERC, DRC, connectivity and schematic parity before fabrication. The layout audit checks the actual board, and cable-model decks/results accompany the other simulations. Neither is a substitute for measuring regulator stability, supply noise, cable edge behaviour, PPS delay, muted spurs and calibration-to-antenna leakage on the first article. Qualify one received board before relying on the batch for measurements.

References: [TI buffer datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc2g125.pdf), [Analog Devices ferrite filtering and damping guidance](https://www.analog.com/en/resources/app-notes/an-1368.html).
