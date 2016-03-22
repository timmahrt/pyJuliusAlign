
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


.. sectnum::
.. contents::


Important notice
==================

I have tested this on Mac OS X.  I think it should work fine on other Unix systems.

On *Windows*, I tested it and got as far as running Julius.  Perl tried to run gzip
which I couldn't get to install.  If you can get it working, then this should code
should run fine on Windows.  Any feedback or comments would be appreciated.


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

In the folder 'test' open the folder align.

If sox, cabocha, julius, and perl are all in your path, you won't need
to specify them in any of the arguments--leave them with your default values.
Otherwise, you'll need to specify the full path of their bin/executable files.

Also, you will need to configure "segment_julius4.pl" which is a part of the
Julius Segmentation Kit.


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



