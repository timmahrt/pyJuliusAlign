# -*- coding: utf-8 -*-
'''
Created on Aug 20, 2014

@author: tmahrt
'''

import os
from os.path import join
import datetime
import subprocess

import Levenshtein

from pyjuliusalign import jProcessingSnippet
from pyjuliusalign import audioScripts
from pyjuliusalign import utils
from pyjuliusalign import convertKana
from pyjuliusalign import yomi2voca

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


def runJuliusAlignment(resourcePath, juliusScriptPath, perlPath, loggerFd):

    if not os.path.exists(juliusScriptPath):
        raise JuliusRunError(juliusScriptPath)

    resourcePath = os.path.abspath(resourcePath)

    cmdList = [perlPath, juliusScriptPath, resourcePath]
    print(cmdList)
    myProcess = subprocess.Popen(cmdList, stdout=loggerFd)

    if myProcess.wait():
        raise JuliusScriptExecutionFailed(cmdList)


def parseJuliusOutput(juliusOutputFn):
    with open(juliusOutputFn, "r") as fd:
        juliusOutput = fd.read()

    returnList = []
    for row in juliusOutput.split("\n"):
        row = row.strip()
        if row == "":
            continue
        row = row.split(" ")
        start = float(row[0])
        stop = float(row[1])
        label = row[2]
        returnList.append((start, stop, label))

    return returnList


