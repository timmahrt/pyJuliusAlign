# -*- coding: utf-8 -*-
"""
Created on Aug 6, 2014

@author: tmahrt

Contains a basic workflow of functions that may be useful in force
alignment but are not strictly necessary.  If your input is from
textgrid files or files in the form ("start time", "stop time", "text")
you may find these functions useful.
"""

import os
from os.path import join
import io
import csv

from pyjuliusalign import utils
from pyjuliusalign import juliusAlignment
from pyjuliusalign import audioScripts

from praatio import tgio
from pydub import AudioSegment, silence


def getSilencesInAudio(audioFN):
    # https://stackoverflow.com/questions/40896370/detecting-the-index-of-silence-from-a-given-audio-file-using-python
    audio = AudioSegment.from_wav(audioFN)
    silences = silence.detect_silence(
        audio, min_silence_len=300, silence_thresh=audio.dBFS - 16
    )

    return [((start / 1000), (stop / 1000)) for start, stop in silences]


def invertIntervalList(inputList, minValue, maxValue):
    """
    Inverts the segments of a list of intervals

    e.g.
    [(0,1), (4,5), (7,10)] -> [(1,4), (5,7)]
    [(0.5, 1.2), (3.4, 5.0)] -> [(0.0, 0.5), (1.2, 3.4)]
    """
    inputList = sorted(inputList)

    # Special case -- empty lists
    if len(inputList) == 0 and minValue is not None and maxValue is not None:
        invList = [
            (minValue, maxValue),
        ]
    else:
        # Insert in a garbage head and tail value for the purpose
        # of inverting, in the range does not start and end at the
        # smallest and largest values
        if minValue is not None and inputList[0][0] > minValue:
            inputList.insert(0, (-1, minValue))
        if maxValue is not None and inputList[-1][1] < maxValue:
            inputList.append((maxValue, maxValue + 1))

        invList = [
            (inputList[i][1], inputList[i + 1][0]) for i in range(0, len(inputList) - 1)
        ]

        # If two intervals in the input share a boundary, we'll get invalid intervals in the output
        # eg invertIntervalList([(0, 1), (1, 2)]) -> [(1, 1)]
        invList = [interval for interval in invList if interval[0] != interval[1]]

    return invList


def segmentPhrasesOnSmallPause(transcriptPath, wavPath, outputPath, tmpFolder, soxPath):
    utils.makeDir(outputPath)
    utils.makeDir(tmpFolder)

    for fn in utils.findFiles(transcriptPath, filterExt=".txt"):
        wavFN = os.path.splitext(fn)[0] + ".wav"
        tmpWavFN = join(tmpFolder, wavFN)
        outputList = []
        with io.open(join(transcriptPath, fn), "r", encoding="utf-8") as fd:
            csv_reader = csv.reader(fd, delimiter=";")
            for (
                head,
                _transcript,
                phrases,
                kana,
                phones,
            ) in csv_reader:
                _, start, stop = head.split(",")
                start, stop = float(start), float(stop)

                audioScripts.extractSubwav(
                    join(wavPath, wavFN),
                    tmpWavFN,
                    start,
                    stop,
                    singleChannelFlag=False,
                    soxPath=soxPath,
                )
                silences = getSilencesInAudio(tmpWavFN)
                audio = AudioSegment.from_wav(tmpWavFN)
                speechSegments = invertIntervalList(silences, 0, audio.duration_seconds)
                speechSegments = [
                    (start + snippetStart, start + snippetEnd)
                    for snippetStart, snippetEnd in speechSegments
                ]
                # speechSegments = bumpUltrashortSegments(speechSegments)
                bucketDurations = [
                    snippetEnd - snippetStart
                    for snippetStart, snippetEnd in speechSegments
                ]
                speechDuration = sum(bucketDurations)

                phrasePhoneList = [
                    phrasePhones.split() for phrasePhones in phones.split(",")
                ]
                phraseLengthsInPhones = [
                    len(phrasePhones) for phrasePhones in phrasePhoneList
                ]

                phoneDuration = speechDuration / float(sum(phraseLengthsInPhones))
                phraseLengthsInSeconds = [
                    numPhones * phoneDuration for numPhones in phraseLengthsInPhones
                ]

                bestChunking = getBestChunking(phraseLengthsInSeconds, bucketDurations)
                finalChunking = copyChunking(phrases.split(","), bestChunking)

                # Add the timing information to each chunk
                for segment, subChunks in zip(speechSegments, finalChunking):
                    start, stop = segment
                    outputList.append((start, stop, "".join(subChunks)))

            with io.open(join(outputPath, fn), "w", encoding="utf-8") as fd:
                csv_writer = csv.writer(fd)
                csv_writer.writerows(outputList)


