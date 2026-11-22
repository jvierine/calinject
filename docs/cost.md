# Five-board cost basis

Currency: USD. Planning date: 2026-11-22. Quantity: **five complete, programmed boards**, with one first article qualified before the remaining four. No supplier has quoted or accepted this design.

The circuit-manifest component estimate is approximately **$86.95 per board**, or **$434.75 for five**, before supplementary module headers, sourcing losses, PCB fabrication, stencil/setup, mixed SMT/through-hole assembly, programming, RF qualification, shipping or tax. Some values are distributor small-quantity prices and others are engineering allowances; this is not a purchase-ready price list.

| Major component | Allowance per board |
|---|---:|
| PDC-20-3+ coupler | $39.02 |
| Tunable ECS TCXO | $12.71 |
| MAX-M10S GNSS | $11.42 |
| PE4312 attenuator | $4.40 |
| RP2040-Zero | $4.00 |
| Five SMA jacks | $6.00 |
| Remaining components, including reference buffers | about $9.40 |

The under-$100 target leaves only about $13.05 per board for all non-component costs. **It is not demonstrated and is unlikely for five fully built units with substantial first-article RF/timing qualification.** Obtain an itemized quotation; do not treat a generic PCBA setup advertisement as a complete price. A reliable all-in estimate cannot be given without that quote. The dedicated reference-output addition accounts for about $3.58 of the parts estimate.

The cheaper ADCB-20-82+ coupler considered during development starts at 1 MHz. It was not selected because lower-HF operation is required. A custom bridge made from factory-wound transformers could reduce parts cost, but its directionality across 0.2–70 MHz needs another design and qualification cycle; no such unverified alternative is included in the manufacturing package. Hand-wound components are excluded.

The price scope excludes the external GPS antenna, USB/SMA cables, optional external combiner/terminator and receiver. Case printing is by the customer. Ask the factory to quote programming and per-board electrical testing separately from one-time RF/timing engineering. All assembly and initial programming must remain factory work.

See [pricing and manufacturer references](sources.md) and the ready-to-use [quote request](../manufacturing/QUOTE_REQUEST.txt).
