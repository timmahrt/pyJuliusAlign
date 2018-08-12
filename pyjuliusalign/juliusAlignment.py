# -*- coding: utf-8 -*-
'''
Created on Aug 20, 2014

@author: tmahrt
'''

import os
from os.path import join

import subprocess

from pyjuliusalign import jProcessingSnippet
from pyjuliusalign import audioScripts
from pyjuliusalign import utils

PHONE = "phones"
WORD = "words"
UTTERANCE = "utterances"


class JuliusRunError(Exception):

    def __init__(self, juliusPath):
        super(JuliusRunError, self).__init__()
        self.path = juliusPath

    def __str__(self):
        return ("Tried to run julius at location but it does not exist: \n%s"
                % self.path)

    
class JuliusAlignmentError(Exception):

    def __str__(self):
        return "Failed to align: "


class JuliusScriptExecutionFailed(Exception):
    
    def __init__(self, cmdList):
        super(JuliusScriptExecutionFailed, self).__init__()
        self.cmdList = cmdList
    
    def __str__(self):
        errorStr = ("\ Execution Failed.  Please check the following:\n"
                    "- Perl and the julius4.pl script exist in the "
                    "locations specified\n"
                    "- you have edited the 'user configuration' part of "
                    "'segment_julius4.pl'\n"
                    "- script arguments are correct\n\n"
                    "If you can't locate the problem, I recommend using "
                    "absolute paths rather than relative "
                    "paths and using paths without spaces in any folder "
                    "or file names\n\n"
                    "Here is the command that python attempted to run:\n")
        cmdTxt = " ".join(self.cmdList)
        return errorStr + cmdTxt


def runJuliusAlignment(wavFN, transFN, juliusScriptPath, perlPath):
    
    if not os.path.exists(juliusScriptPath):
        raise JuliusRunError(juliusScriptPath)
    
    cmdList = [perlPath, juliusScriptPath, wavFN, transFN]
    myProcess = subprocess.Popen(cmdList)
    
    if myProcess.wait():
        raise JuliusScriptExecutionFailed(cmdList)


def parseJuliusOutput(juliusOutputFN):
    '''Parse the output of julius'''
    with open(juliusOutputFN, "r") as fd:
        output = fd.read()
    try:
        output = output.split("----------------------------------------")[1]
    except IndexError:
        raise JuliusAlignmentError()
    output = output.split("re-computed")[0]
    
    # Extract the individual phones, along with their timing information
    start = 0
    matchList = []
    while True:
        try:
            start = output.index('[', start)
            end = output.index(']', start)
        except ValueError:
            break
        
        matchList.append(output[start + 1:end])
        start = end
        
    matchList = [[float(value.strip()) for value in row.split()]
                 for row in matchList]

    return matchList


