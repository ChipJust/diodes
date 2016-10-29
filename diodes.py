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

NR      Emission coefficient for ISR                    no unit 2.0
ISR     Recombination current parameter
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
        "ISR"   :   0,
        "JSW"   :   1e-14,
        "N"     :   1,
        "NR"    :   2,
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
    def __init__(self, name, parameters, linenum=0):
        self.name=name
        self.linenum = linenum
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
    def __str__(self):
        parameters = ", ".join(
            ["{parameter} = {value}".format(
                parameter=p,
                value=getattr(self, p))
             for p in self.spice_parameters if self.spice_parameters[p] != getattr(self, p)])
        return ".MODEL {name} D  ({parameters})".format(
            name=self.name,
            parameters=parameters)
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
    re_scientific_notation = re.compile("\s*(-?\d*\.?\d*E[-+]?\d*)[AVFH]?\s*", re.I)
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
    re_model_d = re.compile("^\s*\.model\s+(?P<name>\S+)\s+D\s*[\( ]\s*(?P<parameters>[^\)]*?)\s*\)?$", re.I)
    re_subckt = re.compile("^\s*\.SUBCKT\s+(?P<name>\S+)\s+(?P<nodes>.+)", re.I)
    re_ends = re.compile("^\s*\.ENDS.*", re.I)
    @classmethod
    def parse(cls, f, skip_subckt=True):
        """
        Return a list of SpiceDiode objects from the file-like object f.
        If a string is passed, this function will treat it as a file path
        and attempt to open it.
        """
        if isinstance(f, str):
            _f = open (f)
        else:
            _f = f
        in_subckt = False
        for line, linenum in cls.preparse(_f):
            if skip_subckt:
                if in_subckt: # this will not handle nested subckts
                    m = cls.re_ends.match(line)
                    if m:
                        in_subckt = False
                        #print ("{linenum:<8}{match}".format(linenum=linenum, match=m.group(0)))
                    continue
                m = cls.re_subckt.match(line)
                if m:
                    in_subckt = True
                    #print ("{linenum:<8}{name:<16}{nodes}".format(linenum=linenum, name=m.group('name'), nodes=m.group('nodes')))
                    continue
            m = cls.re_model_d.match(line)
            if m:
                try:
                    yield cls(m.group('name'), m.group('parameters'), linenum)
                except ValueError:
                    print ("Error parsing line %d." % linenum)
                    raise
        if isinstance(f, str):
            _f.close()
    re_continue_line = re.compile("^\s*\+(?P<content>.*)")
    @classmethod
    def preparse(cls, f):
        """
        Join continued lines. Yield one full line at a time.
        """
        last_line = ""
        linenum = 0
        for line in f:
            linenum += 1
            m = cls.re_continue_line.match(line)
            if m:
                last_line += m.group('content')
                continue
            if last_line:
                yield last_line, linenum-1
            last_line = line
        if last_line:
            yield last_line, linenum
    @staticmethod
    def thermal_voltage(tempurature=300):
        return tempurature*8.6173324e-5
    def forward_voltage(self, current):
        try:
            return self.N*self.thermal_voltage()*math.log((current/self.IS)-1)
        except ValueError as e:
            # if (current/self.IS) <= 1 we will get a domain error. Many models assume we dropped this -1.
            return self.N*self.thermal_voltage()*math.log((current/self.IS))
        

class AntiParallelDiodes():
    subckt_string = """
.SUBCKT {name} {pos_node} {mid_node} {neg_node}
{diodes}
Rf      {mid_node:<3} {neg_node:<3} {resistance}
.ENDS"""
    doide_string = "D{i:<6} {anode:<3} {cathode:<3} {model}"
    line_string = "X{line_name:<6} {positive_node:<7} {middle_node:<7} {negative_node:<7} {name}"
    def __init__(self, positive, negative, resistance=0):
        self.resistance = resistance
        # Checking for '__iter__' to identify list vs string. String won't have this attribute.
        if hasattr(positive, '__iter__'):
            self.positive = list(positive)
        else:
            self.positive = [positive]
        if hasattr(negative, '__iter__'):
            self.negative = list(negative)
        else:
            self.negative = [negative]
        self.name = "D_ANTI__{positve}__{negative}__{resistance}".format(
            positve = "_".join(self.positive),
            negative = "_".join(self.negative),
            resistance = self.resistance
        )
    def __repr__(self):
        return "AntiParallelDiodes(positive = [{positive}], negative = [{negative}], resistance = {resistance}, name = {name})".format (
            positive = ", ".join(self.positive),
            negative = ", ".join(self.negative),
            resistance = self.resistance,
            name = self.name
        )
    def __eq__(self, other):
        return self.name == other.name
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return hash(self.name)
    def node(self, line_name, positive_node, middle_node, negative_node):
        return self.line_string.format(
            line_name = line_name,
            positive_node = positive_node,
            middle_node = middle_node,
            negative_node = negative_node,
            name = self.name
        )
    def subckt(self):
        """Return the string for the subckt for this anit-parallel circuit."""
        return self.subckt_string.format(
            name = self.name,
            pos_node = 1,
            mid_node = len(self.positive) + 1,
            neg_node = len(self.positive) + len(self.negative) + 2,
            resistance = self.resistance,
            diodes = "\n".join([self.doide_string.format(
                i = i + 1,
                anode = i + 1,
                cathode = i + 2 if i + 1 < len(self.positive + self.negative) else 1,
                model = model
            ) for i, model in enumerate(self.positive + self.negative) ])
        )
    def diodes(self):
        for diode in self.positive:
            yield diode
        for diode in self.negative:
            yield diode

def main():
    diodes = [diode for diode in SpiceDiode.parse(r"E:\eda\diodes\diodes-inc.txt")]
    #diodes = [diode for diode in SpiceDiode.parse(r"E:\eda\diodes\test-data.txt")]
    
    for diode in diodes:
        Vf1mA=diode.forward_voltage(.001)
        print ("{linenum:<8}{model:<16}Vf1mA={Vf1mA:.3f}     N={N}".format(
            linenum=diode.linenum,
            model=diode.name,
            Vf1mA=Vf1mA,
            N=diode.N))
    print (len(diodes))

if __name__ == "__main__":
    main()
    