import os
import math


def good_proc(nproc, ncore):
    if ncore == 24:
        if nproc == 5:
            nproc = 4
        elif nproc == 7:
            nproc = 6
        elif 8 < nproc < 12:
            nproc = 8
        elif 12 < nproc < 24:
            nproc = 12
    else:  # ncore == 40
        if nproc == 3:
            nproc = 2
        elif 5 < nproc < 8:
            nproc = 5
        elif nproc == 9:
            nproc = 8
        elif 10 < nproc < 20:
            nproc = 10
        elif 20 < nproc < 40:
            nproc = 20

    return nproc


def write_sh(nkcbz, nkc, nks, nkd, nk_path, atom, atomwfc_dict, queue, path="", flg_phonon=False, flg_sctk=False, flg_respack=True):
    
    pw = path + "pw.x"
    ph = path + "ph.x"
    proj = path + "projwfc.x"
    vf = path + "fermi_velocity.x"
    bands = path +  "bands.x"
    sumpdos = path + "sumpdos.x"
    fproj = path + "fermi_proj.x"
    sctk = path + "sctk.x"
    qe = "/home/issp/materiapps/qe/q-e-6.3.sh"
    respack = "/home/issp/materiapps/respack/respackvars.sh"
    typ = set(atom)
    #
    if queue == "F4cpus":
        maxnode = 4
        ncore = 24
        runtime = "12:00:00"
    elif queue == "F4cpue":
        maxnode = 4
        ncore = 40
        runtime = "12:00:00"
    elif queue == "i18cpus":
        maxnode = 18
        ncore = 24
        runtime = "0:30:00"
    elif queue == "F36cpus":
        maxnode = 36
        ncore = 24
        runtime = "12:00:00"
    elif queue == "F9cpue":
        maxnode = 9
        ncore = 40
        runtime = "12:00:00"
    elif queue == "F36cpue":
        maxnode = 36
        ncore = 40
        runtime = "12:00:00"
    else:  # queue == "F144cpus":
        maxnode = 144
        ncore = 24
        runtime = "12:00:00"
    #
    # Structure optimization
    #
    nk = min(ncore*maxnode, nks)
    ntg = good_proc(int(ncore*maxnode / nk), ncore)
    nproc = nk*ntg
    node = math.ceil(nproc / ncore)
    if not os.path.isfile("rx.sh"):
        with open("rx.sh", 'w') as f:
            print("#!/bin/sh", file=f)
            print("#QSUB -queue", queue[0:len(queue) - 1], file=f)
            print("#QSUB -node", node, file=f)
            print("#PBS -l walltime="+runtime, file=f)
            print("source ~/.bashrc", file=f)
            print("source "+qe, file=f)
            print("cd $PBS_O_WORKDIR", file=f)
            print("mpijob -n %d %s -nk %d -ntg %d -in rx.in > rx_s.out"
                  % (nproc, pw, nk, ntg), file=f)
            print("sed -n -e '/occupations/c occupations=\"tetrahedra_opt\"' -e '1,/CELL_PARAMETERS/p' rx.in > rx_t.in",
                  file=f)
            print("grep -A 3 CELL_PARAMETERS rx_s.out | tail -n 3 >> rx_t.in", file=f)
            print("awk '/ATOMIC_SPECIES/,/ATOMIC_POSITIONS/' rx.in >> rx_t.in", file=f)
            print("grep -A %d ATOMIC_POSITIONS rx_s.out |tail -n %d >> rx_t.in" % (len(atom), len(atom)), file=f)
            print("sed -n -e '/K_POINTS/,$p' rx.in >> rx_t.in", file=f)
            print("sed -i -e '/occupations/c occupations=\"tetrahedra_opt\"' rx_t.in", file=f)
            print("mpijob -n %d %s -nk %d -ntg %d -in rx_t.in > rx_t.out"
                  % (nproc, pw, nk, ntg), file=f)
    #
    # Charge optimization
    #
    if not os.path.isfile("scf.sh"):
        with open("scf.sh", 'w') as f:
            print("#!/bin/sh", file=f)
            print("#QSUB -queue", queue[0:len(queue) - 1], file=f)
            print("#QSUB -node", node, file=f)
            print("#PBS -l walltime="+runtime, file=f)
            #print("#PBS -l walltime=8:00:00", file=f)
            print("source ~/.bashrc", file=f)
            print("source "+qe, file=f)
            #print("source /home/issp/materiapps/qe/q-e-6.2.1-oldxml.sh", file=f)
            print("cd $PBS_O_WORKDIR", file=f)
            print("mpijob -n %d %s -nk %d -ntg %d -in scf.in > scf.out"
                  % (nproc, pw, nk, ntg), file=f)
    #
    # non scf
    #
    if not os.path.isfile("nscf_r.sh"):
        with open("nscf_r.sh", 'w') as f:
            print("#!/bin/sh", file=f)
            print("#QSUB -queue", queue[0:len(queue) - 1], file=f)
            print("#QSUB -node", node, file=f)
            print("#PBS -l walltime="+runtime, file=f)
            #print("#PBS -l walltime=8:00:00", file=f)
            print("source ~/.bashrc", file=f)
            print("source "+qe, file=f)
            #print("source /home/issp/materiapps/qe/q-e-6.2.1-oldxml.sh", file=f)
            print("cd $PBS_O_WORKDIR", file=f)
            print("mpijob -n %d %s -nk %d -ntg %d -in nscf_r.in > nscf_r.out"
                  % (nproc, pw, nk, ntg), file=f)
 
    #
    # Phonon
    #
    if flg_phonon is True:
        if not os.path.isfile("ph.sh"):
            with open("ph.sh", 'w') as f:
                print("#!/bin/sh", file=f)
                print("#QSUB -queue", queue[0:len(queue) - 1], file=f)
                print("#QSUB -node", node, file=f)
                print("#PBS -l walltime="+runtime, file=f)
                #print("#PBS -l walltime=8:00:00", file=f)
                print("source ~/.bashrc", file=f)
                print("source "+qe, file=f)
                #print("source /home/issp/materiapps/qe/q-e-6.2.1-oldxml.sh", file=f)
                print("cd $PBS_O_WORKDIR", file=f)
                print("mpijob -n %d %s -nk %d -ntg %d -in nscf_p.in > nscf_p.out"
                      % (nproc, pw, nk, ntg), file=f)
                print("mpijob -n %d %s -nk %d -ntg %d -in ph.in > ph.out"
                      % (nproc, ph, nk, ntg), file=f)
                print("find ./ -name \"*.wfc*\" -delete", file=f)
    #
    # Projected DOS
    #
    nk = min(ncore*maxnode, nkd)
    ntg = good_proc(int(ncore*maxnode / nk), ncore)
    nproc = nk * ntg
    node = math.ceil(nproc / ncore)
    #
    # Atomwfc dictionary for fermi_proj.x
    #
    pfermi = {ityp: [[] for il in range(len(atomwfc_dict[ityp][0]))] for ityp in typ}
    ii = 0
    for iat in atom:
        for il in range(len(atomwfc_dict[iat][0])):
            for im in range(atomwfc_dict[iat][0][il]):
                ii += 1
                pfermi[iat][il].append(ii)
    #
    if not os.path.isfile("proj.sh"):
        with open("proj.sh", 'w') as f:
            print("#!/bin/sh", file=f)
            print("#QSUB -queue", queue[0:len(queue) - 1], file=f)
            print("#QSUB -node", node, file=f)
            #print("#PBS -l walltime=8:00:00", file=f)
            print("#PBS -l walltime="+runtime, file=f)
            print("source ~/.bashrc", file=f)
            print("source "+qe, file=f)
            #print("source /home/issp/materiapps/qe/q-e-6.2.1-oldxml.sh", file=f)
            print("cd $PBS_O_WORKDIR", file=f)
            print("mpijob -n %d %s -nk %d -ntg %d -in nscf.in > nscf.out"
                  % (nproc, pw, nk, ntg), file=f)
            print("mpijob -n 1 %s -in nscf.in > vfermi.out" % vf, file=f)
            print("ef=`grep Fermi nscf.out| awk '{print $5}'`", file=f)
            print("sed -i -e '/emin/c emin = '${ef}'' -e '/emax/c emax = '${ef}'' proj.in", file=f)
            print("mpijob -n %d %s -nk %d -ntg %d -in proj.in > proj.out"
                  % (nproc, proj, nk, ntg), file=f)
            #
            # Sum PDOS at each Atom and L
            #
            for ityp in typ:
                for il in range(len(atomwfc_dict[ityp][1])):
                    print("%s pwscf.pdos_atm*\\(%s\\)_wfc#%d* > pdos_%s%s"
                          % (sumpdos, ityp, il+1, ityp, atomwfc_dict[ityp][1][il]), file=f)
            #
            # Fermi surface with atomic projection
            #
            for ityp in typ:
                for il in range(len(atomwfc_dict[ityp][1])):
                    print("sed -e '$a %d\\n" % len(pfermi[ityp][il]), end="", file=f)
                    for ii in pfermi[ityp][il]:
                        print(" %d" % ii, end="", file=f)
                    print("' proj.in > proj_f.in", file=f)
                    print("mpijob -n 1 %s -in proj_f.in" % fproj, file=f)
                    print("mv proj.frmsf %s%s.frmsf" % (ityp, atomwfc_dict[ityp][1][il]), file=f)
    #
    # Electron-phonon
    #
    if flg_phonon is True:
        if not os.path.isfile("elph.sh"):
            with open("elph.sh", 'w') as f:
                print("#!/bin/sh", file=f)
                print("#QSUB -queue", queue[0:len(queue) - 1], file=f)
                print("#QSUB -node", node, file=f)
                print("#PBS -l walltime="+runtime, file=f)
                #print("#PBS -l walltime=8:00:00", file=f)
                print("source ~/.bashrc", file=f)
                print("source "+qe, file=f)
                #print("source /home/issp/materiapps/qe/q-e-6.2.1-oldxml.sh", file=f)
                print("cd $PBS_O_WORKDIR", file=f)
                print("mpijob -n %d %s -nk %d -ntg %d -in nscf_pd.in > nscf_pd.out"
                      % (nproc, pw, nk, ntg), file=f)
                print("mpijob -n %d %s -nk %d -ntg %d -in elph.in > elph.out"
                      % (nproc, ph, nk, ntg), file=f)
                print("find ./ -name \"*.wfc*\" -delete", file=f)
    #
    # Band
    #
    nk = min(ncore*maxnode, nk_path)
    ntg = good_proc(int(ncore*maxnode / nk), ncore)
    nproc = nk * ntg
    node = math.ceil(nproc / ncore)
    if not os.path.isfile("band.sh"):
        with open("band.sh", 'w') as f:
            print("#!/bin/sh", file=f)
            print("#QSUB -queue", queue[0:len(queue) - 1], file=f)
            print("#QSUB -node", node, file=f)
            print("#PBS -l walltime="+runtime, file=f)
            #print("#PBS -l walltime=8:00:00", file=f)
            print("source ~/.bashrc", file=f)
            print("source "+qe, file=f)
            #print("source /home/issp/materiapps/qe/q-e-6.2.1-oldxml.sh", file=f)
            print("cd $PBS_O_WORKDIR", file=f)
            print("mpijob -n %d %s -nk %d -ntg %d -in band.in > band.out"
                  % (nproc, pw, nk, ntg), file=f)
            print("mpijob -n %d %s -nk %d -ntg %d -in bands.in > bands.out"
                  % (nproc, bands, nk_path, ntg), file=f)
    #
    # Electron-phonon matrix
    #
    if flg_phonon is True:
        nk = min(ncore * maxnode, nkc)
        ntg = good_proc(int(ncore * maxnode / nk), ncore) / 2
        nproc = nk * ntg
        node = math.ceil(nproc / ncore)
        if not os.path.isfile("epmat.sh"):
            with open("epmat.sh", 'w') as f:
                print("#!/bin/sh", file=f)
                print("#QSUB -queue", queue[0:len(queue) - 1], file=f)
                print("#QSUB -node", node, file=f)
                print("#PBS -l walltime="+runtime, file=f)
                #print("#PBS -l walltime=8:00:00", file=f)
                print("source ~/.bashrc", file=f)
                print("source "+qe, file=f)
                #print("source /home/issp/materiapps/qe/q-e-6.2.1-oldxml.sh", file=f)
                print("cd $PBS_O_WORKDIR", file=f)
                print("bmax=`grep \"Highest band which contains FS\" vfermi.out elph.out| awk 'NR==1{print $NF}'`",
                      file=f)
                print("bmin=`grep \"Lowest band which contains FS\" vfermi.out elph.out| awk 'NR==1{print $NF}'`",
                      file=f)
                print("sed -i -e \"/elph_nbnd_min/c elph_nbnd_min=$bmin\" "
                      "-e \"/elph_nbnd_max/c elph_nbnd_max=$bmax\" epmat.in", file=f)
                print("mpijob -n %d %s -nk %d -ntg %d -in nscf_pc.in > nscf_pc.out"
                      % (nproc, pw, nk, ntg), file=f)
                print("mpijob -n %d %s -nk %d -ntg %d -in epmat.in > epmat.out"
                      % (nproc, ph, nk, ntg), file=f)
                print("find ./ -name \"*.wfc*\" -delete", file=f)
    #
    # Coulomb matrix
    #
    if flg_sctk is True:
        nk = min(ncore * maxnode, nkcbz*2)
        ntg = 1
        nproc = nk * ntg
        node = math.ceil(nproc / ncore)
        if not os.path.isfile("kel.sh"):
            with open("kel.sh", 'w') as f:
                print("#!/bin/sh", file=f)
                print("#QSUB -queue", queue[0:len(queue) - 1], file=f)
                print("#QSUB -node", node, file=f)
                print("#PBS -l walltime="+runtime, file=f)
                #print("#PBS -l walltime=8:00:00", file=f)
                print("source ~/.bashrc", file=f)
                print("cd $PBS_O_WORKDIR", file=f)
                print("mpijob -n %d %s -nk %d -in twin.in > twin.out"
                      % (nproc, pw, nk), file=f)
                print("mpijob -n %d %s -nk %d -in sctk.in > sctk.out"
                      % (nproc, sctk, nk), file=f)
    #
    # CalcChi for RESPACK 
    #
    if flg_respack is True:
        node  = maxnode
        nproc = maxnode
        nomp  = ncore
        if not os.path.isfile("calcChi.sh"):
            with open("calcChi.sh", 'w') as f:
                print("#!/bin/sh", file=f)
                print("#QSUB -queue", queue[0:len(queue) - 1], file=f)
                print("#QSUB -node", node, file=f)
                print("#QSUB -omp ", nomp, file=f)
                print("#QSUB -mpi ", nproc, file=f)
                print("#PBS -l walltime="+runtime, file=f)
                #print("#PBS -l walltime=8:00:00", file=f)
                print("source ~/.bashrc", file=f)
                print("source "+respack, file=f)
                print("cd $PBS_O_WORKDIR", file=f)
                print("mpijob -n %d calc_chiqw  < respack.in > calc_chi.out"
                      % (nproc), file=f)
    #
    # CalcWJ for RESPACK 
    #
    if flg_respack is True:
        node  = 1
        nproc = 1
        nomp  = ncore
        if not os.path.isfile("calcWJ.sh"):
            with open("calcWJ.sh", 'w') as f:
                print("#!/bin/sh", file=f)
                print("#QSUB -queue", queue[0:len(queue) - 1], file=f)
                print("#QSUB -node", node, file=f)
                print("#QSUB -omp ", nomp, file=f)
                print("#QSUB -mpi ", nproc, file=f)
                print("#PBS -l walltime="+runtime, file=f)
                #print("#PBS -l walltime=8:00:00", file=f)
                print("source ~/.bashrc", file=f)
                print("source "+respack, file=f)
                print("cd $PBS_O_WORKDIR", file=f)
                print("calc_w3d < respack.in > calc_w3d.out", file=f)
                print("calc_j3d < respack.in > calc_j3d.out", file=f)
    #
    # Wannier for RESPACK 
    #
    if flg_respack is True:
        node  = 1
        nproc = 1
        nomp  = ncore
        if not os.path.isfile("wannier.sh"):
            with open("wannier.sh", 'w') as f:
                print("#!/bin/sh", file=f)
                print("#QSUB -queue i18cpu", file=f)
                #print("#QSUB -queue", queue[0:len(queue) - 1], file=f)
                print("#QSUB -node", node, file=f)
                print("#QSUB -omp ", nomp, file=f)
                print("#QSUB -mpi ", nproc, file=f)
                print("#PBS -I ", file=f)
                print("#PBS -l walltime="+runtime, file=f)
                #print("#PBS -l walltime=8:00:00", file=f)
                #print("source ~/.bashrc", file=f)
                #print("source "+respack, file=f)
                print("cd $PBS_O_WORKDIR", file=f)
