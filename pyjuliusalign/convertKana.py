
import io
import os
from os.path import join

jNlp_KATAKANA_CHART_PATH = join(os.path.dirname(__file__), "katakanaChart.txt")
jNlp_HIRAGANA_CHART_PATH = join(os.path.dirname(__file__), "hiraganaChart.txt")


def parseChart(chartFN):
    """
    @return chartDict
    ��� ==> g,a
    ��� ==> k,i
    ������ ==> k,ya
    Similarily for Hiragana
    @setrofim : http://www.python-forum.
     org/pythonforum/viewtopic.php?f=3&t=31935
    """
    with io.open(chartFN, "r", encoding="utf-8") as fd:
        chart = fd.read()

    lines = chart.split('\n')
    chartDict = {}
    output = {}
    col_headings = lines.pop(0).split()
    for line in lines:
        cells = line.split()
        for i, c in enumerate(cells[1:]):
            output[c] = cells[0], col_headings[i]

    for k in sorted(output.keys()):
        # @k = katakana
        # @r = first romaji in row
        # @c = concatinating romaji in column
        r, c = output[k]
        if k == 'X':
            continue
        romaji = ''.join([item.replace('X', '') for item in [r, c]])
        chartDict[k] = romaji

    return chartDict


def _invertDict(tmpDict):
    '''Flips key-value relationship in a dictionary'''
    retDict = {}
    for key, value in tmpDict.items():
        retDict[value] = key

    return retDict


def _getKataToKanaDict():
    retDict = {u"ャ": u"ゃ", u"ュ": u"ゅ", u"ョ": u"ょ", u"ッ": u"っ",
               u"ァ": u"ぁ", u"ィ": u"ぃ", u"ゥ": u"ぅ", u"ェ": u"ぇ", u"ォ": u"ぉ",
               }

    for kata in kataToRomajiDict.keys():
        kana = romajiToKanaDict[kataToRomajiDict[kata]]
        retDict[kata] = kana

    return retDict


kataToRomajiDict = parseChart(jNlp_KATAKANA_CHART_PATH)
kanaToRomajiDict = parseChart(jNlp_HIRAGANA_CHART_PATH)
romajiToKataDict = _invertDict(kataToRomajiDict)
romajiToKanaDict = _invertDict(kanaToRomajiDict)
kataToKanaDict = _getKataToKanaDict()
kanaToKataDict = _invertDict(kataToKanaDict)


def convertKanaToKata(inputStr):
    '''Input hiragana and return the corresponding string in katakana'''
    retStr = u""
    for char in inputStr:
        if char in kanaToKataDict.keys():
            char = kanaToKataDict[char]
        retStr += char

    return retStr


def convertKataToKana(inputStr):
    '''Input hiragana and return the corresponding string in katakana'''
    retStr = u""
    for char in inputStr:
        if char in kataToKanaDict.keys():
            char = kataToKanaDict[char]
        retStr += char

    return retStr
