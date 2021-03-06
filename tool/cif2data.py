#!/usr/bin/python3
import sys
import seekpath
import glob
import pymatgen
from pymatgen.analysis.structure_matcher import StructureMatcher
import numpy


if __name__ == '__main__':

    matcher = StructureMatcher()
    args = sys.argv
    #
    # Read All files specified as command-line arguments
    #
    for ifile in range(len(args)-1):
        cif_file = args[ifile+1]
        print("Reading "+cif_file+" ... ", end="")
        #
        # PyMatGen structure from CIF file
        #
        structure = pymatgen.Structure.from_file(cif_file)
        structure.remove_oxidation_states()
        #
        # Refine 3-folded Wyckoff position
        #
        frac_coord2 = numpy.array(structure.frac_coords)
        for ipos in range(len(frac_coord2)):
            for iaxis in range(3):
                coord3 = frac_coord2[ipos, iaxis] * 6.0
                if abs(round(coord3) - coord3) < 0.001:
                    frac_coord2[ipos, iaxis] = float(round(coord3)) / 6.0
        #
        # Disordered structure raises AttributeError. So it is skipped.
        #
        try:
            skp = seekpath.get_explicit_k_path((structure.lattice.matrix, frac_coord2,
                                               [pymatgen.Element(str(spc)).number for spc in structure.species]))
            structure2 = pymatgen.Structure(skp["primitive_lattice"],
                                            skp["primitive_types"], skp["primitive_positions"])
        except AttributeError:
            print("Fractional occupancy, may be disordered.")
            continue
        #
        # This structure is the same or not as the known structures
        #
        known = False
        for xsf_file in glob.glob("*.xsf"):
            known_structure = pymatgen.Structure.from_file(xsf_file)
            if matcher.fit(structure2, known_structure):
                print("Same as " + xsf_file)
                known = True
                break
        #
        # If it is new structure, save it as XSF
        #
        if not known:
            #
            xsf_file = structure2.formula.replace(" ", "")+"_"+skp['spacegroup_international'].replace("/", "s")+'_' \
                       + cif_file[0:len(cif_file) - 4].replace("MyBaseFileNameCollCode", "")+".xsf"
            print("Write to "+xsf_file)
            structure2.to(fmt="xsf", filename=xsf_file)
