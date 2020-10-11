# -*- coding: utf-8 -*-
'''
Created on Aug 20, 2014

@author: tmahrt

katakanaChart.txt, hiraganaChart.txt, formdamage(), parseChart(),
cabocha() and jReads()
were all taken with modification from the project
https://github.com/kevincobain2000/jProcessing
# Copyright (c) 2011, Pulkit Kathuria
# All rights reserved.

Modifications were made specifically for prepping data in use with julius

All other code is from me
'''

import os
from os.path import join
import subprocess
import tempfile

import xml.etree.cElementTree as etree

from pyjuliusalign import convertKana


class UnidentifiedJapaneseText(Exception):

    def __init__(self, sentence, word):
        super(UnidentifiedJapaneseText, self).__init__()
        self.sentence = sentence
        self.word = word

    def __str__(self):
        return (u"No match in dictionary for word '%s' in sentence: \n'%s'" %
                (self.word, self.sentence))


class ChunkingError(Exception):
    '''Raised when a katakana string cannot be parsed correctly'''

    def __init__(self, txt):
        super(ChunkingError, self).__init__()
        self.textStr = txt

    def __str__(self):
        return u"Chunking error for string: \n %s" % self.textStr


class EmptyStrError(Exception):

    def __str__(self):
        return "Empty string passed in"


class NonKatakanaError(Exception):

    def __init__(self, char, utterance):
        super(NonKatakanaError, self).__init__()
        self.char = char
        self.utterance = utterance

    def __str__(self):
        return (u"Wrongly interpreted character '%s' as kana in utterance:\n%s"
                % (unicode(self.char), unicode(self.utterance)))


class CabochaNotRunError(Exception):

    def __init__(self, cabochaCmd):
        super(CabochaNotRunError, self).__init__()
        self.cabochaCmd = cabochaCmd

    def __str__(self):
        return (u"Cabocha not installed or not in path.  "
                "Attempted to run command:\n%s" % self.cabochaCmd)


class CabochaOutputError(Exception):

    def __init__(self, outputStr):
        super(CabochaOutputError, self).__init__()
        self.outputStr = outputStr

    def __str__(self):
        return ("Unexpected error in cabocha output "
                "(possibly a problem with cabocha).  See error:\n%s" %
                self.outputStr)


class TextDecodingError(Exception):

    def __init__(self, encoding):
        super(TextDecodingError, self).__init__()
        self.encoding = encoding

    def __str__(self):
        print(self.encoding)
        return ("Cabocha tried to decode text with the encoding '%s' but it failed. "
                "If you specify a different encoding in "
                "alignFromTextgrid.convertCorpusToKanaAndRomaji() that will probably "
                "fix the problem." %
                self.encoding)


def _formdamage(sent):
    rectify = []
    for ch in sent:
        try:
            rectify.append(ch.encode('euc-jp'))
        except:
            pass
    return ''.join(rectify)


def cabocha(sentence, cabochaEncoding, cabochaPath=None):
    '''
    Sends the sentence to be processed by cabocha

    /cabochaEncoding/ is either 'jis-shift', 'utf-8', or 'euc-jp',
    whichever cabocha was installed with
    '''

    if cabochaPath is None:
        cabochaPath = "cabocha"  # Assumes cabocha is in user path

    temp = tempfile.NamedTemporaryFile(delete=False)

    try:
        sentence = sentence.encode(cabochaEncoding)
    except:
        sentence = _formdamage(sentence)

    temp.write(sentence)
    temp.close()

    command = [cabochaPath, '-f', '3', temp.name]
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE)
    except OSError:
        raise CabochaNotRunError(" ".join(command))
    output = process.communicate()[0]
    os.unlink(temp.name)

    try:
        retStr = unicode(output, cabochaEncoding)
    except NameError:  # unicode() does not exist in python 3
        try:
            retStr = str(output, cabochaEncoding)
        except UnicodeDecodeError:
            raise TextDecodingError(cabochaEncoding)

    return retStr


def jReads(target_sent, cabochaEncoding, cabochaPath):

    xmlStr = cabocha(target_sent, cabochaEncoding, cabochaPath).encode('utf-8')
#     print(target_sent)
#     print(xmlStr)
    try:
        sentence = etree.fromstring(xmlStr)
    except etree.ParseError:
        raise CabochaOutputError(xmlStr)

    retJReadsToks = []
    retWordList = []

    keyList = list(convertKana.kataToRomajiDict.keys())
    validKatakanaList = [u"ャ", u"ュ", u"ョ", u"ッ", u"ァ", u"ィ",
                         u"ゥ", u"ェ", u"ォ", u"ー", ] + keyList
