#! python3
r"""
THD = sqrt ( Sum(2, n)(Mag^2[n]) ) / Mag[1]
"""

import argparse
import re
import collections
import math
import itertools
import os

parser = argparse.ArgumentParser(description='Create fourier tables out of a collection of fourier files')
#parser.add_argument('models', nargs='+', help='The name(s) of the diode model(s) to make a test circuit for.')

class Harmonic():
    def __init__(self, m):
        self.Harmonic = int(m.group('Harmonic'))
        self.Frequency = int(m.group('Frequency'))
        self.Magnitude = float(m.group('Magnitude'))
        self.Phase = float(m.group('Phase'))
        self.NormMag = float(m.group('NormMag'))
        self.NormPhase = float(m.group('NormPhase'))
    def __str__(self):
        return "{Harmonic}, {Frequency}, {Magnitude}, {Phase}, {NormMag}, {NormPhase}".format(**self.__dict__)
        
class FourierAnalysis():
    fp = "[-+]?(?:(?:\d*\.\d+)|(?:\d+\.?))(?:[Ee][+-]?\d+)?"
    re_fourier_analysis = re.compile(r"Fourier analysis for.*No. Harmonics:\s*(?P<n>\d+),\s*THD:\s*(?P<thd>{fp})\s*%".format(fp=fp), re.DOTALL)
    re_harmonic = re.compile(r"^\s*(?P<Harmonic>\d+)\s+(?P<Frequency>\d+)\s+(?P<Magnitude>{fp})\s+(?P<Phase>{fp})\s+(?P<NormMag>{fp})\s+(?P<NormPhase>{fp})\s+$".format(fp=fp), re.MULTILINE)
    def __init__(self, filename):
        self.filename = filename
        with open(filename, "r") as f:
            buffer = f.read()
        m = self.re_fourier_analysis.search(buffer)
        if not m:
            raise ValueError("{filename} does not look like a fourier analysis file. File contents follow...\n{contents}".format(filename=filename, contents=buffer))
        self.n = int(m.group('n'))
        self.thd = float(m.group('thd'))
        self.harmonics = collections.OrderedDict()
        for m in self.re_harmonic.finditer(buffer):
            self.harmonics[int(m.group('Harmonic'))] = Harmonic(m)
        self.distortion = {}
        last = 0
        for i in range(2, self.n):
            try:
                thd = self.harmonic_distortion(i)
            except KeyError as e:
                print (self.filename)
                print (e)
                continue
            self.distortion[i] = thd - last
            last = thd

    def __repr__(self):
        return "FourierAnalysis({filename}): n={n} thd={thd}".format(**self.__dict__)
    
    def harmonic_distortion(self, k=0):
        if k == 0:
            k = self.n
        elif k >= self.n:
            k = self.n
        else:
            k = k + 1 # because the arrary is zero based
        SumMag2 = 0
        for i in range(2, k):
            SumMag2 += math.pow(self.harmonics[i].Magnitude, 2)
        return 100 * math.sqrt(SumMag2) / self.harmonics[1].Magnitude

def show_thds(filename):
    fa = FourierAnalysis(filename)
    print (fa)

    SumNormMag = 0
    for i in range(fa.n):
        SumNormMag += fa.harmonics[i].NormMag
    print ("SumNormMag = {SumNormMag}".format(SumNormMag=SumNormMag))
    last = 0
    for i in range(2, fa.n):
        thd = fa.harmonic_distortion(i)
        print ("{0:<3} {1:0<12.10f} {2:0<12.10f} {3:0<12.10f}".format(i, fa.harmonics[i].Magnitude, thd, thd - last))
        last = thd

def flatten(positive, negative, four_folder, out_file):
    fourier_file = r"{four_folder}\{positive}__{negative}.four".format(
        four_folder = four_folder,
        positive = positive,
        negative = negative)
    if not os.path.exists(fourier_file):
        return
    fa = FourierAnalysis (fourier_file)
    h = []
    last = 0
    for i in range(2, fa.n):
        try:
            thd = fa.harmonic_distortion(i)
        except KeyError as e:
            print (fourier_file)
            print (e)
            return
        h.append("{0:.4f}".format(thd - last))
        last = thd
    out_file.write("{positive},{negative},{thd},{harmonics}\n".format(
        positive = positive,
        negative = negative,
        thd = fa.thd,
        harmonics = ",".join(h)
        ))
    return

def is_close(fa, m, n, ratio=2):
    """
    Is the percent harmonic distortion at m close to the percent harmonic distortion
    at harmonic n?
    Close is defined as (larger / smaller) < ratio
    """
    if m not in fa.distortion or n not in fa.distortion:
        return False
    if fa.distortion[m] == fa.distortion[n]:
        return True
    if fa.distortion[m] == 0 or fa.distortion[n] == 0:
        return False
    biggest = fa.distortion[m] / fa.distortion[n] if fa.distortion[m] > fa.distortion[n] else fa.distortion[n] / fa.distortion[m]
    return biggest < ratio

def main():
    #show_thds("testfile.four")
    
    four_folder = r"E:\eda\fourier" # where all the .four files are
    diode_list_file = r"E:\eda\diodes\diode-list.txt"
    #diode_list_file = r"E:\eda\diodes\diode-list-test.txt"
    out_file = r"four_table.txt"

    with open(diode_list_file) as f:
        diode_list = f.read().splitlines()
    combo_list = [(i, i) for i in diode_list]
    combo_list.extend(itertools.combinations(diode_list, 2))

    fa = {}
    for pd, nd in combo_list:
        fourier_file = r"{four_folder}\{positive}__{negative}.four".format(
            four_folder = four_folder,
            positive = pd,
            negative = nd)
        if not os.path.exists(fourier_file):
            continue
        fa[(pd, nd)] = FourierAnalysis (fourier_file)
    
    close_2_3 = {k : v for k, v in fa.items() if is_close(v, 2, 3)}
    
    with open(out_file, "w") as four_table:
        four_table.write("Positive,Negative,THD,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20\n")
        for (dp, dn), v in close_2_3.items():
            flatten(dp, dn, four_folder, four_table)

if __name__ == '__main__':
    main()
