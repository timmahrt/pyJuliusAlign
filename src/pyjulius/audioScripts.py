'''
Created on Aug 29, 2014

@author: tmahrt
'''

import os
from os.path import join

import wave
import audioop

from pyjulius import utils


JULIUS_MODEL_DEFAULT_FRAMERATE = 16000


class IncompatibleSampleFrequencyError(Exception):
    
    def __init__(self, actualSamplingRate, targetSamplingRate):
        self.actualSR = actualSamplingRate
        self.targetSR = targetSamplingRate
        
    
    def __str__(self):
        return "File's sampling rate=%s but system requires=%s\n Please resample audio files or ensure that sox is in your path" % (self.actualSR, self.targetSR)
        

def getSoundFileDuration(fn):
    '''
    Returns the duration of a wav file (in seconds)
    '''
    audiofile = wave.open(fn, "r")
    
    params = audiofile.getparams()
    nchannels, sampwidth, framerate, nframes, comptype, compname = params
    
    duration = float(nframes) / framerate
    return duration


def extractSubwav(fn, outputFN, startT, endT, singleChannelFlag, soxPath=None):
    
    if soxPath == None:
        soxPath = "sox" # Assumes it is in the user's path
    
    path, fnNoPath = os.path.split(fn)
    resampledAudioPath = join(path, "resampledAudio")
    resampledFN = join(resampledAudioPath, fnNoPath)
    
    audiofile = wave.open(fn, "r")
    nchannels, sampwidth, framerate, nframes, comptype, compname = audiofile.getparams()

    # If you are not using the default Julius training model, you might
    # need to change the value here.  Results will fail if the sampling
    # frequency is different.
    if framerate != JULIUS_MODEL_DEFAULT_FRAMERATE:
        if not os.path.exists(resampledFN):
            utils.makeDir(resampledAudioPath)
            sr = str(JULIUS_MODEL_DEFAULT_FRAMERATE)
            soxCmd = "%s %s -r %s %s rate -v 96k" % (soxPath, fn, sr, resampledFN)
            os.system(soxCmd)
        
        if not os.path.exists(resampledFN):
            raise IncompatibleSampleFrequencyError(framerate, JULIUS_MODEL_DEFAULT_FRAMERATE)
        
        audiofile = wave.open(resampledFN, "r")
        nchannels, sampwidth, framerate, nframes, comptype, compname = audiofile.getparams()

    # Extract the audio frames
    audiofile.setpos(int(framerate*startT))
    audioFrames = audiofile.readframes(int(framerate*(endT - startT)))
    
    # Convert to single channel if needed
    if singleChannelFlag == True and nchannels > 1:
        audioFrames = audioop.tomono(audioFrames, sampwidth, 1, 0)
        nchannels = 1
    
    outParams = [nchannels, sampwidth, framerate, len(audioFrames), comptype, compname]
    
    outWave = wave.open(outputFN, "w")
    outWave.setparams(outParams)
    outWave.writeframes(audioFrames)



    
    