delete_me_later = """

.ENDS

* Anti-parallel Diode Schottky CFSH05-20L 
.SUBCKT D_ANTI_CFSH05_20L_2       1   2
Dp  1   2   CFSH05_20L
Dn1 2   2a  CFSH05_20L
Dn2 2a  1   CFSH05_20L
.ENDS

* Anti-parallel Diode Schottky CFSH05-20L
.SUBCKT D_ANTI_CFSH05_20L_3       1   2
Dp  1   2   CFSH05_20L
Dn1 2   2a  CFSH05_20L
Dn2 2a  2b  CFSH05_20L
Dn3 2b  1   CFSH05_20L
.ENDS

* Anti-parallel Diode Schottky CFSH05-20L
.SUBCKT D_ANTI_CFSH05_20L_5       1   2
Dp      1   2   CFSH05_20L
Dn1     2   3   CFSH05_20L
Dn2     3   4   CFSH05_20L
Dn3     4   5   CFSH05_20L
Dn4     5   6   CFSH05_20L
Dn5     6   1   CFSH05_20L
"""

head = """
* Anti-parallel Diodes {model}: {up} up {down} down
.SUBCKT D_ANTI_{model}_{up}_{down} {anode} {cathode}
Dp      1   2   {model}"""

body = "Dn{number:<6}{anode:<4}{cathode:<4}{model}"

tail = ".ENDS"

import argparse
parser = argparse.ArgumentParser(description='Make some diode sub circuits')
parser.add_argument('model', help='The name of the diode model to make sub-circuts for')
parser.add_argument('--depth', type=int, default=4)

def main():
    args = parser.parse_args()
    
    for depth in range (1, args.depth+1):
        print (head.format(model=args.model, up=1, down=depth, anode=1, cathode=2))
        for i in range (1, depth):
            print (body.format(number=i, anode=i+1, cathode=i+2, model=args.model))
        print (body.format(number=depth, anode=depth+1, cathode=1, model=args.model))
        print (tail)
        if depth==1:
            continue
    
        print (head.format(model=args.model, up=depth, down=1, anode=2, cathode=1))
        for i in range (1, depth):
            print (body.format(number=i, anode=i+1, cathode=i+2, model=args.model))
        print (body.format(number=depth, anode=depth+1, cathode=1, model=args.model))
        print (tail)

if __name__ == '__main__':
    main()
