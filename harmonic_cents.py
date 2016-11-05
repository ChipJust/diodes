#! python3
r"""
THD = sqrt ( Sum(2, n)(Mag^2[n]) / Mag^2[1])
"""

import math
import argparse

parser = argparse.ArgumentParser(description='Show relationship between the harmonic series and the equal temperament scale degrees.')
#parser.add_argument('models', nargs='+', help='The name(s) of the diode model(s) to make a test circuit for.')
parser.add_argument('--number', '-n', type=int, default=20, help='The number of harmonics to show')

def closest(n):
    degrees = {
        0  : '  ',
        1  : 'm2',
        2  : ' 2',
        3  : 'm3',
        4  : ' 3',
        5  : 'P4',
        6  : 'tt',
        7  : 'P5',
        8  : 'm6',
        9  : ' 6',
        10 : 'm7',
        11 : ' 7',
        12 : '  '
    }
    cents = (1200 * math.log(n, 2)) % 1200
    degree = int (cents / 100)
    cents = cents % 100
    if cents > 50:
        degree = degree + 1
        cents = cents - 100
    return (degrees[degree], cents)

def main():
    args = parser.parse_args()
    print ("\nHarmonic  Degree    Cents")
    print ("---------------------------")
    for i in range(1, args.number + 1):
        degree, cents = closest(i)
        print ("{0:>8}      {1:>2} {2:>8}".format(i, degree, int(cents)))

if __name__ == '__main__':
    main()
