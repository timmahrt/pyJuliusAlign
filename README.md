
# pyJuliusAlign

 [![](https://badges.gitter.im/pyJuliusAlign/Lobby.svg)](https://gitter.im/pyJuliusAlign/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) [![](https://img.shields.io/badge/license-MIT-blue.svg?)](http://opensource.org/licenses/MIT) [![](https://img.shields.io/pypi/v/pyjuliusalign.svg)](https://pypi.org/project/pyjuliusalign/)

*Questions?  Comments?  Feedback?  Chat with us on gitter!*

-----

A python interface to Julius, the speech recognition system.

**The primary function right now is the Japanese forced aligner.**  Given the transcript for an audio file in Japanese, this series of scripts will estimate where those phones were produced in the audio.

*/examples/align_example.py* should be sufficient for a large number of cases.

*/pyjuliusalign/alignFromTextgrid.py* provides a good example of building your own custom alignment code (with different inputs and outputs than textgrids).  


Here is a cropped view of the before and after output file in the example files:

![PyJuliusAlign example](./examples/files/pyjulius_example.png)

# Table of contents
1. [Major Revisions](#major-revisions)
2. [Requirements](#requirements)
  * [Mac-specific Requirements Information](#mac-specific-requirements-information)
  * [Windows-specific Requirements Information](#windows-specific-requirements-information)
3. [Installation](#installation)
4. [Testing Installation](#testing-installation)
5. [Example Usage](#example-usage)
6. [Troubleshooting](#troubleshooting)


## Major Revisions

Ver 2.0 (January 12, 2019)
- pyJuliusAlign now works with the latest version of Julius and the Julius Segmentation Kit.
  - If you need to use the old segmentation kit (segment_julius4.pl), please use pyJuliusAlign ver 1.1 
- Quality of life improvements + documentation

Ver 1.1 (August 12, 2018)
- Python 3.x support

Ver 1.0 (September 2, 2014)
- Users can force-align words and phones for transcribed speech in Japanese


## Requirements

python - https://www.python.org/

pyPraat - https://github.com/timmahrt/pyPraat
 - for textgrid manipulations

Julius - https://github.com/julius-speech/julius
 - the speech recognition engine
 - pyJuliusAlign has been tested with Julius 4.5, released on January 2nd, 2019.

Julius Segmentation Kit - https://github.com/julius-speech/segmentation-kit
 - it's not a file you "install" but something you'll want to put in a stable folder where you can access it when needed

Change line 33 to:
```perl
## data directory
$datadir = "./wav";
if (defined $ARGV[0]) {
  $datadir = $ARGV[0];
}
```

Also in the configuration section, I recommend setting `$hmmdefs` to an absolute path e.g. `$hmmdefs="/Users/tmahrt/segmentation-kit/models/hmmdefs_monof_mix16_gid.binhmm"; # monophone model`

Sox - http://sox.sourceforge.net/
 - Converts the sampling frequency of the audio if needed.
 - Optional.  If you choose to not install sox, you'll need to make sure your audio files are at the same sampling frequency as the model data (the included data is 14khz)
 - If you forced the script to run Julius on audio that has a different sampling frequency, the aligner would completely fail.

Cabocha - http://taku910.github.io/cabocha/ 
 - used to convert typical Japanese text into romaji/phones.
 - (throw it into google translate if you need it in English)
 - make a note of which encoding you use for the dictionary file--you'll need it in the code

Perl (for Julius)


### Mac-specific Requirements Information

I use a mac and was able to easily install many requirements using Homebrew.  Here are some guides that I found useful (they translate well enough from Japanese using google translate):
 - Sox https://qiita.com/samurai20000@github/items/2af98b6c468af317bb09
 - Cabocha https://qiita.com/musaprg/items/9a572ad5c4e28f79d2ae
 - I manually built Julius using the configure and make scripts included in that project


### Windows-specific Requirements Information

I currently don't have access to a Windows machine. Earlier, I tested installation and got as far as running Julius. Perl tried to run gzip which I couldn't get to install.

One user was able to get it working on Windows by installing cygwin and adding cygwin to the path in environment variables.  Also, they had to install MeCab before running Cabocha, otherwise, they would receive an exception saying there's something wrong with Cabocha.


## Installation

PyJuliusAlign is on pypi and can be installed or upgraded from the command-line shell with pip like so::

    python -m pip install pyjuliusalign --upgrade

Otherwise, to manually install, after downloading the source from github, from a command-line shell, navigate to the directory containing setup.py and type::

    python setup.py install

If python is not in your path, you'll need to enter the full path e.g.::

	C:\Python36\python.exe setup.py install


## Testing Installation

In the folder 'examples' run the file 'align_example.py'.

If sox, cabocha, julius, and perl are all in your path, you won't need to specify them in any of the arguments--leave them with your default values. Otherwise, you'll need to specify the full path of their bin/executable files.

If you have difficulties running the code without specifying the full path, try using the full paths anyways.

Also, you will need to configure "segment_julius.pl" which is a part of the Julius Segmentation Kit.


## Example Usage

Please see /examples for an example usage.

There is pretty much only one way to use this library at the moment. Please contact me if you are having difficulties using this library.


## Troubleshooting

The scripts should catch any issues along the way with the exception of  issues stemming from Julius.  If you get bogus/null results, most likely Julius hasn't been set up correctly.

The Julius Segmentation kit comes with an example.  If you can force align that, then you should be able to force align using this script as well.



