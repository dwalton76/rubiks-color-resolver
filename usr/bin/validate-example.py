#!/usr/bin/env micropython

"""
This is an example of how to use RubiksColorSolverGenericBase to
determine if the state of your cube is valid
"""

from rubikscolorresolver.base import RubiksColorSolverGenericBase

cube = RubiksColorSolverGenericBase(3)
cube.enter_cube_state("FFBFUBFBBUDDURDUUDRLLRFLRRLBBFBDFBFFUDDULDUUDLRRLBRLLR")
cube.sanity_check_edge_squares()
cube.validate_all_corners_found()
cube.validate_odd_cube_midge_vs_corner_parity()
cube.print_cube()
print("".join(cube.cube_for_kociemba_strict()))
