# -*- coding: utf-8 -*-
'''
Created on Aug 31, 2014

@author: tmahrt

This is an example that will force align a directory of wav files and
corresponding TextGrid files.
'''

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from os.path import join


from pyjulius import alignFromTextgrid


path = join(".", "files")
cabochaOutput = join(path, "cabocha_output")
alignedOutput = join(path, "aligned_output")
juliusScriptPath = "/Users/tmahrt/Documents/julius4-segmentation-kit-v1.0"
soxPath = "/opt/local/bin/sox"
cabochaPath = "/usr/local/bin/cabocha"

alignFromTextgrid.textgridToCSV(inputPath=path,
                                outputPath=path)

alignFromTextgrid.convertCorpusToKanaAndRomaji(inputPath=path,
                                               outputPath=cabochaOutput,
                                               cabochaEncoding="euc-jp",
                                               cabochaPath=cabochaPath,
                                               encoding="utf-8")

alignFromTextgrid.forceAlignCorpus(wavPath=path, txtPath=cabochaOutput,
                                   outputPath=alignedOutput,
                                   juliusScriptPath=juliusScriptPath,
                                   soxPath=soxPath)
