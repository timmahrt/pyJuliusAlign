# -*- coding: utf-8 -*-
"""
Created on Aug 31, 2014

@author: tmahrt

This is an example that will force align a directory of wav files and
corresponding TextGrid files.
"""

from os.path import join

from pyjuliusalign import alignFromTextgrid


path = join(".", "files")
cabochaOutput = join(path, "cabocha_output")
alignedOutput = join(path, "aligned_output")

# Windows executables
juliusScriptPath = (
    r"C:\Users\Tim\Documents\julius4-segmentation-kit-v1.0\segment_julius.pl"
)
soxPath = "C:\sox\sox-14-4-2\sox.exe"
cabochaPath = r"C:\Program Files (x86)\CaboCha\bin\cabocha.exe"
perlPath = r""

# Mac/Unix executables
# Use them directly if they're in your path or write out the full path to them
juliusScriptPath = "/Users/tmahrt/Downloads/segmentation-kit/segment_julius.pl"
soxPath = "sox"
cabochaPath = "cabocha"
perlPath = "perl"

# One of: 'jis-shift', 'utf-8', or 'euc-jp'
# Whichever cabocha was installed with
cabochaEncoding = "utf-8"  # "utf-8" is nice if possible

# Use this to convert your textgrids to .txt files which are used by julius
# If you do not have textgrids or you already have text transcripts, skip this step
print("\nSTEP 1: Generating transcripts")
alignFromTextgrid.textgridToCSV(inputPath=path, outputPath=path, outputExt=".txt")

# Julius expects kana, so we must first convert kanji to kana
# If your transcripts are all in kana, skip this step
print("\nSTEP 2: Converting all text to kana")
alignFromTextgrid.convertCorpusToKanaAndRomaji(
    inputPath=path,
    outputPath=cabochaOutput,
    cabochaEncoding=cabochaEncoding,
    cabochaPath=cabochaPath,
    encoding="utf-8",
)

print("\nSTEP 3: Run the force aligner")
alignFromTextgrid.forceAlignCorpus(
    wavPath=path,
    txtPath=cabochaOutput,
    outputPath=alignedOutput,
    juliusScriptPath=juliusScriptPath,
    soxPath=soxPath,
    perlPath=perlPath,
)
