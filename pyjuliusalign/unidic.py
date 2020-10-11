# -*- coding: utf-8 -*-
'''
Created on Aug 19, 2014

@author: tmahrt
'''

from os.path import join
import cPickle
import io


class UnidicTool(object):
    '''
    A Japanese pronunciation dictionary developed by Ninjal
    '''

    def __init__(self, unidicPath):
        self.data = None
        self.cachedData = None

        self.unidicPath = join(unidicPath, "lex.csv")
        self.unidicCachePath = join(unidicPath, "lex.pickle")

    def lookup(self, word):
        if self.data is None:
            with io.open(self.unidicPath, "r", encoding="utf-8") as fd:
                self.data = fd.read()

        startI = 0
        matchList = []
        while True:
            try:
                matchI = self.data.index(u"\n" + word, startI) + 1
                endI = self.data.index(u"\n", matchI)
            except ValueError:
                break

            matchList.append(self.data[matchI + len(word) + 1:endI].split(','))
            startI = matchI

        return matchList

    def saveCache(self):
        cPickle.dump(self.cachedData, open(self.unidicCachePath, "w"))
