# -*- coding: utf-8 -*-
'''
Created on Aug 6, 2014

@author: tmahrt
'''

import sys
reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append("/Users/tmahrt/Dropbox/workspace/Thesis/")


from os.path import join
import io
import shutil

from pyjuliusalign import utils
from pyjuliusalign import jProcessingSnippet
from pyjuliusalign import juliusAlignment
from pyjuliusalign import audioScripts

from praatio import tgio


def convertCorpusToUTF8(path):
    
    outputDir = join(path, "output")
    utils.makeDir(outputDir)
    
    for fn in utils.findFiles(path, filterExt=".txt"):
        # cp932 = Japanese
        with io.open(join(path, fn), "rU", encoding="cp932") as fd:
            text = fd.read()
        with io.open(join(outputDir, fn), "w", encoding='utf-8') as fd:
            fd.write(text)


def convertCRESTToKanaAndRomaji(inputPath, outputPath, cabochaEncoding,
                                cabochaPath, encoding="cp932"):
    
    timeInfoPath = join(outputPath, "speaker_info_and_utterance_timing")
    
    for path in [timeInfoPath]:
        utils.makeDir(path)
    
    numUnnamedEntities = 0
    numUnidentifiedUtterances = 0
    finishedList = utils.findFiles(timeInfoPath, filterExt=".txt")
    for fn in utils.findFiles(inputPath, filterExt=".txt",
                              skipIfNameInList=finishedList):
        with io.open(join(inputPath, fn), "r", encoding=encoding) as fd:
            text = fd.read()
        textList = text.split("\n")
        
        numUnnamedEntitiesForFN = 0
        numUnidentifiedUtterancesForFN = 0
        speakerInfoList = []
        for line in textList:
            line = line.strip()
            try:
                speakerCode, startTime, stopTime, line = line.split(" ", 3)
            except ValueError:
                continue
            
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
                tmp = jProcessingSnippet.getChunkedKana(line, cabochaEncoding,
                                                        cabochaPath)
                tmpWordList, tmpKanaList, tmpromajiList = tmp
            except (jProcessingSnippet.ChunkingError,
                    jProcessingSnippet.NonKatakanaError) as e:
                print(u"%s, %s" % (str(e), origLine))
                tmpWordList = [""]
                tmpKanaList = [""]
                tmpromajiList = [""]
                numUnidentifiedUtterancesForFN += 1
            except jProcessingSnippet.UnidentifiedJapaneseText as e:
                if all([char == u"X" for char in e.word]):
                    numUnnamedEntitiesForFN += 1
                else:
                    print(u"%s" % str(e))
                    numUnidentifiedUtterancesForFN += 1
                tmpWordList = [""]
                tmpKanaList = [""]
                tmpromajiList = [""]
            except jProcessingSnippet.EmptyStrError as e:
                tmpWordList = [""]
                tmpKanaList = [""]
                tmpromajiList = [""]
            except Exception:
                print(line)
                raise
            line = line.replace(u",", u"")
            outputList = [u"%s,%s,%s" % (speakerCode, startTime, stopTime),
                          origLine, ','.join(tmpWordList),
                          ",".join(tmpKanaList), ",".join(tmpromajiList)]
            outputStr = ";".join(outputList)
            
            speakerInfoList.append(outputStr)
        
        print(fn)
        print("Number of unnamed entities for fn: %d" %
              numUnnamedEntitiesForFN)
        print("Number of unidentified utterances for fn: %d" %
              numUnidentifiedUtterancesForFN)
        numUnnamedEntities += numUnnamedEntitiesForFN
        numUnidentifiedUtterances += numUnidentifiedUtterancesForFN

        outputFN = join(timeInfoPath, fn)
        with io.open(outputFN, "w", encoding="utf-8") as fd:
            fd.write("\n".join(speakerInfoList))
    
    print("\n")
    print("Number of unnamed entities: %d" % numUnnamedEntities)
    print("Number of unidentified utterances: %d" % numUnidentifiedUtterances)


