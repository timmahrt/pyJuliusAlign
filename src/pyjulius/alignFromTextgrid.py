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
import codecs

from pyjulius import utils
from pyjulius import juliusAlignment
from pyjulius import audioScripts

from pypraat import praatIO


def textgridToCSV(inputPath, outputPath):
    utils.makeDir(outputPath)
    
    existsFNList = utils.findFiles(outputPath, filterExt=".csv")
    for fn in utils.findFiles(inputPath, filterExt=".TextGrid", 
                              skipIfNameInList=existsFNList):
        tg = praatIO.openTextGrid(join(inputPath, fn), tossSilence=True)
        tier = tg.tierDict["utterances"]
        outputList = []
        for start, stop, label in tier.entryList:
            outputList.append("%s,%s,%s" % (start, stop, label))
        
        name = os.path.splitext(fn)[0]
        outputTxt = "\n".join(outputList)
        codecs.open(join(outputPath, "%s.csv" % name), "w", encoding="utf-8").write(outputTxt)


def convertCorpusToKanaAndRomaji(inputPath, outputPath, cabochaEncoding, cabochaPath=None, encoding="cp932"):
    '''
    Reduces a corpus of typical Japanese text to both kana and romaji
    
    Each line of input should be of the form:
    startTime, stopTime, Japanese text 
    '''
    utils.makeDir(outputPath)
    
    numUnnamedEntities = 0
    numUnidentifiedUtterances = 0
    finishedList = utils.findFiles(outputPath, filterExt=".csv")
    for fn in utils.findFiles(inputPath, filterExt=".csv", skipIfNameInList=finishedList):
        print fn
        text = codecs.open(join(inputPath, fn), "rU", encoding=encoding).read()
        textList = text.split("\n")
        
        numUnnamedEntitiesForFN = 0
        numUnidentifiedUtterancesForFN = 0
        speakerInfoList = []
        for line in textList:
            line = line.strip()
            try:
                startTime, stopTime, line = line.split(",", 2)
            except ValueError:
                print "error"
                continue
            origLine = line
            
            line, tmpWordList, tmpKanaList, tmpRomajiList, unidentifiedUtterance, unnamedEntity = juliusAlignment.prepData(line, cabochaEncoding, cabochaPath)
            numUnnamedEntities += unnamedEntity
            numUnidentifiedUtterances += unidentifiedUtterance
            
            name = os.path.splitext(fn)[0]
            outputList = [u"%s,%s,%s" % (name, startTime, stopTime), origLine, tmpWordList, tmpKanaList, tmpRomajiList]
            outputStr = ";".join(outputList)
            
            speakerInfoList.append(outputStr)
        
        print fn
        print "Number of unnamed entities for fn: ", numUnnamedEntitiesForFN
        print "Number of unidentified utterances for fn: ", numUnidentifiedUtterancesForFN
        numUnnamedEntities += numUnnamedEntitiesForFN
        numUnidentifiedUtterances += numUnidentifiedUtterancesForFN

        codecs.open(join(outputPath, fn), "w", encoding="utf-8").write("\n".join(speakerInfoList))
     
    print "\n"   
    print "Number of unnamed entities: ", numUnnamedEntities
    print "Number of unidentified utterances: ", numUnidentifiedUtterances


