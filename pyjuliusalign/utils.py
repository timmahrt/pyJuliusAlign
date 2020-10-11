'''
Created on Aug 29, 2014

@author: tmahrt
'''

import os
import functools


def _getMatchFunc(pattern):
    '''
    An unsophisticated pattern matching function
    '''

    # '#' Marks word boundaries, so if there is more than one we need to do
    #    something special to make sure we're not mis-representings them
    assert(pattern.count('#') < 2)

    def startsWith(subStr, fullStr):
        return fullStr[:len(subStr)] == subStr

    def endsWith(subStr, fullStr):
        return fullStr[-1 * len(subStr):] == subStr

    def inStr(subStr, fullStr):
        return subStr in fullStr

    # Selection of the correct function
    if pattern[0] == '#':
        pattern = pattern[1:]
        cmpFunc = startsWith

    elif pattern[-1] == '#':
        pattern = pattern[:-1]
        cmpFunc = endsWith

    else:
        cmpFunc = inStr

    return functools.partial(cmpFunc, pattern)


def findFiles(path, filterPaths=False, filterExt=None, filterPattern=None,
              skipIfNameInList=None, stripExt=False):

    fnList = os.listdir(path)

    if filterPaths is True:
        fnList = [folderName for folderName in fnList
                  if os.path.isdir(os.path.join(path, folderName))]

    if filterExt is not None:
        splitFNList = [[fn, ] + list(os.path.splitext(fn)) for fn in fnList]
        fnList = [fn for fn, name, ext in splitFNList if ext == filterExt]

    if filterPattern is not None:
        splitFNList = [[fn, ] + list(os.path.splitext(fn)) for fn in fnList]
        matchFunc = _getMatchFunc(filterPattern)
        fnList = [fn for fn, name, ext in splitFNList if matchFunc(name)]

    if skipIfNameInList is not None:
        targetNameList = [os.path.splitext(fn)[0] for fn in skipIfNameInList]
        fnList = [fn for fn in fnList
                  if os.path.splitext(fn)[0] not in targetNameList]

    if stripExt is True:
        fnList = [os.path.splitext(fn)[0] for fn in fnList]

    fnList.sort()
    return fnList


def makeDir(path):
    '''Makes the desired directory if it doesn't already exist'''
    if not os.path.exists(path):
        os.mkdir(path)


def divide(numerator, denominator, zeroValue):
    if denominator == 0:
        retValue = zeroValue
    else:
        retValue = numerator / float(denominator)

    return retValue