def forceAlignFile(wavPath, wavName, txtPath, txtFN, outputPath,
                   juliusScriptPath, soxPath):
    '''
    '''
    
    utils.makeDir(outputPath)
    
    wavFNDict = {"L": wavName + "_L.wav",
                 "R": wavName + "_R.wav"}
    
    # Formatted output of cabocha
    data = open(join(txtPath, txtFN), "rU").read()
    dataList = data.split("\n")
    dataList = [[subRow.split(",") for subRow in row.split(";")]
                for row in dataList if row != ""]
    
    dataDict = {"L": [], "R": []}
    for timingInfo, line, wordList, kanaList, romajiList in dataList:
        # Undoing the unnecessary split that just happened
        line = ",".join(line)
        
        speaker, startTimeStr, endTimeStr = timingInfo
        speaker, startTime, endTime = (speaker.strip(), float(startTimeStr),
                                       float(endTimeStr))
        
        dataDict[speaker].append([startTime, endTime, line, wordList,
                                  kanaList, romajiList])

    speakerEntryDict = {}
    numPhonesFailedAlignment = 0
    numPhones = 0
    numFailedIntervals = 0
    numIntervals = 0
    for speaker in ["L", "R"]:
        tmp = juliusAlignment.juliusAlignCabocha(dataDict[speaker], wavPath,
                                                 wavFNDict[speaker],
                                                 juliusScriptPath,
                                                 soxPath,
                                                 False, True, True)
        speakerEntryDict[speaker], statList = tmp
        numPhonesFailedAlignment += statList[0]
        numPhones += statList[1]
        numFailedIntervals += statList[2]
        numIntervals += statList[3]

    # Create tiers and textgrids
    tg = tgio.Textgrid()
    maxDuration = audioScripts.getSoundFileDuration(join(wavPath,
                                                         wavName + "_L.wav"))
    for speaker in ["L", "R"]:
        for aspect in [juliusAlignment.UTTERANCE, juliusAlignment.WORD,
                       juliusAlignment.PHONE]:
            
            tierName = "%s_%s" % (aspect, speaker)

            tier = tgio.IntervalTier(tierName,
                                        speakerEntryDict[speaker][aspect],
                                        minT=0, maxT=maxDuration)
            tg.addTier(tier)
    
    tg.save(join(outputPath, wavName + ".TextGrid"))

    return (numPhonesFailedAlignment, numPhones,
            numFailedIntervals, numIntervals)


def forceAlignCrest(wavPath, txtPath, outputPath, juliusScriptPath, soxPath):
    
    totalNumPhonesFailed = 0
    totalNumPhones = 0
    
    totalNumIntervalsFailed = 0
    totalNumIntervals = 0
    
    finishedList = utils.findFiles(outputPath, filterExt=".TextGrid",
                                   stripExt=True)
    for name in utils.findFiles(txtPath, filterExt=".txt",
                                skipIfNameInList=finishedList, stripExt=True):
        
        (numPhonesFailedAlignment, numPhones, numFailedIntervals,
         numIntervals) = forceAlignFile(wavPath, name, txtPath,
                                        name + ".txt", outputPath,
                                        juliusScriptPath, soxPath)

        percentFailed = utils.divide(numPhonesFailedAlignment,
                                     numPhones, 0) * 100
        percentFailedIntervals = utils.divide(numFailedIntervals,
                                              numIntervals, 0) * 100
        print("%d intervals of %d total intervals (%0.2f%%) and %d phones "
              "of %d total phones (%0.2f%%) failed to align for %s" %
              (numFailedIntervals, numIntervals, percentFailedIntervals,
               numPhonesFailedAlignment, numPhones, percentFailed, name))

        totalNumPhonesFailed += numPhonesFailedAlignment
        totalNumPhones += numPhones
        
        totalNumIntervalsFailed += numFailedIntervals
        totalNumIntervals += numIntervals
    
    totalPercentFailed = utils.divide(totalNumPhonesFailed,
                                      totalNumPhones, 0) * 100
    totalPercentFailedIntervals = utils.divide(totalNumIntervalsFailed,
                                               totalNumIntervals, 0) * 100
    print("====Summary====")
    print("%d intervals of %d total intervals (%0.2f%%) and %d phones of %d "
          "total phones (%0.2f%%) failed to align" %
          (totalNumIntervalsFailed, totalNumIntervals,
           totalPercentFailedIntervals, totalNumPhonesFailed,
           totalNumPhones, totalPercentFailed))


