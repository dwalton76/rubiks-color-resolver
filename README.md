# rubiks-color-resolver

rubiks_rgb_solver.py accepts a JSON structure of RGB values for each square of
either a 2x2x2 or 3x3x3 rubiks cube and returns the kociemba representation of
that cube.

In the following example the RGB values for square 1 is (39, 71, 43).  In this
particular example the RGB values were collected via the Lego Mindstorms EV3
color sensor.

dwalton@laptop ~/l/rubiks-color-resolver> ./rubiks_rgb_solver.py '{"1": [39, 71, 43], "2": [54, 90, 62], "3": [5, 16, 17], "4": [41, 74, 50], "5": [64, 103, 74], "6": [33, 17, 5], "7": [30, 53, 31], "8": [50, 86, 59], "9": [33, 17, 6], "10": [24, 9, 4], "11": [23, 11, 5], "12": [22, 12, 4], "13": [5, 18, 18], "14": [6, 19, 21], "15": [4, 18, 17], "16": [6, 18, 18], "17": [4, 17, 18], "18": [4, 15, 15], "19": [5, 14, 12], "20": [5, 17, 18], "21": [28, 35, 6], "22": [32, 18, 6], "23": [44, 22, 8], "24": [29, 38, 7], "25": [25, 15, 5], "26": [33, 16, 5], "27": [28, 35, 6], "28": [4, 23, 9], "29": [5, 31, 11], "30": [28, 15, 4], "31": [5, 30, 11], "32": [6, 37, 14], "33": [35, 18, 5], "34": [4, 27, 10], "35": [4, 32, 10], "36": [33, 19, 5], "37": [35, 65, 37], "38": [5, 29, 11], "39": [5, 24, 8], "40": [51, 86, 60], "41": [32, 14, 6], "42": [27, 11, 4], "43": [49, 83, 58], "44": [25, 11, 4], "45": [25, 12, 5], "46": [22, 30, 6], "47": [31, 40, 7], "48": [25, 11, 5], "49": [28, 38, 7], "50": [37, 45, 9], "51": [25, 11, 4], "52": [23, 32, 6], "53": [29, 38, 7], "54": [5, 31, 10]}'

2016-11-29 16:59:46,853  INFO: Cube

           Wh Wh Bu
           Wh Wh OR
           Wh Wh OR
 Rd Rd Rd  Bu Bu Ye  Gr Gr OR  Wh Gr Gr
 Bu Bu Bu  OR OR Ye  Gr Gr OR  Wh Rd Rd
 Bu Bu Bu  OR OR Ye  Gr Gr OR  Wh Rd Rd
           Ye Ye Rd
           Ye Ye Rd
           Ye Ye Gr


UULUUFUUFRRFRRFRRFLLDFFDFFDDDBDDBDDRBBBLLLLLLURRUBBUBB
dwalton@laptop ~/l/rubiks-color-resolver>


In the output above the Cube printout is a log message which is printed to stderr.
The actual result is the 'UULUUFUUFRRFRRFRRFLLDFFDFFDDDBDDBDDRBBBLLLLLLURRUBBUBB'
string. So how to read that string? Break it down in groups of 9 so we have one
row per side.

UULUUFUUF
RRFRRFRRF
LLDFFDFFD
DDBDDBDDR
BBBLLLLLL
URRUBBUBB
    ^
    |-- This column is the middle square for each side

The sides are printed Upper, Right, Front, Down, Left, Back because this is the
order expected by kociemba. The Upper side

    Wh Wh Bu
    Wh Wh OR
    Wh Wh OR

is represented via UULUUFUUF but lets lay it out to be nice and neat:

     U U L
     U U F
     U U F

So Bu was replaced with L because Bu is the color of side L, Or was replaced
with F because Or is the color of side F, etc
