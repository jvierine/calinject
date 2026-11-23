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
