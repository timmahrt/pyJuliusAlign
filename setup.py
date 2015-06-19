'''
Created on Aug 29, 2014

@author: tmahrt
'''
import os
from distutils.core import setup
setup(name='pyJulius',
      version='1.0.0',
      author='Tim Mahrt',
      author_email='timmahrt@gmail.com',
      package_dir={'pyjulius':os.path.join('src', "pyjulius")},
      packages=['pyjulius'],
      package_data = {'pyjulius':["hiraganaChart.txt", "katakanaChart.txt"]},
      license='LICENSE',
      long_description=open('README.rst', 'r').read(),
      install_requires=[
                        "pypraat", # https://github.com/timmahrt/pyPraat
                        "jNlp" # https://github.com/kevincobain2000/jProcessing
                        ],    
      )