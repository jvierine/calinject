# Printed enclosure

The base and lid are provided as STL and plain 3MF geometry, in millimetres and ready in their print orientations. The 3MF files are models, not Bambu printer profiles or sliced jobs. Import both into Bambu Studio, select your H2D and installed nozzle/material, and slice locally.

Suggested starting settings: PETG, 0.4 mm nozzle, 0.20 mm layers, four walls and 20% infill. Print the base floor down and the lid's outer face down; the locating lip points upward. No supports should be necessary apart from a short USB opening bridge. Check the slicer's bridge preview. PLA is also suitable indoors, but is less tolerant of heat.

Assembled outside dimensions are 104 × 79 × 20 mm. Board origin is 7 mm from the north/west case walls; PCB top is 7 mm above the outside bottom. The board is 1.6 mm thick. Four M3 mounting holes align with integral standoffs. Five 12 mm lid openings provide access to GPS ANT, RF IN, TO SDR, 10 MHz OUT and 1 PPS OUT, and the small opening accesses the LEVEL trimmer. The USB-C opening assumes the genuine module mounted on 2.54 mm spacers as specified to the assembler.

Use four M3 × 6 mm screws for the PCB and four M3 × 10 mm screws for the lid, checking actual head height and engagement before tightening. The 2.5 mm pilots can be tapped or used with suitable plastic-thread screws. No heat-set inserts are required. Do not overtighten printed bosses. Install the fully built board and screw on the lid; there is no electrical assembly for the user.

The meshes are watertight and the assembled base/lid solids do not intersect. Physical fit has not been printed or tested. Check SMA mating-nut clearance and USB-plug reach on a first print before printing all five cases. BOOT/RESET access requires removing the lid. The PCB STEP contains the board only, not a complete component clearance model.

Rev B enlarges the USB opening to 14 mm wide × 8.5 mm high (8–16.5 mm above the outside base), allowing the cable housing to enter the recess around the module's connector. The board, standoffs and SMA locations are unchanged.

Plastic provides no RF shielding. Optional conductive foil needs insulation and a deliberate ground connection; it is not part of the qualified design. Do not place exposed foil against pads or leads.

`enclosure.py` is the editable parametric source. Rebuild with `conda run -n base python mechanical/enclosure.py`. The exported parts fit readily within the H2D build area.