def juliusAlignCabocha(dataList, wavPath, wavFN, juliusScriptPath, soxPath,
                       perlPath, silenceFlag, forceEndTimeFlag,
                       forceMonophoneAlignFlag):
    '''
    Given utterance-level timing and a wav file, phone-align the audio
    
    dataList is the formatted output of cabocha of the form
    [startTime, endTime, wordList, kanaList, romajiList]
    '''
    tmpOutputPath = join(wavPath, "align_tmp")
    utils.makeDir(tmpOutputPath)
    
    tmpTxtFN = join(tmpOutputPath, "tmp.txt")
    tmpWavFN = join(tmpOutputPath, "tmp.wav")
    tmpOutputFN = join(tmpOutputPath, "tmp.txt.align")
    
    entryDict = {}
    for aspect in [UTTERANCE, WORD, PHONE]:
        entryDict[aspect] = []
    
    # one speech interval at a time
    numTotalPhones = 0
    numPhonesFailedToAlign = 0
    numIntervals = 0
    numFailedIntervals = 0
    # intervalStart, intervalEnd, line, wordList, kanaList, romajiList
    for rowTuple in dataList:
        intervalStart = rowTuple[0]
        intervalEnd = rowTuple[1]
        line = rowTuple[2]
        wordList = rowTuple[3]
        romajiList = rowTuple[5]
        
        if line.strip() != "":
            entryDict[UTTERANCE].append((str(intervalStart),
                                         str(intervalEnd),
                                         line))
        
        if len([word for word in wordList if word != '']) == 0:
            continue
        
        assert(intervalStart < intervalEnd)
        
        # Create romajiTxt (for forced alignment) and
        # phoneList (for the textgrid)
        # Phones broken up by word
        tmpRomajiList = [row.split(" ") for row in romajiList]
        numPhones = len(tmpRomajiList)
        wordTimeList = [[] for i in range(len(wordList))]
        phoneToWordIndexList = []
        for i in range(numPhones):
            for j in range(len(tmpRomajiList[i])):
                phoneToWordIndexList.append(i)
        
        romajiTxt = " ".join(romajiList)
        phoneList = [phone for phone in romajiTxt.split(" ")]
        
        # No forced-alignment if there is no romaji
        if romajiTxt.strip() == "":
            continue
        
        # Encapsulate each phone string in boundary silence
        #    - in my limited experience, this messes up the output even more
        if silenceFlag:
            romajiTxt = "silB " + romajiTxt + " silE"
        
        # Save temporary transcript and wav files for interval
        with open(tmpTxtFN, "w") as fd:
            fd.write(romajiTxt)
                
        audioScripts.extractSubwav(join(wavPath, wavFN), tmpWavFN,
                                   intervalStart, intervalEnd,
                                   singleChannelFlag=False,
                                   soxPath=soxPath)
        
        # Run forced alignment
        runJuliusAlignment(tmpWavFN, tmpTxtFN, juliusScriptPath, perlPath)
        
        # Get the output (timestamps for each phone)
        numIntervals += 1
        try:
            matchList = parseJuliusOutput(tmpOutputFN)
        except JuliusAlignmentError:
            if forceMonophoneAlignFlag is True and numPhones == 1:
                # One phone occupies the whole interval
                matchList = [(0.0, (intervalEnd - intervalStart) * 100)]
            else:
                numPhonesFailedToAlign += numPhones
                numFailedIntervals += 1
                print("Failed to align: %s - %f - %f" %
                      ("".join(romajiList), intervalStart, intervalEnd))
                continue
        
        # Store the phones
        streamStart = matchList[0][0]
        i = 0
        for timeList, label in zip(*[matchList, phoneList]):
            
            start, stop = timeList
            assert(float(start) < float(stop))
            
            phoneStartTime = intervalStart + streamStart * 0.01
            phoneStopTime = intervalStart + stop * 0.01
            
            # Julius is conservative in estimating the final vowel.  Stretch it
            # to be the length of the utterance
            if forceEndTimeFlag is True and i + 1 == len(matchList):
                phoneStopTime = intervalEnd
            
            # Store the phone here
            print(float(phoneStartTime), float(phoneStopTime))
            assert(float(phoneStartTime) < float(phoneStopTime))
            entryDict[PHONE].append((phoneStartTime, phoneStopTime, label))
            
            # Use those same phone times in determining the word time later
            j = phoneToWordIndexList[i]
            wordTimeList[j].extend([phoneStartTime, phoneStopTime])
            
            # Next iteration
            streamStart = stop
            i += 1
        print(wordList)
        print(wordTimeList)
        # Store the words
        for i in range(len(wordList)):
            assert(len(wordTimeList[i]) != 0)
            
            entryDict[WORD].append((min(wordTimeList[i]), max(wordTimeList[i]),
                                    wordList[i]))

        numTotalPhones += numPhones
    
    statList = [numPhonesFailedToAlign, numTotalPhones,
                numFailedIntervals, numIntervals]
    return entryDict, statList


def prepData(line, cabochaEncoding, cabochaPath):
    '''Prepares a line, processed by cabocha, for use in julius'''
    unidentifiedUtterance = 0
    unnamedEntity = 0
        
    origLine = line
    
    # Clean up the line before it gets processed
    # Not sure what "・" is but cabocha doesn't like it
    for char in [u"（", u"）", u" ", u"．", u"？", u"「", u"」",
                 u"［", u"］", u"＠Ｗ", u"＠Ｓ", u"＜", u"＞", u" ", u"。"]:
        line = line.replace(char, "")
    
    # Used to split names?
    for char in [u"・", u"·"]:
        line = line.replace(char, " ")
    
    line = line.strip()
    
    try:
        (tmpWordList, tmpKanaList,
         tmpRomajiList) = jProcessingSnippet.getChunkedKana(line,
                                                            cabochaEncoding,
                                                            cabochaPath)
    except (jProcessingSnippet.ChunkingError,
            jProcessingSnippet.NonKatakanaError) as e:
        print(u"%s, %s" % (str(e), origLine))
        tmpWordList = [""]
        tmpKanaList = [""]
        tmpRomajiList = [""]
        unidentifiedUtterance = 1
    except jProcessingSnippet.UnidentifiedJapaneseText as e:
        # Maybe specific to my corpus?
        if all([char == u"X" for char in e.word]):
            unnamedEntity = 1
        else:
            print(u"%s" % str(e))
            unidentifiedUtterance = 1
        tmpWordList = [""]
        tmpKanaList = [""]
        tmpRomajiList = [""]
    except jProcessingSnippet.EmptyStrError as e:
        tmpWordList = [""]
        tmpKanaList = [""]
        tmpRomajiList = [""]
    except Exception:
        print(line)
        raise
    line = line.replace(u",", u"")
    
    return (line, ",".join(tmpWordList), ",".join(tmpKanaList),
            ",".join(tmpRomajiList), unidentifiedUtterance, unnamedEntity)