def bumpUltrashortSegments(speechSegments):
    newSpeechSegments = []
    minDuration = 0.30
    for start, stop in speechSegments:
        if stop - start < minDuration:
            stop = start + minDuration
        newSpeechSegments.append((start, stop))

    # The silence should be large enough to accomodate the bump
    # but validate this is the case
    i = 0
    while i < len(newSpeechSegments) - 1:
        assert newSpeechSegments[i][1] < newSpeechSegments[i + 1][0]
        i += 1

    return newSpeechSegments


def copyChunking(unchunkedList, modelChunking):
    """
    Chunk an unchunked list according to a chunked list

    Bad things will probably happen if they don't have the same number of elements (when flattened)
    """
    copiedChunking = []
    for modelChunk in modelChunking:
        chunk = []
        for i in range(len(modelChunk)):
            chunk.append(unchunkedList.pop(0))

        copiedChunking.append(chunk)

    return copiedChunking


def getBestChunking(
    chunks,
    bucketDurations,
):
    """
    Given a list of chunks and a list of buckets, return the optimal placement of chunks into buckets

    chunks and buckets are both linearly ordered; the order cannot be mixed
    The sum of the chunks may be smaller or larger than the buckets
    chunks -> a list of integers
    bucketDurations -> a list of integers

    This function returns a grouping of the chunks that is optimal for the buckets
    (minimizes local overfilling or underfilling of buckets)
    """
    bestChunking = None
    minScore = 100000
    for chunking in iterateChunks(chunks, len(bucketDurations)):
        chunkingSums = [sum(chunk) for chunk in chunking]
        score = sum(
            [
                abs(bucketDuration - chunkDuration)
                for bucketDuration, chunkDuration in zip(bucketDurations, chunkingSums)
            ]
        )
        if score < minScore:
            bestChunking = chunking
            minScore = score

    return bestChunking


def iterateChunks(chunks, numBuckets):
    """

    This could probably be solved more efficiently
    with a graph but for small chunks and numBuckets
    it should be ok

    The number of iterations per call is
    numChunks - numBuckets + 1
    (I don't have a good intution for why, but calculated it out on paper)
    7 chunks; 4 buckets
    [1, ...]
    [1 2, ...]
    [1 2 3, ...]
    [1 2 3 4, 5, 6, 7]
    7 - 4 + 1 -> 4 iterations
    """

    gap = len(chunks) - numBuckets

    if numBuckets == 1:
        yield [chunks]  # [[4, 5, 6]]

    elif len(chunks) == numBuckets:
        yield [[chunk] for chunk in chunks]  # [[4], [5], [6]]

    else:
        for i in range(
            1, gap + 2
        ):  # + 2 b/c 1 for the 0-based offset; 1 for the algorithm (see doc string)
            for tailChunk in iterateChunks(chunks[i:], numBuckets - 1):
                yield [chunks[:i]] + tailChunk  # [[1, 2, 3]] + [[4], [5], [6]]


def textgridToCSV(inputPath, outputPath, outputExt=".csv", tierName="utterances"):
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


def convertCorpusToKanaAndRomaji(
    inputPath, outputPath, cabochaEncoding, cabochaPath=None, encoding="cp932"
):
    """
    Reduces a corpus of typical Japanese text to both kana and romaji

    Each line of input should be of the form:
    startTime, stopTime, Japanese text
    """
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

            dataPrepTuple = juliusAlignment.formatTextForJulius(
                line, cabochaEncoding, cabochaPath
            )

            (
                line,
                tmpWordList,
                tmpKanaList,
                tmpRomajiList,
                unidentifiedUtterance,
                unnamedEntity,
                tmpWordCount,
            ) = dataPrepTuple

            numUnnamedEntities += unnamedEntity
            numUnidentifiedUtterances += unidentifiedUtterance
            numWordsProcessedWithNoError += tmpWordCount

            name = os.path.splitext(fn)[0]
            outputList = [
                u"%s,%s,%s" % (name, startTime, stopTime),
                origLine,
                tmpWordList,
                tmpKanaList,
                tmpRomajiList,
            ]
            outputStr = ";".join(outputList)

            speakerInfoList.append(outputStr)

        if numUnnamedEntities > 0 or numUnidentifiedUtterances > 0:
            print(fn)
            print("Number of unnamed entities for fn: %d" % numUnnamedEntitiesForFN)
            print(
                "Number of unidentified utterances for fn: %d"
                % numUnidentifiedUtterancesForFN
            )

        numUnnamedEntities += numUnnamedEntitiesForFN
        numUnidentifiedUtterances += numUnidentifiedUtterancesForFN

        with io.open(join(outputPath, fn), "w", encoding="utf-8") as fd:
            fd.write("\n".join(speakerInfoList))

    print("\n")
    print("Number of transcripts converted: %d" % len(fnList))
    print("Number of unnamed entities: %d" % numUnnamedEntities)
    print("Number of unidentified utterances: %d" % numUnidentifiedUtterances)
    print("Number of words processed without error: %d" % numWordsProcessedWithNoError)


