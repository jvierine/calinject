# Calinject

A small USB-C powered board that adds GPS-timed calibration bursts to an SDR recording. Use the bursts to measure sample timing, sample rate and frequency drift.

![Calinject PCB layout](docs/board-layout.png)

**Prototype, not yet built or tested on hardware.** This figure shows the current Rev B board with its lower-cost SMT transformer combiner.

**Ready for a factory first-article build:** the revised CAD checks and software tests pass. The antenna path is specified for **0.5–70 MHz**, with about **3.2 dB loss**.

What it does:

- Generates a 10 MHz harmonic comb for HF and VHF receivers through 70 MHz.
- Sends a short calibration burst each second: **100 µs by default**, adjustable over USB.
- Lets you adjust the calibration level over USB or with a trimmer.
- Provides separate **10 MHz** and **1 PPS** SMA reference outputs.
- Reports GPS and frequency-servo status over USB. Firmware updates also use USB.

Connect it **after your antenna bias board and before the SDR**, with a separate active GPS antenna and USB-C power. The receiver ports block DC; disable the SDR's own bias tee. See the [connector guide](docs/port-guide.pdf).

The aim is **five factory-assembled boards**, with no user soldering or winding. Parts are estimated at **about $60 per board**; the under-$100 assembled target still needs a factory quote. The first assembled board needs RF and timing tests before building the rest.

[Download all files](https://github.com/jvierine/calinject/releases) · [Connect and control](docs/operation.md) · [USB programming](firmware/README.md) · [Using the calibration](host/README.md) · [Print the case](mechanical/README.md)

Technical details: [design](docs/design.md), [simulations](docs/simulation.md), [end-to-end model](docs/end-to-end.md), [review](docs/review.md), [layout audit](docs/layout-review.md), [cost](docs/cost.md), [KiCad/build instructions](docs/build.md), [factory assembly](manufacturing/ASSEMBLY.md), [acceptance tests](docs/acceptance.md), and [SVG board drawing](docs/board-layout.svg).
