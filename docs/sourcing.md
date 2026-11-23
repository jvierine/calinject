# Parts chosen for repeat builds

Rev C favors established component families, standard packages, useful stock
depth and documented compatibility before the lowest unit price. No sales-volume
ranking or guaranteed future availability is claimed. Check stock again before
ordering, and review manufacturer change/EOL notices for repeat builds.

| Function | Selected part | JLC code | Stock snapshot / reason |
|---|---|---|---|
| Tunable 10 MHz | KDS 1XTV10000MDA, DSA321SDN | C253701 | 400 in JLC search; about $1.07; manufacturer still lists the family |
| Output drivers | TI SN74LVC2G125DCTR | C206035 | 1,944; active TI orderable, standard 0.65 mm SSOP |
| Comb AND gate | Nexperia 74LVC2G08DC,125 | C456135 | 3,098; established LVC logic family |
| 22 pF timing capacitor | Samsung CL10C220JB8NNNC | C1653 | Standard 0603, C0G, 50 V, 5%; basic-library candidate |
| GPS RF protection | Nexperia PESD5V0F1BL,315 | C45961 | 123,959; antenna-rated, low capacitance, DFN1006 |
| Horizontal SMA | Lian Xin SMA-KWE | C7498154 | 8,809 LCSC catalogue snapshot; common right-angle construction; exact 4.2 mm drawing controls |
| Module 1×9 headers | FG-PZ2.54-1-09P | C25687201 | 2,825 catalogue snapshot; standard 0.64 mm square pins |
| Module 1×5 header | FG-PZ2.54-01-05P | C42391439 | 934 catalogue snapshot |
| Range 1×3 headers | FG-PZ2.54-1-03P | C25687200 | 1,911 catalogue snapshot |
| Closed-top shunts | BOOMELE 2.54Short Circuit Cap Closed | C100114 | 242,405 catalogue snapshot |

Snapshots were checked on 2026-11-23. Catalogue stock and JLC assembly stock can
differ. The actual assembly matcher and final factory BOM must confirm every row.
The machine-readable selection and candidate alternatives are in
`manufacturing/sourcing.json`.

The small-package SN74LVC2G125DCU3 was rejected despite available stock: TI marks
it Last Time Buy. DCTR is active and has substantially deeper stock. Its package
requires the revised PCB; it is not a drop-in for the old DCU footprint. The common
quad-buffer option would need a more extensive layout change; the selected active
dual-buffer family meets this build's stock and price needs.

The KDS device shares the usual 3225 VCTCXO pin functions, 3.3 V supply and
0.5–2.5 V control range. It needs its own land pattern, copper keepout, measured
tuning slope and updated noise assumptions. Its specified -135 dBc/Hz point at
1 kHz offset does not define a full noise spectrum. HCI 9132S-M10.000Q33DT2Q is a
stocked candidate fallback, not an automatically approved replacement.

Yageo resistors, Murata/Samsung capacitors, AP2112 LDOs and standard pin headers
avoid unusual passive values/packages except where the RF attenuator needs them.
The genuine Waveshare module, u-blox GNSS, pSemi attenuator and Mini-Circuits
combiner remain specialist purchases. Replacing those requires more than matching
a footprint. A factory first article must qualify timing, comb spectrum, isolation
and output loading before substitution or production of the remaining four.

Primary references: [KDS family](https://www.kds.info/products/dsa321sdn-2/),
[KDS exact specification](https://atta.szlcsc.com/upload/public/pdf/source/20190315/C253701_69B1AE3584D7A6F1B7B612113CD52085.pdf),
[TI active part](https://www.ti.com/product/SN74LVC2G125/part-details/SN74LVC2G125DCTR),
[Nexperia AND gate](https://assets.nexperia.com/documents/data-sheet/74LVC2G08.pdf),
[Nexperia RF protection](https://assets.nexperia.com/documents/data-sheet/PESD5V0F1BL.pdf),
[SMA drawing](https://datasheet.lcsc.com/datasheet/pdf/6bc515fc4ae516d1b058a713f986108e.pdf?productCode=C7498154),
[JLC headers](https://jlcpcb.com/parts/2nd/Connectors/Pin_Headers_3127?Manufacturer=FG),
and [JLC shunts](https://jlcpcb.com/parts/2nd/Connectors/Shunts_Jumpers_3129).
