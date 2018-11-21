#!/usr/bin/python3
import sys
import pymatgen
import argparse
from tool.structure2input import structure2input

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog='cif2input.py',
        description='make input files for QE from a cif file.',
        epilog='end',
        add_help=True,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('-i', '--input_cif',
                        action='store',
                        dest='cif_file',
                        nargs='?',
                        type=str,
                        default="",
                        required = True,
                        help = ("cif file"),
                        metavar=None)

    parser.add_argument('-pp', '--pseudo_path',
                        action='store',
                        dest='pseudo_path',
                        nargs='?',
                        type=str,
                        default="",
                        required = True,
                        help = ("Path to psuedo potentials"),
                        metavar=None)

    parser.add_argument('-k', '--dk_path', action='store', dest='dk_path',
                        nargs='?', default=0.1, type=float, choices=None,
                        help=('Path to input data.'),
                        metavar=None)

    parser.add_argument('-qg', '--dq_grid',
                        action='store',
                        dest='dq_grid',
                        nargs='?',
                        type= float,
                        default =0.3359385398275,
                        metavar=None)

    parser.add_argument('-pk', '--pseudo_kind',
                        action='store',
                        dest='pseudo_kind',
                        nargs='?',
                        type=str,
                        default="sg15",
                        metavar=None)

    parser.add_argument('-q', '--queue',
                        action='store',
                        dest='queue',
                        nargs='?',
                        type=str,
                        default="F4cpus",
                        metavar=None)

    parser.add_argument('-r', '--rel',
                        action='store_true')

    parser.add_argument('-m', '--move_list',
                        action='store',
                        dest='move_list',
                        nargs='?',
                        type=str,
                        default="",
                        help=('Move atom list'),
                        metavar=None)

    args = parser.parse_args()

    #
    # CIF parser
    #
    structure = pymatgen.Structure.from_file(args.cif_file)
    #
    # Set values
    #
    dk_path = args.dk_path
    dq_grid = args.dq_grid
    pseudo_kind = args.pseudo_kind
    pseudo_dir = args.pseudo_path
    queue = args.queue
    rel = args.rel
    _move_list = args.move_list
    #
    print("  dk for band : {0}".format(dk_path))
    print("  dq for grid : {0}".format(dq_grid))
    print("  Pseudo kind is ", pseudo_kind)
    print("  Pseudo is at ", pseudo_dir)

    structure.remove_oxidation_states()

    structure2input(structure, dk_path, dq_grid, pseudo_kind, pseudo_dir, queue, rel, move_list=_move_list)
