# rubiks-color-resolver

## python3 install
```
$ sudo python3 -m pip install git+https://github.com/dwalton76/rubiks-color-resolver.git
```

## micropython install

First [install micropython](https://github.com/micropython/micropython/wiki/Getting-Started) then:
```
$ git clone https://github.com/dwalton76/rubiks-color-resolver.git
$ cd rubiks-color-resolver
$ sudo make install
```

## Overview
rubiks-color-resolver.py and rubiks-color-resolver-micropython.py
- accept a JSON string of RGB values for each square of a rubik'ss cube. 2x2x2, 3x3x3, 4x4x4, 5x5x5, 6x6x6 and 7x7x7 are supported.
- analyzes all RGB values to assign each square one of the six colors of the cube. It then uses a Travelling Salesman algorithm (tsp_solver) to sort the colors.

```
jdoe@laptop[rubiks-color-resolver]# ./usr/bin/rubiks-color-resolver.py --filename ./tests/test-data/3x3x3-tetris.txt
Cube

           OR OR Rd
           OR Ye Rd
           OR Rd Rd
 Ye Wh Wh  Bu Gr Gr  Ye Wh Wh  Gr Bu Bu
 Ye Gr Wh  Bu OR Gr  Ye Bu Wh  Gr Rd Bu
 Ye Ye Wh  Bu Bu Gr  Ye Ye Wh  Gr Gr Bu
           Rd Rd OR
           Rd Wh OR
           Rd OR OR

FFBFUBFBBUDDURDUUDRLLRFLRRLBBFBDFBFFUDDULDUUDLRRLBRLLR
jdoe@laptop[rubiks-color-resolver]#
```
