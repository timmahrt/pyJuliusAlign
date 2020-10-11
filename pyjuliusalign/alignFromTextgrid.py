# -*- coding: utf-8 -*-
'''
Created on Aug 6, 2014

@author: tmahrt

Contains a basic workflow of functions that may be useful in force
alignment but are not strictly necessary.  If your input is from
textgrid files or files in the form ("start time", "stop time", "text")
you may find these functions useful.
'''

import os
from os.path import join
import io

from pyjuliusalign import utils
from pyjuliusalign import juliusAlignment
from pyjuliusalign import audioScripts

from praatio import tgio


def textgridToCSV(inputPath, outputPath, outputExt='.csv', tierName="utterances"):
    utils.makeDir(outputPath)

    for fn in utils.findFiles(inputPath, filterExt=".TextGrid"):
        tg = tgio.openTextgrid(join(inputPath, fn))
        tier = tg.tierDict[tierName]
        outputList = []
        for start, stop, label in tier.entryList:
            outputList.append("%s,%s,%s" % (start, stop, label))

        name = os.path.splitext(fn)[0]
        outputTxt = "\n".join(outputList)
        outputFN = join(outputPath, "%s%s" % (name, outputExt))
        with io.open(outputFN, "w", encoding="utf-8") as fd:
            fd.write(outputTxt)


def convertCorpusToKanaAndRomaji(inputPath, outputPath, cabochaEncoding,
                                 cabochaPath=None, encoding="cp932"):
    '''
    Reduces a corpus of typical Japanese text to both kana and romaji

    Each line of input should be of the form:
    startTime, stopTime, Japanese text
    '''
    utils.makeDir(outputPath)

    numUnnamedEntities = 0
    numUnidentifiedUtterances = 0
    numWordsProcessedWithNoError = 0

    fnList = utils.findFiles(inputPath, filterExt=".txt")
    for fn in fnList:
        with io.open(join(inputPath, fn), "rU", encoding=encoding) as fd:
            text = fd.read()
        textList = text.split("\n")

        numUnnamedEntitiesForFN = 0
        numUnidentifiedUtterancesForFN = 0
        speakerInfoList = []
        for line in textList:
            line = line.strip()
            try:
                startTime, stopTime, line = line.split(",", 2)
            except ValueError:
                print("error")
                continue
            origLine = line

            dataPrepTuple = juliusAlignment.formatTextForJulius(line,
                                                                cabochaEncoding,
                                                                cabochaPath)

            (line, tmpWordList, tmpKanaList, tmpRomajiList,
             unidentifiedUtterance, unnamedEntity, tmpWordCount) = dataPrepTuple

            numUnnamedEntities += unnamedEntity
            numUnidentifiedUtterances += unidentifiedUtterance
            numWordsProcessedWithNoError += tmpWordCount

            name = os.path.splitext(fn)[0]
            outputList = [u"%s,%s,%s" % (name, startTime, stopTime), origLine,
                          tmpWordList, tmpKanaList, tmpRomajiList]
            outputStr = ";".join(outputList)

            speakerInfoList.append(outputStr)

        if(numUnnamedEntities > 0 or numUnidentifiedUtterances > 0):
            print(fn)
            print("Number of unnamed entities for fn: %d" %
                  numUnnamedEntitiesForFN)
            print("Number of unidentified utterances for fn: %d" %
                  numUnidentifiedUtterancesForFN)

        numUnnamedEntities += numUnnamedEntitiesForFN
        numUnidentifiedUtterances += numUnidentifiedUtterancesForFN

        with io.open(join(outputPath, fn), "w", encoding="utf-8") as fd:
            fd.write("\n".join(speakerInfoList))

    print("\n")
    print("Number of transcripts converted: %d" % len(fnList))
    print("Number of unnamed entities: %d" % numUnnamedEntities)
    print("Number of unidentified utterances: %d" % numUnidentifiedUtterances)
    print("Number of words processed without error: %d" %
          numWordsProcessedWithNoError)