def renameMP3Files(path):
    
    outputPath = join(path, "renamed")
    utils.makeDir(outputPath)

    for name in utils.findFiles(path, filterExt=".mp3", stripExt=True):
        if name[-1] == "x":
            newName = name[:-1]
            shutil.move(join(path, name + ".mp3"),
                        join(outputPath, newName + ".mp3"))


def splitAudio(path):
    
    outputPath = join(path, "split_audio")
    utils.makeDir(outputPath)
    
    for fn in utils.findFiles(path, filterExt=".wav"):
        audioScripts.splitStereoAudio(path, fn, outputPath)


def getSelectedTxtFiles(txtPath, wavPath):
    
    outputPath = join(txtPath, "selected_txt")
    utils.makeDir(outputPath)
    
    nameList = utils.findFiles(wavPath, filterExt=".wav", stripExt=True)
    nameList = [name.split("_")[0] for name in nameList]
    nameList = list(set(nameList))
    
    for name in utils.findFiles(txtPath, filterExt=".txt", stripExt=True):
        if name not in nameList:
            continue
        shutil.copy(join(txtPath, name + ".txt"),
                    join(outputPath, name + ".txt"))
        

if __name__ == "__main__":
    _juliusScriptPath = "/Users/tmahrt/Documents/julius4-segmentation-kit-v1.0"
    _cabochaPath = "/usr/local/bin/cabocha"
    _soxPath = "/opt/local/bin/sox"
    _cabochaEncoding = "euc-jp"
    convertCorpusToUTF8("/Users/tmahrt/Downloads/railroad")
    
    _path = "/Users/tmahrt/Desktop/experiments/Kobe_corpus/features/txt"
#     readCorpus(path)

    _outputPath = "/Users/tmahrt/Desktop/experiments/Kobe_corpus/features"
    convertCRESTToKanaAndRomaji(_path, _outputPath, _cabochaEncoding,
                                _cabochaPath)
    
    _wavPath = "/Users/tmahrt/Desktop/experiments/Kobe_corpus/features/wavs"
    _txtPath = ("/Users/tmahrt/Desktop/experiments/Kobe_corpus/features/"
                "speaker_info_and_utterance_timing")
    _outputPath = ("/Users/tmahrt/Desktop/experiments/Kobe_corpus/features/"
                   "textgrids")
#     outputPath = "/Users/tmahrt/Desktop/experiments/Kobe_corpus/mp3/wav16k"
    forceAlignCrest(_wavPath, _txtPath, _outputPath,
                    _juliusScriptPath, _soxPath)

    _mp3Path = "/Users/tmahrt/Desktop/mp3_files"
#     renameMP3Files(mp3Path)
    
    _wavPath = "/Users/tmahrt/Desktop/experiments/Kobe_corpus/mp3/wav16k"
#     splitAudio(path)

    _txtPath = "/Users/tmahrt/Desktop/experiments/Kobe_corpus/txt"
    _txtPath = ("/Users/tmahrt/Desktop/experiments/Kobe_corpus/features/"
                "speaker_info_and_utterance_timing")
    _wavPath = "/Users/tmahrt/Desktop/experiments/Kobe_corpus/features/wavs"
#     getSelectedTxtFiles(txtPath, wavPath)
