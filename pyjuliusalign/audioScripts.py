'''
Created on Aug 29, 2014

@author: tmahrt
'''

import os
from os.path import join

import wave
import audioop

from pyjuliusalign import utils

# The default framerate in Julius
DEFAULT_FRAMERATE = 16000


class IncompatibleSampleFrequencyError(Exception):

    def __init__(self, actualSamplingRate, targetSamplingRate):
        super(IncompatibleSampleFrequencyError, self).__init__()
        self.actualSR = actualSamplingRate
        self.targetSR = targetSamplingRate

    def __str__(self):
        return ("File's sampling rate=%s but system requires=%s\n "
                "Please resample audio files or ensure that sox is in "
                "your path" % (self.actualSR, self.targetSR))


def getSoundFileDuration(fn):
    '''
    Returns the duration of a wav file (in seconds)
    '''
    audiofile = wave.open(fn, "r")

    params = audiofile.getparams()
    framerate = params[2]
    nframes = params[3]

    duration = float(nframes) / framerate
    return duration


def extractSubwav(fn, outputFN, startT, endT, singleChannelFlag, soxPath=None):

    if soxPath is None:
        soxPath = "sox"  # Assumes it is in the user's path

    path, fnNoPath = os.path.split(fn)
    resampledAudioPath = join(path, "resampledAudio")
    resampledFN = join(resampledAudioPath, fnNoPath)

    audiofile = wave.open(fn, "r")
    params = audiofile.getparams()
    nchannels = params[0]
    sampwidth = params[1]
    framerate = params[2]
    comptype = params[4]
    compname = params[5]

    # If you are not using the default Julius training model, you might
    # need to change the value here.  Results will fail if the sampling
    # frequency is different.
    if framerate != DEFAULT_FRAMERATE:
        if not os.path.exists(resampledFN):
            utils.makeDir(resampledAudioPath)
            sr = str(DEFAULT_FRAMERATE)
            soxCmd = "%s %s -r %s %s rate -v 96k" % (soxPath, fn, sr,
                                                     resampledFN)
            os.system(soxCmd)

        if not os.path.exists(resampledFN):
            raise IncompatibleSampleFrequencyError(framerate,
                                                   DEFAULT_FRAMERATE)

        audiofile = wave.open(resampledFN, "r")
        params = audiofile.getparams()
        nchannels = params[0]
        sampwidth = params[1]
        framerate = params[2]
        comptype = params[4]
        compname = params[5]

    # Extract the audio frames
    audiofile.setpos(int(framerate * startT))
    audioFrames = audiofile.readframes(int(framerate * (endT - startT)))

    # Convert to single channel if needed
    if singleChannelFlag is True and nchannels > 1:
        audioFrames = audioop.tomono(audioFrames, sampwidth, 1, 0)
        nchannels = 1

    outParams = [nchannels, sampwidth, framerate, len(audioFrames),
                 comptype, compname]

    outWave = wave.open(outputFN, "w")
    outWave.setparams(outParams)
    outWave.writeframes(audioFrames)


def splitStereoAudio(path, fn, outputPath=None):

    if outputPath is None:
        outputPath = join(path, "split_audio")

    if not os.path.exists(outputPath):
        os.mkdir(outputPath)

    name = os.path.splitext(fn)[0]

    fnFullPath = join(path, fn)
    leftOutputFN = join(outputPath, "%s_L.wav" % name)
    rightOutputFN = join(outputPath, "%s_R.wav" % name)

    audiofile = wave.open(fnFullPath, "r")

    params = audiofile.getparams()
    sampwidth = params[1]
    nframes = params[3]
    audioFrames = audiofile.readframes(nframes)

    for leftFactor, rightFactor, outputFN in ((1, 0, leftOutputFN),
                                              (0, 1, rightOutputFN)):

        monoAudioFrames = audioop.tomono(audioFrames, sampwidth,
                                         leftFactor, rightFactor)
        params = tuple([1, ] + list(params[1:]))

        outputAudiofile = wave.open(outputFN, "w")
        outputAudiofile.setparams(params)
        outputAudiofile.writeframes(monoAudioFrames)
