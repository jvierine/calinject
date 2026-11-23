# Printed enclosure

The base and lid are provided as STL and plain 3MF geometry, in millimetres and ready in their print orientations. The 3MF files are models, not Bambu printer profiles or sliced jobs. Import both into Bambu Studio, select your H2D and installed nozzle/material, and slice locally.

Suggested starting settings: PETG, 0.4 mm nozzle, 0.20 mm layers, four walls and 20% infill. Print the base floor down and the lid's outer face down; the locating lip points upward. No supports should be necessary apart from a short USB opening bridge. Check the slicer's bridge preview. PLA is also suitable indoors, but is less tolerant of heat.

Rev C outside dimensions are **98 × 73 × 20 mm**. The board origin is 4 mm from the north/west outside walls; PCB top is 7 mm above the outside bottom. The board is 1.6 mm thick. Four M3 mounting holes align with integral standoffs. All five SMAs connect horizontally: GPS and 10 MHz on the right, PPS on the left, RF IN and TO SDR on the south wall. The lid has only the LEVEL tool opening and screw holes.

The case splits at the 13 mm SMA-axis height. Drop the fully soldered board into the base's open notches, then fit the lid; no connector removal or electrical assembly is required. Ports have 7.2 mm openings with 11 mm outside nut relief. Use four M3 × 6 mm screws for the PCB and four M2 × 12 mm screws for the lid, checking actual head height and engagement. PCB pilots are 2.5 mm; lid pilots are 1.6 mm. No heat-set inserts are required. Do not overtighten printed bosses.

The meshes are watertight and the assembled base/lid solids do not intersect. Physical fit has not been printed or tested. Check SMA mating-nut clearance and USB-plug reach on a first print before printing all five cases. BOOT/RESET access requires removing the lid. The PCB STEP contains the board only, not a complete component clearance model.

The USB opening is 14 mm wide × 8.5 mm high (8–16.5 mm above the outside base), allowing the cable housing to enter the recess. It assumes the genuine module on 2.5 mm spacers. Rev B cases with vertical SMA access holes do not fit Rev C.

Plastic provides no RF shielding. Optional conductive foil needs insulation and a deliberate ground connection; it is not part of the qualified design. Do not place exposed foil against pads or leads.

`enclosure.py` is the editable parametric source. Rebuild with `conda run -n base python mechanical/enclosure.py`. The exported parts fit readily within the H2D build area.