def forceAlignFile(
    speakerList,
    wavPath,
    wavNameDict,
    txtPath,
    txtFN,
    outputPath,
    outputWavName,
    juliusScriptPath,
    soxPath,
    perlPath,
):
    """

    Normally:
    speakerList = [name]
    and
    wavNameDict = {name:"name.wav"}

    But, if you have multiple speakers for each file (assuming audio is synced)
    e.g. in a stereo audio situation:
    speakerList=["L","R"]
    and
    wavNameDict={"L":"%s_%s.wav" % (name, "L"), "R":"%s_%s.wav" % (name, "R")}
    """

    utils.makeDir(outputPath)

    # Formatted output of cabocha
    with io.open(join(txtPath, txtFN), "r", encoding="utf-8") as fd:
        data = fd.read()
    dataList = data.split("\n")
    dataList = [
        [subRow.split(",") for subRow in row.split(";")]
        for row in dataList
        if row != ""
    ]

    dataDict = {speaker: [] for speaker in speakerList}

    # Undoing the unnecessary split that just happened
    for timingInfo, line, wordList, kanaList, romajiList in dataList:
        line = ",".join(line)

        speaker, startTimeStr, endTimeStr = timingInfo
        speaker, startTime, endTime = (
            speaker.strip(),
            float(startTimeStr),
            float(endTimeStr),
        )

        dataDict[speaker].append(
            [startTime, endTime, line, wordList, kanaList, romajiList]
        )

    # Do the forced alignment
    speakerEntryDict = {}
    numPhonesFailedAlignment = 0
    numPhones = 0
    numFailedIntervals = 0
    numIntervals = 0
    for speaker in speakerList:
        output = juliusAlignment.juliusAlignCabocha(
            dataDict[speaker],
            wavPath,
            wavNameDict[speaker],
            juliusScriptPath,
            soxPath,
            perlPath,
            False,
            True,
            True,
        )
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
        for aspect in [
            juliusAlignment.UTTERANCE,
            juliusAlignment.WORD,
            juliusAlignment.PHONE,
        ]:

            tierName = "%s_%s" % (aspect, speaker)
            tier = tgio.IntervalTier(
                tierName, speakerEntryDict[speaker][aspect], minT=0, maxT=maxDuration
            )
            tg.addTier(tier)

    tg.save(join(outputPath, outputWavName + ".TextGrid"))

    return (numPhonesFailedAlignment, numPhones, numFailedIntervals, numIntervals)


def forceAlignCorpus(
    wavPath, txtPath, outputPath, juliusScriptPath=None, soxPath=None, perlPath=None
):
    """Force aligns every file and prints out summary statistics"""
    totalNumPhonesFailed = 0
    totalNumPhones = 0

    totalNumIntervalsFailed = 0
    totalNumIntervals = 0

    utils.makeDir(outputPath)

    for name in utils.findFiles(txtPath, filterExt=".txt", stripExt=True):
        wavNameDict = {name: "%s.wav" % name}
        output = forceAlignFile(
            [
                name,
            ],
            wavPath,
            wavNameDict,
            txtPath,
            name + ".txt",
            outputPath,
            name,
            juliusScriptPath,
            soxPath,
            perlPath,
        )

        (numPhonesFailedAlignment, numPhones, numFailedIntervals, numIntervals) = output

        percentFailed = utils.divide(numPhonesFailedAlignment, numPhones, 0) * 100
        percentFailedIntervals = utils.divide(numFailedIntervals, numIntervals, 0) * 100
        print(
            "%d intervals of %d total intervals (%0.2f%%) and %d phones "
            "of %d total phones (%0.2f%%) successfully aligned for %s"
            % (
                numIntervals - numFailedIntervals,
                numIntervals,
                100 * (1 - percentFailedIntervals),
                numPhones - numPhonesFailedAlignment,
                numPhones,
                100 * (1 - percentFailed),
                name,
            )
        )

        totalNumPhonesFailed += numPhonesFailedAlignment
        totalNumPhones += numPhones

        totalNumIntervalsFailed += numFailedIntervals
        totalNumIntervals += numIntervals

    totalPercentFailed = utils.divide(totalNumPhonesFailed, totalNumPhones, 0) * 100
    totalPercentFailedIntervals = (
        utils.divide(totalNumIntervalsFailed, totalNumIntervals, 0) * 100
    )
    print("====Summary====")
    print(
        "%d intervals of %d total intervals (%0.2f%%) and %d phones of "
        "%d total phones (%0.2f%%) successfully aligned"
        % (
            totalNumIntervals - totalNumIntervalsFailed,
            totalNumIntervals,
            100 * (1 - totalPercentFailedIntervals),
            totalNumPhones - totalNumPhonesFailed,
            totalNumPhones,
            100 * (1 - totalPercentFailed),
        )
    )
