# Rev C test review — 24 November 2026

The RF PCB Design tooling and Calinject software/model checks pass. The strict CAD audit **does not pass**. These results do not establish physical performance.

| Check | Result |
| --- | --- |
| RF PCB Design tooling suite | 29 passed, including native KiCad report tests |
| Calinject unit tests | 33 passed |
| Actual firmware compilation and PIO assembly | Pass |
| Standalone firmware behavioral scenarios | 14 passed; includes power without a computer |
| Complete behavioral simulation chain | All 10 acceptance assertions passed |
| Native board/manifest/BOM placement checks | Pass: 99 components, 81 SMT placements, 273 through vias |
| JLC placement file checks | Pass: 95 factory placements, outward SMA and USB orientation |
| Fresh KiCad 10.0.8 ERC/DRC with submitted project settings | Zero reported violations, zero unrouted connections, zero parity findings |
| Strict report audit | Blocked: ignored checks and eight findings under expanded PCB checks |

## Findings

The submitted project settings disable five PCB checks. A temporary CAD copy enabled them as warnings without changing submitted copper or manufacturing files. It reports:

- Six footprint-type mismatches: TP1–TP6 have surface pads but through-hole component metadata. This is a classification issue requiring correction in a future revision; it is not an additional unrouted connection.
- Two ground-track endpoints do not coincide with the ground via center near (84.4322, 48.0174) mm. KiCad reports electrical connectivity as complete, but these junction geometries need explicit copper review before calling the stricter audit clean.

The four remaining ERC ignored checks are KiCad defaults (single global label, four-way junction, simulation model issue, footprint filter). They remain explicitly reported and were not blanket-approved. Enabling project-stored ignored settings does not override these ERC defaults in this run. No claim is made that those checks passed.

No manufacturing files, board geometry, component selection or paid order were changed. The expanded checks are diagnostic; no new fabrication package was released.

## Fabrication snapshot

The annotated tag [`fabrication-revC-2026-11-23`](https://github.com/jvierine/calinject/tree/fabrication-revC-2026-11-23) points to `97830a06bd13f6005d6d1b55f701d71652623b5a`, including the MCP4725A1 substitution and corrected JLC SMA rotations. The Gerber archive SHA-256 matches the recorded submission: `ab6dc3be98725234e36925019c18a6ac8090136fae86514fb7fba34dc5b14ef4`. The submitted assembly archive hash is recorded in the tag annotation and DAC substitution record; later documentation archives are not asserted to be byte-identical to that upload.

Detailed machine-readable evidence is in the validation directory. Simulations use assumed oscillator, receiver and noise models; physical phase noise, cable-driver behavior, RF isolation, timing delays, power integrity and case fit still require received-board measurements.
