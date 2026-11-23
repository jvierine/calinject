# Paid prototype order — 2026-11-23

Five assembled, unprogrammed Rev C boards: JLC's payment-success page and order history confirm payment of **$388.14**. Production-file and parts-placement review were requested. Shipping and personal contact details are deliberately excluded from this public repository. Hardware qualification remains pending. See [cost](cost.md) for the payment and separately reviewed charges.

The historical draft records below describe earlier quote states and do not describe current payment status.

# JLC stock correction — 2026-11-23

The cart reported C144198 out of stock for this five-board build: live Select Parts showed only four available. U5 has been replaced with MCP4725A1T-E/CH (C61423), with 690 in JLC assembly inventory at selection time. The revised BOM is uploaded, and all required components including JP1 headers are selected. Firmware C-0.4.3 supports both 0x60 (A0) and 0x62 (A1); 33 unit tests and the MicroPython compiler check passed. PCB DRC reports zero violations, unconnected items or schematic-parity issues. Native PCB changes are limited to the DAC value text; copper and the existing Gerber archive are unchanged.

Revised quote: PCB $31.07 + assembly $315.68 = $346.75 displayed. Depaneling $3.31 is excluded, giving $350.06 ($70.01 per board) before delivery, tax and remark-review charges. A $66.20 rush charge appeared during cart editing; standard three-day PCB lead time was restored. Hainan uses SF Express outside Guangdong. No payment was made.

The JLC-specific SMA rotation correction is included in the placement file. All five SMA threads were visually checked outward in the live preview: J1/J4 east, J2/J3 south, J5 west. U1 USB faces north, verified against the genuine module pinout. This is a preliminary preview check; JLC final placement/DFM and physical first-article tests remain required.

# Previous JLC quote — Rev C, 2026-11-23

[Open the saved JLC draft](https://cart.jlcpcb.com/smt-order/?pcbFileNo=0b8c3cd6f17641d3b02a37cb10f7fb73). Quote only: no order, payment, pre-order or manufacturing authorization.

Five fully electrically assembled boards, **supplied unprogrammed**. Customer performs USB-C firmware loading and RF/GPS/timing acceptance tests. Standard PCBA, top side, 95 placements per board; all 45 BOM rows confirmed. JLC combines duplicate rows into 40 purchasing items. JP1 headers initially matched at quantity zero; explicitly selected, resulting in 12 purchased headers for the 10 fitted positions plus allowance. No parts omitted or substituted.

| Item | Five-board total, USD |
|---|---:|
| PCB and PCB options | 31.07 |
| Standard PCBA including parts | 309.74 |
| Displayed total | **340.81** |
| Depaneling, explicitly excluded from displayed total | 3.31 |
| Subtotal including depaneling | **344.12** |
| Per board including depaneling | **68.82** |

Shipping, tax and any assembly-remark/DFM review adjustments are not finalized or included above. The earlier $2.87 shipping estimate used a smaller weight and must not be treated as the final charge. Hainan is outside Guangdong; SF Express outside Guangdong was selected for the estimate. Quote-stage weight is 997.50 g. Current schedule displays three PCB days plus five–six assembly days, with one additional day for advanced options; this is an estimate.

The compact `calinject-revC-JLC-assembly-only.zip` is attached under Assembly remark. It contains the revised assembly-only instructions and manufacturing files, without large simulation data. Function test is **No**. All five SMAs are the exact horizontal C7498154; TCXO C253701 and revised buffers/gate/ESD parts match. Production-file and parts-placement confirmation remain manual.

The online 3D preview was inspected as a preliminary view, not approved as a final placement drawing. JLC explicitly says final placement is checked during DFM after ordering. Package/library rotations, pin 1, module/header overlap in the simplified model, SMA mating depth and shunt installation require final review against the native PCB and ASSEMBLY.md before manufacture. No claim of hardware qualification follows from this quote.

## Earlier snapshots (superseded)

# Rev C quotation update — 2026-11-23

The new Rev C Gerber archive was uploaded through Chrome. JLC processed it and detected a four-layer 65 × 90 mm board. The Rev C full-assembly BOM/CPL and factory package have been generated locally; matching them in the new draft and obtaining a complete assembled/programmed quote remain pending. No order or payment has been placed. Do not manufacture the older Rev B draft below.

---

> Historical Rev B upload. Rev C supersedes these files and requires a new Gerber/BOM/CPL upload. The prior draft must not be manufactured.

# JLC quotation status — 2026-11-23

Five complete Rev B assemblies, delivery to Hainan, China. Hardware unchanged;
u-blox MAX-M10S-00B retained. Quote only; no payment or manufacturing order placed.

Gerbers and factory firmware/test package uploaded through Chrome. Standard PCBA,
top assembly, four layers, 1.6 mm, JLC041611-7628 stack, 1 oz outer/inner copper,
green mask, lead-free HASL, five units. Production and placement confirmation
required. Function testing requested; custom module programming/test capability
remains unconfirmed.

The initial $31.07 display was PCB/options only, not a complete assembly price.
SF Express outside Guangdong displayed $2.87 before final assembled weight/address.

The original SMT-only CPL omitted manual assembly. The separate
`manufacturing/jlc-turnkey/` upload now includes 95 placements and every assembly
material on a single BOM worksheet. JLC accepted these files on retry after one
generic processing error. Exact MPNs in Comment fixed dangerous fuzzy matches
(including a through-hole fuse and incorrect resistor values).

Latest matcher state: 45 BOM rows, 37 confirmed, six inventory-shortage rows,
two unmatched rows. These are BOM row counts, not individual placement counts.

| Required item | JLC result |
|---|---|
| C17 GRM1885C1H220JA01D | C77031, 20 shortfall including purchase allowance |
| U10/U11 SN74LVC2G125DCUR | C21404, 9 shortfall; 1 in JLC inventory |
| U1 left/right M20-9990946 headers | C3325656, 10 shortfall, represented as two rows |
| U8 SN74LVC2G08DCUR | C91875, 5 shortfall |
| Y1 ECS-VC-TXO32-S3-33-100-BN-TR | C2613109, 5 shortfall |
| D1 PESD5V0F1BLS,315 | Unmatched; exact part still required |
| Two closed-top 2.54 mm jumper shunts | Unmatched; assembler to propose matching part |

JP1 headers matched C168677 but were not selected automatically (quantity zero);
they also require review. U1 module matched C5350143 ($29.7485 for five), genuine
manufacturer and manual installation remain subject to factory confirmation.
U4 matched the exact C4153167 ($53.835 for five). Neither amount is a full quote.

NEXT displayed “Project has unselected parts” with a “Do not place” option.
Selected “Select parts” to preserve full assembly. No missing part was authorized
for omission. JLC's parts-order page warns pre-orders cannot be canceled once
quotation finishes; no pre-order submitted. Manual Parts Selection page had no
requests. A complete price therefore remains unavailable pending sourcing and
factory capability review. No factory inquiry was sent in chat or email.
