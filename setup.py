#!/usr/bin/env python

import setuptools

setuptools.setup(name='aisdownsampler',
      version='0.1',
      description='Streaming downsampler of NMEA AIS data',
      long_description='Streaming downsampler of NMEA AIS data',
      long_description_content_type="text/markdown",
      author='Saghar Asadi',
      author_email='saghar@innovationgarage.no',
      url='https://github.com/innovationgarage/ElCheapoAIS-aisdownsampler',
      packages=setuptools.find_packages(),
      install_requires=[
          'libais==0.17',
          'socket-tentacles',
          'click',
          'click-datetime'
      ],
      include_package_data=True,
      entry_points='''
      [console_scripts]
      elcheapoais-downsampler = aisdownsampler.cli:main
      '''
  )
