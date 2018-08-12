
-----------
pyJulius
-----------

.. image:: https://img.shields.io/badge/license-MIT-blue.svg?
   :target: http://opensource.org/licenses/MIT

A python interface to Julius, the speech recognition system.

**The primary function right now is the Japanese forced aligner.**  Given the transcript
for an audio file in Japanese, this series of scripts will estimate where those 
phones were produced in the audio.

/test/align_example.py should be sufficient for a large number of cases.

/src/pyjulius/alignFromTextgrid.py provides a good example of building your own custom
alignment code (with different inputs and outputs than textgrids).  


Here is a cropped view of the before and after output file in the example files:

.. image:: examples/files/pyjulius_example.png
   :width: 500px

.. sectnum::
.. contents::


Important notice
==================

I have tested this on Mac OS X.  I think it should work fine on other Unix systems.

On *Windows*, I tested it and got as far as running Julius.  Perl tried to run gzip
which I couldn't get to install.

One user was able to get it working on Windows by installing cygwin and adding
cygwin to the path in environment variables.  Also, they
had to install MeCab before running Cabocha, otherwise, they would
receive an exception saying there's something wrong with Cabocha.


Julius new version vs old version
==================================

Around 2015, Julius was moved to github (https://github.com/julius-speech/segmentation-kit).
I have not tried this version yet.  There is also a new version of the Julius Segmentation Kit with
a new script (segment_julius.pl).  It will not work.  For the moment, please use segment_julius4.pl
supplied with the older code.

With the file segment_julius4.pl you'll need to change line 69 to `push(@words, $_);`

Please do not use segment_julius.pl which is available on the newer github site.


Major revisions
================

Ver 1.1 (August 12, 2018)

- Python 3.x support


Ver 1.0 (September 2, 2014)

- Users can force-align words and phones for transcribed speech in Japanese


Prerequisites
==================

python - https://www.python.org/

pyPraat - https://github.com/timmahrt/pyPraat

 * for textgrid manipulations

Julius - http://julius.sourceforge.jp/en_index.php?q=index-en.html

 * the speech recognition engine

 * you'll also need to download the /Julius Segmentation Kit/, which is available on
   the same page.  It's not a file you "install" but something you'll want to put
   in a stable folder where you can access it when needed

Sox - http://sox.sourceforge.net/

 * Converts the sampling frequency of the audio if needed.

 * Optional.  If you choose to not install sox, you'll need to make sure your audio
   files are at the same sampling frequency as the model data (the included data is
   14khz)
   
 * If you forced the script to run Julius on audio that has a different sampling
   frequency, the aligner would completely fail.

Cabocha - https://code.google.com/p/cabocha/ 

 * used to convert typical Japanese text into romaji/phones.

 * (throw it into google translate if you need it in English)

 * make a note of which encoding you use for the dictionary file--you'll need it in the code

Perl (for Julius)



Installation
==================

From a command-line shell, navigate to the directory this is located in 
and type::

    python setup.py install

If python is not in your path, you'll need to enter the full path e.g.::

    C:\Python27\python.exe setup.py install


Testing installation
=====================

In the folder 'examples' run the file 'align_example.py'.

If sox, cabocha, julius, and perl are all in your path, you won't need
to specify them in any of the arguments--leave them with your default values.
Otherwise, you'll need to specify the full path of their bin/executable files.

If you have difficulties running the code without specifying the full path, try using the
full paths anyways.

Also, you will need to configure "segment_julius4.pl" which is a part of the
Julius Segmentation Kit.  (The more recent "segment_julius.pl" available on
github will not work.  Please use the version available on the old julius website.)


Example usage
==================

Please see \\test for an example usage.  

There is pretty much only one way to use this library at the moment.  
Please contact me if you are having difficulties using this library.


Troubleshooting
==================

The scripts should catch any issues along the way with the exception of 
issues stemming from Julius.  If you get bogus/null results, most likely Julius
hasn't been set up correctly.

The Julius Segmentation kit comes with an example.  If you can force align that,
then you should be able to force align using this script as well.



