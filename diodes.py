r""" diodes.py

Copyright (c) 2016 Chip Ueltschey
Released under the terms of MIT license (see LICENSE for details)

Name    Parameter                                       Units   Default
BV      Reverse breakdown voltage                       V       infinite
IBV     Reverse breakdown current                       A       1E-3
IK (IKF) Forward knee current                           A       1E-3
IKR     Reverse knee current                            A       1E-3
IS (JS) Saturation current (diode equation)             A       1E-14
JSW     Sidewall saturation current                     A       1E-14
N       Emission coefficient, 1 to 2                    -       1
RS      Parsitic resistance (series resistance)         ohm     0

CJO     Zero-bias junction capacitance                  F       0
CJP     Zero-bias junction sidewall capacitance         F       0
FC      Forward bias depletion capacitance coefficient  -       0.5
FCS     Coefficient for forward-bias depletion sidewall capacitance formula -   0.5
M       Junction grading coefficient                    -       0.5
-       0.33 for linearly graded junction               -       -
-       0.5 for abrupt junction                         -       -
MJSW    Periphery junction grading coefficient          -       0.33
VJ      Junction potential                              V       1
PHP     Periphery junction potential                    V       1
TT      Transit time                                    s       0

EG      Activation energy:                              eV      1.11
-       Si: 1.11                                        -       -
-       Ge: 0.67                                        -       -
-       Schottky: 0.69                                  -       -
TNOM (TREF) Parameter measurement temperature           C       27
XTI     IS temperature exponent                         -       3.0
-       pn junction: 3.0                                -       -
-       Schottky: 2.0                                   -       -

KF      Flicker noise coefficient                       -       0
AF      Flicker noise exponent                          -       1

NR
ISR
-- LT Spice Power Parameters --
VPK     Peak voltage rating
IPK     Peak current rating
IAVE    Ave current rating
IRMS    RMS current rating
DISS    Maximum power dissipation rating
NBVL
IBVL
"""
import re
import io
import math

class SpiceDiode():
    re_model_paramter_clean = re.compile(r"\n\s*\+")
    re_parameters = re.compile(r"\s*(?P<attribute>\S+)\s*=\s*(?P<value>\S+)\s*")
    spice_parameters = { # All values must be coersible to float
        "BV"    :   1E100,
        "IBV"   :   1E-3,
        "IK"    :   1E-3,
        "IKR"   :   1E-3,
        "IS"    :   1E-14,
        "JSW"   :   1e-14,
        "N"     :   1,
        "RS"    :   0,
        "CJO"   :   0,
        "CJP"   :   0,
        "FC"    :   0.5,
        "FCS"   :   0.5,
        "M"     :   0.5,
        "MJSW"  :   0.33,
        "VJ"    :   1,
        "PHP"   :   1,
        "TT"    :   0,
        "EG"    :   1.11,
        "TNOM"  :   27,
        "XTI"   :   3.0,
        "KF"    :   0,
        "AF"    :   1,
        "VPK"   :   0,
        "IPK"   :   0,
        "IAVE"  :   0,
        "IRMS"  :   0,
        "DISS"  :   0,
    }
    infomational_parameters = { # All values must be coersible to string
        "MFG"   :   "",
        "TYPE"  :   "",
    }
    parameter_alias = {
        "CJ0"   :   "CJO",
        "MJ"    :   "M",
        "IKF"   :   "IK",
        "JS"    :   "IS",
        "CJSW"  :   "CJP",
        "PB"    :   "VJ",
        "TREF"  :   "TNOM",
    }
    def __init__(self, name, parameters):
        self.name=name
        # Set defaults
        for p, v in self.spice_parameters.items():
            setattr(self, p, v)
        for p, v in self.infomational_parameters.items():
            setattr(self, p, v)
        # Parse parameters, override defaults
        for m in self.re_parameters.finditer(parameters):
            parameter = m.group('attribute').upper()
            value = m.group('value')
            if parameter in self.infomational_parameters:
                setattr(self, parameter, value)
                continue
            if parameter not in self.spice_parameters:
                if parameter in self.parameter_alias:
                    parameter = self.parameter_alias[parameter]
                else:
                    print ("Ignoring parameter %s=%s in %s." % (parameter, value, name))
                    continue
            try:
                setattr(self, parameter, self.float(value))
            except ValueError:
                print ("Error parsing diode named %s: could not covert a paramter to float.\n  %s=%s" % (self.name, parameter, value))
                raise
    def __repr__(self):
        return "SpiceDiode(%s, %s)" % (self.name, " ".join(["%s=%s" % (p, getattr(self, p, None)) for p in self.spice_parameters]))
    re_scientific_notation = re.compile("\s*(-?\d*\.?\d*E-?\d*)[AVFH]?\s*", re.I)
    re_scale_notation = re.compile("\s*(?P<number>-?\d*\.?\d*)(?P<scale>(?:t)|(?:g)|(?:x)|(?:meg)|(?:k)|(?:m)|(?:u)|(?:n)|(?:p)|(?:f))[AVFH]?\s*", re.I)
    re_unit = re.compile("\s*(?P<number>-?\d*\.?\d*)[AVFH]?\s*", re.I)
    scales = {
        't' : 12,
        'g' : 9,
        'x' : 6,
        'meg' : 6,
        'k' : 3,
        'm' : -3,
        'u' : -6,
        'n' : -9,
        'p' : -12,
        'f' : -15
    }
    def float(self, x):
        """
        Return a float from a string, may have units, scientific notation or scale factors
        Suffix      Scale   Number              Name
        T           E+12    1,000,000,000,000   Tera
        G           E+09    1,000,000,000       Giga
        X or MEG    E+06    1,000,000           Mega
        K           E+03    1,000               Kilo
        M           E-03    0.001               Milli
        U           E-06    0.000001            Micro
        N           E-09    0.000000001         Nano
        P           E-12    0.000000000001      Pico
        F           E-15    0.000000000000001   Femto
        """
        m = self.re_scientific_notation.match(x)
        if m:
            return float(m.group(1))
        m = self.re_scale_notation.match(x)
        if m:
            scale = m.group('scale').lower()
            if scale not in self.scales:
                print ("Parse error for diode named %s: %s not in scales" % (self.name, scale))
            return float(m.group('number')) * math.pow(10, self.scales[scale])
        m = self.re_unit.match(x)
        if m:
            return float(m.group('number'))
        return float(x)
    re_model_d = re.compile("^\s*.model\s+(?P<name>\S+)\s+D\s*[\( ]\s*(?P<parameters>[^\)]*?)\s*\)?$", re.I)
    @staticmethod
    def parse(f):
        """
        Return a list of SpiceDiode objects from the file-like object f.
        """
        l = []
        for line in SpiceDiode.preparse(f):
            m = SpiceDiode.re_model_d.match(line)
            if m:
                l.append(SpiceDiode(m.group('name'), m.group('parameters')))
        return l
    re_continue_line = re.compile("^\s*\+(?P<content>.*)")
    @staticmethod
    def preparse(f):
        """
        Join continued lines. Yield one full line at a time.
        """
        last_line = ""
        for line in f:
            m = SpiceDiode.re_continue_line.match(line)
            if m:
                last_line += m.group('content')
                continue
            if last_line:
                yield last_line
            last_line = line
        if last_line:
            yield last_line

