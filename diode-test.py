r"""
BAS70LP DI_BAS70JW

I1  0   1   DC 1
D1  1   _BAS70LP   BAS70LP
R1  _BAS70LP   0   1k

D2  1   _DI_BAS70JW   DI_BAS70JW
R2  _DI_BAS70JW   0   1k

.MODEL BAS70LP D  ( IS=1.5n RS=14 ISR=3n BV=75 NBV=300 IBV=15n IKF=.4m
+ CJO=2.04p  M=0.19 VJ=.4 N=.99 TT=1.6n EG=.8 XTI=.3 TBV1=.0001 TRS1=.0048)

.MODEL DI_BAS70JW D  ( IS=99.5p RS=0.600 BV=70.0 IBV=10.0u
+ CJO=2.00p  M=0.333 N=1.70 TT=7.20n )

* ANALYSIS *************************************
.control
set noaskquit
run
dc I1 0 .001 .00000001
plot V(1,_BAS70LP) V(1,_DI_BAS70JW)
.endc

.END
"""

import argparse
parser = argparse.ArgumentParser(description='Create a spice listing for testing diodes.')
parser.add_argument('models', nargs='+', help='The name(s) of the diode model(s) to make a test circuit for.')
parser.add_argument('--model_file', '-f', help='The file to get the model(s) from.')

import diodes

circuit = """
{model_list}

I1      0               1                DC 1

{nodes}

{models}

* ANALYSIS *************************************
.control
set noaskquit
run
dc I1 0 .001 .00000001
plot {voltage_list}
.endc

.END
"""

node = """
D{i:<7}1               _{model:<16}{model:<16}
R{i:<7}_{model:<15}0                1k
"""

voltage = "V(1,_{model})"

def main():
    args = parser.parse_args()
    
    if not args.model_file:
        model_file = r"E:\eda\diodes\diodes-inc.txt"
    d = {diode.name : diode for diode in diodes.SpiceDiode.parse(model_file)}

    print (circuit.format(
        model_list=" ".join(args.models),
        nodes="\n".join([node.format(i=i, model=model) for i, model in enumerate(args.models)]),
        models="\n".join([str(d[model]) for model in args.models]),
        voltage_list=" ".join([voltage.format(model=model) for model in args.models]),
    ))
        

if __name__ == '__main__':
    main()