def mapJuliusPronunciationToCabocha(juliusPhonesTxt, cabochaPhonesByWord):
    '''
    Aligns the phones in a julius pronunciation list into phones chunked into words by cabocha

    The phonetisation is a little different, so the mapping tries to do so gracefully.

    Basically, modify cabochaPhonesByWord to have the same number of phones as juliusPhonesTxt.
    This is done by finding the edits necessary to make the two strings the same and then applying
    those edits.
    Once the two strings contain the same number of phones, dump the phones from julius into the slots for
    the phones inside of the modified cabocha words.
    '''

    def _buildWordIndicies(cabochaPhonesByWord):
        startI = 0
        wordIndicies = []
        for word in cabochaPhonesByWord:
            wordIndicies.append([startI, startI + len(word)])
            startI += len(word)

        return wordIndicies

    def _getWordForCharIndex(indiciesForWords, targetI):
        returnI = None
        for i, indicies in enumerate(indiciesForWords):
            start, stop = indicies
            if targetI >= start and targetI < stop:
                returnI = i
                break
        return returnI

    cabochaPhonesByWord = [phones.replace(
        ":", "") for phones in cabochaPhonesByWord]
    cabochaPhonesTxt = " ".join(cabochaPhonesByWord)

    # Mutate cabochaPhonesByWord to contain the same number
    # of phones as juliusPhonesTxt
    edits = Levenshtein.editops(cabochaPhonesTxt, juliusPhonesTxt)
    wordIndicies = _buildWordIndicies(cabochaPhonesByWord)
    for operation, startIndex, _ in edits:
        wordI = _getWordForCharIndex(wordIndicies, startIndex)
        if operation == 'delete':
            cabochaPhonesByWord[wordI] = cabochaPhonesByWord[wordI][:-1]
        elif operation == 'insert':
            cabochaPhonesByWord[wordI] += '-'

    # Chunk juliusPhonesByWord according to the number
    # of phones in the now aligned cabochaPhonesByWord
    juliusPhonesByWord = []
    startI = 0
    for wordNum, phones in enumerate(cabochaPhonesByWord):
        endI = startI + len(phones)
        juliusWordPhones = juliusPhonesTxt[startI: endI]

        juliusPhonesByWord.append(juliusWordPhones)
        startI = endI + 1  # Add 1 space for the space between words

    return juliusPhonesByWord


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

    logFn = join(tmpOutputPath, 'align_log_' +
                 str(datetime.datetime.now()) + '.txt')
    loggerFd = open(logFn, "w")

    utils.makeDir(tmpOutputPath)

    tmpTxtFN = join(tmpOutputPath, "tmp.txt")
    tmpWavFN = join(tmpOutputPath, "tmp.wav")
    tmpOutputFN = join(tmpOutputPath, "tmp.lab")

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
        kanaList = convertKana.convertKataToKana(
            [char for row in rowTuple[4] for char in row])
        cabochaPhonesByWord = rowTuple[5]

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
        tmpRomajiList = []
        tmpFlattenedRomajiList = []
        juliusPhones = yomi2voca.convert(kanaList)
        juilusPronunciationByWord = mapJuliusPronunciationToCabocha(
            juliusPhones, cabochaPhonesByWord)
        for row in juilusPronunciationByWord:
            rowList = row.split(" ")
            tmpRomajiList.append(rowList)
            tmpFlattenedRomajiList.extend(rowList)

        numWords = len(wordList)
        wordTimeList = [[] for i in range(numWords)]

        # No forced-alignment if there is no romaji
        romajiTxt = "".join(kanaList)
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
        runJuliusAlignment(tmpOutputPath, juliusScriptPath, perlPath, loggerFd)

        # Get the output (timestamps for each phone)
        numIntervals += 1
        try:
            matchList = parseJuliusOutput(tmpOutputFN)
        except JuliusAlignmentError:
            if forceMonophoneAlignFlag is True and numWords == 1:
                # One phone occupies the whole interval
                matchList = [(0.0, (intervalEnd - intervalStart) * 100)]
            else:
                numPhonesFailedToAlign += numWords
                numFailedIntervals += 1
                print("Failed to align: %s - %f - %f" %
                      ("".join(romajiList), intervalStart, intervalEnd))
                continue

        adjustedPhonList = [[intervalStart + start, intervalStart + stop, label]
                            for start, stop, label in matchList]

        # Julius is conservative in estimating the final vowel.  Stretch it
        # to be the length of the utterance
        if forceEndTimeFlag:
            adjustedPhonList[-1][1] = intervalEnd

        entryDict[PHONE].extend(adjustedPhonList)

        # Get the bounding indicies for the phones in each word
        phoneToWordIndexList = []
        phonesSoFar = 0
        for i in range(len(wordList)):
            numPhones = len(tmpRomajiList[i])
            phoneToWordIndexList.append(
                (phonesSoFar, phonesSoFar + numPhones - 1))
            phonesSoFar += numPhones

        # If julius uses a silence model and we don't, then adjust our timings
        phoneListFromJulius = [label for _, _, label in adjustedPhonList]
        if "silB" in phoneListFromJulius and "silB" not in tmpFlattenedRomajiList:
            phoneToWordIndexList = [(startI + 1, endI + 1)
                                    for startI, endI in phoneToWordIndexList]
            lastI = phoneToWordIndexList[-1][1]
            phoneToWordIndexList = [
                (0, 0)] + phoneToWordIndexList + [(lastI + 1, lastI + 1)]
            wordList = [""] + wordList + [""]

        # Store the words
        for i in range(len(wordList)):
            startI, stopI = phoneToWordIndexList[i]
            entryDict[WORD].append((adjustedPhonList[startI][0],
                                    adjustedPhonList[stopI][1],
                                    wordList[i]))

        numTotalPhones += numWords

    statList = [numPhonesFailedToAlign, numTotalPhones,
                numFailedIntervals, numIntervals]
    return entryDict, statList


def formatTextForJulius(line, cabochaEncoding, cabochaPath):
    '''Prepares a single line of text, processed by cabocha, for use in julius'''
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
        unidentifiedUtterance = 1
    except jProcessingSnippet.UnidentifiedJapaneseText as e:
        # Maybe specific to my corpus?
        if all([char == u"X" for char in e.word]):
            unnamedEntity = 1
        else:
            print(u"%s" % str(e))
            unidentifiedUtterance = 1
    except jProcessingSnippet.EmptyStrError as e:
        pass
    except Exception:
        print(line)
        raise
    line = line.replace(u",", u"")

    return (line, ",".join(tmpWordList), ",".join(tmpKanaList),
            ",".join(tmpRomajiList), unidentifiedUtterance, unnamedEntity,
            len(tmpWordList))
