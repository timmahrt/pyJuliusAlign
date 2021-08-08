#!/usr/bin/env python
# encoding: utf-8
"""
Created on Aug 29, 2014

@author: tmahrt
"""
from setuptools import setup
import io

setup(
    name="pyjuliusalign",
    version="3.0.1",
    author="Tim Mahrt",
    author_email="timmahrt@gmail.com",
    url="https://github.com/timmahrt/pyJuliusAlign",
    package_dir={"pyjuliusalign": "pyjuliusalign"},
    packages=["pyjuliusalign"],
    package_data={"pyjuliusalign": ["hiraganaChart.txt", "katakanaChart.txt"]},
    license="LICENSE",
    description="A helper library for doing forced-alignment in Japanese with Julius.",
    install_requires=["praatio ~= 4.1", "python-Levenshtein"],
    long_description=io.open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
)