#     validHiraganaList = [u"ゃ", u"ゅ", u"ょ", u"っ"] + convertKana.kanaToRomajiDict.keys()
    for chunk in sentence:
        jReadsToks = []
        wordList = []
        for tok in chunk.findall('tok'):

            # Determine if this word is punctuation (and if so, skip it)
            # Contains syntactic and morphological information
            featureStr = tok.get("feature")
            featureList = featureStr.split(',')
            if featureList[0] == u"記号":
                continue

            # Don't process empty words (can happen a lot,
            # depending on the annotation scheme)
            word = tok.text.strip()
            if word == "":
                continue

            kana = featureList[-1]

            if kana != '*':
                jReadsToks.append(kana)
            else:
                # Map all hiragana to katakana (in what situations would a
                # hiragana word not appear in our dictionary?
                word = convertKana.convertKanaToKata(word)

                # If the text is all katakana, keep it,
                # otherwise, assume an error
                if (all([char in validKatakanaList for char in word])):
                    jReadsToks.append(word)
                else:
                    raise UnidentifiedJapaneseText(target_sent, word)

            wordList.append(word)

        retJReadsToks.append(jReadsToks)
        retWordList.append(wordList)

    return retJReadsToks, retWordList


def getChunkedKana(string, cabochaEncoding, cabochaPath):

    if string == "":
        raise EmptyStrError()

    kanaList, wordList = jReads(string, cabochaEncoding, cabochaPath)
    kanaList = ["".join(subList) for subList in kanaList if len(subList) > 0]
    wordList = ["".join(subList) for subList in wordList if len(subList) > 0]

    # Special case - sometimes 'ー' ends up in its own word or at the start
    # of a word, but really it just makes the last vowel longer.  If its
    # by itself, attach it to the previous word
    def mergeTailingVowel(tmpList):
        retList = []
        for word in tmpList:
            if word[0] == u"ー":
                retList[-1] += word
            else:
                retList.append(word)
        return retList

    kanaList = mergeTailingVowel(kanaList)
    wordList = mergeTailingVowel(wordList)

    vowelList = [u"ア", u"イ", u"ウ", u"エ", u"オ"]
    vowelModifierDict = {u"ァ": u"a", u"ィ": u"i", u"ゥ": u'u',
                         u"ェ": u"e", u"ォ": u'o'}
    yModifierDict = {u"ャ": u"ya", u"ュ": u"yu", u"ョ": u"yo"}

    romanjiedTextList = []
    for word in kanaList:

        # Sanitize kana
        try:
            kanaInputList = chunkKatakana(word)
        except IndexError:
            raise ChunkingError(word)

        # Convert kana to romanji
        romanjiList = []
        for kana in kanaInputList:

            # Over-write the previous vowel (foreign words)
            if kana in vowelModifierDict.keys():
                romanjiList[-1] = (romanjiList[-1][:-1] +
                                   vowelModifierDict[kana])

            # Last vowel is a long vowel
            elif kana == u'ー':  # Long vowel
                # e.g. 'ホーー' becomes "ho::" or 'ふうんー' becomes "hu:n:"
                #  -- both bad
                if romanjiList[-1][-1] != ":" and romanjiList[-1][-1] != "N":
                    romanjiList[-1] += ":"

                # Should get recognized as a single vowel by the forced aligner

            # Normal case
            else:
                # Single-phone characters
                if kana == u"ン" or kana in vowelList:
                    romanjiList.append(convertKana.kataToRomajiDict[kana])
                else:
                    if kana in yModifierDict.keys():  # e.g. 'ィ' in 'ティム'
                        romanjiList.pop(-1)
                        syllable = yModifierDict[kana]
                    else:
                        try:
                            # Normal case for two-phone characters
                            syllable = convertKana.kataToRomajiDict[kana]
                        except KeyError:
                            raise NonKatakanaError(kana, string)

                    # The consonant (e.g. 's' or 'sh')
                    romanjiList.append(syllable[:-1])
                    # The vowel
                    romanjiList.append(syllable[-1])

        romanjiedTextList.append(" ".join(romanjiList))

    return wordList, kanaList, romanjiedTextList


def chunkKatakana(kanaStr):
    '''
    Chunks katakana for use in the katakana chart
    '''
    kanaList = list(kanaStr)

    returnList = []
    i = 0
    while i < len(kanaStr):
        kana = kanaList[i]
        # Some palatalized consonants are in our chart
        # (notably 'jy' and 'shy' are missing)
        kanaFlag = kana in [u"ャ", u"ュ", u"ョ"]
        if kanaFlag and returnList[-1] + kana in convertKana.kataToRomajiDict.keys():
            returnList[-1] += kana
        elif kana == u'ッ':  # Geminate consonant
            pass
        else:  # Normal case
            returnList.append(kana)
        i += 1

    return returnList
