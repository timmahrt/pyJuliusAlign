# -*- coding: utf-8 -*-
'''
Created on Aug 31, 2014

@author: tmahrt

This is an example that will force align a directory of wav files and
corresponding TextGrid files.
'''

from os.path import join

from pyjuliusalign import alignFromTextgrid


path = join(".", "files")
cabochaOutput = join(path, "cabocha_output")
alignedOutput = join(path, "aligned_output")

# Windows executables
juliusScriptPath = r"C:\Users\Tim\Documents\julius4-segmentation-kit-v1.0\segment_julius.pl"
soxPath = "C:\sox\sox-14-4-2\sox.exe"
cabochaPath = r"C:\Program Files (x86)\CaboCha\bin\cabocha.exe"
perlPath = r""

# Mac/Unix executables
juliusScriptPath = "/Users/tmahrt/Documents/julius4-segmentation-kit-v1.0/segment_julius4.pl"
soxPath = "/opt/local/bin/sox"
cabochaPath = "/usr/local/bin/cabocha"
perlPath = "/opt/local/bin/perl"

# One of: 'jis-shift', 'utf-8', or 'euc-jp'
# Whichever cabocha was installed with
cabochaEncoding = "euc-jp"

alignFromTextgrid.textgridToCSV(inputPath=path,
                                outputPath=path)

alignFromTextgrid.convertCorpusToKanaAndRomaji(inputPath=path,
                                               outputPath=cabochaOutput,
                                               cabochaEncoding=cabochaEncoding,
                                               cabochaPath=cabochaPath,
                                               encoding="utf-8")

alignFromTextgrid.forceAlignCorpus(wavPath=path, txtPath=cabochaOutput,
                                   outputPath=alignedOutput,
                                   juliusScriptPath=juliusScriptPath,
                                   soxPath=soxPath,
                                   perlPath=perlPath)
