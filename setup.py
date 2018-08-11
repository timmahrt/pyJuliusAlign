#!/usr/bin/env python
# encoding: utf-8
'''
Created on Aug 29, 2014

@author: tmahrt
'''
from setuptools import setup
import io
import os
setup(name='pyjulius',
      version='1.1.0',
      author='Tim Mahrt',
      author_email='timmahrt@gmail.com',
      url='https://github.com/timmahrt/pyJulius',
      package_dir={'pyjulius':os.path.join('src', 'pyjulius')},
      packages=['pyjulius'],
      package_data={'pyjulius': ["hiraganaChart.txt", "katakanaChart.txt"]},
      license='LICENSE',
      description='A helper library for doing forced-alignment in Japanese with Julius.',
      long_description=io.open('README.rst', 'r', encoding="utf-8").read(),
#       install_requires=[], # No requirements! # requires 'from setuptools import setup'
      )
