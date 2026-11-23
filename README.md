# Calinject

A small USB-C powered board that adds GPS-timed calibration bursts to an SDR recording. Use the bursts to measure sample timing, sample rate and frequency drift.

![Calinject PCB layout](docs/board-layout.png)

**Prototype, not yet built or tested on hardware.** Rev C uses commonly stocked parts and horizontal SMA connectors through the sides of the case.

**Ready for a factory first-article build:** the revised CAD checks and software tests pass. The antenna path is specified for **0.5–70 MHz**, with about **3.2 dB loss**.

What it does:

- Generates a 10 MHz harmonic comb for HF and VHF receivers through 70 MHz.
- Sends a short calibration burst each second: **100 µs by default**, adjustable over USB.
- Lets you adjust the calibration level over USB or with a trimmer.
- Provides separate **10 MHz** and **1 PPS** SMA reference outputs.
- Reports GPS and frequency-servo status over USB. Firmware updates also use USB.

Runs from a **5 V USB-C supply without a computer**. Saved settings restore automatically. Its RGB LED is solid green during startup, amber while acquiring, flashes green on PPS once frequency tracking is established, and blinks red on faults.

Connect it **after your antenna bias board and before the SDR**, with a separate active GPS antenna and USB-C power. The receiver ports block DC; disable the SDR's own bias tee. See the [connector guide](docs/port-guide.pdf).

JLC's current quote is **about $69 per fully assembled board at five units**, before shipping, tax and review adjustments. We load the firmware ourselves through USB-C; no user soldering or winding. Qualify one received board before relying on the batch. See the [quote](docs/cost.md).

[Download all files](https://github.com/jvierine/calinject/releases) · [Connect and control](docs/operation.md) · [USB programming](firmware/README.md) · [Using the calibration](host/README.md) · [Print the case](mechanical/README.md)

Technical details: [design](docs/design.md), [simulations](docs/simulation.md), [end-to-end model](docs/end-to-end.md), [review](docs/review.md), [layout audit](docs/layout-review.md), [cost](docs/cost.md), [KiCad/build instructions](docs/build.md), [factory assembly](manufacturing/ASSEMBLY.md), [acceptance tests](docs/acceptance.md), and [SVG board drawing](docs/board-layout.svg).