def forceAlignFile(speakerList, wavPath, wavNameDict, txtPath, txtFN,
                   outputPath, outputWavName, juliusScriptPath, soxPath,
                   perlPath):
    '''

    Normally:
    speakerList = [name]
    and
    wavNameDict = {name:"name.wav"}

    But, if you have multiple speakers for each file (assuming audio is synced)
    e.g. in a stereo audio situation:
    speakerList=["L","R"]
    and
    wavNameDict={"L":"%s_%s.wav" % (name, "L"), "R":"%s_%s.wav" % (name, "R")}
    '''

    utils.makeDir(outputPath)

    # Formatted output of cabocha
    with io.open(join(txtPath, txtFN), "r", encoding="utf-8") as fd:
        data = fd.read()
    dataList = data.split("\n")
    dataList = [[subRow.split(",") for subRow in row.split(";")]
                for row in dataList if row != ""]

    dataDict = {speaker: [] for speaker in speakerList}

    # Undoing the unnecessary split that just happened
    for timingInfo, line, wordList, kanaList, romajiList in dataList:
        line = ",".join(line)

        speaker, startTimeStr, endTimeStr = timingInfo
        speaker, startTime, endTime = (speaker.strip(), float(startTimeStr),
                                       float(endTimeStr))

        dataDict[speaker].append([startTime, endTime, line, wordList,
                                  kanaList, romajiList])

    # Do the forced alignment
    speakerEntryDict = {}
    numPhonesFailedAlignment = 0
    numPhones = 0
    numFailedIntervals = 0
    numIntervals = 0
    for speaker in speakerList:
        output = juliusAlignment.juliusAlignCabocha(dataDict[speaker], wavPath,
                                                    wavNameDict[speaker],
                                                    juliusScriptPath, soxPath,
                                                    perlPath, False, True, True)
        speakerEntryDict[speaker], statList = output

        numPhonesFailedAlignment += statList[0]
        numPhones += statList[1]
        numFailedIntervals += statList[2]
        numIntervals += statList[3]

    # All durations should be the same
    inputWavFN = next(iter(wavNameDict.values()))
    maxDuration = audioScripts.getSoundFileDuration(join(wavPath, inputWavFN))

    # Create tiers and textgrids from the output of the alignment
    tg = tgio.Textgrid()
    for speaker in speakerList:
        for aspect in [juliusAlignment.UTTERANCE, juliusAlignment.WORD,
                       juliusAlignment.PHONE]:

            tierName = "%s_%s" % (aspect, speaker)
            tier = tgio.IntervalTier(tierName,
                                     speakerEntryDict[speaker][aspect],
                                     minT=0, maxT=maxDuration)
            tg.addTier(tier)

    tg.save(join(outputPath, outputWavName + ".TextGrid"))

    return (numPhonesFailedAlignment, numPhones,
            numFailedIntervals, numIntervals)


def forceAlignCorpus(wavPath, txtPath, outputPath, juliusScriptPath=None,
                     soxPath=None, perlPath=None):
    '''Force aligns every file and prints out summary statistics'''
    totalNumPhonesFailed = 0
    totalNumPhones = 0

    totalNumIntervalsFailed = 0
    totalNumIntervals = 0

    utils.makeDir(outputPath)

    for name in utils.findFiles(txtPath, filterExt=".txt", stripExt=True):
        wavNameDict = {name: "%s.wav" % name}
        output = forceAlignFile([name, ], wavPath, wavNameDict, txtPath,
                                name + ".txt", outputPath, name,
                                juliusScriptPath, soxPath, perlPath)

        (numPhonesFailedAlignment, numPhones,
         numFailedIntervals, numIntervals) = output

        percentFailed = utils.divide(numPhonesFailedAlignment,
                                     numPhones, 0) * 100
        percentFailedIntervals = utils.divide(numFailedIntervals,
                                              numIntervals, 0) * 100
        print("%d intervals of %d total intervals (%0.2f%%) and %d phones "
              "of %d total phones (%0.2f%%) successfully aligned for %s" %
              (numIntervals - numFailedIntervals, numIntervals, 100 * (1 - percentFailedIntervals),
               numPhones - numPhonesFailedAlignment, numPhones, 100 * (1 - percentFailed), name))

        totalNumPhonesFailed += numPhonesFailedAlignment
        totalNumPhones += numPhones

        totalNumIntervalsFailed += numFailedIntervals
        totalNumIntervals += numIntervals

    totalPercentFailed = utils.divide(totalNumPhonesFailed,
                                      totalNumPhones, 0) * 100
    totalPercentFailedIntervals = utils.divide(totalNumIntervalsFailed,
                                               totalNumIntervals, 0) * 100
    print("====Summary====")
    print("%d intervals of %d total intervals (%0.2f%%) and %d phones of "
          "%d total phones (%0.2f%%) successfully aligned" %
          (totalNumIntervals - totalNumIntervalsFailed, totalNumIntervals, 100 * (1 - totalPercentFailedIntervals),
           totalNumPhones - totalNumPhonesFailed, totalNumPhones, 100 * (1 - totalPercentFailed)))
