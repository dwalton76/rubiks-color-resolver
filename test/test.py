#!/usr/bin/env python3

from rubikscolorresolver import RubiksColorSolverGeneric
from math import sqrt
import argparse
import json
import logging
import sys

# logging.basicConfig(filename='rubiks-rgb-solver.log',
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)5s: %(message)s')
log = logging.getLogger(__name__)

# Color the errors and warnings in red
logging.addLevelName(logging.ERROR, "\033[91m  %s\033[0m" % logging.getLevelName(logging.ERROR))
logging.addLevelName(logging.WARNING, "\033[91m%s\033[0m" % logging.getLevelName(logging.WARNING))

# To add a test case:
# - place the cube in the robot, solve it
# - in the log output grab the "RGB json" and save that in a file in test-data
# - in the log output grab the "Final cube for kociema", this is what you put in the entry in the test_cases tuple
test_cases = (
    ('2x2x2 solved 02',    'test-data/2x2x2-solved-02.txt',    'DDDDLLLLFFFFUUUURRRRBBBB'),
    ('2x2x2 random 01',    'test-data/2x2x2-random-01.txt',    'LRLURFDFDFBBRRBLUBLUDFDU'),
    ('2x2x2 random 02',    'test-data/2x2x2-random-02.txt',    'FBRUFUBLBLRDDLDUUDFFRRBL'),
    ('3x3x3 solved',       'test-data/3x3x3-solved.txt',       'UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB'),
    ('3x3x3 checkerboard', 'test-data/3x3x3-checkerboard.txt', 'UDUDUDUDURLRLRLRLRFBFBFBFBFDUDUDUDUDLRLRLRLRLBFBFBFBFB'),
    ('3x3x3 cross',        'test-data/3x3x3-cross.txt',        'DUDUUUDUDFRFRRRFRFRFRFFFRFRUDUDDDUDUBLBLLLBLBLBLBBBLBL'),
    ('3x3x3 tetris',       'test-data/3x3x3-tetris.txt',       'FFBFUBFBBUDDURDUUDRLLRFLRRLBBFBDFBFFUDDULDUUDLRRLBRLLR'),
    ('3x3x3 superflip',    'test-data/3x3x3-superflip.txt',    'UBULURUFURURFRBRDRFUFLFRFDFDFDLDRDBDLULBLFLDLBUBRBLBDB'),
    ('3x3x3 random 01',    'test-data/3x3x3-random-01.txt',    'DURUULDBRFDFLRRLFBRLUUFFUFFLRUDDDRRDLBBDLLBBBDFFBBRLUU'),
    ('3x3x3 random 02',    'test-data/3x3x3-random-02.txt',    'UUUUUUUUURRRRRLRRLFFFFFFBFFDDDDDDDDDLLLRLLLLRBBBBBBFBB'),
    ('3x3x3 dark 01',      'test-data/3x3x3-dark-01.txt',      'UUBUUBUUBRRRRRRRRRFFUFFUFFUDDFDDFDDFLLLLLLLLLDBBDBBDBB'),
    # I don't yet know what the valid cube string here should be
    # ('3x3x3 dark 02',      'test-data/3x3x3-dark-02.txt',      'UUBUUBUUBRRRRRRRRRFFUFFUFFUDDFDDFDDFLLLLLLLLLDBBDBBDBB'),
    ('4x4x4 solved 01',    'test-data/4x4x4-solved-01.txt',    'DDDDDDDDDDDDDDDDBBBBBBBBBBBBBBBBLLLLLLLLLLLLLLLLUUUUUUUUUUUUUUUUFFFFFFFFFFFFFFFFRRRRRRRRRRRRRRRR'),
    ('4x4x4 random 01',    'test-data/4x4x4-random-01.txt',    'LUFLUBLBRBLFBFFLBDRFLUURLUUUFDFDRLRURFLBRFLBUDUDRLRRBBBBFFFLLLRBDBUUUDDDUDDBDDDFUULBFRRFLRRBRDDF'),
    ('4x4x4 random 02',    'test-data/4x4x4-random-02.txt',    'RUFFURLLRBBFFFFBDUUDDRFFRLFFLLDRDDDRLDDBBUUDLRRFDBBUDFFUULRLBRDUUFULBBLFBBRULRLBRLBBRUULRDDLFBDU'),
    ('4x4x4 random 03',    'test-data/4x4x4-random-03.txt',    'DBDLLLBRLLDRFDUUBBBDDUULFRBBURUURFRRUURBUBFRUBBBFLLLDLFDRFDFDFDFRFFDUULRDDDLLFLLFRUBURFFURBBRLDB'),
    ('4x4x4 random 04',    'test-data/4x4x4-random-04.txt',    'FLLDDLLBUDBDURRLFRUBURFFURBBRLDBBBBDDUULFRBBURUULDFFLFDDLLFFFDRDRFRRUURBUBFRUBBBRFFDUULRDDDLLFLL'),
    ('5x5x5 random 01',    'test-data/5x5x5-random-01.txt',    'RRURRDDUFFDDULLDDLDDDDLDDLLBRBLLBRBRRRUURRDBBUUDBBFFFFFFFFFFRRFBBLLRBBLLRLLDDUFFDDUFFFFDLLLLDURLLDURFRBRRFRBRRUFLDDUURBBUURBBUUFUUUUBUUBUBLLDLFBBDLFBB'),
    ('5x5x5 random 02',    'test-data/5x5x5-random-02.txt',    'RFFFUDUDURBFULULFDBLRLDUFDBLUBBBDDURLRDRFRUDDBFUFLFURRLDFRRRUBFUUDUFLLBLBBULDDRRUFUUUBUDFFDRFLRBBLRFDLLUUBBRFRFRLLBFRLBRRFRBDLLDDFBLRDLFBBBLBLBDUUFDDD'),
    ('6x6x6 random 01',    'test-data/6x6x6-random-01.txt',    'RLLDLBDDDUBBFUDDUBLUDDDFDRDDLRLLLUBBLUDDLUUDRRRFBFRRFLRLBFFRDBBBUDFFLBRRBUFLDDRULRFBUFFBRDFFLRLFRLRRRFLUBLDDULRUBRRLDDLRDDUUUDDUUUULURUDDBDFUURUBLUDRUBDFLFBULFLRFUFBLRRFUFLBUFBRRFFRDFBFDLUBBFLFBBFBBBBRLBRFBLLFUFDBRUL'),
)

#test_cases = (
#    ('2x2x2 solved',       'test-data/2x2x2-solved-02.txt',    'DDDDBBBBLLLLUUUUFFFFRRRR'),
#)

results = []

for (desc, filename, expected) in test_cases:
    log.warning("Test: %s" % desc)
    with open('test/' + filename, 'r') as fh:
        scan_data_str_keys = json.load(fh)
        scan_data = {}

        for (key, value) in scan_data_str_keys.items():
            scan_data[int(key)] = value

        square_count = len(scan_data.keys())
        square_count_per_side = int(square_count/6)
        width = int(sqrt(square_count_per_side))

        cube = RubiksColorSolverGeneric(width)
        try:
            cube.enter_scan_data(scan_data)
            cube.crunch_colors()
            output = ''.join(cube.cube_for_kociemba_strict())
        except Exception as e:
            log.exception(e)
            log.info(json.dumps(scan_data))
            output = 'Exception'
            #break

        if output == expected:
            results.append("\033[92mPASS\033[0m: %s" % desc)
        else:
            results.append("\033[91mFAIL\033[0m: %s" % desc)
            results.append("   expected %s" % expected)
            results.append("   output   %s" % output)
            log.info(json.dumps(scan_data))
            #break

print('\n'.join(results))
