# rubiks-color-resolver

## Install
```
$ sudo apt-get install python-pip
$ sudo pip install https://github.com/dwalton76/rubiks-color-resolver.git
```

## Overview
rubiks-color-resolver.py
- accepts a JSON string of RGB values for each square of a rubiks cube (any size)
- analyzes all RGB values to assign each square one of the six colors of the cube. The CIE 2000 algorithm is used to calculate the color distance between colors.

In the following example the RGB values for square 1 is (39, 71, 43).  In this
particular example the RGB values were collected via the Lego Mindstorms EV3
color sensor.

In the output below the Cube printout is a log message which is printed to stderr.
The actual result is the json output. The 'FinalSide' field is the one of
interest, this tell you which side a square belong to.
```
dwalton@laptop ~/l/rubiks-color-resolver> rubiks-color-resolver.py --json '{"1": [39, 71, 43], "2": [54, 90, 62], "3": [5, 16, 17], "4": [41, 74, 50], "5": [64, 103, 74], "6": [33, 17, 5], "7": [30, 53, 31], "8": [50, 86, 59], "9": [33, 17, 6], "10": [24, 9, 4], "11": [23, 11, 5], "12": [22, 12, 4], "13": [5, 18, 18], "14": [6, 19, 21], "15": [4, 18, 17], "16": [6, 18, 18], "17": [4, 17, 18], "18": [4, 15, 15], "19": [5, 14, 12], "20": [5, 17, 18], "21": [28, 35, 6], "22": [32, 18, 6], "23": [44, 22, 8], "24": [29, 38, 7], "25": [25, 15, 5], "26": [33, 16, 5], "27": [28, 35, 6], "28": [4, 23, 9], "29": [5, 31, 11], "30": [28, 15, 4], "31": [5, 30, 11], "32": [6, 37, 14], "33": [35, 18, 5], "34": [4, 27, 10], "35": [4, 32, 10], "36": [33, 19, 5], "37": [35, 65, 37], "38": [5, 29, 11], "39": [5, 24, 8], "40": [51, 86, 60], "41": [32, 14, 6], "42": [27, 11, 4], "43": [49, 83, 58], "44": [25, 11, 4], "45": [25, 12, 5], "46": [22, 30, 6], "47": [31, 40, 7], "48": [25, 11, 5], "49": [28, 38, 7], "50": [37, 45, 9], "51": [25, 11, 4], "52": [23, 32, 6], "53": [29, 38, 7], "54": [5, 31, 10]}'

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

{
    "sides": {
        "B": {
            "blue": 6,
            "color": "Rd",
            "green": 14,
            "red": 32
        },
        "D": {
            "blue": 9,
            "color": "Ye",
            "green": 45,
            "red": 37
        },
        "F": {
            "blue": 8,
            "color": "OR",
            "green": 22,
            "red": 44
        },
        "L": {
            "blue": 21,
            "color": "Wh",
            "green": 19,
            "red": 6
        },
        "R": {
            "blue": 14,
            "color": "Gr",
            "green": 37,
            "red": 6
        },
        "U": {
            "blue": 74,
            "color": "Bu",
            "green": 103,
            "red": 64
        }
    },
    "squares": {
        "1": {
            "blue": 43,
            "color": "Bu",
            "currentPosition": 1,
            "currentSide": "U",
            "finalSide": "U",
            "green": 71,
            "red": 39
        },
        "2": {
            "blue": 62,
            "color": "Bu",
            "currentPosition": 2,
            "currentSide": "U",
            "finalSide": "U",
            "green": 90,
            "red": 54
        },
        "3": {
            "blue": 17,
            "color": "Wh",
            "currentPosition": 3,
            "currentSide": "U",
            "finalSide": "L",
            "green": 16,
            "red": 5
        },
[snip]
```
