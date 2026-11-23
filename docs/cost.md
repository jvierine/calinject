# Five-board Rev B cost basis

Currency: USD. Planning date: 2026-11-23. Quantity: five fully assembled, programmed boards, starting with one factory-qualified first article. No supplier has issued a quote.

The component-manifest estimate is **$60.13 per board**, or **$300.65 for five**. It excludes supplementary module headers, sourcing overhead/MOQs, PCB fabrication, stencil/setup, SMT/THT/module assembly, programming/test, shipping and tax. Some figures are small-quantity distributor references; others are engineering allowances.

| Major item | Per-board allowance |
|---|---:|
| ADP-2-1+ SMT combiner | $12.04 |
| Tunable ECS TCXO | $12.71 |
| MAX-M10S GPS | $11.42 |
| PE4312 attenuator | $4.40 |
| RP2040-Zero module | $4.00 |
| Five SMA jacks | $6.00 |
| Other components | $9.40 |

Replacing the $39.02 Rev A coupler saves approximately **$26.98 per board**. The under-$100 assembled target now leaves about $40 per board for non-component costs. It is more plausible, but remains unconfirmed at five units. Obtain an itemized turnkey quote; quote one-time RF/timing qualification separately from repeat assembly/programming/test. There is no evidence for a firm all-in price yet.

The tradeoffs are a specified 500 kHz lower limit and about 3.2 dB antenna-path loss. Isolation is finite, so use a weak calibration level and qualify actual antenna leakage. No hand-wound parts or user electrical assembly are required.

External GPS antenna, USB/SMA cables, optional terminator/external combiner, receiver, case printing and case screws are outside this parts estimate. See [sources](sources.md) and the [quote request](../manufacturing/QUOTE_REQUEST.txt).
