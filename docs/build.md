# Editing and reproducing Rev C

Use KiCad 10.0.8 or a compatible later KiCad 10 release. All schematic symbols and PCB footprints used by this design are included locally; no global library lookup is needed. Open `cad/calinject.kicad_pro`.

## Frozen-board exports

`tools/export.py` validates schematic ERC and PCB DRC, including schematic/PCB parity, and stops if any findings remain. It then exports the schematic/assembly/copper PDFs, Gerbers, drill data/map/report, IPC-D-356 netlist, SMT positions and board-only STEP.

```bash
conda run -n base python tools/export.py
conda run -n base python -m unittest discover -s tests -v
conda run -n base python mechanical/enclosure.py
```

Set `KICAD_CLI` if `kicad-cli` is not on PATH. The exporter also recognizes the normal macOS KiCad application and the development DMG mount. Normal project Python uses base conda. The `pcbnew` helper scripts require **KiCad's bundled Python**, whose ABI matches its SWIG module; this is a CAD application interpreter, not the macOS system Python.

## Circuit generators

`tools/design.py` defines circuit parts, pins, nets, placement, manufacturer part numbers, approximate costs and body dimensions. `tools/schematic.py` creates the editable hierarchical schematic and symbol library. `tools/plan_ground.py` plans ground escape vias. `tools/kicad_board.py` makes footprints, manual RF tracks and a Specctra DSN. **Regenerating the PCB destroys the existing routing.** Work on a branch/copy before regeneration.

The development sequence is design → ground planner → board generator → FreeRouting → SES import/plane fill → layout finalization → freeze_board.py → apply_sourcing.py → improve_returns.py → schematic → export. The board generator exports two routing layers; the native board has four, with both inner layers reserved for ground. FreeRouting 2.5.0 Java was used; its native macOS CLI failed during serialization. Its reported opens are checked after importing and filling planes; final KiCad DRC is authoritative. `apply_sourcing.py` adds the KDS top/Inner1 copper keepout and checks the frozen sourcing footprints using native S-expressions, then refills through KiCad CLI. DSN omits that keepout because its format cannot express the permitted component-pad exception; final KiCad DRC enforces it.

Run `tools/finish_board.py --import` only on a fresh generated board; it adds planes. Run `tools/finalize_layout.py` once on that board; it assigns unused-pin nets and adds fabrication pin-1 marks. They are development steps, not idempotent frozen-board exporters.

After those steps run `tools/freeze_board.py` with KiCad's bundled interpreter. It applies the final reviewed routing clearances, assembly-reference placement and native nominal stack, then refreshes the local footprint library. `tools/export.py` must pass after this step. For the current frozen board, simply export; do not rerun the router.

The nominal native stack is four 35 µm copper layers with 0.20 mm outer dielectrics and a 1.04 mm central dielectric, plus two 0.01 mm masks, totaling 1.6 mm. The fabricator must confirm its real materials, pressed thicknesses and RF impedance before fabrication. The native design and assembly document must be updated together if the stack changes.

## Workbooks and release

`tools/bom.mjs` builds BOM/CPL XLSX and JSON from `cad/design.json` using `@oai/artifact-tool`. It needs Node.js and that package available through Node's normal package resolution. The root CPL is SMT-only. Run with `--jlc` to generate the separate single-sheet full-assembly upload in `manufacturing/jlc-turnkey/`; that version includes manual module, headers, SMA jacks, trimmer and shunt placements. `manufacturing/sourcing.json` controls verified purchasing codes. X is right and Y is up from the upper-left KiCad origin, so on-board Y values are negative. Review package pin1 and horizontal SMA orientation.

`tools/package.py` packages the complete source/export tree and a smaller factory quotation package with SHA-256 manifests. Neither package proves measured hardware performance. The `validation/` reports cover software, CAD rules and enclosure mesh geometry only. The tests exercise UBX parsing, UTC flags, servo counting/fault handling, synthetic SDR timing/frequency fits and the actual PIO instruction bodies; they do not execute on physical RP2040 hardware.

Manufacturer documents are linked in `docs/sources.md` and excluded from redistribution. External runtimes and packages retain their own licenses. Numeric model/test data use HDF5, metadata use JSON, and factory spreadsheets use XLSX.

Rev C verification also includes `tools/verify_board.py` (KiCad interpreter), which checks manifest/CPL placement and nets, combiner pin mapping, pad layers, track/via rules and existing ERC/DRC reports. `tools/verify_firmware.py` runs from base conda with `mpy-cross==1.29.0.post2`; it compiles all five application files and assembles the actual PIO functions using a hash-pinned upstream MicroPython 1.29.0 assembler. The result is in `validation/firmware-compile.json`; it explicitly does not claim on-device execution. Source files remain the normal customer USB programming inputs; the compiled `.mpy` files are verification artifacts.

After reproducing the original frozen routing, the latest layout audit edits are applied with `tools/add_local_bypass.py` (once) followed by `tools/improve_returns.py`, using KiCad Python. They avoid existing copper rather than rerouting signals. The former records new capacitor placements in the design source and manifest; do not run it on a board that already contains C29/C31/C32/C33. `tools/audit_layout.py` measures the resulting ground-transition and bypass geometry. The delivered native PCB already includes these changes; normal export does not rerun these development edits.

Run the behavioral system simulation with `conda run -n base python tools/run_end_to_end.py`. It creates HDF5/JSON results in `validation/end-to-end/` and the illustrated `docs/end-to-end.md` report. Source/data hashes are stored as metadata. Generic receiver filters, assumed additive jitter and gain replace unavailable measured hardware models; the report lists the scope and exclusions.
