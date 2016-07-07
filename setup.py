#!/usr/bin/env python
# encoding: utf-8
'''
Created on Aug 29, 2014

@author: tmahrt
'''
import os
import codecs
from distutils.core import setup
setup(name='pyJulius',
      version='1.0.0',
      author='Tim Mahrt',
      author_email='timmahrt@gmail.com',
      package_dir={'pyjulius': os.path.join('src', "pyjulius")},
      packages=['pyjulius'],
      package_data={'pyjulius': ["hiraganaChart.txt", "katakanaChart.txt"]},
      license='LICENSE',
      long_description=codecs.open('README.rst', 'r', encoding="utf-8").read(),
      requires=["praatio (>=2.1.0)",  # https://github.com/timmahrt/praatIO
                "jNlp"  # https://github.com/kevincobain2000/jProcessing
                ],
      )
