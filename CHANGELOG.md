
# PyJuliusAlign Changelog

*PyJuliusAlign uses semantic versioning (Major.Minor.Patch)*

Ver 4.0.0 (July, 15, 2023)
- Remove support for python 2.x

Ver 3.1.0 (August 21, 2021)
- Added alignFromTextgrid.segmentPhrasesOnSmallPause for avoided problems with small pauses
  - it is a very fuzzy process thats guesses and makes assumptions -- feedback is helpful!
  - (see align_example.py and new test file introduction_one_line.TextGrid)
- Requires a new python library (pydub)

Ver 3.0.0 (October 11, 2020)
- Fixed a bug preventing the use of triphone models.
- Requires a new python library (python-Levenshtein)

Ver 2.0 (January 12, 2019)
- pyJuliusAlign now works with the latest version of Julius and the Julius Segmentation Kit.
  - If you need to use the old segmentation kit (segment_julius4.pl), please use pyJuliusAlign ver 1.1
- Quality of life improvements + documentation

Ver 1.1 (August 12, 2018)
- Python 3.x support

Ver 1.0 (September 2, 2014)
- Users can force-align words and phones for transcribed speech in Japanese
