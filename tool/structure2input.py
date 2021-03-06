import pymatgen
import seekpath
import numpy
import os
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from write.write_openmx import write_openmx
from write.write_pwx import write_pwx
from write.write_pp import write_pp
from write.write_ph import write_ph
from write.write_wannier import write_wannier
from write.write_sh import write_sh
from pymatgen.core.periodic_table import get_el_sp


def structure2input(structure, dk_path, dq_grid, pseudo_kind, pseudo_dir, queue, rel, norm_con, path="", flg_phonon=False, flg_wan90 = False, flg_sctk = False, flg_openmx = False):
    _flg_phonon = flg_phonon
    _flg_wan90 = flg_wan90
    _flg_sctk = flg_sctk
    if pseudo_kind == "sg15":
        if rel:
            from pseudo.sg15_rel import pseudo_dict, ecutwfc_dict, ecutrho_dict, valence_dict, atomwfc_dict
        else:
            from pseudo.sg15 import pseudo_dict, ecutwfc_dict, ecutrho_dict, valence_dict, atomwfc_dict
    elif pseudo_kind == "sg15_2":
        if rel:
            from pseudo.sg15_2_rel import pseudo_dict, ecutwfc_dict, ecutrho_dict, valence_dict, atomwfc_dict
        else:
            from pseudo.sg15_2 import pseudo_dict, ecutwfc_dict, ecutrho_dict, valence_dict, atomwfc_dict
    elif pseudo_kind == "pslibrary":
        if rel:
            from pseudo.pslibrary_rel import pseudo_dict, ecutwfc_dict, ecutrho_dict, valence_dict, atomwfc_dict
        elif norm_con:
            from pseudo.pslibrary_nc import pseudo_dict, ecutwfc_dict, ecutrho_dict, valence_dict, atomwfc_dict
        else:
            from pseudo.pslibrary import pseudo_dict, ecutwfc_dict, ecutrho_dict, valence_dict, atomwfc_dict
    elif pseudo_kind == "dojo":
        if norm_con:
            from pseudo.dojo import pseudo_dict, ecutwfc_dict, ecutrho_dict, valence_dict, atomwfc_dict
        else:
            print("under construction")
    else:
        from pseudo.sssp import pseudo_dict, ecutwfc_dict, ecutrho_dict, valence_dict, atomwfc_dict
    #
    # Band path and primitive lattice
    #
    frac_coord2 = numpy.array(structure.frac_coords)
    for ipos in range(len(frac_coord2)):
        for iaxis in range(3):
            coord3 = frac_coord2[ipos, iaxis] * 6.0
            if abs(round(coord3) - coord3) < 0.001:
                frac_coord2[ipos, iaxis] = float(round(coord3)) / 6.0
    #
    skp = seekpath.get_explicit_k_path((structure.lattice.matrix, frac_coord2,
                                        [pymatgen.Element(str(spc)).number for spc in structure.species]),
                                       reference_distance=dk_path)
    #
    # Lattice information
    #
    bvec = skp["reciprocal_primitive_lattice"]
    atom = [str(get_el_sp(iat)) for iat in skp["primitive_types"]]
    typ = set(atom)
    #
    # WFC and Rho cutoff
    #
    ecutwfc = 0.0
    ecutrho = 0.0
    for ityp in typ:
        if ecutwfc < ecutwfc_dict[str(ityp)]:
            ecutwfc = ecutwfc_dict[str(ityp)]
        if ecutrho < ecutrho_dict[str(ityp)]:
            ecutrho = ecutrho_dict[str(ityp)]
    #
    # k and q grid
    #
    nq = numpy.zeros(3, numpy.int_)
    for ii in range(3):
        norm = numpy.sqrt(numpy.dot(bvec[ii][:], bvec[ii][:]))
        nq[ii] = round(norm / dq_grid)
        if nq[ii] == 0 :
            nq[ii] = 1
        print(norm)
    print("Coarse grid : ", nq[0], nq[1], nq[2])
    #
    # Band path
    #
    print("Band path")
    for ipath in range(len(skp["path"])):
        start = skp["explicit_segments"][ipath][0]
        final = skp["explicit_segments"][ipath][1] - 1
        print("%5d %8s %10.5f %10.5f %10.5f %8s %10.5f %10.5f %10.5f" % (
            final - start + 1,
            skp["explicit_kpoints_labels"][start],
            skp["explicit_kpoints_rel"][start][0],
            skp["explicit_kpoints_rel"][start][1],
            skp["explicit_kpoints_rel"][start][2],
            skp["explicit_kpoints_labels"][final],
            skp["explicit_kpoints_rel"][final][0],
            skp["explicit_kpoints_rel"][final][1],
            skp["explicit_kpoints_rel"][final][2]))
    #
    # Number of electrons
    #
    nbnd = 0
    for iat in atom:
        nbnd += valence_dict[iat]
    nbnd = nbnd / 2 + len(atom)*50
    if rel:
        nbnd *= 2
    #
    # Shell scripts
    #
    structure2 = pymatgen.Structure(skp["primitive_lattice"],
                                    skp["primitive_types"], skp["primitive_positions"])
    spg_analysis = SpacegroupAnalyzer(structure2)
    coarse = spg_analysis.get_ir_reciprocal_mesh(mesh=(nq[0], nq[1], nq[2]), is_shift=(0, 0, 0))
    middle = spg_analysis.get_ir_reciprocal_mesh(mesh=(nq[0]*2, nq[1]*2, nq[2]*2), is_shift=(0, 0, 0))
    dense = spg_analysis.get_ir_reciprocal_mesh(mesh=(nq[0]*4, nq[1]*4, nq[2]*4), is_shift=(0, 0, 0))
    print("Number of irreducible k : ", len(coarse), len(middle), len(dense))
    write_sh(nq[0]*nq[1]*nq[2], len(coarse), len(middle), len(dense),
             len(skp["explicit_kpoints_rel"]), atom, atomwfc_dict, queue, path, flg_phonon= _flg_phonon, flg_sctk=_flg_sctk)
    #
    # rx.in, scf.in, nscf.in, band.in , nscf_w.in, nscf_r.in
    #
    write_pwx(skp, pseudo_dir, ecutwfc, ecutrho, pseudo_dict, nq, nbnd, rel, flg_phonon= _flg_phonon, flg_wan90=_flg_wan90, flg_sctk = _flg_sctk)
    #
    # ph.in, elph.in, epmat.in, phdos.in, rpa.in, scdft.in
    #
    if _flg_phonon is True:
        write_ph(nq, ecutwfc, nbnd)
    #
    # bands.in, pp.in, proj.in, pw2wan.in, q2r.in
    #
    write_pp(flg_wan90=_flg_wan90)
    #
    # band.gp, pwscf.win, respack.in, disp.in
    #
    write_wannier(skp, nbnd, nq, flg_phonon=_flg_phonon, flg_wan90=_flg_wan90)
    #
    # openmx.in : Input file for openmx
    #
    if flg_openmx is True:
        if not os.path.isfile("openmx.dat"):
            write_openmx(skp, nq, rel)