test_data = [
".model KD203B D(Is=303.3f Rs=30.57m N=1 Xti=3 Eg=1.11 Bv=799.9v Ibv=7.607u Cjo=21.2p Vj=.73 M=.28 Fc=.5 Tt=9.09e-7 mfg=USSR type=silicon)\n",
".model KD203V D(Is=268.8f Rs=14.95m N=1 Xti=3 Eg=1.11 Bv=799.9 Ibv=7.607u Cjo=21.2p Vj=.73 M=.28 Fc=.5 Tt=9.09e-7 mfg=USSR type=silicon)\n",
".model KD203G D(Is=303.3f Rs=30.57m N=1 Xti=3 Eg=1.11 Bv=999.9 Ibv=7.607u Cjo=21.2p Vj=.73 M=.28 Fc=.5 Tt=9.09e-7 mfg=USSR type=silicon)\n",
"    .model KD203D D(Is=268.8f Rs=14.95m N=1 Xti=3 Eg=1.11 Bv=999.9 Ibv=7.607u Cjo=21.2p Vj=.73 M=.28 Fc=.5 Tt=9.09e-7 mfg=USSR type=silicon)\n",
" .Model KD204A D(Is=4.110n N=1.52 Rs=7.5e-2 Cjo=31.5p Tt=1.16e-7 M=0.35 Vj=0.68 Fc=0.5 Bv=400 IBv=1e-10 Eg=1.11 Xti=3 mfg=USSR type=silicon )\n",
".MODEL DF D ( IS=6.18p RS=29.6 N=1.10\n",
"+ CJO=20.1p VJ=1.00 M=0.330 TT=50.1n )\n",
".model SS24 D(Is=.4mA Rs=.016 N=2.1 Cjo=800p Eg=.69 Xti=2 Iave=2 Vpk=40 mfg=Fairchild type=Schottky)\n",
".model APT1608SURCK d(IS=2.01E-17 N=2.139 RS=2 m=0.431 Vj=2.32 Cjo=35pF IBV=10u BV=5 EG=2.26 XTI=3 Iave=30mA Vpk=5 mfg=Kingbright type=LED)\n",
".MODEL UF4007 D N=3.97671 IS=3.28772u RS=0.149734 EG=1.11 XTI=3 CJO=2.92655E-011 VJ=0.851862 M=0.334552 FC=0.5 TT=1.84973E-007 BV=1000 IBV=0.2 Iave=1 Vpk=1000 type=silicon\n",
".Model BYW96E D(IS=59.77971E-6 N=3.61403 RS=52.308E-3 IKF=0.566356 CJO=27.010E-12 M=.43978 VJ=.81612 ISR=447.9139E-9 NR=2.54303 BV=1.2003E3 IBV=2.5910 TT=295.54E-9 Iave=3 Vpk=1000 mfg=Philips type=Silicon)\n",
]

def main():
    with open (r"E:\eda\diodes.cir") as f:
        diodes = SpiceDiode.parse(f)
    
    #for diode in diodes:
    #    print (diode)

if __name__ == "__main__":
    main()
    