def forceAlignFile(speakerList, wavPath, wavNameDict, txtPath, txtFN,
                   outputPath, outputWavName, juliusScriptPath, soxPath):
    '''
    
    Normally:
    speakerList = [name]
    and
    wavNameDict = {name:"name.wav"} 
    
    But, if you have multiple speakers for each file (assuming audio is synced).
    e.g. in a stereo audio situation:
    speakerList=["L","R"] 
    and 
    wavNameDict={"L":"%s_%s.wav" % (name, "L"), "R":"%s_%s.wav" % (name, "R")}
    '''
    
    utils.makeDir(outputPath)
    
    # Formatted output of cabocha
    data = codecs.open(join(txtPath, txtFN), "r", encoding="utf-8").read()
    dataList = data.split("\n")
    dataList = [[subRow.split(",") for subRow in row.split(";")] 
                for row in dataList if row != ""]    
    
    dataDict = {speaker:[] for speaker in speakerList}
    for timingInfo, line, wordList, kanaList, romajiList in dataList:
        line = ",".join(line) # Undoing the unnecessary split that just happened
        
        speaker, startTimeStr, endTimeStr = timingInfo
        speaker, startTime, endTime = speaker.strip(), float(startTimeStr), float(endTimeStr)
        
        dataDict[speaker].append([startTime, endTime, line, wordList, kanaList, romajiList])

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
                                                    False, True, True)
        
        speakerEntryDict[speaker], statList = output
        
        numPhonesFailedAlignment += statList[0]
        numPhones += statList[1]
        numFailedIntervals += statList[2]
        numIntervals += statList[3]

    # All durations should be the same
    inputWavFN = wavNameDict.values()[0] 
    maxDuration = audioScripts.getSoundFileDuration(join(wavPath, inputWavFN))

    # Create tiers and textgrids from the output of the alignment
    tg = praatIO.Textgrid()
    for speaker in speakerList:
        for aspect in [juliusAlignment.UTTERANCE, juliusAlignment.WORD, juliusAlignment.PHONE]:
            
            tierName = "%s_%s" % (aspect, speaker)

            tier = praatIO.TextgridTier(tierName,
                                        speakerEntryDict[speaker][aspect],
                                        praatIO.INTERVAL_TIER,
                                        minT=0, maxT=maxDuration)
            tier = tier.fillInBlanks("", startTime=0, endTime=maxDuration)
            tg.addTier(tier)
    
    tg.save(join(outputPath, outputWavName+".TextGrid"))

    return numPhonesFailedAlignment, numPhones, numFailedIntervals, numIntervals


def forceAlignCorpus(wavPath, txtPath, outputPath, juliusScriptPath=None, soxPath=None):
    '''Force aligns every file and prints out summary statistics'''
    totalNumPhonesFailed = 0
    totalNumPhones = 0
    
    totalNumIntervalsFailed = 0
    totalNumIntervals = 0
    
    utils.makeDir(outputPath)
    
    finishedList = utils.findFiles(outputPath, filterExt=".TextGrid", stripExt=True)
    for name in utils.findFiles(txtPath, filterExt=".csv", 
                                skipIfNameInList=finishedList, stripExt=True):
        wavNameDict = {name:"%s.wav" % name}
        output = forceAlignFile([name,], wavPath, wavNameDict, txtPath, name+".csv", 
                                outputPath, name, juliusScriptPath, soxPath)

        numPhonesFailedAlignment, numPhones, numFailedIntervals, numIntervals = output
        
        percentFailed = utils.divide(numPhonesFailedAlignment, numPhones, 0) * 100
        percentFailedIntervals = utils.divide(numFailedIntervals, numIntervals, 0) * 100
        print "%d intervals of %d total intervals (%0.2f%%) and %d phones of %d total phones (%0.2f%%) failed to align for %s" % (numFailedIntervals, numIntervals, percentFailedIntervals, numPhonesFailedAlignment, numPhones, percentFailed, name)

        totalNumPhonesFailed += numPhonesFailedAlignment
        totalNumPhones += numPhones
        
        totalNumIntervalsFailed += numFailedIntervals
        totalNumIntervals += numIntervals
    
    totalPercentFailed = utils.divide(totalNumPhonesFailed, totalNumPhones, 0) * 100
    totalPercentFailedIntervals = utils.divide(totalNumIntervalsFailed, totalNumIntervals, 0) * 100
    print "====Summary===="
    print "%d intervals of %d total intervals (%0.2f%%) and %d phones of %d total phones (%0.2f%%) failed to align" % (totalNumIntervalsFailed, totalNumIntervals, totalPercentFailedIntervals, totalNumPhonesFailed, totalNumPhones, totalPercentFailed) 


